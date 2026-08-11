"""Genera tests/fixtures/features_escuela_mock.parquet — datos sintéticos para desarrollo sin gold.features_escuela real."""
import random
import pandas as pd
import numpy as np

random.seed(42)
np.random.seed(42)

ENTIDADES = ["09", "15", "19", "14"]
NIVELES = ["PREESCOLAR", "PRIMARIA", "SECUNDARIA", "BACHILLERATO"]
DRIVERS = ["d1_rezago_social", "d2_incidencia_delictiva", "d3_infraestructura_score",
           "d4_conectividad_score", "d5_estres_hidrico", "d6_calidad_aire"]
CICLOS = [f"{y}-{str(y+1)[-2:]}" for y in range(2013, 2024)]  # 2013-14 … 2023-24

N_ESCUELAS = 50   # ≤500 filas por ciclo para cumplir la regla del vault

rows = []
for ciclo in CICLOS:
    for i in range(N_ESCUELAS):
        entidad = random.choice(ENTIDADES)
        cct = f"{entidad}DPR{i:04d}X"

        matricula_base = random.randint(30, 400)
        matricula = max(0, matricula_base + random.randint(-20, 20))
        delta = float(random.randint(-30, 30))

        # D5 y D6 tienen cobertura parcial: ~40% de escuelas sin dato
        d5_disponible = int(random.random() > 0.4)
        d6_disponible = int(random.random() > 0.6)

        row = {
            "cct": cct,
            "ciclo": ciclo,
            "entidad_id": entidad,
            "nivel": random.choice(NIVELES),
            "matricula": matricula,
            "delta_matricula": delta,
            "d1_rezago_social": round(np.random.uniform(0, 1), 4),
            "d2_incidencia_delictiva": round(np.random.uniform(0, 200), 2),
            "d3_infraestructura_score": round(np.random.uniform(0, 1), 4),
            "d4_conectividad_score": round(np.random.uniform(0, 1), 4),
            # Imputación con mediana sintética cuando no hay dato; nunca cero
            "d5_estres_hidrico": round(np.random.uniform(0.1, 1), 4) if d5_disponible else round(np.random.uniform(0.3, 0.6), 4),
            "d5_dato_disponible": d5_disponible,
            "d6_calidad_aire": round(np.random.uniform(0, 100), 2) if d6_disponible else round(np.random.uniform(30, 60), 2),
            "d6_dato_disponible": d6_disponible,
            "indice_completitud_drivers": round((4 + d5_disponible + d6_disponible) / 6, 4),
            "driver_dominante": random.choice(DRIVERS),
        }
        rows.append(row)

df = pd.DataFrame(rows)
output_path = "tests/fixtures/features_escuela_mock.parquet"
df.to_parquet(output_path, index=False)
print(f"Fixture generado: {output_path} ({len(df)} filas, {df['ciclo'].nunique()} ciclos, {df['cct'].nunique()} escuelas únicas)")
print(df.dtypes)
