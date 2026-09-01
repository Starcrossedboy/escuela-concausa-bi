"""
Fixtures sintéticas para US-221 (Series de matrícula, distribución por nivel
educativo y tarjetas de KPI reutilizables).

Reglas seguidas (ver Plan de Sprint §8 y Screen_Specs.md):
- Dataset ≤500 filas, anonimizado, sin datos personales ni reales.
- Alcance geográfico: SCOPE_ENTIDADES = 09 (CDMX), 15 (Edomex), 19 (Nuevo León), 14 (Jalisco).
- Llaves de cruce: CCT sintético + clave INEGI de municipio (cve_mun, 5 dígitos).
- Se deja explícitamente una fracción de escuelas SIN cobertura de predicción (ML-01
  aún no las ha puntuado) para poder probar que KPI-03/04 filtran correctamente y que
  ninguna consulta finge un 0 donde hay SIN_DATO.

Uso:
    python generate_fixtures.py           # crea fixtures.db (SQLite) en este directorio
"""
import random
import sqlite3
from pathlib import Path

random.seed(221)  # determinista, como pide la regla de fixtures del plan de sprint

DB_PATH = Path(__file__).parent / "fixtures.db"

SCOPE_ENTIDADES = {
    "09": ("Ciudad de México", ["Álvaro Obregón", "Coyoacán", "Iztapalapa"]),
    "15": ("México", ["Toluca", "Naucalpan", "Ecatepec"]),
    "19": ("Nuevo León", ["Monterrey", "San Pedro Garza García", "Apodaca"]),
    "14": ("Jalisco", ["Guadalajara", "Zapopan", "Tlaquepaque"]),
}
NIVELES = ["Preescolar", "Primaria", "Secundaria", "Media Superior"]
CICLOS = ["2023-2024", "2024-2025", "2025-2026"]


def build_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE dim_tiempo (
            id_ciclo INTEGER PRIMARY KEY,
            ciclo TEXT NOT NULL,
            anio_inicio INTEGER NOT NULL
        );

        CREATE TABLE dim_municipio (
            cve_mun TEXT PRIMARY KEY,
            cve_ent TEXT NOT NULL,
            nombre_municipio TEXT NOT NULL,
            nombre_entidad TEXT NOT NULL
        );

        CREATE TABLE dim_escuela (
            cct TEXT PRIMARY KEY,
            nivel TEXT NOT NULL,
            sostenimiento TEXT NOT NULL,
            cve_mun TEXT NOT NULL REFERENCES dim_municipio(cve_mun)
        );

        CREATE TABLE fact_escuela_ciclo (
            cct TEXT NOT NULL REFERENCES dim_escuela(cct),
            id_ciclo INTEGER NOT NULL REFERENCES dim_tiempo(id_ciclo),
            cve_mun TEXT NOT NULL REFERENCES dim_municipio(cve_mun),
            matricula_total INTEGER NOT NULL,
            matricula_ciclo_anterior INTEGER NOT NULL,  -- denominador directo de KPI-02 (BUG-031)
            variacion_matricula REAL NOT NULL,          -- alumnos absolutos = total - anterior
            PRIMARY KEY (cct, id_ciclo)
        );

        CREATE TABLE predicciones (
            cct TEXT NOT NULL,
            id_ciclo INTEGER NOT NULL,
            modelo TEXT NOT NULL,
            indice_riesgo REAL,
            valor REAL,
            probabilidad REAL
        );
        """
    )


def seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    for i, ciclo in enumerate(CICLOS, start=1):
        cur.execute(
            "INSERT INTO dim_tiempo VALUES (?, ?, ?)", (i, ciclo, 2023 + i - 1)
        )

    municipios = []
    for cve_ent, (nombre_ent, munis) in SCOPE_ENTIDADES.items():
        for j, muni in enumerate(munis, start=1):
            cve_mun = f"{cve_ent}{j:03d}"
            municipios.append(cve_mun)
            cur.execute(
                "INSERT INTO dim_municipio VALUES (?, ?, ?, ?)",
                (cve_mun, cve_ent, muni, nombre_ent),
            )

    escuelas = []
    cct_seq = 1
    for cve_mun in municipios:
        for _ in range(random.randint(8, 12)):  # ~100-120 escuelas totales
            cct = f"FIC{cct_seq:04d}9"  # CCT sintético, nunca uno real
            cct_seq += 1
            nivel = random.choice(NIVELES)
            sostenimiento = random.choice(["Público", "Privado"])
            escuelas.append((cct, nivel, sostenimiento, cve_mun))
            cur.execute(
                "INSERT INTO dim_escuela VALUES (?, ?, ?, ?)",
                (cct, nivel, sostenimiento, cve_mun),
            )

    for id_ciclo, _ in enumerate(CICLOS, start=1):
        for cct, _nivel, _sost, cve_mun in escuelas:
            # Tras BUG-031 el fact guarda alumnos ABSOLUTOS, no una fracción: se genera la
            # matrícula del ciclo anterior como base y la del ciclo actual aplicándole una
            # tasa realista (±15/10 %); variacion_matricula es la diferencia en alumnos.
            # KPI-02 = SUM(matricula_total)/SUM(matricula_ciclo_anterior)-1 cae así en [-1, 1].
            matricula_anterior = random.randint(80, 900)
            tasa = random.uniform(-0.15, 0.10)
            matricula = max(1, round(matricula_anterior * (1 + tasa)))
            variacion = matricula - matricula_anterior
            cur.execute(
                "INSERT INTO fact_escuela_ciclo VALUES (?, ?, ?, ?, ?, ?)",
                (cct, id_ciclo, cve_mun, matricula, matricula_anterior, variacion),
            )

            # ML-01 aún no puntúa a todas las escuelas (llega en S4) -> SIN_DATO real.
            # Dejamos ~20% de escuelas sin predicción a propósito.
            if random.random() > 0.20:
                indice_riesgo = round(random.betavariate(2, 5), 4)  # sesgado a valores bajos
                cur.execute(
                    "INSERT INTO predicciones VALUES (?, ?, 'ML-01', ?, ?, ?)",
                    (
                        cct,
                        id_ciclo,
                        indice_riesgo,
                        round(random.uniform(-0.1, 0.1), 4),
                        round(random.uniform(0.5, 0.99), 4),
                    ),
                )

    conn.commit()


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    try:
        build_schema(conn)
        seed(conn)
        n_escuelas = conn.execute("SELECT COUNT(*) FROM dim_escuela").fetchone()[0]
        n_filas = conn.execute("SELECT COUNT(*) FROM fact_escuela_ciclo").fetchone()[0]
        print(f"Fixtures generadas en {DB_PATH}")
        print(f"  escuelas: {n_escuelas} | filas fact_escuela_ciclo: {n_filas}")
        assert n_filas <= 500, "Regla del plan de sprint: fixtures ≤500 filas"
    finally:
        conn.close()


if __name__ == "__main__":
    main()
