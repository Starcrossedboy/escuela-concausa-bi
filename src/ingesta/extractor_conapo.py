import logging
from datetime import datetime, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-08_CONAPO"
SOURCE_URL = "PENDIENTE-CONFIRMAR"  # ver DS-08_CONAPO.md — dueño: Emilio Galnares Ruiz
BRONZE_PATH = "data/bronze/conapo"


def extraer_conapo() -> str:
    """
    Descarga las Proyecciones de la Población de México (CONAPO) y las guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si la URL no está confirmada todavía, o si la respuesta viene vacía.
        requests.RequestException: si falla la descarga.
    """
    if SOURCE_URL == "PENDIENTE-CONFIRMAR":
        raise ValueError(
            f"{SOURCE_NAME}: URL aún no confirmada por el dueño de la fuente (Emilio Galnares Ruiz). "
            "Ver 14_Data_Sources/DS-08_CONAPO.md"
        )

    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    response = requests.get(SOURCE_URL, timeout=60)
    response.raise_for_status()

    # TODO: reemplazar por el parseo real del CSV de CONAPO
    data = response.json() if response.content else None
    if not data:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = pd.DataFrame(data)
    # Esquema esperado: cve_ent, cve_mun, anio, edad/grupo_edad, poblacion
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/conapo_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path