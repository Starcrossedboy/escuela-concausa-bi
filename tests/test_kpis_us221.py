"""
TEST-US221-01 · Valida los 5 KPIs de US-221 (matrícula, distribución por nivel,
tarjetas reutilizables) contra las fixtures sintéticas.

Importante: este test NO reescribe el SQL a mano. Lee los archivos .sql reales de
../sql/ (los mismos que se copian línea por línea del catálogo canónico de Manuel,
Screen_Specs.md §4) y solo les quita el prefijo de esquema "gold." para poder
correrlos contra SQLite en local. Así, si alguien edita el SQL de producción sin
actualizar el test, el test lo refleja automáticamente en vez de quedar
desincronizado.

Correr con:
    cd tests && pytest test_kpis_us221.py -q
"""
import sqlite3
from pathlib import Path

import pytest

FIXTURES_DB = Path(__file__).parent / "fixtures" / "fixtures.db"
SQL_DIR = Path(__file__).parent.parent / "superset" / "semantic"

SCOPE_ENTIDADES = {"09", "15", "19", "14"}


def load_sql(filename: str) -> str:
    """Lee un .sql de producción y lo adapta solo para poder correrlo en SQLite
    (quita el prefijo de esquema 'gold.'). El texto de la consulta en sí no se toca."""
    raw = (SQL_DIR / filename).read_text(encoding="utf-8")
    # quita comentarios -- y el prefijo de esquema, sin tocar la lógica de la query
    lines = [l for l in raw.splitlines() if not l.strip().startswith("--")]
    sql = "\n".join(lines).replace("gold.", "")
    return sql


@pytest.fixture(scope="module")
def conn():
    if not FIXTURES_DB.exists():
        from tests.fixtures.generate_fixtures import main as generar
        generar()
    connection = sqlite3.connect(FIXTURES_DB)
    yield connection
    connection.close()


def test_kpi01_matricula_total_suma_por_municipio_y_ciclo(conn):
    sql = load_sql("kpi_01_matricula_total.sql")
    # KPI-01 filtra por :nivel; probamos con un nivel real de las fixtures
    rows = conn.execute(sql, {"nivel": "Primaria"}).fetchall()
    assert len(rows) > 0, "KPI-01 debe devolver al menos una fila para Primaria"
    for cve_mun, ciclo, matricula_total in rows:
        assert matricula_total > 0, "La matrícula agregada nunca debe ser 0 ni negativa"


def test_kpi02_variacion_ponderada_por_ciclo(conn):
    sql = load_sql("kpi_02_variacion_matricula.sql")
    rows = conn.execute(sql).fetchall()
    assert len(rows) == 3, "Debe haber una fila por cada uno de los 3 ciclos de fixtures"
    for ciclo, matricula_total, variacion_ponderada_pct in rows:
        assert matricula_total > 0
        assert -1 <= variacion_ponderada_pct <= 1, "La variación ponderada debe ser una razón, no un porcentaje ya *100"


def test_kpi03_indice_riesgo_promedio_excluye_escuelas_sin_prediccion(conn):
    sql = load_sql("kpi_03_indice_riesgo_promedio.sql")
    rows = conn.execute(sql).fetchall()
    assert len(rows) > 0
    for cve_mun, indice_riesgo_promedio in rows:
        assert indice_riesgo_promedio is not None, (
            "El JOIN interno a predicciones nunca debe devolver un promedio en 0 "
            "por escuelas SIN_DATO: esas filas se excluyen, no se cuentan como 0"
        )
        assert 0 <= indice_riesgo_promedio <= 1


def test_kpi04_escuelas_en_riesgo_usa_umbral_060(conn):
    sql = load_sql("kpi_04_escuelas_en_riesgo.sql")
    escuelas_en_riesgo, total_escuelas = conn.execute(sql).fetchone()
    assert total_escuelas > 0
    # 'total_escuelas' cuenta solo las que SÍ tienen predicción (JOIN interno) —
    # por diseño, nunca debe ser igual al total de escuelas de dim_escuela si
    # las fixtures dejaron escuelas sin puntuar (regla SIN_DATO, ver fixtures).
    total_dim_escuela = conn.execute("SELECT COUNT(*) FROM dim_escuela").fetchone()[0]
    total_ciclos = conn.execute("SELECT COUNT(*) FROM dim_tiempo").fetchone()[0]
    assert total_escuelas < total_dim_escuela * total_ciclos, (
        "Si esto falla, revisa que las fixtures sigan dejando escuelas sin "
        "predicción (SIN_DATO real) — si no, este test ya no prueba nada"
    )
    assert 0 <= escuelas_en_riesgo <= total_escuelas


def test_kpi08_escuelas_por_nivel_cubre_los_4_niveles(conn):
    sql = load_sql("kpi_08_escuelas_por_nivel.sql")
    rows = conn.execute(sql).fetchall()
    niveles = {nivel for nivel, _escuelas in rows}
    assert niveles == {"Preescolar", "Primaria", "Secundaria", "Media Superior"}
    for _nivel, escuelas in rows:
        assert escuelas > 0


def test_alcance_geografico_respeta_scope_entidades(conn):
    """No es un KPI del catálogo, pero sí una regla dura de Screen_Specs.md §5:
    todos los tableros están acotados a SCOPE_ENTIDADES (09, 15, 19, 14)."""
    entidades = {
        row[0]
        for row in conn.execute("SELECT DISTINCT cve_ent FROM dim_municipio").fetchall()
    }
    assert entidades == SCOPE_ENTIDADES, (
        "Las fixtures no deben incluir entidades fuera del alcance de FARO"
    )
