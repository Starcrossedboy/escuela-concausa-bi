import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-08_CONAPO"
SOURCE_URL = (
    "https://www.datos.gob.mx/dataset/proyecciones-de-poblacion/"
    "resource/3c3092be-583e-4490-8c23-67ef9a64b198"
)
SOURCE_FILE = "data/raw/pobproy_quinq1.csv"
BRONZE_PATH = "data/bronze/conapo"

# NOTA (US-121a, Emilio Galnares Ruiz): CONAPO distribuye este dataset vía una
# aplicación web con sesiones temporales (sin URL de descarga permanente), por lo
# que este extractor parte del archivo ya descargado en SOURCE_FILE en vez de una
# descarga automática por internet. Ver vault/14_Data_Sources/DS-08_CONAPO_Proyecciones.md,
# sección 10 (Riesgos conocidos).


def extraer_conapo() -> str:
    """
    Procesa las Proyecciones de la Población de México (CONAPO) desde el archivo
    ya descargado, corrige la clave de municipio a 5 dígitos y las guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        FileNotFoundError: si el archivo fuente no existe en SOURCE_FILE.
        ValueError: si el archivo viene vacío.
    """
    if not Path(SOURCE_FILE).exists():
        raise FileNotFoundError(
            f"{SOURCE_NAME}: no se encontró {SOURCE_FILE}. CONAPO no ofrece URL de "
            f"descarga estable; el archivo debe descargarse manualmente desde "
            f"{SOURCE_URL} y colocarse en esa ruta antes de correr este extractor."
        )

    logger.info("Iniciando extracción de %s", SOURCE_NAME)

    df = pd.read_csv(SOURCE_FILE)
    if df.empty:
        raise ValueError(f"{SOURCE_NAME}: archivo vacío, no se guarda nada")

    # Esquema real confirmado: CLAVE, CLAVE_ENT, NOM_ENT, NOM_MUN, SEXO, ANO,
    # POB_TOTAL, POB_00_04 ... POB_85_mm (ver DS-08_CONAPO_Proyecciones.md sección 5)
    df["cve_mun"] = df["CLAVE"].astype(str).str.zfill(5)

    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{BRONZE_PATH}/conapo_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d filas)", output_path, len(df))

    return output_path