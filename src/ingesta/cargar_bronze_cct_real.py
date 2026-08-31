"""Parsea el CSV real de DS-02 SEP Catalogo CCT (dos partes, ya descargadas a mano por Diana
Alvarez Varela desde SIGED -- https://www.siged.sep.gob.mx/SIGED/datos_abiertos.html, seccion
"Descarga del Catalogo de Centros de Trabajo", ver DS-02_Catalogo_CCT.md SS9), y lo carga a
bronze.<tabla> en Postgres.

El catalogo llega partido por rango de entidad: *_01_16_CSV.zip (entidades 01-16) y
*_17_32_CSV.zip (entidades 17-32). Hay que cargar los DOS -- de las 4 SCOPE_ENTIDADES del
proyecto, Nuevo Leon (19) cae solo en el segundo archivo.

Reutiliza cargar_fixture() de cargar_bronze_fixture.py (esquema="cct", ya definido con su DDL
propio) para el INSERT a Postgres -- no duplica esa logica, solo la alimenta con los dos CSV ya
transformados al esquema esperado por bronze.cct / silver/escuela.sql.

Decisiones tomadas aqui, ninguna adivinada en silencio (ver detalle abajo):

1. ENCODING: el CSV real de SIGED no es UTF-8 (acentos/enies llegan corruptos si se lee como
   tal -- verificado a mano, ver DS-02_Catalogo_CCT.md SS9). Se lee con encoding="latin-1",
   que sí decodifica el archivo correctamente.

2. FILTRO DE TIPO: el catalogo de "Centros de Trabajo" no es solo escuelas -- trae tambien
   supervisiones de zona, jefaturas de sector, bibliotecas, centros de maestros, etc. Se filtra
   por C_TIPO == "ESCUELA" (valor exacto verificado contra el archivo real, sin variantes de
   mayusculas). OJO: "ESCUELA" por si solo NO implica basica -- tambien incluye MEDIA SUPERIOR,
   SUPERIOR, INICIAL, CAM y FORMACION PARA EL TRABAJO (verificado con value_counts() real). El
   segundo filtro (punto 3) es el que de verdad acota a basica.

3. FILTRO DE NIVEL: el proyecto opera sobre educacion basica -- verificado contra el fixture
   real de DS-01 (tests/fixtures/bronze_formato911_sample.csv, 73 filas): los unicos valores de
   `nivel` que trae son PREESCOLAR/PRIMARIA/SECUNDARIA. Aqui se filtra
   TIPONIVELSUB_C_SERVICION2 a esos tres valores exactos -- no se adivina un cuarto valor
   "valido" ni se incluye MEDIA SUPERIOR aunque tambien sea C_TIPO=="ESCUELA" en algunos casos.

4. ENTIDAD: NO se filtra por SCOPE_ENTIDADES aqui -- Bronze/Silver son nacionales por
   convencion del proyecto (Data_Model.md SS7), el acotamiento a las 4 entidades del alcance
   pasa hasta Gold (dim_escuela.sql via scope_entidades()). Los dos archivos juntos ya cubren
   las 32 entidades.

5. MUNICIPIO: INMUEBLE_CV_MUN en el archivo real es el codigo LOCAL de 3 digitos (CHAR(3) por
   el diccionario de datos), no la clave INEGI de 5 digitos que usa el resto del proyecto. No
   se concatena aqui -- se carga tal cual junto con `entidad`, y es
   normalize_cve_mun(cve_ent, cve_mun) en silver/escuela.sql quien ya sabe concatenar
   entidad(2) + municipio(3) -> cve_mun(5). Concatenar aqui hubiera duplicado esa logica.

6. DUPLICADOS DE CCT: DS-02_Catalogo_CCT.md SS10 anticipaba CCT duplicados por turno. Verificado
   real contra el archivo completo (las 4 SCOPE_ENTIDADES, filtrado por ESCUELA+basica): CERO
   duplicados. Por eso este script no agrega logica de deduplicacion por turno (no hay turno
   que agregar) -- en vez de asumir que eso se mantiene, valida explicito y truena si aparece
   algun duplicado real, en vez de aceptarlo en silencio.

7. COORDENADAS EN 0,0: existen (6 filas en las 4 SCOPE_ENTIDADES, verificado real). Este script
   las carga TAL CUAL vienen (no las convierte a NULL) -- silver/escuela.sql hoy solo nulifica
   cadenas vacias, no ceros literales, asi que "0.000000" pasa como coordenada valida. Es un
   hueco real, no resuelto aqui a proposito (está fuera del alcance de este script tocar
   Silver): documentado como seguimiento pendiente en el DevLog de esta sesion.

Uso:
    python -m src.ingesta.cargar_bronze_cct_real \\
        --csv-01-16 ~/Downloads/CATALOGO_CENTRO_TRABAJO_01_16_CSV.csv \\
        --csv-17-32 ~/Downloads/CATALOGO_CENTRO_TRABAJO_17_32_CSV.csv \\
        --tabla cct_siged_202608
"""
import argparse
import logging
from datetime import datetime, timezone

import pandas as pd

from src.ingesta.cargar_bronze_fixture import cargar_fixture

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-02_CATALOGO_CCT"
SOURCE_URL = "https://www.siged.sep.gob.mx/SIGED/datos_abiertos.html"

