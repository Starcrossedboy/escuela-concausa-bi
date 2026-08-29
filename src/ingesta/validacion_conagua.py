"""Validaciones de calidad de DS-06 CONAGUA (Bronze) con Great Expectations.

Estructura pensada para ser probada sin depender de una corrida real contra
Bronze: `limpiar_columnas_numericas` es una función pura sobre un DataFrame,
y `construir_suite` arma las reglas sin necesitar datos todavía -- ambas se
prueban de forma aislada en `tests/test_validacion_ds06.py`.
"""
import glob

import great_expectations as gx
import pandas as pd

SOURCE_NAME = "DS-06_CONAGUA_SINA"
BRONZE_GLOB = "data/bronze/conagua/conagua_*.parquet"
SUITE_NAME = "suite_ds06_conagua"


def limpiar_columnas_numericas(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte a numérico las columnas que CONAGUA entrega como texto.

    Valores no convertibles quedan como NaN (errors="coerce") en vez de
    tronar -- eso es justo lo que las expectativas de nulos deben atrapar.
    """
    df = df.copy()
    for columna in ("cap_namo", "cap_name", "alt_cort"):
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    return df


def construir_suite(context: gx.data_context.AbstractDataContext) -> gx.ExpectationSuite:
    """Arma la suite de reglas de calidad de DS-06 (nulos, unicidad, rangos)."""
    suite = context.suites.add_or_update(gx.ExpectationSuite(name=SUITE_NAME))

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
    return suite


def validar(df: pd.DataFrame, context: gx.data_context.AbstractDataContext):
    """Registra el DataFrame como batch y corre la suite de DS-06 sobre él."""
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

    suite = construir_suite(context)
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    return batch.validate(suite)


def main() -> None:
    archivos = sorted(glob.glob(BRONZE_GLOB))
    if not archivos:
        raise FileNotFoundError(
            f"{SOURCE_NAME}: no hay archivos en {BRONZE_GLOB}. Corre el extractor primero."
        )
    df = limpiar_columnas_numericas(pd.read_parquet(archivos[-1]))

    context = gx.get_context(context_root_dir="great_expectations")
    resultados = validar(df, context)

    print("¿Pasó todo?", resultados.success)
    print(resultados)

    context.build_data_docs()
    print("\nData Docs generado. Ábrelo con: context.open_data_docs()")


if __name__ == "__main__":
    main()