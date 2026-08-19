"""Genera fixtures Bronze (<=500 filas, anonimizados) para bronze.cct (DS-02) y
bronze.conapo (DS-08), alineados a las mismas 72 CCT / 12 municipios de
bronze_formato911_sample.csv, para validar gold.dim_escuela y gold.dim_municipio (US-103)
con datos reales.

Uso:
    python tests/fixtures/generate_bronze_cct_conapo_fixtures.py
"""
import csv
import os

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))
FORMATO911_PATH = os.path.join(FIXTURES_DIR, "bronze_formato911_sample.csv")

INGESTED_AT = "2026-08-19T12:00:00+00:00"


def _leer_filas():
    with open(FORMATO911_PATH, newline="") as f:
        return list(csv.DictReader(f))


def generar_cct(rows):
    """DS-02 Catálogo CCT: identidad y georreferencia por escuela. Una fila SIN_DATO
    (lat/lon vacíos) para ejercer la rama de nulos permitidos en esas dos columnas."""
    path = os.path.join(FIXTURES_DIR, "bronze_cct_sample.csv")
    cols = [
        "cct", "nombre", "nivel", "sostenimiento", "entidad", "municipio",
        "latitud", "longitud", "_ingested_at", "_source", "_source_url",
    ]
    vistos = set()
    filas = []
    for i, row in enumerate(rows):
        cct = row["cct"].upper().zfill(10)
        if cct in vistos:
            continue
        vistos.add(cct)
        # coordenadas de ejemplo dentro de México, variadas por índice (no reales)
        lat = round(19.0 + (i % 20) * 0.15, 5)
        lon = round(-99.0 - (i % 15) * 0.20, 5)
        filas.append({
            "cct": cct,
            "nombre": f"Escuela {cct}",
            "nivel": row["nivel"],
            "sostenimiento": "PUBLICO" if i % 4 != 0 else "PRIVADO",
            "entidad": row["entidad"],
            "municipio": row["municipio"],
            "latitud": "" if i % 13 == 0 else str(lat),
            "longitud": "" if i % 13 == 0 else str(lon),
            "_ingested_at": INGESTED_AT,
            "_source": "DS-02_CATALOGO_CCT",
            "_source_url": "https://www.gob.mx/sep (pendiente confirmar URL real, ver DS-02.md)",
        })
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    return path, len(filas)


def generar_conapo(rows):
    """DS-08 CONAPO: proyecciones de población por municipio y grupo de edad. 3 grupos de
    edad por municipio (para que dim_municipio tenga que sumar, no solo leer 1 fila)."""
    path = os.path.join(FIXTURES_DIR, "bronze_conapo_sample.csv")
    cols = [
        "cve_ent", "cve_mun", "anio", "grupo_edad", "poblacion",
        "_ingested_at", "_source", "_source_url",
    ]
    municipios = sorted({(r["entidad"].zfill(2), r["municipio"].zfill(3)) for r in rows})
    grupos = [("0-14", 1), ("15-64", 3), ("65+", 1)]
    n = 0
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, (ent, mun) in enumerate(municipios):
            base = 8000 + i * 1500
            for grupo, factor in grupos:
                w.writerow({
                    "cve_ent": ent,
                    "cve_mun": ent + mun,
                    "anio": "2024",
                    "grupo_edad": grupo,
                    "poblacion": str(base * factor),
                    "_ingested_at": INGESTED_AT,
                    "_source": "DS-08_CONAPO",
                    "_source_url": "https://www.gob.mx/conapo",
                })
                n += 1
    return path, n


if __name__ == "__main__":
    rows = _leer_filas()
    p1, n1 = generar_cct(rows)
    p2, n2 = generar_conapo(rows)
    print(f"OK: {p1} ({n1} filas)")
    print(f"OK: {p2} ({n2} filas)")