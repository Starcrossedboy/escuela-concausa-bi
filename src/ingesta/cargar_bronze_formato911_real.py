"""Parsea el CSV real de DS-01 Formato 911 (uno o mas ciclos, ya descargados a mano por
Diana Alvarez Varela desde la fuente oficial, ver DS-01_Formato_911.md SS9), y lo carga a
bronze.formato911_2024_2025 en Postgres.

Reemplaza el uso de cargar_bronze_fixture.py para esta tabla: ese script es solo para fixtures
de desarrollo (<=500 filas, ver su propio docstring). Este es el cargador real de produccion
para el archivo nacional completo (~230k filas). Reutiliza la funcion cargar_fixture() de
cargar_bronze_fixture.py para el INSERT a Postgres (DDL + ON CONFLICT DO NOTHING ya
probados) -- no duplica esa logica, solo la alimenta con el CSV ya transformado al esquema
esperado.

Decisiones tomadas aqui, ninguna adivinada en silencio (ver detalle abajo):

1. GRANO: el archivo real es CCT x turno (una escuela puede reportar matutino y vespertino
   por separado). bronze.formato911_2024_2025 fue disenada para una fila por (cct, ciclo) --
   silver/matricula.sql dedupea con row_number() partition by (cct, ciclo), no por turno. Cargar
   el archivo crudo tal cual haria que Silver descarte en silencio uno de los turnos. Por eso
   este script SUMA alumnos_total/docentes_total/grupos_total por cct antes de cargar -- mismo
   principio que ya aplica el pipeline historico (silver.matricula_historica suma por turno),
   solo que aqui se hace un paso antes porque el schema de esta tabla nunca contemplo turno.

2. COLUMNA DE DOCENTES: el CSV real trae dos candidatos -- tot_doc (pareja docente_h/docente_m)
   y tot_doc_p (pareja t_doc_p_h/t_doc_p_m). Se eligio tot_doc por ser el nombre generico sin
   sufijo, mas consistente con "Plantilla docente" (DS-01_Formato_911.md SS5). Es una decision,
   no una confirmacion contra un diccionario de datos oficial de la SEP -- si aparece uno,
   validar aqui antes de un uso critico de docentes_total (hoy ese campo no alimenta ningun
   modelo de riesgo, solo el hecho central).

3. CICLO: no existe como columna en el archivo (cada distribucion es de un solo ciclo) -- se
   recibe por --ciclo y no se adivina del nombre del archivo, igual que hace
   extractor_formato911_historico.py por cada URL. Verificado real (ver DS-01_Formato_911.md
   SS9) que las columnas fijas (clave_cct/clavecct, entidad, municipio, nivel, turno, insc_t,
   tot_doc, gpos_t) son identicas entre 2024-2025 y 2023-2024 -- no hace falta remapear nada
   por ciclo, solo el nombre del archivo y el valor de ciclo/URL.

4. VALORES NO NUMERICOS EN insc_t/tot_doc/gpos_t: fallan explicito (_coercer_metrica_o_fallar),
   nunca se asumen como 0. Un cero silencioso en alumnos_total falsearia el hecho central del
   proyecto (una escuela con "0 alumnos" por un dato sucio se veria como una desercion total).
   Verificado real (DS-01_Formato_911.md SS9): 0 filas no numericas en los 6 ciclos comparados
   a mano -- si eso deja de ser cierto en un ciclo futuro, este script debe detenerse y pedir
   revision a mano, no inventar un manejo de nulo nunca observado en la fuente real.

Uso:
    python -m src.ingesta.cargar_bronze_formato911_real --csv /Users/diana/Downloads/educacion_basica_2024_2025.csv --ciclo 2024-2025
    python -m src.ingesta.cargar_bronze_formato911_real --csv /Users/diana/Downloads/ESTANDAR_BASICA_I2324.csv --ciclo 2023-2024
"""
import argparse
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.ingesta.cargar_bronze_fixture import cargar_fixture

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-01_FORMATO911"

# URLs verificadas a mano por Diana (ver extractor_formato911_historico.py) -- una por ciclo,
# no hay formula derivable entre ellas.
SOURCE_URL_POR_CICLO = {
    "2019-2020": "https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2019-2020.csv",
    "2020-2021": "https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2020-2021.csv",
    "2021-2022": "https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2021-2022.csv",
    "2022-2023": "https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2022-2023.csv",
    "2023-2024": "https://repodatos.atdt.gob.mx/s_educacion_publica/f911/ESTANDAR_BASICA_I2324.csv",
    "2024-2025": (
        "https://repodatos.atdt.gob.mx/api_update/secretaria_educacion/"
        "registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/"
        "educacion_basica_2024_2025.csv"
    ),
}

# Mismo patron que extractor_formato911_historico.py: no adivinar el nombre de la columna
# llave de escuela, detectar entre variantes conocidas y fallar explicito si no aparece
# ninguna.
VARIANTES_COLUMNA_CCT = ["clave_cct", "clavecct"]

COLUMNAS_FIJAS_REQUERIDAS = ["entidad", "municipio", "nivel", "turno", "insc_t", "tot_doc", "gpos_t"]

COLUMNAS_BRONZE = [
    "cct", "ciclo", "entidad", "municipio", "nivel",
    "alumnos_total", "docentes_total", "grupos_total",
    "_ingested_at", "_source", "_source_url",
]


def _detectar_columna_cct(columnas_csv: list) -> str:
    for variante in VARIANTES_COLUMNA_CCT:
        if variante in columnas_csv:
            return variante
    raise ValueError(
        f"{SOURCE_NAME}: no se encontro ninguna variante conocida de la columna llave de "
        f"escuela ({VARIANTES_COLUMNA_CCT}) en el archivo. No adivinar -- revisar a mano."
    )


