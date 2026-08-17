import pandas as pd

df = pd.read_csv("data/raw/pobproy_quinq1.csv")

print("Forma (filas, columnas):", df.shape)

print("\nColumnas:")
print(df.columns.tolist())

print("\nPrimeras filas:")
print(df.head())
# Revisamos la columna CLAVE con más detalle
print("\nTipo de dato de CLAVE:", df["CLAVE"].dtype)
print("Ejemplo de valores CLAVE:", df["CLAVE"].head(10).tolist())
print("¿Cuántos caracteres tiene CLAVE como texto?")
print(df["CLAVE"].astype(str).str.len().value_counts())
# Convertimos CLAVE a texto y rellenamos con ceros a la izquierda hasta 5 dígitos
df["cve_mun"] = df["CLAVE"].astype(str).str.zfill(5)

# Verificamos que ahora TODOS tengan 5 caracteres
print("\nDespués de corregir, longitudes de cve_mun:")
print(df["cve_mun"].str.len().value_counts())

print("\nEjemplo de valores corregidos:")
print(df["cve_mun"].head(10).tolist())