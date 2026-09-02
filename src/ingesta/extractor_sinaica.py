"""
Extractor de SINAICA (DS-05) — Calidad del aire, periodicidad horaria.

SINAICA/INECC no publica una API REST/JSON documentada. Los endpoints usados aquí son
los mismos que usa internamente el sitio `sinaica.inecc.gob.mx`; se identificaron por
ingeniería inversa del paquete open-source `rsinaica`
(https://github.com/diegovalle/rsinaica) y se verificaron en vivo el 2026-08-14 (ver
`vault/14_Data_Sources/DS-05_SINAICA_Calidad_Aire.md`, sección 9).

Produce dos tablas Bronze independientes (así las espera
`dbt/models/silver/aire_estacion.sql`):
  - `sinaica_estaciones`: catálogo de estaciones (identidad + georreferencia).
  - `sinaica_observaciones`: lecturas horarias por estación y parámetro.
"""
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-05_SINAICA"
BASE_URL = "https://sinaica.inecc.gob.mx"
ESTACIONES_URL = f"{BASE_URL}/lib/j/php/getData.php"
ULTIMOS_ENVIOS_URL = f"{BASE_URL}/lib/libd/cnxn.php"
DATOS_URL = f"{BASE_URL}/pags/datGrafs.php"

BRONZE_PATH_ESTACIONES = "data/bronze/sinaica/estaciones"
BRONZE_PATH_OBSERVACIONES = "data/bronze/sinaica/observaciones"

# Parámetros de calidad del aire por defecto (contaminantes criterio). Cada estación
# reporta solo un subconjunto; los que no aplican se descartan por estación sin
# tumbar la corrida (ver _extraer_dato_horario).
PARAMETROS_DEFAULT = ("PM2.5", "PM10", "O3", "CO", "NO2", "SO2")

# La respuesta de datGrafs.php es HTML+JS, no JSON puro: los datos vienen embebidos
# en una línea `var dat = [...];` que hay que extraer antes de poder parsearlos.
_DAT_PATTERN = re.compile(r"var\s+dat\s*=\s*(\[[\s\S]*?\])\s*;")


