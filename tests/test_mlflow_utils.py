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


# --------------------------------------------------------------------- compatibilidad (US-311)
# Añadido por Héctor Morales: un cliente 3.x contra un servidor 2.x registra métricas pero pierde
# los modelos con un 404 poco evidente. Estas pruebas fijan el comportamiento del preflight.

from src.modelos import mlflow_utils


def test_backend_local_no_consulta_servidor() -> None:
    """`sqlite:///` y `file:` no tienen servidor: no hay nada que verificar ni red que tocar."""
    assert mlflow_utils.version_del_servidor("sqlite:///mlflow.db") is None
    mlflow_utils.verificar_compatibilidad("sqlite:///mlflow.db")  # no debe lanzar


def test_servidor_inalcanzable_no_bloquea(monkeypatch) -> None:
    """Si `/version` no responde, no se inventa una incompatibilidad: manda el error real."""
    monkeypatch.setattr(mlflow_utils, "version_del_servidor", lambda uri, **_: None)
    mlflow_utils.verificar_compatibilidad("http://localhost:5001")  # no debe lanzar


def test_rechaza_versiones_mayores_distintas(monkeypatch) -> None:
    """El caso real: servidor 2.8.0 (docker/mlflow.Dockerfile) vs cliente 3.x."""
    monkeypatch.setattr(mlflow_utils, "version_del_servidor", lambda uri, **_: "2.8.0")
    with pytest.raises(RuntimeError, match="MLflow incompatible"):
        mlflow_utils.verificar_compatibilidad("http://localhost:5001", version_cliente="3.15.1")


def test_el_mensaje_dice_donde_arreglarlo(monkeypatch) -> None:
    """Un error accionable ahorra horas: debe nombrar los dos archivos a alinear."""
    monkeypatch.setattr(mlflow_utils, "version_del_servidor", lambda uri, **_: "2.8.0")
    with pytest.raises(RuntimeError) as error:
        mlflow_utils.verificar_compatibilidad("http://localhost:5001", version_cliente="3.15.1")
    mensaje = str(error.value)
    assert "docker/mlflow.Dockerfile" in mensaje
    assert "requirements/celula-3.txt" in mensaje
    assert "AC-003.4" in mensaje


def test_acepta_misma_version_mayor(monkeypatch) -> None:
    monkeypatch.setattr(mlflow_utils, "version_del_servidor", lambda uri, **_: "3.0.0")
    mlflow_utils.verificar_compatibilidad("http://localhost:5001", version_cliente="3.15.1")


def test_sin_cliente_instalado_no_bloquea(monkeypatch) -> None:
    """Sin MLflow instalado no hay nada que registrar ni que comparar: no debe estorbar.

    Es el caso del CI, que instala sólo `requirements.txt`.
    """
    monkeypatch.setattr(mlflow_utils, "version_del_servidor", lambda uri, **_: "2.8.0")
    monkeypatch.setattr(mlflow_utils, "version_del_cliente", lambda: None)
    mlflow_utils.verificar_compatibilidad("http://localhost:5001")  # no debe lanzar
