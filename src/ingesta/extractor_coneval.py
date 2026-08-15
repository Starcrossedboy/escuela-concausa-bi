import logging
from datetime import datetime, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-07_CONEVAL"
SOURCE_URL = "PENDIENTE-CONFIRMAR"  # ver DS-07_CONEVAL.md — dueño: Deni Garrido Fragoso
BRONZE_PATH = "data/bronze/coneval"


def extraer_coneval() -> str:
    """
    Descarga el Índice de Rezago Social / Medición de Pobreza municipal (CONEVAL) y la guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si la URL no está confirmada todavía, o si la respuesta viene vacía.
        requests.RequestException: si falla la descarga.
    """
    if SOURCE_URL == "PENDIENTE-CONFIRMAR":
        raise ValueError(
            f"{SOURCE_NAME}: URL aún no confirmada por el dueño de la fuente (Deni Garrido Fragoso). "
            "Ver 14_Data_Sources/DS-07_CONEVAL.md"
        )

    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    response = requests.get(SOURCE_URL, timeout=60)
    response.raise_for_status()

    # TODO: reemplazar por el parseo real del XLSX de CONEVAL (encabezados en varias filas/hojas)
    data = response.json() if response.content else None
    if not data:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = pd.DataFrame(data)
    # Esquema esperado: cve_mun, entidad, municipio, indice_rezago_social, grado_rezago, pobreza_pct
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/coneval_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path