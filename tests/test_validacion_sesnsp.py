"""Pruebas de la suite Great Expectations de DS-04 SESNSP
(`src/ingesta/validacion_sesnsp.py`, `TEST-011`).

Corre completamente offline: `validar_sesnsp()` acepta un DataFrame explícito y un
`ge_context_dir` de prueba (`tmp_path`) en vez de tocar `data/bronze/sesnsp/` o el
`great_expectations/` real del repo -- exactamente lo que pide `US-124b` ("que CI
corra sin descargar datos reales"), sin necesitar un archivo de fixture separado
porque los datos sintéticos caben en el propio test.

Los datos son sintéticos pero reproducen fielmente el esquema real confirmado el
2026-08-24 (12 553 440 filas de Bronze reales), incluyendo el mismo tipo de anomalía
que se encontró en producción (conteo negativo por corrección retroactiva de SESNSP) --
así la prueba demuestra que la suite SÍ atrapa ese caso, no solo que corre sin tronar.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.ingesta.validacion_sesnsp import CATALOGO_TIPO_DELITO, validar_sesnsp


def _fila_sesnsp(cve_ent, cve_mun, anio, mes, tipo_delito, conteo) -> dict:
    return {
        "cve_ent": cve_ent, "cve_mun": cve_mun, "anio": anio, "mes": mes,
        "tipo_delito": tipo_delito, "conteo": conteo,
        "_ingested_at": datetime.now(timezone.utc),
        "_source": "DS-04_SESNSP", "_source_url": "https://ejemplo.test/sesnsp.csv",
    }


def _df_limpio() -> pd.DataFrame:
    return pd.DataFrame([
        _fila_sesnsp("1", "001", 2015, 1, "Homicidio", 14),
        _fila_sesnsp("1", "001", 2015, 2, "Homicidio", 11),
        _fila_sesnsp("21", "002", 2019, 3, "Robo", 7),
        _fila_sesnsp("9", "006", 2017, 8, "Extorsión", 0),
    ])


def test_datos_limpios_pasan_todas_las_expectativas(tmp_path) -> None:
    resultado = validar_sesnsp(
        df=_df_limpio(), ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )
    assert resultado.success is True


def test_detecta_conteo_negativo(tmp_path) -> None:
    """Caso real (2026-08-24): CDMX, sep-2017, conteo=-1 -- una corrección
    retroactiva de SESNSP. La suite debe marcarlo, no filtrarlo ni corregirlo."""
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila_sesnsp(
            "9", "006", 2017, 9,
            "Otros delitos que atentan contra la libertad personal", -1,
        )]),
    ], ignore_index=True)

    resultado = validar_sesnsp(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallos = [r.expectation_config.type for r in resultado.results if not r.success]
    assert fallos == ["expect_column_values_to_be_between"]
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.kwargs["column"] == "conteo"
    assert fallo.result["partial_unexpected_list"] == [-1]


def test_detecta_tipo_delito_fuera_del_catalogo(tmp_path) -> None:
    """Si SESNSP agrega una categoría nueva no confirmada en el catálogo, la suite
    debe fallar de forma visible -- es la señal de que hay que revisar a mano, no
    dejarla pasar en silencio."""
    assert "Delito Inventado No Real" not in CATALOGO_TIPO_DELITO
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila_sesnsp("1", "001", 2020, 5, "Delito Inventado No Real", 3)]),
    ], ignore_index=True)

    resultado = validar_sesnsp(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.kwargs["column"] == "tipo_delito"


def test_detecta_llave_duplicada(tmp_path) -> None:
    """Dos filas con la misma (cve_ent, cve_mun, anio, mes, tipo_delito) significaría
    que el extractor no agregó correctamente subtipo/modalidad -- regresión real, no
    un hallazgo de la fuente (ver extractor_sesnsp._finalizar_agregado)."""
    df = pd.concat([
        _df_limpio(),
        pd.DataFrame([_fila_sesnsp("1", "001", 2015, 1, "Homicidio", 99)]),  # llave repetida
    ], ignore_index=True)

    resultado = validar_sesnsp(
        df=df, ge_context_dir=str(tmp_path / "gx"), construir_data_docs=False
    )

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.type == "expect_compound_columns_to_be_unique"
