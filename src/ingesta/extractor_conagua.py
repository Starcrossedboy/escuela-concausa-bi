"""
Extractor de CONAGUA SINA (DS-06) — Disponibilidad hídrica, periodicidad diaria.
Descarga la lectura más reciente por estación/presa y la guarda en Bronze.

Fuente confirmada en Semana 1 (US-121a, Emilio Galnares Ruiz): el sitio de consulta
de presas (https://sisuar.imta.mx/aplicacion/vista/presa/presas.php) no ofrece
descarga directa, pero su formulario envía internamente una petición POST al
endpoint mapa.php, que responde en JSON con el listado completo de presas y sus
volúmenes (cap_name, cap_namo). El payload replica exactamente el que arma el
formulario web al seleccionar todos los estados (id_estado=1..33) — ver el DevLog
de la sesión para el detalle de cómo se capturó (Herramientas de Desarrollador,
pestaña Network). Detalle en 14_Data_Sources/DS-06_CONAGUA_SINA.md.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-06_CONAGUA_SINA"
SOURCE_URL = "https://sisuar.imta.mx/aplicacion/controlador/mapa.php"
BRONZE_PATH = "data/bronze/conagua"


def extraer_conagua() -> str:
    """
    Descarga el listado completo de presas de CONAGUA (vía IMTA/SISUAR) con sus
    volúmenes de almacenamiento (NAME/NAMO) y lo guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si la respuesta viene vacía.
        requests.RequestException: si falla la descarga.
    """
    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    # Replica la consulta del formulario web pidiendo las 33 entidades en una sola llamada
    condiciones = " or ".join([f"id_estado={i}" for i in range(1, 34)])
    payload = {
        "query": f"({condiciones})",
        "Accion": "Presas",
    }

    response = requests.post(SOURCE_URL, data=payload, timeout=30)
    response.raise_for_status()

    data = response.json() if response.content else None
    if not data:
        raise ValueError(f"{SOURCE_NAME}: respuesta vacía, no se guarda nada")

    df = pd.DataFrame(data)
    # Esquema real confirmado: id_presa, nombre_oficial, corriente, estado,
    # anio_term, alt_cort, cap_name, cap_namo (ver DS-06_CONAGUA_SINA.md sección 5)
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    Path(BRONZE_PATH).mkdir(parents=True, exist_ok=True)
    output_path = f"{BRONZE_PATH}/conagua_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path