def _validar_columnas_fijas(columnas_csv: list) -> None:
    faltantes = [c for c in COLUMNAS_FIJAS_REQUERIDAS if c not in columnas_csv]
    if faltantes:
        raise ValueError(
            f"{SOURCE_NAME}: faltan columnas esperadas en el archivo real: {faltantes}. "
            f"No se asume su ausencia como dato vacio -- revisar el archivo a mano."
        )


def _coercer_metrica_o_fallar(serie: pd.Series, columna_origen: str) -> pd.Series:
    """Convierte insc_t/tot_doc/gpos_t (texto) a entero. Nunca usa fillna(0): un valor no
    numerico ahi no significa "cero alumnos/docentes/grupos" -- significa un dato corrupto o
    inesperado en el archivo. Silenciarlo como 0 falsearia alumnos_total, el hecho central del
    proyecto (Data_Model.md: "SIN_DATO explicito, nunca cero ni nulo silencioso"). Verificado
    real (DS-01_Formato_911.md SS9): 0 filas no numericas en los 6 ciclos comparados a mano --
    por eso la decision correcta hoy es fallar explicito si eso cambia, no adivinar un manejo
    de nulo nunca observado en la fuente real."""
    numerico = pd.to_numeric(serie, errors="coerce")
    malos = numerico.isna()
    if malos.any():
        ejemplos = sorted(set(serie[malos]))[:5]
        raise ValueError(
            f"{SOURCE_NAME}: {int(malos.sum())} valor(es) no numericos en la columna "
            f"'{columna_origen}' (ejemplos: {ejemplos}). No se asumen como 0 -- revisar el "
            f"archivo a mano."
        )
    return numerico.astype(int)


def parsear_y_agregar(ruta_csv: str, ciclo: str) -> pd.DataFrame:
    """Lee el CSV real (crudo, grano cct x turno) de un ciclo dado, valida columnas sin
    adivinar, y agrega (SUMA) alumnos/docentes/grupos por cct para que el resultado tenga el
    grano que espera bronze.formato911_2024_2025 / silver.matricula.sql (una fila por cct).

    Verificado real contra dos ciclos (2024-2025 y 2023-2024, ver DevLog): las columnas fijas
    (clave_cct/clavecct, entidad, municipio, nivel, turno, insc_t, tot_doc, gpos_t) son
    identicas entre ambos -- no hace falta remapear nada por ciclo."""
    encabezado = pd.read_csv(ruta_csv, dtype=str, keep_default_na=False, nrows=0)
    columnas_csv = list(encabezado.columns)

    columna_cct = _detectar_columna_cct(columnas_csv)
    _validar_columnas_fijas(columnas_csv)

    columnas_a_leer = [columna_cct, "entidad", "municipio", "nivel", "turno", "insc_t", "tot_doc", "gpos_t"]
    df = pd.read_csv(ruta_csv, dtype=str, keep_default_na=False, usecols=columnas_a_leer)

    crudo = pd.DataFrame({
        "cct": df[columna_cct],
        "entidad": df["entidad"],
        "municipio": df["municipio"],
        "nivel": df["nivel"],
        "alumnos_total": _coercer_metrica_o_fallar(df["insc_t"], "insc_t"),
        "docentes_total": _coercer_metrica_o_fallar(df["tot_doc"], "tot_doc"),
        "grupos_total": _coercer_metrica_o_fallar(df["gpos_t"], "gpos_t"),
    })

    # Agregacion por cct: SUMA de las 3 metricas a traves de turnos (ver punto 1 del docstring).
    # entidad/municipio/nivel se toman del primer turno -- son constantes por cct en el archivo
    # real (una escuela no cambia de municipio/nivel entre turnos).
    agregado = crudo.groupby("cct", as_index=False).agg({
        "entidad": "first",
        "municipio": "first",
        "nivel": "first",
        "alumnos_total": "sum",
        "docentes_total": "sum",
        "grupos_total": "sum",
    })

    ingested_at = datetime.now(timezone.utc)
    agregado["ciclo"] = ciclo
    agregado["_ingested_at"] = ingested_at.isoformat()
    agregado["_source"] = SOURCE_NAME
    agregado["_source_url"] = SOURCE_URL_POR_CICLO[ciclo]

    return agregado[COLUMNAS_BRONZE]


def cargar(ruta_csv: str, ciclo: str, tabla: str = "formato911_2024_2025") -> int:
    df = parsear_y_agregar(ruta_csv, ciclo)
    n_cct = df["cct"].nunique()
    logger.info("%s (%s): %d filas (1 por cct) tras agregar por turno, %d cct unicos", SOURCE_NAME, ciclo, len(df), n_cct)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        df.to_csv(tmp.name, index=False)
        tmp_path = tmp.name

    try:
        insertadas = cargar_fixture(tmp_path, tabla, esquema="formato911")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return insertadas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="Ruta al CSV real ya descargado (ver DS-01_Formato_911.md SS9)")
    parser.add_argument("--ciclo", required=True, choices=sorted(SOURCE_URL_POR_CICLO), help="Ciclo escolar del archivo")
    parser.add_argument("--tabla", default="formato911_2024_2025")
    args = parser.parse_args()

    n = cargar(args.csv, args.ciclo, args.tabla)
    print(f"OK: {n} filas nuevas cargadas en bronze.{args.tabla} (ciclo {args.ciclo})")