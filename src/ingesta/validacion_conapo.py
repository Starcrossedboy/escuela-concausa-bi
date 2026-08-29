import glob

import pandas as pd
import great_expectations as gx

# 1. Cargamos el archivo más reciente que el extractor guardó en Bronze
archivos = sorted(glob.glob("data/bronze/conapo/conapo_*.parquet"))
df = pd.read_parquet(archivos[-1])

# 2. Contexto y fuente de datos
context = gx.get_context(context_root_dir="great_expectations")
try:
    data_source = context.data_sources.add_pandas("pandas_ds08")
except gx.exceptions.DataContextError:
    data_source = context.data_sources.get("pandas_ds08")
try:
    data_asset = data_source.add_dataframe_asset(name="ds08_poblacion")
except ValueError:
    data_asset = data_source.get_asset("ds08_poblacion")
try:
    batch_definition = data_asset.add_batch_definition_whole_dataframe("batch_ds08")
except ValueError:
    batch_definition = data_asset.get_batch_definition("batch_ds08")

# 3. Suite de reglas para DS-08
suite = context.suites.add_or_update(gx.ExpectationSuite(name="suite_ds08_conapo"))

# --- Nulos: campos clave que nunca deben venir vacíos ---
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="cve_mun"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="NOM_MUN"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="POB_TOTAL"))

# --- Llave: la combinación de municipio + sexo + año no debe repetirse ---
#     (aquí sí puede haber "duplicados" de cve_mun solo, porque cada municipio
#      aparece una vez por año y por sexo — por eso NO usamos "unique" en cve_mun solo)
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="ANO"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="SEXO"))

# --- Rangos físicos: la población no puede ser negativa, ni absurdamente alta ---
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
    column="POB_TOTAL", min_value=0, max_value=25000000
))

# --- Tipos/formato: cve_mun siempre debe tener 5 caracteres ---
suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToEqual(column="cve_mun", value=5))

# 4. Corremos la validación
batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
resultados = batch.validate(suite)

print("¿Pasó todo?", resultados.success)
print(f"\nExpectativas exitosas: {resultados.statistics['successful_expectations']}/{resultados.statistics['evaluated_expectations']}")

# 5. Generamos el reporte visual
context.build_data_docs()
print("\nData Docs actualizado.")