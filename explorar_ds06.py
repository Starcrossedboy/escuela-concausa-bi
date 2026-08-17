import pandas as pd

# Cargamos el archivo CSV de presas de CONAGUA
df = pd.read_csv("data/raw/ds06_conagua_presas.csv")

# Cuántas filas y columnas tiene
print("Forma (filas, columnas):", df.shape)

# Nombres de todas las columnas
print("\nColumnas:")
print(df.columns.tolist())

# Primeras 5 filas, para ver cómo se ven los datos
print("\nPrimeras filas:")
print(df.head())