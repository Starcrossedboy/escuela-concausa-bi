"""
Fixtures sintéticas para US-223 (DB-10 Monitor del pipeline).

Replica el esquema REAL confirmado en dbt/models/gold/cubo_pipeline.sql
(no se pudo materializar contra Postgres real: Bronze/Silver incompletos
en este ambiente — ver docs/Cube_Specs_DB10.md §Bloqueo).

Reglas seguidas (mismas que US-221/US-222):
- Dataset ≤500 filas, anonimizado, sin datos reales.
- Se incluyen las 8 fuentes esperadas del catálogo (DS-01..DS-08), dejando
  a propósito 2-3 sin ingesta (cobertura_pipeline='SIN_DATO') para probar
  que el SUM(filas) las excluye en vez de contarlas como 0.

Uso:
    python generate_fixtures_db10.py    # crea fixtures_db10.db (SQLite)
"""
import random
import sqlite3
from pathlib import Path
from datetime import date, timedelta

random.seed(223)  # determinista

DB_PATH = Path(__file__).parent / "fixtures_db10.db"

FUENTES_ESPERADAS = [
    ("DS-01", "DS-01_FORMATO911"),
    ("DS-02", "DS-02_CATALOGO_CCT"),
    ("DS-03", "DS-03_CEMABE"),
    ("DS-04", "DS-04_SESNSP"),
    ("DS-05", "DS-05_SINAICA"),
    ("DS-06", "DS-06_CONAGUA_SINA"),
    ("DS-07", "DS-07_CONEVAL"),
    ("DS-08", "DS-08_CONAPO"),
]

# Fuentes que a propósito se dejan SIN_DATO (mismo patrón de bloqueo real
# que documentamos: Bronze incompleto afecta justo a varias de estas)
SIN_DATO = {"DS-04", "DS-06", "DS-08"}


def build_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE cubo_pipeline (
            id_fuente          TEXT NOT NULL,
            fuente             TEXT NOT NULL,
            fecha_ingesta      TEXT,
            filas              INTEGER,
            _ingested_at       TEXT,
            source_url         TEXT,
            cobertura_pipeline TEXT NOT NULL
        );
        """
    )


def seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    hoy = date(2026, 8, 30)
    n_rows = 0

    for id_fuente, fuente in FUENTES_ESPERADAS:
        if id_fuente in SIN_DATO:
            cur.execute(
                "INSERT INTO cubo_pipeline VALUES (?,?,?,?,?,?,?)",
                (id_fuente, fuente, None, None, None, None, "SIN_DATO"),
            )
            n_rows += 1
        else:
            # cada fuente OK tiene 1-2 fechas de ingesta recientes
            for dias_atras in random.sample(range(5), k=random.randint(1, 2)):
                fecha = (hoy - timedelta(days=dias_atras)).isoformat()
                filas = random.randint(50, 5000)
                cur.execute(
                    "INSERT INTO cubo_pipeline VALUES (?,?,?,?,?,?,?)",
                    (
                        id_fuente, fuente, fecha, filas,
                        f"{fecha}T10:00:00", f"https://fuente.example/{id_fuente.lower()}",
                        "OK",
                    ),
                )
                n_rows += 1

    conn.commit()
    return n_rows


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    try:
        build_schema(conn)
        n_rows = seed(conn)
        n_fuentes = conn.execute("SELECT COUNT(DISTINCT id_fuente) FROM cubo_pipeline").fetchone()[0]
        print(f"Fixtures generadas en {DB_PATH}")
        print(f"  fuentes: {n_fuentes} | filas cubo_pipeline: {n_rows}")
        assert n_rows <= 500, "Regla del plan de sprint: fixtures <=500 filas"
    finally:
        conn.close()


if __name__ == "__main__":
    main()