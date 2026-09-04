"""Pruebas de la suite Great Expectations de DS-01 Formato 911 (distribucion HISTORICA)
(`src/ingesta/validacion_formato911_historico.py`).

Corre completamente offline: `validar_formato911_historico()` acepta un DataFrame explicito y
un `ge_context_dir` de prueba (`tmp_path`) -- mismo patron que
`tests/test_validacion_sesnsp.py` (TEST-011/US-124b) y `tests/test_validacion_cct.py`.

Los datos son sinteticos pero reproducen el esquema y formato reales confirmados en
tests/fixtures/bronze_formato911_historico_sample.csv.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.ingesta.validacion_formato911_historico import validar_formato911_historico


def _fila(cct, ciclo, turno, entidad, municipio, nivel, matricula) -> dict:
    return {
        "cct": cct, "ciclo": ciclo, "turno": turno, "entidad": entidad, "municipio": municipio,
        "nivel": nivel, "matricula_total": matricula,
        "_ingested_at": datetime.now(timezone.utc),
        "_source": "DS-01_FORMATO911_HISTORICO",
        "_source_url": "https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2019-2020.csv",
    }


def _df_limpio() -> pd.DataFrame:
    return pd.DataFrame([
        _fila("09DJN0001A", "2019-2020", "1", "09", "003", "PREESCOLAR", 87),
        _fila("09DPR0002B", "2019-2020", "1", "09", "003", "PRIMARIA", 210),
        _fila("09DPR0002B", "2019-2020", "2", "09", "003", "PRIMARIA", 35),
        _fila("19DES0003C", "2019-2020", "1", "19", "039", "SECUNDARIA", 340),
    ])


def test_datos_limpios_pasan_todas_las_expectativas(tmp_path) -> None:
    resultado = validar_formato911_historico(
        df=_df_limpio(), ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )
    assert resultado.success is True


def test_detecta_matricula_negativa(tmp_path) -> None:
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila("14DPR0004D", "2019-2020", "1", "14", "001", "PRIMARIA", -5)]),
    ], ignore_index=True)

    resultado = validar_formato911_historico(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.kwargs["column"] == "matricula_total"


def test_detecta_ciclo_con_formato_invalido(tmp_path) -> None:
    """Un ciclo que no cumple AAAA-AAAA es senal de un archivo fuente distinto/corrupto --
    no se adivina, se marca (no se valida un value_set fijo de los 6 ciclos actuales porque
    la fuente sigue publicando ciclos nuevos, ver docstring del modulo)."""
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila("14DPR0004D", "2019", "1", "14", "001", "PRIMARIA", 40)]),
    ], ignore_index=True)

    resultado = validar_formato911_historico(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.kwargs["column"] == "ciclo"


def test_detecta_cct_con_formato_invalido(tmp_path) -> None:
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila("CCT-INVALIDO", "2019-2020", "1", "09", "003", "PRIMARIA", 40)]),
    ], ignore_index=True)

    resultado = validar_formato911_historico(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.kwargs["column"] == "cct"


def test_detecta_nulo_en_columna_critica(tmp_path) -> None:
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila(None, "2019-2020", "1", "09", "003", "PRIMARIA", 40)]),
    ], ignore_index=True)

    resultado = validar_formato911_historico(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallos = [r for r in resultado.results if not r.success]
    assert any(f.expectation_config.kwargs.get("column") == "cct" for f in fallos)
