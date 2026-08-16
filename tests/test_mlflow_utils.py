"""Pruebas del contrato local de MLflow para US-303."""

from __future__ import annotations

import pytest

from src.modelos.mlflow_utils import NOMBRES_MODELOS_CANONICOS, validar_nombre_modelo


def test_nombres_canonicos_incluyen_los_tres_modelos() -> None:
    assert NOMBRES_MODELOS_CANONICOS == {
        "ML01_RegresionMatricula",
        "ML02_DriverClasificador",
        "ML03_ClusteringEscuelas",
    }


def test_validar_nombre_modelo_acepta_nombres_canonicos() -> None:
    validar_nombre_modelo("ML02_DriverClasificador")


def test_validar_nombre_modelo_rechaza_alias_no_acordados() -> None:
    with pytest.raises(ValueError, match="no canonico"):
        validar_nombre_modelo("driver_classifier")
