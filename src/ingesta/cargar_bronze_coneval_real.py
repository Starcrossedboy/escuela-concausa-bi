"""Carga los Parquet Bronze reales de DS-07 CONEVAL a Postgres.

Este módulo NO usa `cargar_bronze_fixture.py`: aquel loader corresponde al contrato
sintético histórico de una sola tabla CONEVAL. DS-07 real tiene dos artefactos
físicos oficiales y cada uno se conserva por separado:

- bronze.coneval_irs_2020
- bronze.coneval_pobreza_2020

Las columnas de negocio se crean con los nombres físicos serializados por
`extractor_coneval.py`. No se hacen joins, aliases ni selección de métricas aquí.
La conformación ocurre en dbt Silver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

TABLAS_PERMITIDAS = {
    "irs": "coneval_irs_2020",
    "pobreza": "coneval_pobreza_2020",
}

_METADATA_COLUMNS = {"_periodo_medicion", "_ingested_at", "_source", "_source_url"}


def _pg_column_name(original: str) -> str:
    """Nombre técnico estable <=63 bytes para evitar truncamiento de PostgreSQL."""
    original = str(original)
    if original in _METADATA_COLUMNS:
        return original
    return "c_" + hashlib.sha1(original.encode("utf-8")).hexdigest()[:12]


def _renombrar_para_postgres(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    mapping = {str(c): _pg_column_name(str(c)) for c in df.columns}
    values = list(mapping.values())
    if len(values) != len(set(values)):
        raise ValueError("DS-07: colisión de identificadores técnicos PostgreSQL")
    return df.rename(columns=mapping), mapping


def _guardar_mapeo_local(producto: str, mapping: dict[str, str]) -> str:
    root = Path("data/bronze/coneval/manifests")
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"ds07_postgres_columns_{producto}_2020.json"
    payload = {
        "producto": producto,
        "tabla": f"bronze.{TABLAS_PERMITIDAS[producto]}",
        "columnas": [
            {"source_column": original, "postgres_column": tecnico}
            for original, tecnico in mapping.items()
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


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
        pass
    if isinstance(valor, np.generic):
        return valor.item()
    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()
    return valor


def _crear_tabla(cur, tabla: str, df: pd.DataFrame, source_mapping: dict[str, str]) -> None:
    cur.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    definiciones = []
    for columna in df.columns:
        definiciones.append(
            sql.SQL("{} {}").format(
                sql.Identifier(str(columna)),
                sql.SQL(_tipo_postgres(df[columna])),
            )
        )
    ddl = sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({})").format(
        sql.Identifier("bronze"),
        sql.Identifier(tabla),
        sql.SQL(", ").join(definiciones),
    )
    cur.execute(ddl)

    for original, tecnico in source_mapping.items():
        if original == tecnico:
            continue
        cur.execute(
            sql.SQL("COMMENT ON COLUMN {}.{}.{} IS %s").format(
                sql.Identifier("bronze"),
                sql.Identifier(tabla),
                sql.Identifier(tecnico),
            ),
            (f"DS-07 CONEVAL source header: {original}",),
        )


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
    """Carga un snapshot real de DS-07 de forma idempotente por ingesta."""
    if producto not in TABLAS_PERMITIDAS:
        raise ValueError(f"Producto inválido: {producto!r}")

    ruta = Path(parquet_path)
    if not ruta.is_file():
        raise FileNotFoundError(ruta)

    df = pd.read_parquet(ruta)
    if df.empty:
        raise ValueError(f"{ruta}: Parquet vacío")

    obligatorias = {"_ingested_at", "_source", "_source_url", "_periodo_medicion"}
    faltantes = obligatorias - set(df.columns)
    if faltantes:
        raise ValueError(f"{ruta}: faltan metadatos Bronze: {sorted(faltantes)}")

    periodos = set(pd.to_numeric(df["_periodo_medicion"], errors="coerce").dropna().astype(int))
    if periodos != {2020}:
        raise ValueError(f"{ruta}: período inesperado: {sorted(periodos)}")

    tabla = TABLAS_PERMITIDAS[producto]
    df_pg, source_mapping = _renombrar_para_postgres(df)
    columnas = [str(c) for c in df_pg.columns]
    snapshot_source = str(df_pg["_source"].iloc[0])
    snapshot_ingested = pd.Timestamp(df_pg["_ingested_at"].iloc[0]).to_pydatetime()

    registros = [
        tuple(_valor_python(v) for v in fila)
        for fila in df_pg.itertuples(index=False, name=None)
    ]

    with psycopg2.connect(_dsn()) as conn:
        with conn.cursor() as cur:
            _crear_tabla(cur, tabla, df_pg, source_mapping)
            _validar_schema_existente(cur, tabla, columnas)

            cur.execute(
                sql.SQL(
                    'select count(*) from {}.{} '
                    'where "_source" = %s and "_ingested_at" = %s'
                ).format(sql.Identifier("bronze"), sql.Identifier(tabla)),
                (snapshot_source, snapshot_ingested),
            )
            existentes = int(cur.fetchone()[0])
            if existentes:
                if existentes != len(df):
                    raise ValueError(
                        f"bronze.{tabla}: snapshot parcial existente "
                        f"({existentes}/{len(df)} filas); no se completa en silencio"
                    )
                return 0, existentes

            insert = sql.SQL("INSERT INTO {}.{} ({}) VALUES %s").format(
                sql.Identifier("bronze"),
                sql.Identifier(tabla),
                sql.SQL(", ").join(sql.Identifier(c) for c in columnas),
            )
            execute_values(cur, insert.as_string(conn), registros, page_size=500)
            insertadas = len(registros)

        conn.commit()

    _guardar_mapeo_local(producto, source_mapping)
    return int(insertadas), len(df_pg)


def _ultimo_parquet(producto: str) -> Path:
    carpeta = Path("data/bronze/coneval") / producto
    candidatos = sorted(carpeta.glob(f"coneval_{producto}_2020_*.parquet"))
    if not candidatos:
        raise FileNotFoundError(f"No hay Parquet real DS-07 para {producto} en {carpeta}")
    return candidatos[-1]


def cargar_ultimos() -> dict[str, dict[str, object]]:
    salida = {}
    for producto in ("irs", "pobreza"):
        ruta = _ultimo_parquet(producto)
        insertadas, total = cargar_parquet(producto, str(ruta))
        salida[producto] = {
            "parquet": str(ruta),
            "tabla": f"bronze.{TABLAS_PERMITIDAS[producto]}",
            "insertadas": insertadas,
            "filas_snapshot": total,
        }
    return salida


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producto", choices=["irs", "pobreza", "ambos"], default="ambos")
    parser.add_argument("--parquet")
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
            f"OK {args.producto}: bronze.{TABLAS_PERMITIDAS[args.producto]} — "
            f"{insertadas} insertadas / {total} snapshot"
        )
