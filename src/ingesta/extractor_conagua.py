"""
Extractor de CONAGUA SINA (DS-06) — Disponibilidad hídrica, periodicidad diaria.
Descarga la lectura más reciente por estación/presa y la guarda en Bronze.

NOTA: la URL real de la fuente está PENDIENTE-CONFIRMAR (dueño: Emilio Galnares Ruiz,
prueba de descarga Semana 1). Este extractor queda listo para conectarse en cuanto
se confirme el endpoint — ver 14_Data_Sources/DS-06_CONAGUA_SINA.md.
"""
import logging
from datetime import datetime, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-06_CONAGUA_SINA"
SOURCE_URL = "PENDIENTE-CONFIRMAR"  # ver DS-06_CONAGUA_SINA.md — bloqueado por prueba de descarga
BRONZE_PATH = "data/bronze/conagua"


def extraer_conagua() -> str:
    """
    Descarga la lectura diaria más reciente de CONAGUA SINA y la guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si la URL no está confirmada todavía, o si la respuesta viene vacía.
        requests.RequestException: si falla la descarga.
    """
    if SOURCE_URL == "PENDIENTE-CONFIRMAR":
        raise ValueError(
            f"{SOURCE_NAME}: URL aún no confirmada por el dueño de la fuente (Emilio Galnares). "
            "Ver 14_Data_Sources/DS-06_CONAGUA_SINA.md"
        )

    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()

    # TODO: reemplazar por el parseo real del formato de CONAGUA (CSV o API, confirmar)
    data = response.json() if response.content else None
    if not data:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = pd.DataFrame(data)
    # Esquema esperado: id_estacion, region_hidrologica, latitud, longitud, indicador, valor, fecha
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/conagua_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path