"""Pruebas de la suite Great Expectations de DS-05 SINAICA
(`src/ingesta/validacion_sinaica.py`, `TEST-010`).

Corre completamente offline: `validar_sinaica_estaciones()`/`validar_sinaica_observaciones()`
aceptan un DataFrame explícito y un `ge_context_dir` de prueba (`tmp_path`) en vez de
tocar `data/bronze/sinaica/` o el `great_expectations/` real del repo -- lo que pide
`US-124b` ("que CI corra sin descargar datos reales").

Los datos son sintéticos pero reproducen el esquema real confirmado el 2026-08-21,
incluyendo el mismo tipo de anomalía encontrada en producción (~6.3% de estaciones con
georreferencia inutilizable: nulo genuino o placeholder "0.0") -- así la prueba
demuestra que la suite SÍ atrapa ese caso, no solo que corre sin tronar.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.ingesta.validacion_sinaica import (
    validar_sinaica_estaciones,
    validar_sinaica_observaciones,
)

# --------------------------------------------------------------------------- estaciones


def _fila_estacion(id_, nombre, municipio_id, lat, lon) -> dict:
    return {
        "id": id_, "nombre": nombre, "municipioId": municipio_id,
        "latitud": lat, "longitud": lon,
        "_ingested_at": datetime.now(timezone.utc),
        "_source": "DS-05_SINAICA", "_source_url": "https://ejemplo.test/estaciones",
    }


def test_estaciones_con_georreferencia_valida_pasan(tmp_path) -> None:
    df = pd.DataFrame([
        _fila_estacion(33, "Centro", "1", "21.883780555556", "-102.295825"),
        _fila_estacion(271, "Xalostoc", "57", "19.53", "-99.08"),
    ])
    resultado = validar_sinaica_estaciones(df=df, ge_context_dir=str(tmp_path / "gx"))
    assert resultado.success is True


def test_detecta_placeholder_0_0_como_sin_georreferencia(tmp_path) -> None:
    """Caso real (2026-08-21): 21/384 estaciones traen '0.0' literal en vez de un
    SIN_DATO explícito -- exactamente el patrón que la regla del proyecto prohíbe."""
    df = pd.DataFrame([
        _fila_estacion(33, "Centro", "1", "21.883780555556", "-102.295825"),
        _fila_estacion(999, "Estación Rota", "0", "0.0", "0.0"),
    ])
    resultado = validar_sinaica_estaciones(df=df, ge_context_dir=str(tmp_path / "gx"))

    assert resultado.success is False
    columnas_con_fallo = {
        r.expectation_config.kwargs["column"] for r in resultado.results if not r.success
    }
    assert columnas_con_fallo == {"latitud", "longitud"}


def test_detecta_nulo_genuino_en_georreferencia(tmp_path) -> None:
    """Caso real (2026-08-21): 3/384 estaciones traen nulo genuino, distinto del
    placeholder '0.0' -- ambos deben quedar atrapados, son dos formas del mismo
    problema."""
    df = pd.DataFrame([
        _fila_estacion(33, "Centro", "1", "21.883780555556", "-102.295825"),
        _fila_estacion(998, "Sin Coordenadas", "0", None, None),
    ])
    resultado = validar_sinaica_estaciones(df=df, ge_context_dir=str(tmp_path / "gx"))
    assert resultado.success is False


def test_detecta_id_duplicado(tmp_path) -> None:
    df = pd.DataFrame([
        _fila_estacion(33, "Centro", "1", "21.88", "-102.29"),
        _fila_estacion(33, "Centro (duplicada)", "1", "21.88", "-102.29"),
    ])
    resultado = validar_sinaica_estaciones(df=df, ge_context_dir=str(tmp_path / "gx"))

    assert resultado.success is False
    fallo = next(r for r in resultado.results if not r.success)
    assert fallo.expectation_config.type == "expect_column_values_to_be_unique"


# --------------------------------------------------------------------------- observaciones


def _fila_observacion(id_estacion, parametro, fecha, hora, valor, val) -> dict:
    return {
        "fecha": fecha, "hora": hora, "valor": valor, "val": val,
        "id_estacion": id_estacion, "parametro": parametro,
        "_ingested_at": datetime.now(timezone.utc),
        "_source": "DS-05_SINAICA", "_source_url": "https://ejemplo.test/datGrafs.php",
    }


def _df_observaciones_limpio() -> pd.DataFrame:
    return pd.DataFrame([
        _fila_observacion(33, "PM2.5", "2026-08-01", 0, 16.0, 1),
        _fila_observacion(33, "O3", "2026-08-01", 0, 0.02, 1),
        _fila_observacion(271, "PM10", "2026-08-01", 5, 45.0, 1),
    ])


def test_observaciones_limpias_pasan(tmp_path) -> None:
    resultado = validar_sinaica_observaciones(
        df=_df_observaciones_limpio(), ge_context_dir=str(tmp_path / "gx")
    )
    assert resultado.success is True


def test_detecta_valor_fuera_de_rango_fisico_por_parametro(tmp_path) -> None:
    """O3 se mide en ppm (rango plausible 0-0.5); un valor de 900 solo tiene sentido
    si es PM2.5/PM10 en µg/m³ -- señal de que el `parametro` viene mal etiquetado o el
    dato está corrupto. El rango es por parámetro, no genérico para toda la columna
    `valor` (unidades distintas por contaminante)."""
    df = pd.concat([
        _df_observaciones_limpio(),
        pd.DataFrame([_fila_observacion(33, "O3", "2026-08-02", 10, 900.0, 1)]),
    ], ignore_index=True)

    resultado = validar_sinaica_observaciones(df=df, ge_context_dir=str(tmp_path / "gx"))

    assert resultado.success is False
    fallo = next(
        r for r in resultado.results
        if not r.success and r.expectation_config.kwargs.get("row_condition")
    )
    condicion = fallo.expectation_config.kwargs["row_condition"]
    assert condicion["column"]["name"] == "parametro"
    assert condicion["parameter"] == "O3"


def test_detecta_hora_fuera_de_rango(tmp_path) -> None:
    df = pd.concat([
        _df_observaciones_limpio(),
        pd.DataFrame([_fila_observacion(33, "PM2.5", "2026-08-03", 24, 10.0, 1)]),
    ], ignore_index=True)

    resultado = validar_sinaica_observaciones(df=df, ge_context_dir=str(tmp_path / "gx"))

    assert resultado.success is False
    columnas_con_fallo = {
        r.expectation_config.kwargs.get("column") for r in resultado.results if not r.success
    }
    assert "hora" in columnas_con_fallo


def test_detecta_llave_compuesta_duplicada(tmp_path) -> None:
    """Misma estación/parámetro/fecha/hora dos veces dentro del mismo archivo Bronze
    -- no debería pasar nunca en una extracción normal (ver DS-05 doc, riesgos)."""
    df = pd.concat([
        _df_observaciones_limpio(),
        pd.DataFrame([_fila_observacion(33, "PM2.5", "2026-08-01", 0, 17.0, 1)]),  # repetida
    ], ignore_index=True)

    resultado = validar_sinaica_observaciones(df=df, ge_context_dir=str(tmp_path / "gx"))

    assert resultado.success is False
    fallo = next(
        r for r in resultado.results
        if not r.success and r.expectation_config.type == "expect_compound_columns_to_be_unique"
    )
    assert fallo is not None
