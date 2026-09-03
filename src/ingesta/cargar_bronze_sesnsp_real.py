"""Carga el Parquet Bronze real de DS-04 SESNSP a Postgres.

Toma el Parquet que produce `extractor_sesnsp.py` (ya agregado a nivel
municipio/año/mes/tipo_delito, ver ese módulo para el porqué) y lo inserta en
`bronze.sesnsp` de forma idempotente por snapshot (`_source` + `_ingested_at`).
No agrega, transforma ni corrige valores -- eso es trabajo de Silver
(`dbt/models/silver/delitos_municipio.sql`).

Este loader NO corre las expectativas de Great Expectations
(`validacion_sesnsp.py`) -- son un paso separado, pensado para correr antes de
llamar a este script.

Nota: `dbt/models/sources.yml` sigue apuntando por default a
`bronze_sesnsp_identifier=sesnsp_test` (fixture). Una vez cargada la tabla real
con este script, falta actualizar ese var (o pasarlo con `--vars` en
`dbt run`) para que Silver lea `bronze.sesnsp` en vez del fixture.

Uso:
    python -m src.ingesta.cargar_bronze_sesnsp_real
    python -m src.ingesta.cargar_bronze_sesnsp_real --parquet data/bronze/sesnsp/sesnsp_20260824_120000.parquet
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

TABLA = "sesnsp"
BRONZE_PATH = "data/bronze/sesnsp"

COLUMNAS_REQUERIDAS = {
    "cve_ent", "cve_mun", "anio", "mes", "tipo_delito", "conteo",
    "_ingested_at", "_source", "_source_url",
}
LLAVE_NATURAL = ["cve_ent", "cve_mun", "anio", "mes", "tipo_delito"]


def _dsn() -> str:
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'escuela_concausa_db')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', '')}"
    )


def _tipo_postgres(serie: pd.Series) -> str:
    """Mapeo técnico de dtype Parquet a tipo Bronze; no aplica semántica."""
    if pd.api.types.is_datetime64_any_dtype(serie.dtype):
        return "TIMESTAMPTZ"
    if pd.api.types.is_bool_dtype(serie.dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(serie.dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(serie.dtype):
        return "DOUBLE PRECISION"
    return "TEXT"


def _valor_python(valor):
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        # pd.isna lanza sobre array-like/tipos no escalares: no es nulo, se conserva
        pass
    if isinstance(valor, np.generic):
        return valor.item()
    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()
    return valor


def _validar_df(df: pd.DataFrame) -> None:
    faltan = COLUMNAS_REQUERIDAS - set(df.columns)
    if faltan:
        raise ValueError(f"DS-04 SESNSP: faltan columnas Bronze: {sorted(faltan)}")
    if df.empty:
        raise ValueError("DS-04 SESNSP: Parquet vacío")
    if df[LLAVE_NATURAL].isna().any().any():
        raise ValueError(f"DS-04 SESNSP: llave natural con nulos ({LLAVE_NATURAL})")
    if df.duplicated(subset=LLAVE_NATURAL).any():
        raise ValueError(
            f"DS-04 SESNSP: llave natural duplicada dentro del mismo Parquet ({LLAVE_NATURAL}) "
            "-- el extractor ya debería agregar a este grano, revisar extractor_sesnsp.py"
        )


def _crear_tabla(cur, tabla: str, df: pd.DataFrame) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    definiciones = [
        sql.SQL("{} {}").format(sql.Identifier(str(c)), sql.SQL(_tipo_postgres(df[c])))
        for c in df.columns
    ]
    ddl = sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({})").format(
        sql.Identifier("bronze"), sql.Identifier(tabla), sql.SQL(", ").join(definiciones),
    )
    cur.execute(ddl)


def _validar_schema_existente(cur, tabla: str, columnas: list[str]) -> None:
    cur.execute(
        """
        select column_name
        from information_schema.columns
        where table_schema = 'bronze' and table_name = %s
        order by ordinal_position
        """,
        (tabla,),
    )
    existentes = [fila[0] for fila in cur.fetchall()]
    if existentes != columnas:
        raise ValueError(
            f"bronze.{tabla}: schema existente no coincide con el Parquet real. "
            f"existentes={existentes}; parquet={columnas}"
        )


def cargar_parquet(parquet_path: str, tabla: str = TABLA) -> tuple[int, int]:
    """Carga un snapshot real de DS-04 a `bronze.<tabla>`, de forma idempotente por ingesta.

    Returns:
        (filas_insertadas, filas_en_snapshot). Si el snapshot (`_source` +
        `_ingested_at`) ya existía completo, `filas_insertadas` es 0.
    """
    ruta = Path(parquet_path)
    if not ruta.is_file():
        raise FileNotFoundError(ruta)

    df = pd.read_parquet(ruta)
    _validar_df(df)

    columnas = [str(c) for c in df.columns]
    source = str(df["_source"].iloc[0])
    ingested = pd.Timestamp(df["_ingested_at"].iloc[0]).to_pydatetime()

    with psycopg2.connect(_dsn()) as conn:
        with conn.cursor() as cur:
            _crear_tabla(cur, tabla, df)
            _validar_schema_existente(cur, tabla, columnas)

            cur.execute(
                sql.SQL(
                    'select count(*) from {}.{} '
                    'where "_source" = %s and "_ingested_at" = %s'
                ).format(sql.Identifier("bronze"), sql.Identifier(tabla)),
                (source, ingested),
            )
            existentes = int(cur.fetchone()[0])
            if existentes:
                if existentes != len(df):
                    raise ValueError(
                        f"bronze.{tabla}: snapshot parcial existente "
                        f"({existentes}/{len(df)} filas); no se completa en silencio"
                    )
                return 0, existentes

            registros = [
                tuple(_valor_python(v) for v in fila)
                for fila in df.itertuples(index=False, name=None)
            ]
            insert = sql.SQL("INSERT INTO {}.{} ({}) VALUES %s").format(
                sql.Identifier("bronze"), sql.Identifier(tabla),
                sql.SQL(", ").join(sql.Identifier(c) for c in columnas),
            )
            execute_values(cur, insert.as_string(conn), registros, page_size=500)
            insertadas = len(registros)

        conn.commit()

    return int(insertadas), len(df)


def _ultimo_parquet() -> Path:
    carpeta = Path(BRONZE_PATH)
    candidatos = sorted(carpeta.glob("sesnsp_*.parquet"))
    if not candidatos:
        raise FileNotFoundError(
            f"No hay Parquet real DS-04 en {carpeta}. Corre extractor_sesnsp primero."
        )
    return candidatos[-1]


if __name__ == "__main__":
    logging_format = "%(levelname)s: %(message)s"
    import logging
    logging.basicConfig(level=logging.INFO, format=logging_format)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parquet",
        help="Ruta al Parquet real; por defecto usa el más reciente en data/bronze/sesnsp/",
    )
    parser.add_argument("--tabla", default=TABLA)
    args = parser.parse_args()

    ruta = Path(args.parquet) if args.parquet else _ultimo_parquet()
    insertadas, total = cargar_parquet(str(ruta), args.tabla)
    print(f"OK DS-04: bronze.{args.tabla} — {insertadas} insertadas / {total} snapshot")
