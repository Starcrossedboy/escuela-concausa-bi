"""Pruebas de la suite Great Expectations de DS-02 Catalogo CCT
(`src/ingesta/validacion_cct.py`).

Corre completamente offline: `validar_cct()` acepta un DataFrame explicito y un
`ge_context_dir` de prueba (`tmp_path`) en vez de tocar CSV reales o el `great_expectations/`
real del repo -- mismo patron que `tests/test_validacion_sesnsp.py` (TEST-011/US-124b).

Los datos son sinteticos pero reproducen el esquema real confirmado en
`cargar_bronze_cct_real.py` (COLUMNAS_BRONZE) y el formato real de CCT verificado en
tests/fixtures/bronze_formato911_historico_sample.csv (p.ej. "09DJN0001A").
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.ingesta.validacion_cct import validar_cct


def _fila_cct(cct, nombre, nivel, sostenimiento, entidad, municipio, lat, lon) -> dict:
    return {
        "cct": cct, "nombre": nombre, "nivel": nivel, "sostenimiento": sostenimiento,
        "entidad": entidad, "municipio": municipio, "latitud": lat, "longitud": lon,
        "_ingested_at": datetime.now(timezone.utc).isoformat(),
        "_source": "DS-02_CATALOGO_CCT", "_source_url": "https://ejemplo.test/cct.zip",
    }


def _df_limpio() -> pd.DataFrame:
    return pd.DataFrame([
        _fila_cct("09DJN0001A", "JARDIN DE NINOS 1", "PREESCOLAR", "PUBLICO", "09", "003", "19.4326", "-99.1332"),
        _fila_cct("09DPR0002B", "PRIMARIA 2", "PRIMARIA", "PUBLICO", "09", "003", "19.4300", "-99.1300"),
        _fila_cct("19DES0003C", "SECUNDARIA 3", "SECUNDARIA", "PRIVADO", "19", "039", "25.6866", "-100.3161"),
    ])


def test_datos_limpios_pasan_todas_las_expectativas(tmp_path) -> None:
    resultado = validar_cct(
        df=_df_limpio(), ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )
    assert resultado.success is True


def test_coordenada_cero_no_rompe_la_suite(tmp_path) -> None:
    """Caso real (BUG-034): 6 escuelas con lat/lon en 0,0 -- Bronze las carga tal cual (la
    correccion es de Silver, no de aqui). La suite debe seguir pasando: 0 es texto numerico
    valido, solo un valor de negocio sospechoso que Silver ya nulifica."""
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila_cct("14DPR0004D", "PRIMARIA 4", "PRIMARIA", "PUBLICO", "14", "001", "0.000000", "0.000000")]),
    ], ignore_index=True)

    resultado = validar_cct(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )
    assert resultado.success is True


def test_detecta_nivel_fuera_de_basica(tmp_path) -> None:
    """El loader real ya filtra a PREESCOLAR/PRIMARIA/SECUNDARIA antes de construir el
    DataFrame Bronze -- si algo con MEDIA SUPERIOR llega aqui, es una regresion real del
    filtro (cargar_bronze_cct_real.py punto 3), no un hallazgo de la fuente."""
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila_cct("09DBA0005E", "PREPA 5", "MEDIA SUPERIOR", "PUBLICO", "09", "003", "19.40", "-99.10")]),
    ], ignore_index=True)

    resultado = validar_cct(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.kwargs["column"] == "nivel"


def test_detecta_cct_duplicado(tmp_path) -> None:
    """El loader real ya truena si dos partes del catalogo comparten un CCT (punto 6 de su
    docstring) -- dentro de una extraccion, cct debe ser unico siempre."""
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila_cct("09DJN0001A", "JARDIN DE NINOS 1 (dup)", "PREESCOLAR", "PUBLICO", "09", "003", "19.43", "-99.13")]),
    ], ignore_index=True)

    resultado = validar_cct(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.type == "expect_column_values_to_be_unique"


def test_detecta_cct_con_formato_invalido(tmp_path) -> None:
    """Un CCT que no cumple el formato real (EE + 3 letras + 4 digitos + 1 letra) es una
    senal de un archivo fuente distinto/corrupto -- no se adivina, se marca."""
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila_cct("CCT-INVALIDO", "ESCUELA RARA", "PRIMARIA", "PUBLICO", "09", "003", "19.40", "-99.10")]),
    ], ignore_index=True)

    resultado = validar_cct(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.kwargs["column"] == "cct"
    assert fallo.expectation_config.type == "expect_column_values_to_match_regex"
