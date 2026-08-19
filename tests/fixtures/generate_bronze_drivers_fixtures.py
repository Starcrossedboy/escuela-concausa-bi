"""Genera fixtures Bronze (<=500 filas, anonimizados) para cemabe, coneval y sesnsp,
alineados a las mismas 72 CCT / 12 municipios que ya usa bronze_formato911_sample.csv,
para poder validar gold.features_escuela (US-104) con datos reales (no solo compile).

Uso:
    python tests/fixtures/generate_bronze_drivers_fixtures.py
"""
import csv
import os

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))
FORMATO911_PATH = os.path.join(FIXTURES_DIR, "bronze_formato911_sample.csv")

INGESTED_AT = "2026-08-18T12:00:00+00:00"


def _leer_ccts_y_municipios():
    with open(FORMATO911_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    ccts = sorted({row["cct"].upper().zfill(10) for row in rows})
    municipios = sorted({
        (row["entidad"].zfill(2), row["municipio"].zfill(3)) for row in rows
    })
    return ccts, municipios


def generar_cemabe(ccts):
    """DS-03 CEMABE: infraestructura escolar a nivel CCT. Incluye un caso SIN_DATO
    deliberado (fila con campos vacíos) para probar la rama de cobertura en D3/D4."""
    path = os.path.join(FIXTURES_DIR, "bronze_cemabe_sample.csv")
    cols = [
        "cct", "agua_red", "drenaje", "electricidad", "sanitarios",
        "internet", "computadoras", "_ingested_at", "_source", "_source_url",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, cct in enumerate(ccts):
            if i % 11 == 0:
                # Escuela sin datos de infraestructura todavía (SIN_DATO explícito)
                row = {
                    "cct": cct, "agua_red": "", "drenaje": "", "electricidad": "",
                    "sanitarios": "", "internet": "", "computadoras": "",
                }
            else:
                row = {
                    "cct": cct,
                    "agua_red": "1" if i % 3 != 0 else "0",
                    "drenaje": "1" if i % 4 != 0 else "0",
                    "electricidad": "1" if i % 5 != 0 else "0",
                    "sanitarios": "1" if i % 6 != 0 else "0",
                    "internet": "1" if i % 2 == 0 else "0",
                    "computadoras": "1" if i % 3 == 0 else "0",
                }
            row.update({
                "_ingested_at": INGESTED_AT,
                "_source": "DS-03_CEMABE",
                "_source_url": "https://www.inegi.org.mx/programas/cemabe/2013/",
            })
            w.writerow(row)
    return path, len(ccts)


NOMBRE_ENTIDAD = {
    "01": "Aguascalientes", "09": "Ciudad de Mexico", "14": "Jalisco",
    "15": "Mexico", "19": "Nuevo Leon", "20": "Oaxaca",
}


def generar_coneval(municipios):
    """DS-07 CONEVAL: rezago social y pobreza a nivel municipio. `entidad`/`municipio` son
    los NOMBRES (Data_Model.md §6: nombre_entidad/nombre_municipio vienen de DS-07), no las
    claves -- las claves numericas ya viven aparte en cve_mun. Un municipio queda
    deliberadamente SIN_DATO (indice_rezago_social vacío)."""
    path = os.path.join(FIXTURES_DIR, "bronze_coneval_sample.csv")
    cols = [
        "cve_mun", "entidad", "municipio", "indice_rezago_social",
        "grado_rezago", "pobreza_pct", "_ingested_at", "_source", "_source_url",
    ]
    grados = ["muy bajo", "bajo", "medio", "alto", "muy alto"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, (ent, mun) in enumerate(municipios):
            cve_mun = ent + mun
            nombre_ent = NOMBRE_ENTIDAD.get(ent, f"Entidad {ent}")
            nombre_mun = f"Municipio {cve_mun}"
            if i == 0:
                row = {
                    "cve_mun": cve_mun, "entidad": nombre_ent, "municipio": nombre_mun,
                    "indice_rezago_social": "", "grado_rezago": "", "pobreza_pct": "",
                }
            else:
                row = {
                    "cve_mun": cve_mun, "entidad": nombre_ent, "municipio": nombre_mun,
                    "indice_rezago_social": str(round(-1.5 + i * 0.35, 4)),
                    "grado_rezago": grados[i % len(grados)],
                    "pobreza_pct": str(round(20.0 + i * 4.2, 2)),
                }
            row.update({
                "_ingested_at": INGESTED_AT,
                "_source": "DS-07_CONEVAL",
                "_source_url": "https://www.coneval.org.mx/Medicion/Paginas/Indice_Rezago_Social.aspx",
            })
            w.writerow(row)
    return path, len(municipios)


def generar_sesnsp(municipios):
    """DS-04 SESNSP: incidencia delictiva municipal, serie mensual. 3 meses x tipo de
    delito por municipio, para que D2 tenga variación real al agregar."""
    path = os.path.join(FIXTURES_DIR, "bronze_sesnsp_sample.csv")
    cols = [
        "cve_ent", "cve_mun", "anio", "mes", "tipo_delito", "conteo",
        "_ingested_at", "_source", "_source_url",
    ]
    tipos = ["robo a casa habitacion", "robo de vehiculo"]
    n = 0
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, (ent, mun) in enumerate(municipios):
            cve_mun = ent + mun
            for mes in (1, 2, 3):
                for j, tipo in enumerate(tipos):
                    w.writerow({
                        "cve_ent": ent,
                        "cve_mun": cve_mun,
                        "anio": "2024",
                        "mes": str(mes),
                        "tipo_delito": tipo,
                        "conteo": str(2 + (i * 3 + mes + j) % 15),
                        "_ingested_at": INGESTED_AT,
                        "_source": "DS-04_SESNSP",
                        "_source_url": "https://www.gob.mx/sesnsp/acciones-y-programas/incidencia-delictiva-del-fuero-comun-nueva-metodologia",
                    })
                    n += 1
    return path, n


if __name__ == "__main__":
    ccts, municipios = _leer_ccts_y_municipios()
    p1, n1 = generar_cemabe(ccts)
    p2, n2 = generar_coneval(municipios)
    p3, n3 = generar_sesnsp(municipios)
    print(f"OK: {p1} ({n1} filas)")
    print(f"OK: {p2} ({n2} filas)")
    print(f"OK: {p3} ({n3} filas)")