NIVELES_BASICA = ["PREESCOLAR", "PRIMARIA", "SECUNDARIA"]

COLUMNAS_CRUDAS_REQUERIDAS = [
    "CV_CCT", "C_NOMBRE", "C_TIPO", "SOSTENIMIENTO_C_CONTROL",
    "INMUEBLE_CV_ENT", "INMUEBLE_CV_MUN", "INMUEBLE_LATITUD", "INMUEBLE_LONGITUD",
    "TIPONIVELSUB_C_SERVICION2",
]

COLUMNAS_BRONZE = [
    "cct", "nombre", "nivel", "sostenimiento", "entidad", "municipio",
    "latitud", "longitud", "_ingested_at", "_source", "_source_url",
]


def _validar_columnas_crudas(columnas_csv: list, ruta: str) -> None:
    faltantes = [c for c in COLUMNAS_CRUDAS_REQUERIDAS if c not in columnas_csv]
    if faltantes:
        raise ValueError(
            f"{SOURCE_NAME}: faltan columnas esperadas en {ruta}: {faltantes}. "
            "No se asume su ausencia como dato vacio -- revisar el archivo a mano."
        )


def _leer_parte(ruta_csv: str) -> pd.DataFrame:
    """Lee una de las dos partes del catalogo (01-16 o 17-32), filtra a escuelas de basica y
    devuelve solo las columnas crudas que interesan (sin renombrar todavia)."""
    encabezado = pd.read_csv(ruta_csv, encoding="latin-1", dtype=str, nrows=0)
    columnas_csv = list(encabezado.columns)
    _validar_columnas_crudas(columnas_csv, ruta_csv)

    df = pd.read_csv(
        ruta_csv, encoding="latin-1", dtype=str, keep_default_na=False,
        usecols=COLUMNAS_CRUDAS_REQUERIDAS, low_memory=False,
    )

    filtrado = df[
        (df["C_TIPO"] == "ESCUELA")
        & (df["TIPONIVELSUB_C_SERVICION2"].isin(NIVELES_BASICA))
    ]
    logger.info(
        "%s: %d filas crudas -> %d escuelas de basica tras filtrar C_TIPO/nivel",
        ruta_csv, len(df), len(filtrado),
    )
    return filtrado


def parsear_y_combinar(ruta_01_16: str, ruta_17_32: str) -> pd.DataFrame:
    """Lee las dos partes del catalogo, las combina, valida que no haya CCT duplicado entre
    ambas (no se espera ninguno -- ver punto 6 del docstring, falla explicito si aparece), y
    devuelve el DataFrame ya con el esquema de bronze.cct."""
    partes = [_leer_parte(ruta_01_16), _leer_parte(ruta_17_32)]
    crudo = pd.concat(partes, ignore_index=True)

    duplicados = crudo["CV_CCT"][crudo["CV_CCT"].duplicated()]
    if not duplicados.empty:
        ejemplos = sorted(set(duplicados))[:5]
        raise ValueError(
            f"{SOURCE_NAME}: {duplicados.nunique()} CCT duplicado(s) entre las dos partes del "
            f"catalogo (ejemplos: {ejemplos}). No se asume cual conservar -- revisar a mano "
            "(DS-02_Catalogo_CCT.md SS10 ya anticipaba este riesgo)."
        )

    ingested_at = datetime.now(timezone.utc)
    salida = pd.DataFrame({
        "cct": crudo["CV_CCT"],
        "nombre": crudo["C_NOMBRE"],
        "nivel": crudo["TIPONIVELSUB_C_SERVICION2"],
        "sostenimiento": crudo["SOSTENIMIENTO_C_CONTROL"],
        "entidad": crudo["INMUEBLE_CV_ENT"],
        "municipio": crudo["INMUEBLE_CV_MUN"],
        "latitud": crudo["INMUEBLE_LATITUD"],
        "longitud": crudo["INMUEBLE_LONGITUD"],
        "_ingested_at": ingested_at.isoformat(),
        "_source": SOURCE_NAME,
        "_source_url": SOURCE_URL,
    })

    return salida[COLUMNAS_BRONZE]


def cargar(ruta_01_16: str, ruta_17_32: str, tabla: str) -> int:
    df = parsear_y_combinar(ruta_01_16, ruta_17_32)
    logger.info("%s: %d escuelas de basica en total (nacional), %d CCT unicos",
                SOURCE_NAME, len(df), df["cct"].nunique())

    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        df.to_csv(tmp.name, index=False)
        tmp_path = tmp.name

    try:
        insertadas = cargar_fixture(tmp_path, tabla, esquema="cct")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return insertadas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-01-16", required=True, help="Ruta al CSV real ya descargado (rango de entidad 01-16)")
    parser.add_argument("--csv-17-32", required=True, help="Ruta al CSV real ya descargado (rango de entidad 17-32)")
    parser.add_argument("--tabla", default="cct_siged_202608")
    args = parser.parse_args()

    n = cargar(getattr(args, "csv_01_16"), getattr(args, "csv_17_32"), args.tabla)
    print(f"OK: {n} filas nuevas cargadas en bronze.{args.tabla}")
