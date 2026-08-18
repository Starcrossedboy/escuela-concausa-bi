"""Carga un fixture de Bronze (CSV en tests/fixtures/, <=500 filas, anonimizado) a Postgres.

Uso exclusivo de DESARROLLO LOCAL / dbt run|test contra la capa Silver, mientras las URLs
reales de las fuentes siguen bloqueadas (ver 14_Data_Sources/*.md). No es el extractor de
producción — ese vive en `extractor_<fuente>.py` y descarga de la fuente real hacia
`data/bronze/` en Parquet (Data_Model.md §2).

Idempotente sin DELETE/UPDATE/DROP (CLAUDE.md §3 "Nunca..."): crea la tabla si no existe con
una restricción UNIQUE natural de bronze (_source, _ingested_at, cct, ciclo) e inserta con
`ON CONFLICT DO NOTHING`, así correr el script varias veces con el mismo fixture no duplica
filas.

Ejemplo:
    python -m src.ingesta.cargar_bronze_fixture \
        --fixture tests/fixtures/bronze_formato911_sample.csv \
        --tabla formato911_2024_2025
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


def _dsn() -> str:
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'escuela_concausa_db')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', '')}"
    )


def cargar_fixture_formato911(fixture_path: str, tabla: str = "formato911") -> int:
    """Carga el CSV de fixture a bronze.<tabla>. Devuelve el número de filas insertadas
    (excluye las que ya existían, gracias a ON CONFLICT DO NOTHING)."""
    df = pd.read_csv(fixture_path, dtype=str)
    faltantes = set(COLUMNAS) - set(df.columns)
    if faltantes:
        raise ValueError(f"Fixture {fixture_path} no trae las columnas esperadas: {faltantes}")

    registros = list(df[COLUMNAS].itertuples(index=False, name=None))

    with psycopg2.connect(_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL_BRONZE_FORMATO911.format(tabla=tabla))
            antes = cur.rowcount
            execute_values(
                cur,
                f"INSERT INTO bronze.{tabla} ({', '.join(COLUMNAS)}) VALUES %s "
                f"ON CONFLICT (_source, _ingested_at, cct, ciclo) DO NOTHING",
                registros,
            )
            insertadas = cur.rowcount
        conn.commit()

    logger.info("bronze.%s: %d filas en el fixture, %d insertadas (resto ya existía)",
                tabla, len(registros), insertadas)
    return insertadas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, help="Ruta al CSV en tests/fixtures/")
    parser.add_argument("--tabla", default="formato911", help="Nombre de la tabla en bronze.*")
    args = parser.parse_args()

    n = cargar_fixture_formato911(args.fixture, args.tabla)
    print(f"OK: {n} filas nuevas cargadas en bronze.{args.tabla}")