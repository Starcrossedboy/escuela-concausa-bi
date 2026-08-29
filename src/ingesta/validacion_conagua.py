import glob

import pandas as pd
import great_expectations as gx

# 1. Cargamos el archivo más reciente que el extractor guardó en Bronze
archivos = sorted(glob.glob("data/bronze/conagua/conagua_*.parquet"))
df = pd.read_parquet(archivos[-1])

# 2. Las columnas numéricas vienen como texto (así las entregó la API de CONAGUA)
#    Las convertimos a número de verdad para poder validar rangos
df["cap_namo"] = pd.to_numeric(df["cap_namo"], errors="coerce")
df["cap_name"] = pd.to_numeric(df["cap_name"], errors="coerce")
df["alt_cort"] = pd.to_numeric(df["alt_cort"], errors="coerce")

# 3. Creamos un "contexto" de Great Expectations que guarda resultados en disco
#    (esto es lo que nos va a permitir generar el Data Docs al final)
context = gx.get_context(context_root_dir="great_expectations")

# 4. Le decimos a GE que nuestra fuente de datos es un DataFrame de pandas
try:
    data_source = context.data_sources.add_pandas("pandas_ds06")
except gx.exceptions.DataContextError:
    data_source = context.data_sources.get("pandas_ds06")
try:
    data_asset = data_source.add_dataframe_asset(name="ds06_presas")
except ValueError:
    data_asset = data_source.get_asset("ds06_presas")
try:
    batch_definition = data_asset.add_batch_definition_whole_dataframe("batch_ds06")
except ValueError:
    batch_definition = data_asset.get_batch_definition("batch_ds06")

# 5. Armamos la "suite": el conjunto de reglas de calidad para DS-06
suite = context.suites.add_or_update(gx.ExpectationSuite(name="suite_ds06_conagua"))

# --- Nulos: estos campos nunca deben venir vacíos ---
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="nombre_oficial"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="estado"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="cap_namo"))

# --- Llave: id_presa debe ser único (no duplicados) ---
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="id_presa"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="id_presa"))

# --- Rangos físicos: valores absurdos serían un error de los datos ---
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
    column="cap_namo", min_value=0, max_value=100000
))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
    column="alt_cort", min_value=0, max_value=500
))

# 6. Corremos la validación sobre nuestros datos reales
batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
resultados = batch.validate(suite)

print("¿Pasó todo?", resultados.success)
print(resultados)

# 7. Generamos el reporte visual (Data Docs)
context.build_data_docs()
print("\nData Docs generado. Ábrelo con: context.open_data_docs()")