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
    """DS-07 CONEVAL: rezago social y pobreza a nivel municipio. BUG-045: el esquema real
    (migrado por Deni, ver vault/14_Data_Sources/DS-07_CONEVAL_Rezago_Social.md S11) son DOS
    tablas -- bronze.coneval_irs_2020 y bronze.coneval_pobreza_2020 -- con las columnas
    oficiales serializadas como identificadores hasheados c_<sha1[:12]> por
    src/ingesta/cargar_bronze_coneval_real.py, que es lo que
    dbt/models/silver/rezago_municipio.sql lee. El esquema "amigable" viejo de una sola
    tabla (cve_mun/entidad/municipio/indice_rezago_social/grado_rezago/pobreza_pct) ya no
    tiene destino en el pipeline: se reemplaza, no se conserva en paralelo.

    Los hashes de columna son deterministicos (sha1 del encabezado oficial real, primeros 12
    hex) y se toman tal cual del manifest real generado por una carga real de DS-07
    (data/bronze/coneval/manifests/ds07_postgres_columns_*.json, verificado 2026-09-04):
    c_b9548dbd414b="Clave entidad", c_deef5d1bd71a="Clave municipio",
    c_9b370f449788="Entidad federativa", c_9e8609cad84d="Municipio",
    c_5d0523b1d4a3="Índice de rezago social", c_91fd46c9babe="Grado de rezago social" (IRS);
    c_9bd1a7aa7fca="Clave de entidad", c_764f3baf1395="Clave de municipio",
    c_1a3c72ae6dd1="Pobreza | Porcentaje 2020" (pobreza). Solo se fixturan las columnas que
    el modelo Silver realmente lee -- el Parquet real trae 19/146 columnas por producto, el
    resto no lo consume ningún modelo.

    Un municipio queda deliberadamente SIN_DATO (índice e IRS vacíos) para probar la rama de
    cobertura de Silver."""
    path_irs = os.path.join(FIXTURES_DIR, "bronze_coneval_irs_sample.csv")
    path_pobreza = os.path.join(FIXTURES_DIR, "bronze_coneval_pobreza_sample.csv")
    cols_irs = [
        "c_b9548dbd414b", "c_deef5d1bd71a", "c_9b370f449788", "c_9e8609cad84d",
        "c_5d0523b1d4a3", "c_91fd46c9babe", "_periodo_medicion",
        "_ingested_at", "_source", "_source_url",
    ]
    cols_pobreza = [
        "c_9bd1a7aa7fca", "c_764f3baf1395", "c_9b370f449788", "c_9e8609cad84d",
        "c_1a3c72ae6dd1", "_periodo_medicion",
        "_ingested_at", "_source", "_source_url",
    ]
    grados = ["muy bajo", "bajo", "medio", "alto", "muy alto"]
    meta = {
        "_periodo_medicion": "2020",
        "_ingested_at": INGESTED_AT,
        "_source": "DS-07_CONEVAL",
        "_source_url": "https://www.coneval.org.mx/Medicion/Paginas/Indice_Rezago_Social.aspx",
    }

    with open(path_irs, "w", newline="") as f_irs, open(path_pobreza, "w", newline="") as f_pobreza:
        w_irs = csv.DictWriter(f_irs, fieldnames=cols_irs)
        w_irs.writeheader()
        w_pobreza = csv.DictWriter(f_pobreza, fieldnames=cols_pobreza)
        w_pobreza.writeheader()
        for i, (ent, mun) in enumerate(municipios):
            nombre_ent = NOMBRE_ENTIDAD.get(ent, f"Entidad {ent}")
            nombre_mun = f"Municipio {ent}{mun}"
            sin_dato = i == 0

            row_irs = {
                "c_b9548dbd414b": ent,
                "c_deef5d1bd71a": mun,
                "c_9b370f449788": nombre_ent,
                "c_9e8609cad84d": nombre_mun,
                "c_5d0523b1d4a3": "" if sin_dato else str(round(-1.5 + i * 0.35, 4)),
                "c_91fd46c9babe": "" if sin_dato else grados[i % len(grados)],
            }
            row_irs.update(meta)
            w_irs.writerow(row_irs)

            row_pobreza = {
                "c_9bd1a7aa7fca": ent,
                "c_764f3baf1395": mun,
                "c_9b370f449788": nombre_ent,
                "c_9e8609cad84d": nombre_mun,
                "c_1a3c72ae6dd1": "" if sin_dato else str(round(20.0 + i * 4.2, 2)),
            }
            row_pobreza.update(meta)
            w_pobreza.writerow(row_pobreza)

    return (path_irs, path_pobreza), len(municipios)


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
    (p2_irs, p2_pobreza), n2 = generar_coneval(municipios)
    p3, n3 = generar_sesnsp(municipios)
    print(f"OK: {p1} ({n1} filas)")
    print(f"OK: {p2_irs} ({n2} filas)")
    print(f"OK: {p2_pobreza} ({n2} filas)")
    print(f"OK: {p3} ({n3} filas)")