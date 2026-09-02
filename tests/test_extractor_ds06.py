"""Pruebas del extractor de DS-06 CONAGUA (`src/ingesta/extractor_conagua.py`) y
de la limpieza de columnas usada antes de validar con Great Expectations.

Sigue el mismo espíritu que `tests/test_extractor_sinaica.py`: datos sintéticos
que reproducen la ESTRUCTURA real confirmada en vivo (ver
`vault/14_Data_Sources/DS-06_CONAGUA_SINA.md` sección 9 y el DevLog de la sesión), sin
depender de una llamada de red real durante la prueba.
"""
from __future__ import annotations

import pandas as pd

from src.ingesta.validacion_conagua import limpiar_columnas_numericas

# Estructura real confirmada por el endpoint mapa.php (POST, Accion=Presas):
# las columnas numéricas llegan como texto, no como número.
_FILA_TIPICA = {
    "id_presa": "237",
    "nombre_oficial": "237 - Rodríguez",
    "corriente": "Río Tijuana",
    "estado": "Baja California",
    "anio_term": "1937",
    "alt_cort": "72",
    "cap_name": "121",
    "cap_namo": "77",
}


def test_limpia_columnas_numericas_que_llegan_como_texto() -> None:
    df = pd.DataFrame([_FILA_TIPICA])
    limpio = limpiar_columnas_numericas(df)

    assert limpio["cap_namo"].iloc[0] == 77.0
    assert limpio["cap_name"].iloc[0] == 121.0
    assert limpio["alt_cort"].iloc[0] == 72.0
    # Deben quedar como número, no como texto
    assert pd.api.types.is_numeric_dtype(limpio["cap_namo"])


def test_valor_no_convertible_queda_como_nan_no_como_error() -> None:
    """Si algún día el endpoint entrega un valor corrupto/vacío, no debe tronar --
    debe quedar como NaN, que es justo lo que las expectativas de nulos atrapan."""
    fila_corrupta = dict(_FILA_TIPICA, cap_namo="N/D")
    df = pd.DataFrame([fila_corrupta])

    limpio = limpiar_columnas_numericas(df)

    assert pd.isna(limpio["cap_namo"].iloc[0])


def test_no_modifica_el_dataframe_original() -> None:
    """limpiar_columnas_numericas debe devolver una copia, no mutar el df de entrada
    (el extractor sigue usando el original más abajo para otras columnas)."""
    df_original = pd.DataFrame([_FILA_TIPICA])
    dtype_original = df_original["cap_namo"].dtype

    limpiar_columnas_numericas(df_original)

    assert df_original["cap_namo"].dtype == dtype_original