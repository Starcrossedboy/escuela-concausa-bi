"""Carga los Parquet Bronze reales de DS-05 SINAICA a Postgres.

Toma los dos Parquet que produce `extractor_sinaica.py` -- catálogo de
estaciones y observaciones horarias, ver ese módulo -- y los inserta en
`bronze.sinaica_estaciones` / `bronze.sinaica_observaciones` de forma
idempotente por snapshot (`_source` + `_ingested_at`). No cruza, tipa ni
corrige valores -- eso es trabajo de Silver (`dbt/models/silver/aire_estacion.sql`).

Este loader NO corre las expectativas de Great Expectations
(`validacion_sinaica.py`) -- son un paso separado, pensado para correr antes de
llamar a este script.

Nota: `dbt/models/sources.yml` sigue apuntando por default a
`sinaica_estaciones_test` / `sinaica_observaciones_test` (fixtures). Una vez
cargadas las tablas reales con este script, falta actualizar esos vars (o
pasarlos con `--vars` en `dbt run`) para que Silver lea las tablas reales.

Uso:
    python -m src.ingesta.cargar_bronze_sinaica_real --producto ambos
    python -m src.ingesta.cargar_bronze_sinaica_real --producto estaciones
    python -m src.ingesta.cargar_bronze_sinaica_real --producto observaciones --parquet <ruta>
"""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

TABLAS = {
    "estaciones": "sinaica_estaciones",
    "observaciones": "sinaica_observaciones",
}

BRONZE_PATHS = {
    "estaciones": "data/bronze/sinaica/estaciones",
    "observaciones": "data/bronze/sinaica/observaciones",
}

LLAVE_NATURAL = {
    "estaciones": ["id"],
    "observaciones": ["id_estacion", "parametro", "fecha", "hora"],
}

COLUMNAS_REQUERIDAS = {
    "estaciones": {"id", "nombre", "latitud", "longitud", "_ingested_at", "_source", "_source_url"},
    "observaciones": {
        "id_estacion", "parametro", "fecha", "hora", "valor", "val",
        "_ingested_at", "_source", "_source_url",
    },
}


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


def _validar_df(producto: str, df: pd.DataFrame) -> None:
    faltan = COLUMNAS_REQUERIDAS[producto] - set(df.columns)
    if faltan:
        raise ValueError(f"DS-05 SINAICA {producto}: faltan columnas Bronze: {sorted(faltan)}")
    if df.empty:
        raise ValueError(f"DS-05 SINAICA {producto}: Parquet vacío")

    llave = LLAVE_NATURAL[producto]
    if df[llave].isna().any().any():
        raise ValueError(f"DS-05 SINAICA {producto}: llave natural con nulos ({llave})")
    if df.duplicated(subset=llave).any():
        raise ValueError(
            f"DS-05 SINAICA {producto}: llave natural duplicada dentro del mismo Parquet ({llave})"
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


def cargar_parquet(producto: str, parquet_path: str) -> tuple[int, int]:
    """Carga un snapshot real de DS-05 (`producto` = estaciones u observaciones), de
    forma idempotente por ingesta.

    Returns:
        (filas_insertadas, filas_en_snapshot). Si el snapshot (`_source` +
        `_ingested_at`) ya existía completo, `filas_insertadas` es 0.
    """
    if producto not in TABLAS:
        raise ValueError(f"Producto inválido: {producto!r}. Opciones: {sorted(TABLAS)}")

    ruta = Path(parquet_path)
    if not ruta.is_file():
        raise FileNotFoundError(ruta)

    df = pd.read_parquet(ruta)
    _validar_df(producto, df)

    tabla = TABLAS[producto]
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


def _ultimo_parquet(producto: str) -> Path:
    carpeta = Path(BRONZE_PATHS[producto])
    candidatos = sorted(carpeta.glob(f"sinaica_{producto}_*.parquet"))
    if not candidatos:
        raise FileNotFoundError(
            f"No hay Parquet real DS-05 para {producto} en {carpeta}. Corre extractor_sinaica primero."
        )
    return candidatos[-1]


def cargar_ultimos() -> dict[str, dict[str, object]]:
    """Carga el Parquet más reciente de cada producto (estaciones + observaciones)."""
    salida = {}
    for producto in ("estaciones", "observaciones"):
        ruta = _ultimo_parquet(producto)
        insertadas, total = cargar_parquet(producto, str(ruta))
        salida[producto] = {
            "parquet": str(ruta),
            "tabla": f"bronze.{TABLAS[producto]}",
            "insertadas": insertadas,
            "filas_snapshot": total,
        }
    return salida


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producto", choices=["estaciones", "observaciones", "ambos"], default="ambos")
    parser.add_argument("--parquet", help="Ruta al Parquet real (ignorado si --producto=ambos)")
    args = parser.parse_args()

    if args.producto == "ambos":
        resultado = cargar_ultimos()
        for producto, meta in resultado.items():
            print(
                f"OK {producto}: {meta['tabla']} — "
                f"{meta['insertadas']} insertadas / {meta['filas_snapshot']} snapshot"
            )
    else:
        ruta = Path(args.parquet) if args.parquet else _ultimo_parquet(args.producto)
        insertadas, total = cargar_parquet(args.producto, str(ruta))
        print(
            f"OK {args.producto}: bronze.{TABLAS[args.producto]} — "
            f"{insertadas} insertadas / {total} snapshot"
        )
