"""
Extractor de SINAICA (DS-05) — Calidad del aire, periodicidad horaria.
Descarga el dato más reciente y lo guarda en la capa Bronze como Parquet.
"""
import logging
from datetime import datetime, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-05_SINAICA"
SOURCE_URL = "https://sinaica.inecc.gob.mx/"  # placeholder, ajustar a endpoint real
BRONZE_PATH = "data/bronze/sinaica"


def extraer_sinaica() -> str:
    """
    Descarga el dato horario más reciente de SINAICA y lo guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si la respuesta viene vacía.
        requests.RequestException: si falla la descarga.
    """
    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()

    # TODO: reemplazar por el parseo real del formato de SINAICA
    data = response.json() if response.content else None
    if not data:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = pd.DataFrame(data)
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/sinaica_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path