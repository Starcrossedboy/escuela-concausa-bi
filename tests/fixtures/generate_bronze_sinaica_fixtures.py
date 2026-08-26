"""Genera fixtures Bronze (<=500 filas, anonimizados) para bronze.sinaica_estaciones y
bronze.sinaica_observaciones (DS-05), para validar el modelo de interpolacion IDW de D6
(calidad del aire) hacia las escuelas de dim_escuela (US-105, ADR-006).

Las coordenadas de las escuelas de prueba (bronze_cct_sample.csv) siguen la formula
lat = 19.0 + (i % 20) * 0.15, lon = -99.0 - (i % 15) * 0.20 (ver generate_bronze_cct_conapo_
fixtures.py). Aqui se colocan estaciones deliberadamente:
  - 2 estaciones cerca de la escuela con i=0 (lat=19.0, lon=-99.0) -- ambas dentro del radio
    de 15km, para ejercer el IDW ponderando 2 estaciones a la vez.
  - 1 estacion cerca de la escuela con i=5 (lat=19.75, lon=-100.0) -- dentro del radio, una
    sola estacion (IDW degenera al valor de esa estacion).
  - 1 estacion lejos de TODAS las escuelas de prueba (Baja California) -- nunca debe producir
    un valor OK, ejercita la rama SIN_DATO fuera de radio.
Tambien se incluyen lecturas invalidas (val=0) y de otro contaminante (PM10) que el modelo
debe descartar (solo usa PM2.5 con val=1).

Uso:
    python tests/fixtures/generate_bronze_sinaica_fixtures.py
"""
import csv
import os

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))
INGESTED_AT = "2026-08-19T12:00:00+00:00"

ESTACIONES = [
    # id, nombre, lat, lon, municipioId, estadoId
    (101, "Cerca-Escuela-i0-A", 19.02, -99.02, "01", "09"),
    (102, "Cerca-Escuela-i0-B", 19.10, -99.05, "01", "09"),
    (103, "Cerca-Escuela-i5", 19.78, -100.03, "05", "15"),
    (104, "Lejos-BajaCalifornia", 30.00, -115.00, "01", "02"),
]

# id_estacion -> [(parametro, valor, val), ...] lecturas horarias de prueba
OBSERVACIONES = {
    101: [("PM2.5", 25.0, 1), ("PM2.5", 27.0, 1), ("PM2.5", 999.0, 0), ("PM10", 80.0, 1)],
    102: [("PM2.5", 45.0, 1), ("PM2.5", 43.0, 1)],
    103: [("PM2.5", 60.0, 1), ("PM2.5", 58.0, 1), ("PM10", 90.0, 1)],
    104: [("PM2.5", 15.0, 1)],
}


def generar_estaciones():
    path = os.path.join(FIXTURES_DIR, "bronze_sinaica_estaciones_sample.csv")
    cols = [
        "id", "nombre", "codigo", "redesId", "nombre_red", "codigo_red",
        "municipioId", "estadoId", "latitud", "longitud", "fechaIniDatos",
        "_ingested_at", "_source", "_source_url",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for id_est, nombre, lat, lon, mun, ent in ESTACIONES:
            w.writerow({
                "id": id_est,
                "nombre": nombre,
                "codigo": f"COD{id_est}",
                "redesId": 1,
                "nombre_red": "Red de prueba",
                "codigo_red": "RP",
                "municipioId": mun,
                "estadoId": ent,
                "latitud": lat,
                "longitud": lon,
                "fechaIniDatos": "2020-01-01",
                "_ingested_at": INGESTED_AT,
                "_source": "DS-05_SINAICA",
                "_source_url": "https://sinaica.inecc.gob.mx",
            })
    return path, len(ESTACIONES)


def generar_observaciones():
    path = os.path.join(FIXTURES_DIR, "bronze_sinaica_observaciones_sample.csv")
    cols = ["fecha", "hora", "valor", "val", "id_estacion", "parametro",
            "_ingested_at", "_source", "_source_url"]
    n = 0
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for id_estacion, lecturas in OBSERVACIONES.items():
            for hora, (parametro, valor, val) in enumerate(lecturas):
                w.writerow({
                    "fecha": "2026-08-19",
                    "hora": hora,
                    "valor": valor,
                    "val": val,
                    "id_estacion": id_estacion,
                    "parametro": parametro,
                    "_ingested_at": INGESTED_AT,
                    "_source": "DS-05_SINAICA",
                    "_source_url": "https://sinaica.inecc.gob.mx",
                })
                n += 1
    return path, n


if __name__ == "__main__":
    p1, n1 = generar_estaciones()
    p2, n2 = generar_observaciones()
    print(f"OK: {p1} ({n1} filas)")
    print(f"OK: {p2} ({n2} filas)")