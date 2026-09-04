"""
Validaciones de calidad (Great Expectations) para DS-02 SEP Catalogo CCT -- capa Bronze.

Reutiliza `parsear_y_combinar()` de `cargar_bronze_cct_real.py` (mismo esquema Bronze que ya
se inserta a Postgres, no se duplica esa logica ni se inventa un glob nuevo -- DS-02 no
persiste un artefacto intermedio propio como si lo hace DS-01 historico, ver
`validacion_formato911_historico.py`) y valida el resultado antes/despues de cargar.

Expectativas basadas SOLO en lo ya verificado real (ver DS-02_Catalogo_CCT.md SS5/SS9/SS10 y
el docstring de cargar_bronze_cct_real.py) -- nada adivinado:

- `nivel`: el loader ya filtra a NIVELES_BASICA antes de construir el DataFrame Bronze, asi
  que PREESCOLAR/PRIMARIA/SECUNDARIA debe cumplirse siempre -- si falla, es una regresion real
  del filtro, no un hallazgo de la fuente.
- `cct`: el loader ya truena si hay CCT duplicado entre las dos partes del catalogo (punto 6
  de su docstring) -- unicidad dentro de una extraccion debe cumplirse siempre por el mismo
  motivo que `nivel`.
- `sostenimiento`: el loader pasa `SOSTENIMIENTO_C_CONTROL` TAL CUAL, sin traducir -- no se
  conoce con certeza su value_set real crudo, asi que aqui solo se exige not_null (no se
  inventa un catalogo).
- `latitud`/`longitud`: llegan como TEXT tal cual del archivo (no convertidas). Se valida que
  sean texto numerico parseable (`not_null` + regex), pero NO se excluye "0.000000" -- BUG-034
  (6 filas reales en 0,0 verificadas) es un defecto conocido DE LA FUENTE que esta corregido en
  Silver (`silver/escuela.sql`, nullif de 0 literal), no en Bronze: exigir aqui que nunca sea
  0,0 duplicaria esa responsabilidad y haria fallar la suite en datos reales conocidos.
- `entidad`/`municipio`: formato verificado contra el fixture real del repo
  (`tests/fixtures/bronze_formato911_historico_sample.csv`, cct `09DJN0001A` con entidad="09",
  municipio="003") y contra DS-02_Catalogo_CCT.md SS5 (INMUEBLE_CV_MUN es CHAR(3) local, no
  INEGI de 5 -- no se homologa aqui, eso es silver/escuela.sql).

Publica Data Docs (HTML) en `great_expectations/uncommitted/data_docs/` (excluido de git),
mismo patron que `validacion_sesnsp.py` (TEST-011).
"""
import logging

import pandas as pd

import great_expectations as gx

from src.ingesta.cargar_bronze_cct_real import parsear_y_combinar

logger = logging.getLogger(__name__)

GE_CONTEXT_DIR = "great_expectations"

NIVELES_BASICA = ["PREESCOLAR", "PRIMARIA", "SECUNDARIA"]

# Formato real verificado (ver docstring del modulo): EE(2 digitos) + T(1 letra, sostenimiento)
# + NN(2 letras, subnivel) + CCCC(4 digitos, consecutivo) + X(1 letra, digito verificador).
REGEX_CCT = r"^\d{2}[A-Z]{3}\d{4}[A-Z]$"
REGEX_ENTIDAD = r"^\d{2}$"
REGEX_MUNICIPIO = r"^\d{1,3}$"
# Texto numerico (con o sin signo, con o sin decimales) -- no excluye 0 (ver docstring, BUG-034).
REGEX_COORDENADA = r"^-?\d+(\.\d+)?$"


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


def _expectativas_cct() -> list:
    return [
        # Nulos en columnas criticas
        gx.expectations.ExpectColumnValuesToNotBeNull(column="cct"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="nombre"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="nivel"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="sostenimiento"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="entidad"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="municipio"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="latitud"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="longitud"),
        # Formato de llave y geografia
        gx.expectations.ExpectColumnValuesToMatchRegex(column="cct", regex=REGEX_CCT),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="entidad", regex=REGEX_ENTIDAD),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="municipio", regex=REGEX_MUNICIPIO),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="latitud", regex=REGEX_COORDENADA),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="longitud", regex=REGEX_COORDENADA),
        # Catalogo valido de nivel -- el loader ya filtra a esto, ver docstring
        gx.expectations.ExpectColumnValuesToBeInSet(column="nivel", value_set=NIVELES_BASICA),
        # Unicidad de cct DENTRO de una extraccion -- el loader ya truena si hay duplicados
        # entre las dos partes del catalogo, esto debe cumplirse siempre (ver docstring)
        gx.expectations.ExpectColumnValuesToBeUnique(column="cct"),
    ]


def validar_cct(
    df: pd.DataFrame | None = None,
    ruta_01_16: str | None = None,
    ruta_17_32: str | None = None,
    ge_context_dir: str = GE_CONTEXT_DIR,
    construir_data_docs: bool = True,
) -> "gx.core.expectation_validation_result.ExpectationSuiteValidationResult":
    """
    Valida el DataFrame Bronze de DS-02 (catalogo CCT) y publica Data Docs.

    Args:
        df: DataFrame ya en esquema Bronze (ver COLUMNAS_BRONZE de cargar_bronze_cct_real.py).
            Si es None, se construye llamando a `parsear_y_combinar(ruta_01_16, ruta_17_32)` --
            hay que pasar esas dos rutas en ese caso. Pasar `df` explicito permite correr esta
            suite en pruebas (`tests/test_validacion_cct.py`) sin CSV reales ni red -- mismo
            patron que TEST-011/US-124b para SESNSP.
        ruta_01_16 / ruta_17_32: rutas a los dos CSV reales ya descargados/extraidos (ver
            extractor_cct.py). Ignoradas si `df` ya viene explicito.
        ge_context_dir: carpeta del Data Context de Great Expectations. Las pruebas pasan un
            `tmp_path` para no mezclar suites de prueba con las reales.
        construir_data_docs: si es False, no reconstruye el sitio HTML.
    """
    if df is None:
        if not ruta_01_16 or not ruta_17_32:
            raise ValueError(
                "validar_cct: pasa 'df' explicito, o las dos rutas 'ruta_01_16'/'ruta_17_32' "
                "de los CSV reales ya descargados (ver extractor_cct.py)."
            )
        logger.info("Validando cct desde %s + %s", ruta_01_16, ruta_17_32)
        df = parsear_y_combinar(ruta_01_16, ruta_17_32)

    context = _contexto(ge_context_dir)
    resultado = _validar(context, df, "ds02_cct", _expectativas_cct())
    logger.info(
        "ds02_cct: success=%s (%d/%d expectativas)",
        resultado.success,
        resultado.statistics["successful_expectations"],
        resultado.statistics["evaluated_expectations"],
    )
    if construir_data_docs:
        context.build_data_docs()
        logger.info("Data Docs actualizados en great_expectations/uncommitted/data_docs/")
    return resultado


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-01-16", required=True)
    parser.add_argument("--csv-17-32", required=True)
    args = parser.parse_args()

    validar_cct(ruta_01_16=args.csv_01_16, ruta_17_32=args.csv_17_32)
