#!/usr/bin/env python3
"""
FARO — Cargar el asset GeoJSON municipal a gold.geo_municipio (US-203).

Lee `superset/assets/geojson/municipios_scope.geojson` (versionado en el repo)
y crea/llena la tabla LOCAL de geometrías que consume el coroplético de DB-02:

    gold.geo_municipio (cve_mun PK, nombre_municipio, cve_ent,
                        nombre_entidad, geometria TEXT)

`geometria` guarda el feature completo como texto GeoJSON: Superset lo lee con
deck_polygon (`line_column = 'geometria'`, `line_type = 'json'`). La llave
`cve_mun` es el CVEGEO INEGI de 5 dígitos, idéntico a gold.dim_municipio.cve_mun.

Idempotente sin DELETE/DROP (regla 3): CREATE TABLE IF NOT EXISTS +
ON CONFLICT DO NOTHING. Re-ejecutar no duplica ni revienta.

Uso:
    source .venv/bin/activate
    set -a; source .env; set +a          # POSTGRES_* para el DSN
    python superset/cargar_geojson_municipios.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

RAIZ = Path(__file__).resolve().parents[1]
ASSET = RAIZ / "superset" / "assets" / "geojson" / "municipios_scope.geojson"

DDL = """
CREATE SCHEMA IF NOT EXISTS gold;
CREATE TABLE IF NOT EXISTS gold.geo_municipio (
    cve_mun           TEXT PRIMARY KEY,
    nombre_municipio  TEXT,
    cve_ent           TEXT,
    nombre_entidad    TEXT,
    geometria         TEXT NOT NULL
);
"""

INSERT = """
INSERT INTO gold.geo_municipio
    (cve_mun, nombre_municipio, cve_ent, nombre_entidad, geometria)
VALUES %s
ON CONFLICT (cve_mun) DO NOTHING
"""

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _dsn() -> str:
    faltantes = [v for v in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD") if not os.environ.get(v)]
    if faltantes:
        logger.error("Faltan variables de entorno: %s (¿source .env?)", ", ".join(faltantes))
        sys.exit(1)
    # El .env apunta a 'db' (nombre del servicio en la red Docker, para Superset).
    # Este script corre en el host, donde 'db' no resuelve: se traduce a localhost.
    host = "localhost" if os.environ["POSTGRES_HOST"] == "db" else os.environ["POSTGRES_HOST"]
    return (
        f"host={host} port={os.environ['POSTGRES_PORT']} "
        f"dbname={os.environ['POSTGRES_DB']} user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )


def cargar(ruta_asset: Path) -> int:
    if not ruta_asset.exists():
        logger.error("No existe %s. Genéralo con generar_geojson_municipios.py", ruta_asset)
        sys.exit(1)

    asset = json.loads(ruta_asset.read_text(encoding="utf-8"))
    filas = [
        (
            feat["properties"]["cve_mun"],
            feat["properties"].get("nombre_municipio"),
            feat["properties"].get("cve_ent"),
            feat["properties"].get("nombre_entidad"),
            json.dumps(feat, ensure_ascii=False, separators=(",", ":")),
        )
        for feat in asset["features"]
    ]

    with psycopg2.connect(_dsn()) as conn, conn.cursor() as cur:
        cur.execute(DDL)
        psycopg2.extras.execute_values(cur, INSERT, filas, page_size=500)
        cur.execute("SELECT count(*) FROM gold.geo_municipio")
        total = cur.fetchone()[0]

    logger.info("gold.geo_municipio: %d features en el asset, %d filas en total", len(filas), total)
    return len(filas)


if __name__ == "__main__":
    cargar(ASSET)
