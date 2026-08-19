"""Carga un fixture de Bronze (CSV en tests/fixtures/, <=500 filas, anonimizado) a Postgres.

Uso exclusivo de DESARROLLO LOCAL / dbt run|test contra la capa Silver, mientras las URLs
reales de las fuentes siguen bloqueadas (ver 14_Data_Sources/*.md). No es el extractor de
producción — ese vive en `extractor_<fuente>.py` y descarga de la fuente real hacia
`data/bronze/` en Parquet (Data_Model.md §2).

Idempotente sin DELETE/UPDATE/DROP (CLAUDE.md §3 "Nunca..."): crea la tabla si no existe con
una restricción UNIQUE natural de bronze e inserta con `ON CONFLICT DO NOTHING`, así correr
el script varias veces con el mismo fixture no duplica filas.

Ejemplo:
    python -m src.ingesta.cargar_bronze_fixture \
        --fixture tests/fixtures/bronze_formato911_sample.csv \
        --tabla formato911_2024_2025 --esquema formato911
"""
import argparse
import logging
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

DDL_BRONZE_FORMATO911 = """
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.{tabla} (
    cct             TEXT,
    ciclo           TEXT,
    entidad         TEXT,
    municipio       TEXT,
    nivel           TEXT,
    alumnos_total   INTEGER,
    docentes_total  INTEGER,
    grupos_total    INTEGER,
    _ingested_at    TIMESTAMPTZ,
    _source         TEXT,
    _source_url     TEXT,
    UNIQUE (_source, _ingested_at, cct, ciclo)
);
"""

COLUMNAS = [
    "cct", "ciclo", "entidad", "municipio", "nivel",
    "alumnos_total", "docentes_total", "grupos_total",
    "_ingested_at", "_source", "_source_url",
]

# DS-03 CEMABE: infraestructura escolar a nivel CCT (alimenta D3/D4, ADR-004)
DDL_BRONZE_CEMABE = """
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.{tabla} (
    cct             TEXT,
    agua_red        TEXT,
    drenaje         TEXT,
    electricidad    TEXT,
    sanitarios      TEXT,
    internet        TEXT,
    computadoras    TEXT,
    _ingested_at    TIMESTAMPTZ,
    _source         TEXT,
    _source_url     TEXT,
    UNIQUE (_source, _ingested_at, cct)
);
"""

COLUMNAS_CEMABE = [
    "cct", "agua_red", "drenaje", "electricidad", "sanitarios",
    "internet", "computadoras", "_ingested_at", "_source", "_source_url",
]

# DS-07 CONEVAL: rezago social y pobreza a nivel municipio (alimenta D1)
DDL_BRONZE_CONEVAL = """
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.{tabla} (
    cve_mun                 TEXT,
    entidad                 TEXT,
    municipio                TEXT,
    indice_rezago_social     TEXT,
    grado_rezago              TEXT,
    pobreza_pct                TEXT,
    _ingested_at             TIMESTAMPTZ,
    _source                  TEXT,
    _source_url               TEXT,
    UNIQUE (_source, _ingested_at, cve_mun)
);
"""

COLUMNAS_CONEVAL = [
    "cve_mun", "entidad", "municipio", "indice_rezago_social",
    "grado_rezago", "pobreza_pct", "_ingested_at", "_source", "_source_url",
]

# DS-04 SESNSP: incidencia delictiva municipal, serie mensual (alimenta D2)
DDL_BRONZE_SESNSP = """
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.{tabla} (
    cve_ent         TEXT,
    cve_mun         TEXT,
    anio            INTEGER,
    mes             INTEGER,
    tipo_delito     TEXT,
    conteo          INTEGER,
    _ingested_at    TIMESTAMPTZ,
    _source         TEXT,
    _source_url     TEXT,
    UNIQUE (_source, _ingested_at, cve_mun, anio, mes, tipo_delito)
);
"""

COLUMNAS_SESNSP = [
    "cve_ent", "cve_mun", "anio", "mes", "tipo_delito", "conteo",
    "_ingested_at", "_source", "_source_url",
]


def _dsn() -> str:
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'escuela_concausa_db')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', '')}"
    )


ESQUEMAS = {
    "formato911": (DDL_BRONZE_FORMATO911, COLUMNAS, ["_source", "_ingested_at", "cct", "ciclo"]),
    "cemabe": (DDL_BRONZE_CEMABE, COLUMNAS_CEMABE, ["_source", "_ingested_at", "cct"]),
    "coneval": (DDL_BRONZE_CONEVAL, COLUMNAS_CONEVAL, ["_source", "_ingested_at", "cve_mun"]),
    "sesnsp": (DDL_BRONZE_SESNSP, COLUMNAS_SESNSP, ["_source", "_ingested_at", "cve_mun", "anio", "mes", "tipo_delito"]),
}


def cargar_fixture(fixture_path: str, tabla: str, esquema: str = "formato911") -> int:
    """Carga el CSV de fixture a bronze.<tabla>, usando el DDL/columnas/llave de conflicto
    del `esquema` dado (ver ESQUEMAS). Devuelve el número de filas insertadas (excluye las
    que ya existían, gracias a ON CONFLICT DO NOTHING)."""
    if esquema not in ESQUEMAS:
        raise ValueError(f"Esquema desconocido: {esquema}. Opciones: {sorted(ESQUEMAS)}")
    ddl, columnas, conflicto = ESQUEMAS[esquema]

    # keep_default_na=False: sin esto, pandas convierte celdas vacías del CSV (nuestro
    # sentinel de SIN_DATO, p.ej. indice_rezago_social="") a float NaN incluso con dtype=str,
    # y ese NaN se inserta en Postgres como el texto literal 'NaN' -- que Postgres SÍ puede
    # castear a double precision, colándose como un "valor" numérico real con cobertura='OK'
    # en vez de activar la rama SIN_DATO de los macros de Silver. Con keep_default_na=False
    # una celda vacía se lee tal cual: cadena vacía '', que es lo que esos macros esperan.
    df = pd.read_csv(fixture_path, dtype=str, keep_default_na=False)
    faltantes = set(columnas) - set(df.columns)
    if faltantes:
        raise ValueError(f"Fixture {fixture_path} no trae las columnas esperadas: {faltantes}")

    registros = list(df[columnas].itertuples(index=False, name=None))

    with psycopg2.connect(_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl.format(tabla=tabla))
            execute_values(
                cur,
                f"INSERT INTO bronze.{tabla} ({', '.join(columnas)}) VALUES %s "
                f"ON CONFLICT ({', '.join(conflicto)}) DO NOTHING",
                registros,
            )
            insertadas = cur.rowcount
        conn.commit()

    logger.info("bronze.%s: %d filas en el fixture, %d insertadas (resto ya existía)",
                tabla, len(registros), insertadas)
    return insertadas


def cargar_fixture_formato911(fixture_path: str, tabla: str = "formato911") -> int:
    """Compatibilidad hacia atrás: equivalente a cargar_fixture(..., esquema='formato911')."""
    return cargar_fixture(fixture_path, tabla, esquema="formato911")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, help="Ruta al CSV en tests/fixtures/")
    parser.add_argument("--tabla", default="formato911", help="Nombre de la tabla en bronze.*")
    parser.add_argument(
        "--esquema", default="formato911", choices=sorted(ESQUEMAS),
        help="Forma del fixture (define DDL, columnas y llave de conflicto)",
    )
    args = parser.parse_args()

    n = cargar_fixture(args.fixture, args.tabla, args.esquema)
    print(f"OK: {n} filas nuevas cargadas en bronze.{args.tabla}")
    