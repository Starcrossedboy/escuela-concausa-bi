"""Genera un fixture Bronze COMPLEMENTARIO (<=500 filas) con un ciclo escolar ANTERIOR para un
subconjunto de las mismas CCT de bronze_formato911_sample.csv.

Por qué hace falta: gold.features_escuela (US-104) calcula target_variacion_matricula con
LAG(matricula_total) OVER (PARTITION BY cct ORDER BY anio_inicio) y excluye explícitamente el
primer ciclo observado de cada cct (no hay "ciclo anterior" del cual calcular una variación real).
bronze_formato911_sample.csv (US-103) tiene 72 cct, cada una en un solo ciclo (2023-2024 o
2024-2025) — grano correcto para validar Silver/dim_tiempo, pero insuficiente para probar el LAG
de Gold: con un solo ciclo por cct, el filtro deja la tabla en 0 filas.

Este fixture reutiliza un subconjunto de las cct existentes y les agrega su ciclo "hermano"
(2023-2024 <-> 2024-2025) con una matrícula ligeramente distinta, para que el LAG tenga con qué
calcular una variación real. Se carga en la MISMA tabla bronze.formato911_2024_2025 (mismo
esquema, misma llave UNIQUE) — es aditivo, no reemplaza ni modifica el fixture de US-103.

Uso:
    python tests/fixtures/generate_bronze_formato911_ciclo_anterior_fixture.py
"""
import csv
import os

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))
FORMATO911_PATH = os.path.join(FIXTURES_DIR, "bronze_formato911_sample.csv")
OUT_PATH = os.path.join(FIXTURES_DIR, "bronze_formato911_ciclo_anterior_sample.csv")

INGESTED_AT = "2026-08-18T12:30:00+00:00"
CICLO_HERMANO = {"2023-2024": "2024-2025", "2024-2025": "2023-2024"}

COLUMNAS = [
    "cct", "ciclo", "entidad", "municipio", "nivel",
    "alumnos_total", "docentes_total", "grupos_total",
    "_ingested_at", "_source", "_source_url",
]


def generar(n_ccts: int = 25):
    with open(FORMATO911_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    seleccion = rows[:n_ccts]

    with open(OUT_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for i, row in enumerate(seleccion):
            alumnos = int(row["alumnos_total"])
            docentes = int(row["docentes_total"])
            grupos = int(row["grupos_total"])
            # variación real: unas escuelas crecen, otras decrecen (nunca 0 para todas)
            delta = (i % 7) - 3
            w.writerow({
                "cct": row["cct"],
                "ciclo": CICLO_HERMANO[row["ciclo"]],
                "entidad": row["entidad"],
                "municipio": row["municipio"],
                "nivel": row["nivel"],
                "alumnos_total": max(alumnos + delta * 5, 1),
                "docentes_total": docentes,
                "grupos_total": grupos,
                "_ingested_at": INGESTED_AT,
                "_source": "DS-01_FORMATO911",
                "_source_url": row["_source_url"],
            })
    return OUT_PATH, len(seleccion)


if __name__ == "__main__":
    path, n = generar()
    print(f"OK: {path} ({n} filas)")