"""Carga el Parquet conformado de DS-03 en ``bronze.cemabe_2013``."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

try:
    from src.ingesta.cargar_bronze_fixture import COLUMNAS_CEMABE, DDL_BRONZE_CEMABE
except ModuleNotFoundError:  # Airflow agrega /opt/airflow/src al sys.path.
    from ingesta.cargar_bronze_fixture import COLUMNAS_CEMABE, DDL_BRONZE_CEMABE

TABLA = "cemabe_2013"


def _dsn() -> str:
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'escuela_concausa_db')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', '')}"
    )


def cargar_cemabe(parquet_path: str) -> tuple[int, int]:
    """Inserta un snapshot completo y evita cargas parciales o duplicadas."""
    ruta = Path(parquet_path)
    if not ruta.is_file():
        raise FileNotFoundError(ruta)
    df = pd.read_parquet(ruta)
    faltantes = set(COLUMNAS_CEMABE) - set(df.columns)
    if faltantes or df.empty:
        raise ValueError(f"{ruta}: faltantes={sorted(faltantes)}, filas={len(df)}")

    fuentes = set(df["_source"].dropna().astype(str))
    ingestas = pd.to_datetime(df["_ingested_at"], utc=True).dropna().unique()
    if fuentes != {"DS-03_CEMABE"} or len(ingestas) != 1:
        raise ValueError(f"{ruta}: snapshot inválido; fuentes={fuentes}, ingestas={len(ingestas)}")

    columnas_sql = [f'"{col}"' for col in COLUMNAS_CEMABE]
    registros = [
        tuple(None if pd.isna(valor) else valor for valor in fila)
        for fila in df[COLUMNAS_CEMABE].itertuples(index=False, name=None)
    ]
    snapshot = pd.Timestamp(ingestas[0]).to_pydatetime()

    with psycopg2.connect(_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL_BRONZE_CEMABE.format(tabla=TABLA))
            cur.execute(
                f"SELECT count(*) FROM bronze.{TABLA} WHERE _source = %s AND _ingested_at = %s",
                ("DS-03_CEMABE", snapshot),
            )
            existentes = int(cur.fetchone()[0])
            if existentes:
                if existentes != len(registros):
                    raise ValueError(
                        f"bronze.{TABLA}: snapshot parcial existente "
                        f"({existentes}/{len(registros)})"
                    )
                return 0, existentes

            resultado = execute_values(
                cur,
                f"INSERT INTO bronze.{TABLA} ({', '.join(columnas_sql)}) VALUES %s "
                "ON CONFLICT (_source, _ingested_at, cct) DO NOTHING RETURNING 1",
                registros,
                page_size=500,
                fetch=True,
            )
        conn.commit()
    return len(resultado), len(registros)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parquet", help="Ruta producida por extractor_cemabe.py")
    args = parser.parse_args()
    insertadas, total = cargar_cemabe(args.parquet)
    print(f"bronze.{TABLA}: {insertadas}/{total} filas insertadas")
