import logging
from datetime import datetime, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-03_CEMABE"
SOURCE_URL = "PENDIENTE-CONFIRMAR"  # ver DS-03_CEMABE.md — dueño: Deni Garrido Fragoso
BRONZE_PATH = "data/bronze/cemabe"


def extraer_cemabe() -> str:
    """
    Descarga el Censo de Escuelas, Maestros y Alumnos de Educación Básica y Especial
    (CEMABE, INEGI/SEP) y lo guarda en Bronze.

    Nota: CEMABE es un censo único levantado en 2013, no una serie periódica.
    No se espera que los datos cambien entre ejecuciones; se re-extrae por
    consistencia del pipeline, no porque la fuente se actualice.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si la URL no está confirmada todavía, o si la respuesta viene vacía.
        requests.RequestException: si falla la descarga.
    """
    if SOURCE_URL == "PENDIENTE-CONFIRMAR":
        raise ValueError(
            f"{SOURCE_NAME}: URL aún no confirmada por el dueño de la fuente (Deni Garrido Fragoso). "
            "Ver 14_Data_Sources/DS-03_CEMABE.md"
        )

    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    response = requests.get(SOURCE_URL, timeout=60)
    response.raise_for_status()

    # TODO: reemplazar por el parseo real del CSV de CEMABE
    data = response.json() if response.content else None
    if not data:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = pd.DataFrame(data)
    # Esquema esperado: cct, agua_red, drenaje, electricidad, sanitarios, internet, computadoras
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/cemabe_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path