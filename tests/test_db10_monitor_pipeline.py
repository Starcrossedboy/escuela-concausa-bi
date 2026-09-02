"""
TEST-US223-01 · Valida el dataset de US-223 (DB-10 Monitor del pipeline)
contra fixtures sintéticas que replican el esquema real de
gold.cubo_pipeline (confirmado leyendo dbt/models/gold/cubo_pipeline.sql —
no se pudo materializar contra Postgres real: Bronze/Silver incompletos en
este ambiente, ver Cube_Specs_DB10.md §Bloqueo).

Igual que en US-221/US-222: este test lee el .sql real de producción y solo
le quita el prefijo de esquema "gold." para poder correrlo en SQLite.

Correr con:
    pytest tests/test_db10_monitor_pipeline.py -v
"""
import sqlite3
from pathlib import Path

import pytest

FIXTURES_DB = Path(__file__).parent / "fixtures" / "fixtures_db10.db"
SQL_DIR = Path(__file__).parent.parent / "superset" / "semantic"

FUENTES_ESPERADAS = {"DS-01", "DS-02", "DS-03", "DS-04", "DS-05", "DS-06", "DS-07", "DS-08"}


def load_sql(filename: str) -> str:
    """Lee un .sql de producción y lo adapta solo para poder correrlo en
    SQLite (quita el prefijo de esquema 'gold.'). La lógica no se toca."""
    if not FIXTURES_DB.exists():
        from tests.fixtures.generate_fixtures_db10 import main as generar
        generar()
    raw = (SQL_DIR / filename).read_text(encoding="utf-8")
    lines = [l for l in raw.splitlines() if not l.strip().startswith("--")]
    return "\n".join(lines).replace("gold.", "")


@pytest.fixture(scope="module")
def conn():
    if not FIXTURES_DB.exists():
        from tests.fixtures.generate_fixtures_db10 import main as generar
        generar()
    connection = sqlite3.connect(FIXTURES_DB)
    yield connection
    connection.close()


def test_db10_cubo_pipeline_incluye_las_8_fuentes(conn):
    sql = load_sql("db10_cubo_pipeline.sql")
    rows = conn.execute(sql).fetchall()
    id_fuentes = {row[0] for row in rows}
    assert id_fuentes == FUENTES_ESPERADAS, (
        "El catálogo debe conservar las 8 fuentes esperadas, incluso las "
        "que no han ingerido nada todavía (SIN_DATO, nunca desaparecen)"
    )


def test_fuentes_sin_dato_no_cuentan_filas_como_cero(conn):
    sql = load_sql("db10_cubo_pipeline.sql")
    rows = conn.execute(sql).fetchall()
    # columnas: id_fuente, fuente, fecha_ingesta, filas, _ingested_at, source_url,
    # cobertura_pipeline, es_ok, es_sin_dato
    for row in rows:
        id_fuente, _fuente, _fecha, filas, _ts, _url, cobertura, _es_ok, _es_sin_dato = row
        if cobertura == "SIN_DATO":
            assert filas is None, (
                f"{id_fuente} está SIN_DATO pero 'filas' no es NULL — "
                "nunca debe rellenarse con 0"
            )
        else:
            assert filas is not None and filas > 0, (
                f"{id_fuente} está OK pero 'filas' es None o <= 0"
            )


def test_kpi13_suma_filas_excluye_sin_dato(conn):
    """KPI-13: SUM(filas) debe ignorar automáticamente las fuentes SIN_DATO
    (SQL NULL se excluye del SUM nativamente), no contarlas como cero."""
    sql = load_sql("db10_cubo_pipeline.sql")
    rows = conn.execute(sql).fetchall()

    suma_manual = sum(row[3] for row in rows if row[3] is not None)
    suma_sql = conn.execute(f"SELECT SUM(filas) FROM ({sql})").fetchone()[0]
    assert suma_sql == suma_manual, (
        "SUM(filas) debe coincidir con la suma manual de las filas no-NULL"
    )
    assert suma_sql > 0


def test_al_menos_una_fuente_sin_dato_en_fixtures(conn):
    """Verifica que las fixtures sí ejercitan el caso SIN_DATO (si esto
    falla, los tests de arriba dejan de probar algo real)."""
    sql = load_sql("db10_cubo_pipeline.sql")
    rows = conn.execute(sql).fetchall()
    sin_dato = [row for row in rows if row[6] == "SIN_DATO"]
    assert len(sin_dato) > 0, "Las fixtures deben incluir al menos una fuente SIN_DATO"


def test_grano_id_fuente_fecha_ingesta_sin_duplicados(conn):
    sql = load_sql("db10_cubo_pipeline.sql")
    rows = conn.execute(sql).fetchall()
    claves = [(row[0], row[2]) for row in rows]  # id_fuente, fecha_ingesta
    assert len(claves) == len(set(claves)), (
        "No debe haber filas duplicadas para la misma combinación "
        "id_fuente + fecha_ingesta"
    )