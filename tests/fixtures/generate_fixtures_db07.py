"""
Fixtures sintéticas para US-222 (DB-07 Calidad y cobertura de datos).

Replica el esquema REAL confirmado contra Postgres:
- gold.cubo_completitud (72 filas reales al validar, grano cve_mun x nivel x
  id_driver x id_ciclo)
- gold.geo_municipio (usada por db07_mapa_vacios.sql para el JOIN geométrico)

Reglas seguidas (mismas que US-221):
- Dataset ≤500 filas, anonimizado, sin datos reales.
- Alcance: SCOPE_ENTIDADES = ['09','15','19','14'].
- Se deja a propósito una mezcla de cobertura_driver = 'OK' / 'SIN_DATO' para
  poder probar que las razones SUM/SUM no cuentan SIN_DATO como cero.

Uso:
    python generate_fixtures.py    # crea fixtures.db (SQLite) en este directorio
"""
import random
import sqlite3
from pathlib import Path

random.seed(222)  # determinista

DB_PATH = Path(__file__).parent / "fixtures_db07.db"

SCOPE_ENTIDADES = {
    "09": ("Ciudad de Mexico", ["Coyoacan", "Benito Juarez"]),
    "15": ("Mexico", ["Naucalpan"]),
    "19": ("Nuevo Leon", ["Monterrey"]),
    "14": ("Jalisco", ["Guadalajara"]),
}
NIVELES = ["PREESCOLAR", "PRIMARIA", "SECUNDARIA", "MEDIA SUPERIOR"]
DRIVERS = [
    ("D1", "Pobreza y rezago social"),
    ("D2", "Inseguridad del entorno"),
    ("D3", "Infraestructura escolar"),
    ("D4", "Conectividad digital"),
    ("D5", "Estres hidrico"),
    ("D6", "Calidad del aire"),
]
CICLOS = [(1, "2023-2024", 2023), (2, "2024-2025", 2024)]


def build_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE cubo_completitud (
            cve_mun            TEXT NOT NULL,
            cve_ent            TEXT NOT NULL,
            nombre_municipio   TEXT NOT NULL,
            nombre_entidad     TEXT NOT NULL,
            nivel              TEXT NOT NULL,
            id_ciclo           INTEGER NOT NULL,
            ciclo              TEXT NOT NULL,
            anio_inicio        INTEGER NOT NULL,
            id_driver          TEXT NOT NULL,
            nombre_driver      TEXT NOT NULL,
            total_escuelas     INTEGER NOT NULL,
            escuelas_con_dato  INTEGER NOT NULL,
            escuelas_sin_dato  INTEGER NOT NULL,
            suma_completitud   REAL NOT NULL,
            cobertura_driver   TEXT NOT NULL
        );

        CREATE TABLE geo_municipio (
            cve_mun          TEXT PRIMARY KEY,
            nombre_municipio TEXT NOT NULL,
            geometria        TEXT NOT NULL
        );
        """
    )


def seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    municipios = []

    for cve_ent, (_nombre_ent, munis) in SCOPE_ENTIDADES.items():
        for j, muni in enumerate(munis, start=1):
            cve_mun = f"{cve_ent}{j:03d}"
            municipios.append((cve_mun, cve_ent, muni, _nombre_ent))
            cur.execute(
                "INSERT INTO geo_municipio VALUES (?, ?, ?)",
                (cve_mun, muni, f'[[[-99.{j},19.{j}],[-99.{j+1},19.{j}],[-99.{j+1},19.{j+1}],[-99.{j},19.{j+1}],[-99.{j},19.{j}]]]'),
            )

    n_rows = 0
    for cve_mun, cve_ent, nombre_municipio, nombre_entidad in municipios:
        for id_ciclo, ciclo, anio_inicio in CICLOS:
            for nivel in random.sample(NIVELES, k=2):  # 2 de 4 niveles por municipio/ciclo
                for id_driver, nombre_driver in DRIVERS:
                    total_escuelas = 1
                    # ~25% de las combinaciones quedan SIN_DATO a propósito
                    sin_dato = random.random() < 0.25
                    escuelas_con_dato = 0 if sin_dato else 1
                    escuelas_sin_dato = 1 if sin_dato else 0
                    suma_completitud = round(random.uniform(0.5, 1.0), 3)
                    cobertura_driver = "SIN_DATO" if sin_dato else "OK"
                    cur.execute(
                        "INSERT INTO cubo_completitud VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            cve_mun, cve_ent, nombre_municipio, nombre_entidad,
                            nivel, id_ciclo, ciclo, anio_inicio,
                            id_driver, nombre_driver,
                            total_escuelas, escuelas_con_dato, escuelas_sin_dato,
                            suma_completitud, cobertura_driver,
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
        n_municipios = conn.execute("SELECT COUNT(*) FROM geo_municipio").fetchone()[0]
        print(f"Fixtures generadas en {DB_PATH}")
        print(f"  municipios: {n_municipios} | filas cubo_completitud: {n_rows}")
        assert n_rows <= 500, "Regla del plan de sprint: fixtures <=500 filas"
    finally:
        conn.close()


if __name__ == "__main__":
    main()
