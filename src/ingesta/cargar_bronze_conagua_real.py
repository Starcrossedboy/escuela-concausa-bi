"""Carga DS-06 real a bronze.conagua_presas sin conformar D5."""
from __future__ import annotations
import argparse, os
from pathlib import Path
import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

TABLE = "conagua_presas"
REQUIRED = {"id_presa","nombre_oficial","estado","cap_namo","_ingested_at","_source","_source_url"}

def _dsn():
    return (
        f"host={os.environ.get('POSTGRES_HOST','localhost')} "
        f"port={os.environ.get('POSTGRES_PORT','5432')} "
        f"dbname={os.environ.get('POSTGRES_DB','faro')} "
        f"user={os.environ.get('POSTGRES_USER','faro_user')} "
        f"password={os.environ.get('POSTGRES_PASSWORD','')}"
    )

def validar_df(df):
    faltan = REQUIRED - set(df.columns)
    if faltan: raise ValueError(f"faltan columnas: {sorted(faltan)}")
    if df.empty: raise ValueError("Parquet vacío")
    if df["id_presa"].isna().any() or df["id_presa"].duplicated().any():
        raise ValueError("id_presa nulo o duplicado")
    cap = pd.to_numeric(df["cap_namo"], errors="coerce")
    if cap.isna().any() or ((cap < 0) | (cap > 100000)).any():
        raise ValueError("cap_namo fuera de contrato")

def _tipo(s):
    if pd.api.types.is_datetime64_any_dtype(s.dtype): return "TIMESTAMPTZ"
    if pd.api.types.is_bool_dtype(s.dtype): return "BOOLEAN"
    if pd.api.types.is_integer_dtype(s.dtype): return "BIGINT"
    if pd.api.types.is_float_dtype(s.dtype): return "DOUBLE PRECISION"
    return "TEXT"

def _py(v):
    if v is None: return None
    try:
        if pd.isna(v): return None
    except Exception:
        pass
    if isinstance(v, np.generic): return v.item()
    if isinstance(v, pd.Timestamp): return v.to_pydatetime()
    return v

def cargar_parquet(path):
    df = pd.read_parquet(path)
    validar_df(df)
    cols = [str(c) for c in df.columns]
    source = str(df["_source"].iloc[0])
    ingested = pd.Timestamp(df["_ingested_at"].iloc[0]).to_pydatetime()
    with psycopg2.connect(_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute("create schema if not exists bronze")
            cur.execute("select column_name from information_schema.columns where table_schema='bronze' and table_name=%s order by ordinal_position",(TABLE,))
            existing = [r[0] for r in cur.fetchall()]
            if not existing:
                defs = [sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(_tipo(df[c]))) for c in cols]
                cur.execute(sql.SQL("create table {}.{} ({})").format(sql.Identifier("bronze"),sql.Identifier(TABLE),sql.SQL(", ").join(defs)))
            elif existing != cols:
                raise ValueError(f"schema existente no coincide: {existing}")
            cur.execute(sql.SQL('select count(*) from {}.{} where "_source"=%s and "_ingested_at"=%s').format(sql.Identifier("bronze"),sql.Identifier(TABLE)),(source,ingested))
            n = int(cur.fetchone()[0])
            if n:
                if n != len(df): raise ValueError(f"snapshot parcial {n}/{len(df)}")
                return 0, len(df)
            rows = [tuple(_py(v) for v in r) for r in df.itertuples(index=False,name=None)]
            stmt = sql.SQL("insert into {}.{} ({}) values %s").format(sql.Identifier("bronze"),sql.Identifier(TABLE),sql.SQL(", ").join(sql.Identifier(c) for c in cols))
            execute_values(cur, stmt.as_string(conn), rows, page_size=500)
        conn.commit()
    return len(df), len(df)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--parquet", required=True); a=ap.parse_args()
    i,t = cargar_parquet(a.parquet)
    print(f"OK DS-06: bronze.{TABLE} — {i} insertadas / {t} snapshot")
