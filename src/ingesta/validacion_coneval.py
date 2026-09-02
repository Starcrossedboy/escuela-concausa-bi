"""Validaciones Great Expectations de DS-07 CONEVAL sobre Silver."""

from __future__ import annotations

import logging
import os

import pandas as pd
import psycopg2
from great_expectations.expectations.row_conditions import Column

import great_expectations as gx

logger = logging.getLogger(__name__)

GE_CONTEXT_DIR = "great_expectations"
SUITE_NAME = "suite_ds07_coneval"
GRADOS_REZAGO = ["MUY BAJO", "BAJO", "MEDIO", "ALTO", "MUY ALTO", "SIN_DATO"]
COBERTURAS = ["OK", "SIN_DATO"]


def _dsn() -> str:
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'escuela_concausa_db')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', '')}"
    )


def cargar_silver() -> pd.DataFrame:
    """Lee el contrato conformado de DS-07 sin modificar la base de datos."""
    query = """
        select
            cve_mun,
            periodo_medicion,
            indice_rezago_social,
            indice_rezago_social_cobertura,
            grado_rezago,
            pobreza_pct,
            pobreza_pct_cobertura
        from silver.rezago_municipio
    """
    with psycopg2.connect(_dsn()) as conn, conn.cursor() as cur:
        cur.execute(query)
        columnas = [descripcion.name for descripcion in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columnas)


def construir_suite(context: gx.data_context.AbstractDataContext) -> gx.ExpectationSuite:
    """Define las reglas de calidad del contrato Silver de DS-07."""
    suite = context.suites.add_or_update(gx.ExpectationSuite(name=SUITE_NAME))

    # Llave y formato INEGI.
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="cve_mun"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="periodo_medicion")
    )
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=["cve_mun", "periodo_medicion"]
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToMatchRegex(
            column="cve_mun", regex=r"^[0-9]{5}$"
        )
    )

    # Catálogos conformados y banderas explícitas de cobertura.
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="grado_rezago"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="grado_rezago", value_set=GRADOS_REZAGO
        )
    )
    for columna in ("indice_rezago_social_cobertura", "pobreza_pct_cobertura"):
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=columna))
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInSet(
                column=columna, value_set=COBERTURAS
            )
        )

    # Rango y coherencia: OK exige valor; SIN_DATO exige ausencia de valor.
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="pobreza_pct",
            min_value=0,
            max_value=100,
            row_condition=Column("pobreza_pct_cobertura") == "OK",
        )
    )
    for valor, cobertura in (
        ("indice_rezago_social", "indice_rezago_social_cobertura"),
        ("pobreza_pct", "pobreza_pct_cobertura"),
    ):
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column=valor, row_condition=Column(cobertura) == "OK"
            )
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeNull(
                column=valor, row_condition=Column(cobertura) == "SIN_DATO"
            )
        )

    return suite


def validar(
    df: pd.DataFrame,
    context: gx.data_context.AbstractDataContext,
) -> gx.core.expectation_validation_result.ExpectationSuiteValidationResult:
    """Valida un DataFrame con el contrato de `silver.rezago_municipio`."""
    data_source = context.data_sources.add_or_update_pandas(name="pandas_ds07")
    if "ds07_coneval" in data_source.get_asset_names():
        data_asset = data_source.get_asset("ds07_coneval")
    else:
        data_asset = data_source.add_dataframe_asset(name="ds07_coneval")

    try:
        batch_definition = data_asset.get_batch_definition("batch_ds07")
    except KeyError:
        batch_definition = data_asset.add_batch_definition_whole_dataframe("batch_ds07")

    suite = construir_suite(context)
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    return batch.validate(suite)


def main() -> None:
    """Valida `silver.rezago_municipio` y actualiza Data Docs locales."""
    context = gx.get_context(mode="file", context_root_dir=GE_CONTEXT_DIR)
    resultado = validar(cargar_silver(), context)

    for validacion in resultado.results:
        configuracion = validacion.expectation_config
        objetivo = configuracion.kwargs.get("column") or configuracion.kwargs.get("column_list")
        print(
            f"{'PASS' if validacion.success else 'FAIL'} "
            f"{configuracion.type} {objetivo}"
        )

    context.build_data_docs()
    logger.info(
        "DS-07: success=%s (%d/%d expectativas)",
        resultado.success,
        resultado.statistics["successful_expectations"],
        resultado.statistics["evaluated_expectations"],
    )
    if not resultado.success:
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
