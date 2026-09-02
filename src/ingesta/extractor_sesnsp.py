"""
Extractor de SESNSP (DS-04) — Incidencia delictiva municipal, periodicidad mensual.

La URL oficial de SESNSP (gob.mx) publica el dataset como un link de SharePoint que
exige login de Microsoft, sin descarga pública anónima (ver
`vault/14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva.md`, sección 9). Este extractor usa
en su lugar el mismo dataset servido por la Agencia de Transformación Digital y
Telecomunicaciones (ATDT) — la infraestructura real detrás de `datos.gob.mx` (mismo
host que ya usa `extractor_formato911.py` para DS-01), verificada en vivo el
2026-08-24: HTTP 200, sin login, contenido confirmado idéntico al de SESNSP.

El archivo fuente es "Delitos" (carpetas de investigación, **no** víctimas — resuelve
la nota abierta en `dbt/models/silver/schema.yml` sobre el origen físico de
`conteo`), en formato ANCHO (un mes por columna) y grano fino (municipio × año × mes
× tipo de delito × **subtipo** × **modalidad**). El modelo Silver
(`delitos_municipio.sql`) espera grano (municipio, año, mes, tipo_delito) y hace
dedup por `_ingested_at` -- ese dedup **no suma** filas, así que si Bronze llegara al
grano fino de la fuente, colapsaría subtipo/modalidad perdiendo conteo en vez de
sumarlo. Por eso este extractor agrega (unpivot + `sum`) hasta el grano que Silver
espera antes de escribir Bronze.
"""
import logging
import os
import tempfile
from datetime import datetime, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-04_SESNSP"
SOURCE_URL = "https://repodatos.atdt.gob.mx/api_update/sesnsp/incidencia_delictiva/IDM_NM_dic25.csv"
BRONZE_PATH = "data/bronze/sesnsp"

# El CSV fuente viene en latin-1 (los acentos se corrompen si se lee como UTF-8).
ENCODING_FUENTE = "latin-1"

MESES = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11,
    "Diciembre": 12,
}

COLUMNAS_ID = ["Año", "Clave_Ent", "Cve. Municipio", "Tipo de delito"]
COLUMNAS_LLAVE_AGREGACION = ["Año", "Clave_Ent", "Cve. Municipio", "mes", "Tipo de delito"]

TAMANO_CHUNK = 200_000


def _agregar_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Convierte un chunk de ancho (12 columnas de mes) a largo y suma subtipo/modalidad."""
    largo = chunk.melt(
        id_vars=COLUMNAS_ID,
        value_vars=list(MESES.keys()),
        var_name="mes_nombre",
        value_name="conteo",
    )
    largo["mes"] = largo["mes_nombre"].map(MESES).astype("int64")
    return largo.groupby(COLUMNAS_LLAVE_AGREGACION, as_index=False)["conteo"].sum()


def _derivar_cve_mun_local(cve_ent: str, cve_municipio_completo: str) -> str:
    """
    `Cve. Municipio` de la fuente es `cve_ent` (sin padding) + código local de 3
    dígitos concatenados (ej. ent="21", "21002" -> local "002"). Se devuelve solo la
    parte local porque `dbt/macros/normalize_cve_mun.sql` ya sabe reconstruir la
    clave INEGI de 5 dígitos a partir de `cve_ent` + este valor.
    """
    return cve_municipio_completo[len(cve_ent):]


def _finalizar_agregado(df_parcial: pd.DataFrame) -> pd.DataFrame:
    """
    Re-agrega los parciales de todos los chunks (un mismo municipio/año/mes/tipo de
    delito puede caer en más de un chunk, el CSV no está particionado por esa llave),
    deriva `cve_mun` local y renombra al esquema final de Bronze.
    """
    df = df_parcial.groupby(COLUMNAS_LLAVE_AGREGACION, as_index=False)["conteo"].sum()

    df["cve_mun_local"] = df.apply(
        lambda fila: _derivar_cve_mun_local(fila["Clave_Ent"], fila["Cve. Municipio"]), axis=1
    )

    return df.rename(columns={
        "Año": "anio",
        "Clave_Ent": "cve_ent",
        "cve_mun_local": "cve_mun",
        "Tipo de delito": "tipo_delito",
    })[["cve_ent", "cve_mun", "anio", "mes", "tipo_delito", "conteo"]]


def _descargar_a_temporal(url: str) -> str:
    """
    Descarga `url` completa a un archivo temporal antes de parsear.

    El CDN (Akamai) de este host corta la conexión de streaming largo antes de
    terminar de transmitir los ~380 MB del archivo (falla intermitente, no
    reproducible siempre al mismo chunk). Separar "descargar" de "parsear" evita que
    un corte de red a la mitad tire también el trabajo de agregación ya hecho.

    También evita el bug del gzip roto/truncado (`Content-Length: 20`) que el mismo
    CDN devuelve si el cliente ofrece `Accept-Encoding: gzip` (lo que `requests` manda
    por default) -- se fuerza `identity`.
    """
    headers = {"Accept-Encoding": "identity"}
    fd, ruta_temporal = tempfile.mkstemp(suffix=".csv", prefix="sesnsp_")
    os.close(fd)

    with requests.get(url, timeout=(30, 60), stream=True, headers=headers) as response:
        response.raise_for_status()
        with open(ruta_temporal, "wb") as archivo:
            descargado = 0
            for bloque in response.iter_content(chunk_size=1024 * 1024):
                archivo.write(bloque)
                descargado += len(bloque)
                if descargado % (50 * 1024 * 1024) < len(bloque):
                    logger.info("Descargados %.0f MB...", descargado / (1024 * 1024))

    return ruta_temporal


def extraer_sesnsp() -> str:
    """
    Descarga la incidencia delictiva municipal de SESNSP (vía mirror ATDT), la agrega
    a nivel municipio/año/mes/tipo de delito y la guarda en Bronze.

    El archivo fuente pesa ~380 MB: se descarga completo a un temporal primero (ver
    `_descargar_a_temporal`) y luego se procesa en chunks desde disco para no cargarlo
    completo en memoria -- cada chunk se agrega de inmediato (unpivot + sum) y solo se
    concatenan los resultados parciales, mucho más chicos.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        requests.RequestException: si falla la descarga.
        ValueError: si no se obtuvo ningún registro.
    """
    logger.info("Iniciando extracción de %s desde %s", SOURCE_NAME, SOURCE_URL)

    ruta_temporal = _descargar_a_temporal(SOURCE_URL)
    logger.info("Descarga completa: %s", ruta_temporal)

    parciales = []
    try:
        lector = pd.read_csv(
            ruta_temporal,
            encoding=ENCODING_FUENTE,
            chunksize=TAMANO_CHUNK,
            dtype={"Clave_Ent": "str", "Cve. Municipio": "str"},
        )
        for i, chunk in enumerate(lector):
            parciales.append(_agregar_chunk(chunk))
            logger.info("Chunk %d procesado (%d filas agregadas)", i, len(parciales[-1]))
    finally:
        os.remove(ruta_temporal)

    if not parciales:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = _finalizar_agregado(pd.concat(parciales, ignore_index=True))

    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    os.makedirs(BRONZE_PATH, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/sesnsp_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extraer_sesnsp()
