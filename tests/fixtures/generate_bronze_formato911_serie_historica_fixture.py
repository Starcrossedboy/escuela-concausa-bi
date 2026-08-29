"""Genera un fixture Bronze COMPLEMENTARIO (<=500 filas) con DOS ciclos escolares ANTERIORES
(2021-2022, 2022-2023) para TODAS las CCT de bronze_formato911_sample.csv (BUG-026).

Por qué hace falta: `bronze_formato911_ciclo_anterior_fixture.py` (US-104) ya resuelve el LAG de
un ciclo para 25 CCT, pero `ventanas_posibles()` (particion_temporal.py) exige **3 ciclos ya con
target** en `gold.features_escuela` para admitir aunque sea 1 ventana de backtesting — y el primer
ciclo de cada cct siempre se sacrifica como referencia del LAG (`con_target` en
features_escuela.sql), así que hacen falta **4 ciclos crudos en Bronze**, no 2. Con solo
`bronze_formato911_sample.csv` + `..._ciclo_anterior_sample.csv`, `gold.features_escuela` sale con
un único `id_ciclo` (2024-2025, 25 filas) — verificado en este dev el 2026-08-29. Ver BUG-026
(Marina García del Buey, 06_Quality_Testing/Bug_Register.md).

`bronze_formato911_historico_sample.csv` (US-1xx, 6 ciclos reales) NO sirve para tapar este hueco:
se generó sobre su propio universo de CCT (`ENTIDAD_MUNICIPIO`, un municipio por entidad, folio
independiente) y comparte solo 3 de 30 CCT con `bronze.cct` — el catálogo real de escuelas — así
que a grano escuela el JOIN de `agregar_a_municipio_nivel()`/Gold se vacía **sin ningún error**
(el modo de falla silenciosa de BUG-012). Además alimenta una tabla Bronze distinta
(`bronze.formato911_historico` -> `silver.matricula_historica` -> `gold.matricula_municipio_nivel`,
el agregado municipio x nivel de DEC-007) que ni siquiera es la que `silver.matricula` consume.

Este generador sigue el patrón ya establecido por `..._ciclo_anterior_fixture.py`: **reutiliza las
CCT de `bronze_formato911_sample.csv` tal cual** (mismo cct, mismo entidad/municipio/nivel) en vez
de inventar un universo propio, así el 100% de solape con `bronze.cct`/`gold.dim_escuela` es
estructural, no una coincidencia que haya que perseguir. Se carga en la MISMA tabla
`bronze.formato911_2024_2025` (mismo esquema, misma llave UNIQUE) — es aditivo, no reemplaza ni
modifica ningún fixture existente ni ningún modelo dbt.

Uso:
    python tests/fixtures/generate_bronze_formato911_serie_historica_fixture.py
"""
import csv
import os

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))
FORMATO911_PATH = os.path.join(FIXTURES_DIR, "bronze_formato911_sample.csv")
OUT_PATH = os.path.join(FIXTURES_DIR, "bronze_formato911_serie_historica_sample.csv")

INGESTED_AT = "2026-08-18T13:00:00+00:00"

#: Ciclos que faltan para que `ventanas_posibles()` (min_ciclos_entrenamiento=2) admita una
#: ventana: con 2021-2022 + 2022-2023 + los 2 que ya existen (2023-2024, 2024-2025) da 4 ciclos
#: crudos por cct -> 3 con target ya calculado, uno de referencia (con_target excluye el primero).
CICLOS_NUEVOS = ["2021-2022", "2022-2023"]

COLUMNAS = [
    "cct", "ciclo", "entidad", "municipio", "nivel",
    "alumnos_total", "docentes_total", "grupos_total",
    "_ingested_at", "_source", "_source_url",
]


def _sin_duplicados_por_cct(rows: list[dict]) -> list[dict]:
    """Una fila por CCT (la primera que aparece en el fixture fuente), para no repetir CCT si
    `bronze_formato911_sample.csv` ya trae el mismo cct en más de un ciclo."""
    vistos: set[str] = set()
    unicas = []
    for row in rows:
        if row["cct"] not in vistos:
            vistos.add(row["cct"])
            unicas.append(row)
    return unicas


def generar():
    with open(FORMATO911_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    base = _sin_duplicados_por_cct(rows)

    with open(OUT_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        n_filas = 0
        for i, row in enumerate(base):
            alumnos_base = int(row["alumnos_total"])
            docentes = int(row["docentes_total"])
            grupos = int(row["grupos_total"])
            # Tendencia determinista hacia atrás en el tiempo (no aleatoria: mismo patrón de
            # reproducibilidad que ya usa `..._ciclo_anterior_fixture.py` con `(i % 7) - 3`),
            # con signo opuesto por ciclo para que 2021-2022 y 2022-2023 no queden idénticos.
            for paso, ciclo in enumerate(CICLOS_NUEVOS, start=1):
                delta = ((i % 7) - 3) * paso
                w.writerow({
                    "cct": row["cct"],
                    "ciclo": ciclo,
                    "entidad": row["entidad"],
                    "municipio": row["municipio"],
                    "nivel": row["nivel"],
                    "alumnos_total": max(alumnos_base - delta * 4, 1),
                    "docentes_total": docentes,
                    "grupos_total": grupos,
                    "_ingested_at": INGESTED_AT,
                    "_source": "DS-01_FORMATO911",
                    "_source_url": row["_source_url"],
                })
                n_filas += 1
    return OUT_PATH, n_filas, len(base)


if __name__ == "__main__":
    path, n_filas, n_ccts = generar()
    print(f"OK: {path} ({n_filas} filas, {n_ccts} CCT x {len(CICLOS_NUEVOS)} ciclos nuevos)")