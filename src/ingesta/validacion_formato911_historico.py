"""
Validaciones de calidad (Great Expectations) para DS-01 SEP Formato 911 -- distribucion
HISTORICA multi-ciclo -- capa Bronze (`bronze.formato911_historico`).

AISLADO de `silver/matricula.sql` (ciclo unico 2024-2025) -- mismo aislamiento que ya sigue
`extractor_formato911_historico.py`, ver su docstring.

Corre sobre el Parquet mas reciente en `data/bronze/formato911_historico/` (un archivo por
ciclo, ver `extraer_formato911_historico()`), mismo patron que `validacion_sesnsp.py`
(TEST-011). Publica Data Docs en `great_expectations/uncommitted/data_docs/` (excluido de git).

Expectativas basadas SOLO en lo ya verificado real (ver DS-01_Formato_911.md SS9, el docstring
de extractor_formato911_historico.py, y tests/fixtures/bronze_formato911_historico_sample.csv)
-- nada adivinado:

- `matricula_total`: "0 filas con matricula_total no numerico" confirmado real en los 6 ciclos
  (DS-01 SS9) -- not_null + no negativo debe cumplirse siempre.
- `ciclo`: formato `AAAA-AAAA` verificado en los 6 ciclos reales cargados -- se valida el
  FORMATO (regex), no un value_set fijo de los 6 ciclos actuales, porque la fuente sigue
  publicando ciclos nuevos cada año (no se quiere que la suite truene solo por eso).
- `cct`/`entidad`/`municipio`: mismo formato verificado que DS-02 (ver
  tests/fixtures/bronze_formato911_historico_sample.csv, cct "09DJN0001A" con entidad="09",
  municipio="003") -- fuentes distintas (SIGED vs ATDT) pero mismo formato real de CCT/INEGI.
- NO se valida unicidad de (cct, ciclo, turno) aqui a proposito: la UNIQUE real de
  bronze.formato911_historico es (_source, _ingested_at, cct, ciclo, turno) -- Bronze permite
  reingestas del mismo cct+ciclo+turno con un _ingested_at mas nuevo por diseno (ver
  tests/fixtures/generate_bronze_formato911_historico_fixtures.py, "Caso 2"), y es
  silver/matricula_historica.sql quien dedupea por _ingested_at (ver su CTE `deduplicado` y el
  fix de BLOCK-004/2026-09-03 para el segundo dedup a grano cct+ciclo). Exigir unicidad aqui
  either duplicaria esa responsabilidad, o fallaria en datos reales legitimos.
"""
import glob
import logging

import pandas as pd

import great_expectations as gx

logger = logging.getLogger(__name__)

GE_CONTEXT_DIR = "great_expectations"
BRONZE_GLOB = "data/bronze/formato911_historico/*.parquet"

REGEX_CCT = r"^\d{2}[A-Z]{3}\d{4}[A-Z]$"
REGEX_CICLO = r"^\d{4}-\d{4}$"
REGEX_ENTIDAD = r"^\d{1,2}$"
REGEX_MUNICIPIO = r"^\d{1,3}$"
REGEX_TURNO = r"^\d+$"


def _archivo_mas_reciente(patron: str) -> str:
    archivos = sorted(glob.glob(patron))
    if not archivos:
        raise FileNotFoundError(
            f"No hay archivos Bronze en '{patron}'. Corre extractor_formato911_historico primero."
        )
    return archivos[-1]


def _contexto(ge_context_dir: str = GE_CONTEXT_DIR):
    return gx.get_context(mode="file", context_root_dir=ge_context_dir)


def _obtener_o_crear_asset(context, nombre_datasource: str, nombre_asset: str):
    data_source = context.data_sources.add_or_update_pandas(name=nombre_datasource)
    if nombre_asset in data_source.get_asset_names():
        return data_source.get_asset(nombre_asset)
    return data_source.add_dataframe_asset(name=nombre_asset)


def _obtener_o_crear_batch_definition(data_asset, nombre_batch_def: str):
    try:
        return data_asset.get_batch_definition(nombre_batch_def)
    except KeyError:
        return data_asset.add_batch_definition_whole_dataframe(nombre_batch_def)


def _validar(context, df: pd.DataFrame, nombre: str, expectativas: list):
    data_asset = _obtener_o_crear_asset(context, f"{nombre}_datasource", f"{nombre}_asset")
    batch_def = _obtener_o_crear_batch_definition(data_asset, f"{nombre}_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name=f"suite_{nombre}", expectations=expectativas)
    suite = context.suites.add_or_update(suite)

    return batch.validate(suite)


def _expectativas_formato911_historico() -> list:
    return [
        # Nulos en columnas criticas
        gx.expectations.ExpectColumnValuesToNotBeNull(column="cct"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="ciclo"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="turno"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="entidad"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="municipio"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="nivel"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="matricula_total"),
        # Formato de llave y geografia
        gx.expectations.ExpectColumnValuesToMatchRegex(column="cct", regex=REGEX_CCT),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="ciclo", regex=REGEX_CICLO),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="turno", regex=REGEX_TURNO),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="entidad", regex=REGEX_ENTIDAD),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="municipio", regex=REGEX_MUNICIPIO),
        # Rango fisico: matricula nunca negativa (0 filas no numericas confirmado real, DS-01 SS9)
        gx.expectations.ExpectColumnValuesToBeBetween(column="matricula_total", min_value=0),
    ]


def validar_formato911_historico(
    df: pd.DataFrame | None = None,
    ge_context_dir: str = GE_CONTEXT_DIR,
    construir_data_docs: bool = True,
) -> "gx.core.expectation_validation_result.ExpectationSuiteValidationResult":
    """
    Valida un DataFrame Bronze de DS-01 historico (un ciclo) y publica Data Docs.

    Args:
        df: DataFrame a validar. Si es None (uso normal en CLI), se lee el Parquet mas
            reciente de `data/bronze/formato911_historico/`. Pasarlo explicito permite correr
            esta suite en pruebas (`tests/test_validacion_formato911_historico.py`) sin red ni
            depender de una extraccion real -- mismo patron que TEST-011/US-124b para SESNSP.
        ge_context_dir: carpeta del Data Context de Great Expectations. Las pruebas pasan un
            `tmp_path` para no mezclar suites de prueba con las reales.
        construir_data_docs: si es False, no reconstruye el sitio HTML.
    """
    if df is None:
        archivo = _archivo_mas_reciente(BRONZE_GLOB)
        logger.info("Validando formato911_historico desde %s", archivo)
        df = pd.read_parquet(archivo)

    context = _contexto(ge_context_dir)
    resultado = _validar(
        context, df, "ds01_formato911_historico", _expectativas_formato911_historico()
    )
    logger.info(
        "ds01_formato911_historico: success=%s (%d/%d expectativas)",
        resultado.success,
        resultado.statistics["successful_expectations"],
        resultado.statistics["evaluated_expectations"],
    )
    if construir_data_docs:
        context.build_data_docs()
        logger.info("Data Docs actualizados en great_expectations/uncommitted/data_docs/")
    return resultado


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    validar_formato911_historico()