def _guardar_parquet(df: pd.DataFrame, bronze_path: str, prefix: str) -> str:
    """Escribe `df` como Parquet en Bronze con timestamp único (idempotente por corrida)."""
    os.makedirs(bronze_path, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = f"{bronze_path}/{prefix}_{timestamp}.parquet"
    df.to_parquet(output_path, index=False)
    return output_path


def _parsear_estaciones_activas(data: list[dict]) -> list[int]:
    """Extrae y deduplica los IDs de estación de la respuesta de `getUltimosEnvios`."""
    return sorted({int(item["idEstacion"]) for item in data})


def _estaciones_activas() -> list[int]:
    """IDs de estaciones con envío reciente (`getUltimosEnvios`)."""
    response = requests.post(
        ULTIMOS_ENVIOS_URL, data={"metodo": "getUltimosEnvios"}, timeout=30
    )
    response.raise_for_status()
    return _parsear_estaciones_activas(response.json())


def extraer_sinaica_estaciones() -> str:
    """
    Descarga el catálogo de estaciones de SINAICA (nombre, red, lat/lon, municipioId)
    y lo guarda en Bronze.

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        requests.RequestException: si falla la descarga.
        ValueError: si la respuesta viene vacía.
    """
    logger.info("Iniciando extracción de catálogo de estaciones de %s", SOURCE_NAME)

    fields = (
        "e.id, e.nombre, e.codigo, e.redesId, r.nombre as nombre_red, "
        "r.codigo as codigo_red, e.municipioId, e.estadoId, e.latitud, e.longitud, "
        "e.fechaIniDatos"
    )
    response = requests.post(
        ESTACIONES_URL,
        data={
            "tabla": "Estaciones e INNER JOIN Redes r ON e.redesid = r.id",
            "fields": fields,
            "where": "1=1 ORDER BY r.nombre, e.codigo",
        },
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    if not data:
        raise ValueError(f"{SOURCE_NAME}: catálogo de estaciones vacío, no se guarda nada")

    df = pd.DataFrame(data)
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = ESTACIONES_URL

    output_path = _guardar_parquet(df, BRONZE_PATH_ESTACIONES, "sinaica_estaciones")
    logger.info("Guardado %s (%d estaciones)", output_path, len(df))

    return output_path


def _parsear_respuesta_datos(texto: str, estacion_id: int, parametro: str) -> pd.DataFrame:
    """
    Extrae el arreglo `var dat = [...]` embebido en la respuesta HTML+JS de
    `datGrafs.php` (no es JSON puro, ver módulo).

    Devuelve un DataFrame vacío (no lanza error) si la estación no reporta ese
    parámetro — es un caso esperado, no una falla.
    """
    match = _DAT_PATTERN.search(texto)
    if not match:
        raise ValueError(
            f"{SOURCE_NAME}: no se encontró 'var dat = [...]' en la respuesta "
            f"(estación={estacion_id}, parametro={parametro})"
        )

    registros = json.loads(match.group(1))
    columnas = ["id_estacion", "parametro", "fecha", "hora", "valor", "val"]
    if not registros:
        return pd.DataFrame(columns=columnas)

    df = pd.DataFrame(registros)
    df["id_estacion"] = int(estacion_id)
    df["parametro"] = parametro
    return df[["fecha", "hora", "valor", "val", "id_estacion", "parametro"]]


def _extraer_dato_horario(estacion_id: int, parametro: str, fecha_ini: str) -> pd.DataFrame:
    """Descarga los datos horarios de un parámetro/estación desde `datGrafs.php`."""
    response = requests.post(
        DATOS_URL,
        data={
            "estacionId": estacion_id,
            "param": parametro,
            "fechaIni": fecha_ini,
            "rango": 1,  # 1 = 1 día (ver DS-05 doc para el resto de los códigos)
            "tipoDatos": "",  # "" = Cruda, "V" = Validada, "M" = Manual
            "datoBase": 1,
        },
        timeout=60,
    )
    response.raise_for_status()
    return _parsear_respuesta_datos(response.text, estacion_id, parametro)


def extraer_sinaica_observaciones(
    estacion_ids: list[int] | None = None,
    parametros: tuple[str, ...] = PARAMETROS_DEFAULT,
    dias_atras: int = 0,
) -> str:
    """
    Descarga las observaciones horarias de SINAICA para una lista de estaciones y
    parámetros, y las guarda en Bronze.

    Args:
        estacion_ids: estaciones a consultar. Si es None, usa todas las estaciones
            con envío reciente (`getUltimosEnvios`).
        parametros: parámetros a descargar por estación.
        dias_atras: desplazamiento en días respecto a hoy para `fechaIni` (0 = hoy).

    Returns:
        Ruta del archivo Parquet generado.

    Raises:
        ValueError: si no se obtuvo ningún registro en toda la corrida.
    """
    logger.info("Iniciando extracción de observaciones horarias de %s", SOURCE_NAME)

    if estacion_ids is None:
        estacion_ids = _estaciones_activas()

    fecha_ini = (datetime.now(timezone.utc) - timedelta(days=dias_atras)).strftime("%Y-%m-%d")

    frames = []
    for estacion_id in estacion_ids:
        for parametro in parametros:
            try:
                frames.append(_extraer_dato_horario(estacion_id, parametro, fecha_ini))
            except (requests.RequestException, ValueError) as exc:
                # Una estación sin ese parámetro, o una falla puntual, no debe tumbar
                # la corrida completa: se registra y se continúa con las demás.
                logger.warning(
                    "Fallo estación=%s parametro=%s: %s", estacion_id, parametro, exc
                )
            # No saturar el servidor -- mismo criterio que usa rsinaica entre llamadas.
            time.sleep(random.uniform(0, 0.5))

    frames = [f for f in frames if not f.empty]
    if not frames:
        raise ValueError(f"{SOURCE_NAME}: no se descargó ningún registro, no se guarda nada")

    df = pd.concat(frames, ignore_index=True)
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source"] = SOURCE_NAME
    df["_source_url"] = DATOS_URL

    output_path = _guardar_parquet(df, BRONZE_PATH_OBSERVACIONES, "sinaica_observaciones")
    logger.info("Guardado %s (%d registros)", output_path, len(df))

    return output_path


def extraer_sinaica() -> dict[str, str]:
    """
    Punto de entrada usado por `dags/dag_horario.py`: corre ambas extracciones
    (catálogo de estaciones + observaciones horarias) en una sola llamada.

    Returns:
        Diccionario con las rutas de los dos Parquet generados.
    """
    return {
        "estaciones": extraer_sinaica_estaciones(),
        "observaciones": extraer_sinaica_observaciones(),
    }
