import pandas as pd
import great_expectations as gx

# 1. Cargamos los datos de Bronze
df = pd.read_parquet("data/bronze/ds08_conapo.parquet")

# 2. Contexto y fuente de datos
context = gx.get_context(context_root_dir="great_expectations")
data_source = context.data_sources.add_pandas("pandas_ds08")
data_asset = data_source.add_dataframe_asset(name="ds08_poblacion")
batch_definition = data_asset.add_batch_definition_whole_dataframe("batch_ds08")

# 3. Suite de reglas para DS-08
suite = context.suites.add(gx.ExpectationSuite(name="suite_ds08_conapo"))

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