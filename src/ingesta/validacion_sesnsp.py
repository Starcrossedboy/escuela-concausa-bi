"""
Validaciones de calidad (Great Expectations) para DS-04 SESNSP — capa Bronze.

Valida la tabla Bronze que produce `extractor_sesnsp.py` (`sesnsp`, ya agregada a
nivel municipio/año/mes/tipo de delito -- ver ese módulo para el porqué de agregar
subtipo/modalidad en la extracción y no dejarlo al dedup de Silver).

Corre sobre el Parquet más reciente en `data/bronze/sesnsp/` y publica Data Docs
(HTML) en `great_expectations/uncommitted/data_docs/` (excluido de git).
"""
import glob
import logging

import pandas as pd

import great_expectations as gx

logger = logging.getLogger(__name__)

GE_CONTEXT_DIR = "great_expectations"
BRONZE_GLOB = "data/bronze/sesnsp/*.parquet"

# Catálogo de "Tipo de delito" confirmado contra el corte real de dic-2025 del
# archivo fuente (ATDT, 12 553 440 filas de Bronze, 2026-08-24). Si SESNSP agrega una
# categoría nueva, esta expectativa debe fallar de forma visible en vez de dejarla
# pasar en silencio -- es la señal de que hay que revisar el catálogo a mano, no un
# error del extractor.
CATALOGO_TIPO_DELITO = [
    "Aborto", "Abuso de confianza", "Abuso sexual", "Acoso sexual",
    "Allanamiento de morada", "Amenazas", "Contra el medio ambiente",
    "Corrupción de menores", "Daño a la propiedad",
    "Delitos cometidos por servidores públicos", "Despojo", "Electorales",
    "Evasión de presos", "Extorsión", "Falsedad", "Falsificación", "Feminicidio",
    "Fraude", "Homicidio", "Hostigamiento sexual", "Incesto",
    "Incumplimiento de obligaciones de asistencia familiar", "Lesiones",
    "Narcomenudeo", "Otros delitos contra el patrimonio",
    "Otros delitos contra la familia", "Otros delitos contra la sociedad",
    "Otros delitos del Fuero Común",
    "Otros delitos que atentan contra la libertad personal",
    "Otros delitos que atentan contra la libertad y la seguridad sexual",
    "Otros delitos que atentan contra la vida y la integridad corporal", "Rapto",
    "Robo", "Secuestro", "Trata de personas", "Tráfico de menores",
    "Violación equiparada", "Violación simple",
    "Violencia de género en todas sus modalidades distinta a la violencia familiar",
    "Violencia familiar",
]

ANIO_MINIMO = 2015
ANIO_MAXIMO = 2030  # margen sobre el año actual del proyecto (2026) para no romper con cada corte


def _archivo_mas_reciente(patron: str) -> str:
    archivos = sorted(glob.glob(patron))
    if not archivos:
        raise FileNotFoundError(
            f"No hay archivos Bronze en '{patron}'. Corre extractor_sesnsp primero."
        )
    return archivos[-1]


def _contexto(ge_context_dir: str = GE_CONTEXT_DIR):
    """Data Context de Great Expectations, persistido en `ge_context_dir`."""
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
    """Registra `df` como asset efímero, define/actualiza la suite y valida."""
    data_asset = _obtener_o_crear_asset(context, f"{nombre}_datasource", f"{nombre}_asset")
    batch_def = _obtener_o_crear_batch_definition(data_asset, f"{nombre}_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name=f"suite_{nombre}", expectations=expectativas)
    suite = context.suites.add_or_update(suite)

    return batch.validate(suite)


def _expectativas_sesnsp(catalogo_tipo_delito: list[str]) -> list:
    return [
        # Nulos en columnas críticas
        gx.expectations.ExpectColumnValuesToNotBeNull(column="cve_ent"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="cve_mun"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="anio"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="mes"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="tipo_delito"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="conteo"),
        # Tipos
        gx.expectations.ExpectColumnValuesToBeOfType(column="anio", type_="int64"),
        gx.expectations.ExpectColumnValuesToBeOfType(column="mes", type_="int64"),
        # Formato de llave: cve_ent y cve_mun crudos (sin padding), ver extractor_sesnsp
        # para por qué NO se homologan aquí a 2/5 dígitos -- eso es trabajo de Silver.
        gx.expectations.ExpectColumnValuesToMatchRegex(column="cve_ent", regex=r"^\d{1,2}$"),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="cve_mun", regex=r"^\d{1,3}$"),
        # Rangos físicos
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="anio", min_value=ANIO_MINIMO, max_value=ANIO_MAXIMO
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(column="mes", min_value=1, max_value=12),
        gx.expectations.ExpectColumnValuesToBeBetween(column="conteo", min_value=0),
        # Catálogo válido de tipo de delito
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="tipo_delito", value_set=catalogo_tipo_delito
        ),
        # Llave / duplicados: el extractor ya agrega a este grano exacto, así que esto
        # debe pasar siempre -- si falla, es un regresión real en `extractor_sesnsp.py`.
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=["cve_ent", "cve_mun", "anio", "mes", "tipo_delito"]
        ),
    ]


def validar_sesnsp(
    df: pd.DataFrame | None = None,
    ge_context_dir: str = GE_CONTEXT_DIR,
    construir_data_docs: bool = True,
) -> "gx.core.expectation_validation_result.ExpectationSuiteValidationResult":
    """
    Valida la tabla Bronze de SESNSP y publica Data Docs.

    Args:
        df: DataFrame a validar. Si es None (uso normal en CLI/DAG), se lee el Parquet
            más reciente de `data/bronze/sesnsp/`. Pasarlo explícito permite correr
            esta suite en pruebas (`tests/test_validacion_sesnsp.py`) sin red ni
            depender de que exista una extracción real -- eso es lo que destraba
            `US-124b` (CI sin descargar datos reales).
        ge_context_dir: carpeta del Data Context de Great Expectations. Las pruebas
            pasan un `tmp_path` para no mezclar suites de prueba con las reales de
            `great_expectations/expectations/`.
        construir_data_docs: si es False, no reconstruye el sitio HTML (pruebas no lo
            necesitan y ahorra tiempo).
    """
    if df is None:
        archivo = _archivo_mas_reciente(BRONZE_GLOB)
        logger.info("Validando sesnsp desde %s", archivo)
        df = pd.read_parquet(archivo)

    context = _contexto(ge_context_dir)
    resultado = _validar(context, df, "sesnsp", _expectativas_sesnsp(CATALOGO_TIPO_DELITO))
    logger.info(
        "sesnsp: success=%s (%d/%d expectativas)",
        resultado.success,
        resultado.statistics["successful_expectations"],
        resultado.statistics["evaluated_expectations"],
    )
    if construir_data_docs:
        context.build_data_docs()
        logger.info("Data Docs actualizados en great_expectations/uncommitted/data_docs/")
    return resultado


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validar_sesnsp()
