import pandas as pd

# --- DS-06: CONAGUA (180 filas totales, cabe completo, pero igual limitamos a 500) ---
df_ds06 = pd.read_parquet("data/bronze/ds06_conagua_presas.parquet")
muestra_ds06 = df_ds06.sample(n=min(500, len(df_ds06)), random_state=42)
muestra_ds06.to_csv("tests/fixtures/ds06_fixture.csv", index=False)
print(f"DS-06 fixture: {len(muestra_ds06)} filas guardadas")

# --- DS-08: CONAPO (252,450 filas, aquí sí se nota el recorte) ---
df_ds08 = pd.read_parquet("data/bronze/ds08_conapo.parquet")
muestra_ds08 = df_ds08.sample(n=min(500, len(df_ds08)), random_state=42)
muestra_ds08.to_csv("tests/fixtures/ds08_fixture.csv", index=False)
print(f"DS-08 fixture: {len(muestra_ds08)} filas guardadas")