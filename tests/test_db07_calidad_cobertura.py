"""
TEST-US222-01 · Valida los 2 datasets de US-222 (DB-07 Calidad y cobertura)
contra fixtures sintéticas que replican el esquema real de
gold.cubo_completitud y gold.geo_municipio (validado contra Postgres real
antes de escribir este test).

Igual que en US-221: este test NO reescribe el SQL a mano. Lee los archivos
.sql reales de producción y solo les quita el prefijo de esquema "gold." para
poder correrlos contra SQLite en local. Si el SQL de producción cambia sin
actualizar el test, el test lo refleja automáticamente.

Correr con:
    pytest tests/test_db07_calidad_cobertura.py -v
"""
import sqlite3
from pathlib import Path

import pytest

FIXTURES_DB = Path(__file__).parent / "fixtures" / "fixtures.db"
SQL_DIR = Path(__file__).parent.parent / "superset" / "semantic"

SCOPE_ENTIDADES = {"09", "15", "19", "14"}


def load_sql(filename: str) -> str:
    """Lee un .sql de producción y lo adapta solo para poder correrlo en
    SQLite (quita el prefijo de esquema 'gold.'). La lógica de la query no
    se toca."""
    if not FIXTURES_DB.exists():
        from tests.fixtures.generate_fixtures import main as generar
        generar()
    raw = (SQL_DIR / filename).read_text(encoding="utf-8")
    lines = [l for l in raw.splitlines() if not l.strip().startswith("--")]
    return "\n".join(lines).replace("gold.", "")


@pytest.fixture(scope="module")
def conn():
    if not FIXTURES_DB.exists():
        from tests.fixtures.generate_fixtures import main as generar
        generar()
    connection = sqlite3.connect(FIXTURES_DB)
    yield connection
    connection.close()


def test_db07_cubo_completitud_grano_detallado(conn):
    sql = load_sql("db07_cubo_completitud.sql")
    rows = conn.execute(sql).fetchall()
    assert len(rows) > 0, "Debe devolver filas al grano detallado"
    # columnas: ... total_escuelas, escuelas_con_dato, escuelas_sin_dato, suma_completitud, cobertura_driver
    for row in rows:
        total, con_dato, sin_dato, cobertura = row[-5], row[-4], row[-3], row[-1]
        assert con_dato + sin_dato == total, (
            "escuelas_con_dato + escuelas_sin_dato debe sumar total_escuelas en cada fila"
        )
        if cobertura == "SIN_DATO":
            assert con_dato == 0, "cobertura_driver='SIN_DATO' implica cero escuelas con dato"
        else:
            assert con_dato > 0, "cobertura_driver='OK' implica al menos una escuela con dato"


def test_kpi05_completitud_promedio_formula_suma_sobre_suma(conn):
    sql = load_sql("db07_cubo_completitud.sql")
    rows = conn.execute(sql).fetchall()
    suma_completitud = sum(r[-2] for r in rows)
    total_escuelas = sum(r[-5] for r in rows)
    completitud_promedio = suma_completitud / total_escuelas
    assert 0 <= completitud_promedio <= 1, (
        "KPI-05 (completitud_promedio) debe quedar en [0,1] al calcularse "
        "como SUM(suma_completitud)/SUM(total_escuelas)"
    )


def test_kpi06_pct_sin_dato_no_es_cero_cuando_hay_sin_dato(conn):
    sql = load_sql("db07_cubo_completitud.sql")
    rows = conn.execute(sql).fetchall()
    escuelas_sin_dato = sum(r[-3] for r in rows)
    total_escuelas = sum(r[-5] for r in rows)
    assert escuelas_sin_dato > 0, (
        "Las fixtures deben incluir SIN_DATO real para que este test pruebe algo"
    )
    pct_sin_dato = escuelas_sin_dato / total_escuelas
    assert pct_sin_dato > 0, (
        "KPI-06 nunca debe calcularse como 0 cuando existen escuelas SIN_DATO reales"
    )


def test_db07_mapa_vacios_grano_agregado_sin_duplicar_municipios(conn):
    sql = load_sql("db07_mapa_vacios.sql")
    rows = conn.execute(sql).fetchall()
    assert len(rows) > 0, "El mapa de vacíos debe devolver filas"

    # el grano debe ser único por (cve_mun, id_ciclo): nunca dos filas para
    # el mismo municipio+ciclo, o el mapa dibujaría polígonos duplicados
    claves = [(r[0], r[4]) for r in rows]  # cve_mun, id_ciclo
    assert len(claves) == len(set(claves)), (
        "db07_mapa_vacios no debe duplicar filas por municipio+ciclo "
        "(rompería el coroplético con polígonos superpuestos)"
    )


def test_db07_mapa_vacios_incluye_geometria(conn):
    sql = load_sql("db07_mapa_vacios.sql")
    rows = conn.execute(sql).fetchall()
    for row in rows:
        geometria = row[-1]
        assert geometria is not None and len(geometria) > 0, (
            "Cada fila del mapa debe traer su geometría vía JOIN a geo_municipio"
        )


def test_db07_mapa_vacios_suma_correctamente_el_detalle(conn):
    """El agregado municipal debe coincidir con la suma manual del detalle,
    confirmando que el GROUP BY sin nivel/driver no pierde ni duplica filas."""
    sql_detalle = load_sql("db07_cubo_completitud.sql")
    sql_mapa = load_sql("db07_mapa_vacios.sql")

    detalle = conn.execute(sql_detalle).fetchall()
    mapa = conn.execute(sql_mapa).fetchall()

    # total_escuelas manual por (cve_mun, id_ciclo) sumando el detalle
    manual = {}
    for row in detalle:
        cve_mun, id_ciclo, total = row[0], row[5], row[-5]
        key = (cve_mun, id_ciclo)
        manual[key] = manual.get(key, 0) + total

    for row in mapa:
        cve_mun, id_ciclo, total_agregado = row[0], row[4], row[7]
        key = (cve_mun, id_ciclo)
        assert manual.get(key) == total_agregado, (
            f"El total_escuelas agregado de {key} no coincide con la suma "
            "manual del detalle"
        )


def test_alcance_geografico_respeta_scope_entidades(conn):
    entidades = {
        row[0] for row in conn.execute("SELECT DISTINCT cve_ent FROM cubo_completitud").fetchall()
    }
    assert entidades.issubset(SCOPE_ENTIDADES), (
        "Las fixtures no deben incluir entidades fuera del alcance de FARO"
    )
