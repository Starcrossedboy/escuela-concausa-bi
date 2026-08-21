"""Pruebas del scaffold de ML-02 (US-302)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.modelos.contrato import DRIVERS
from src.modelos.entrenar_ml02 import (
    CLASES_DRIVER,
    COLUMNA_TARGET_PROXY,
    NOMBRE_MODELO,
    cargar_features_ml02,
    columna_target_disponible,
    entrenar_y_evaluar,
    explicar_driver,
    generar_driver_dominante_proxy,
    predecir_driver,
    recomendacion_para_driver,
)
from src.modelos.particion_temporal import _anio_inicial


def test_deriva_driver_dominante_proxy_sin_imputar_cero(features: pd.DataFrame) -> None:
    proxy = generar_driver_dominante_proxy(features)
    assert set(proxy) <= set(CLASES_DRIVER)

    fila = pd.DataFrame([{driver: np.nan for driver in DRIVERS} | {"d2_inseguridad": 0.7}])
    assert generar_driver_dominante_proxy(fila).iloc[0] == "D2"


def test_falla_si_no_hay_ningun_driver_observado() -> None:
    fila = pd.DataFrame([{driver: np.nan for driver in DRIVERS}])
    with pytest.raises(ValueError, match="sin ningun driver"):
        generar_driver_dominante_proxy(fila)


def test_carga_fixture_y_agrega_target_proxy() -> None:
    df = cargar_features_ml02()
    assert COLUMNA_TARGET_PROXY in df.columns
    assert columna_target_disponible(df) == COLUMNA_TARGET_PROXY


@pytest.fixture(scope="module")
def resultado_ml02(features: pd.DataFrame):
    df = features.copy()
    df[COLUMNA_TARGET_PROXY] = generar_driver_dominante_proxy(df)
    return entrenar_y_evaluar(df, n_ventanas=3)


def test_ml02_genera_backtesting_temporal(resultado_ml02) -> None:
    assert len(resultado_ml02.ventanas) == 3
    for ventana in resultado_ml02.ventanas:
        ultimo_train = max(_anio_inicial(c) for c in ventana.particion.ciclos_entrenamiento)
        primero_test = min(_anio_inicial(c) for c in ventana.particion.ciclos_prueba)
        assert ultimo_train < primero_test


def test_metricas_de_clasificacion_son_acotadas(resultado_ml02) -> None:
    for ventana in resultado_ml02.ventanas:
        assert 0 <= ventana.f1_macro <= 1
        assert 0 <= ventana.accuracy <= 1
        assert 0 <= ventana.precision_macro <= 1


def test_prediccion_incluye_driver_y_recomendacion(resultado_ml02, features: pd.DataFrame) -> None:
    predicciones = predecir_driver(resultado_ml02.modelo, features.head(5))
    assert set(predicciones.columns) == {"cct", "id_ciclo", "driver_dominante", "recomendacion"}
    assert set(predicciones["driver_dominante"]) <= set(CLASES_DRIVER)
    assert predicciones["recomendacion"].str.len().min() > 0


def test_recomendacion_falla_con_driver_desconocido() -> None:
    with pytest.raises(ValueError, match="Driver desconocido"):
        recomendacion_para_driver("D9")


def test_nombre_mlflow_es_canonico() -> None:
    assert NOMBRE_MODELO == "ML02_DriverClasificador"


def test_explicacion_shap_cumple_contrato_api(
    resultado_ml02,
    features: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filas = features.head(2)
    contribuciones = [
        {driver: float(indice) for indice, driver in enumerate(DRIVERS)}
        for _ in range(len(filas))
    ]
    monkeypatch.setattr(
        "src.modelos.entrenar_ml02.calcular_shap_kernel",
        lambda *args, **kwargs: contribuciones,
    )

    explicaciones = explicar_driver(resultado_ml02.modelo, features, filas)

    assert len(explicaciones) == len(filas)
    assert set(explicaciones[0]) == {"cct", "driver_dominante", "contribuciones"}
    assert set(explicaciones[0]["contribuciones"]) == set(CLASES_DRIVER)
    assert explicaciones[0]["cct"] == filas.iloc[0]["cct"]
