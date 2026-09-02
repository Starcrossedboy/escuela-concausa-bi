import logging
from datetime import datetime, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-01_FORMATO911"
SOURCE_URL = "https://repodatos.atdt.gob.mx/api_update/secretaria_educacion/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/educacion_basica_2024_2025.csv"
BRONZE_PATH = "data/bronze/formato911"


def extraer_formato911() -> str:
    """
    Descarga la Estadística Educativa - Formato 911 (SEP/SIGED) y la guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si la URL no está confirmada todavía, o si la respuesta viene vacía.
        requests.RequestException: si falla la descarga.
    """
    if SOURCE_URL == "PENDIENTE-CONFIRMAR":
        raise ValueError(
            f"{SOURCE_NAME}: URL aún no confirmada por el dueño de la fuente (Diana Aracely Alvarez Varela). "
            "Ver vault/14_Data_Sources/DS-01_Formato911.md"
        )

    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    response = requests.get(SOURCE_URL, timeout=60)
    response.raise_for_status()

    # TODO: reemplazar por el parseo real del CSV/XLSX de Formato 911
    data = response.json() if response.content else None
    if not data:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = pd.DataFrame(data)
    # Esquema esperado: cct, ciclo, entidad, municipio, nivel, alumnos_total, docentes_total, grupos_total
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/formato911_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path