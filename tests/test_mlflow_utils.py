"""Pruebas del contrato local de MLflow para US-303."""

from __future__ import annotations

import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from src.modelos.mlflow_utils import (
    NOMBRES_MODELOS_CANONICOS,
    RegistroModelo,
    registrar_sklearn,
    validar_nombre_modelo,
    verificar_artefactos_descargables,
    verificar_modelos_registrados,
)


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


def test_registro_confirma_version_y_la_deja_como_tag(monkeypatch) -> None:
    tags: dict[str, str] = {}
    cliente = SimpleNamespace(
        sklearn=SimpleNamespace(
            log_model=lambda modelo, name: SimpleNamespace(model_uri=f"runs:/run-123/{name}")
        ),
        set_tracking_uri=lambda uri: None,
        set_experiment=lambda nombre: None,
        start_run=lambda run_name: nullcontext(
            SimpleNamespace(info=SimpleNamespace(run_id="run-123"))
        ),
        log_params=lambda parametros: None,
        log_metrics=lambda metricas: None,
        register_model=lambda uri, nombre: SimpleNamespace(version="7"),
        set_tag=lambda clave, valor: tags.__setitem__(clave, valor),
    )
    monkeypatch.setitem(sys.modules, "mlflow", cliente)
    monkeypatch.setattr(mlflow_utils, "verificar_compatibilidad", lambda uri: None)
    config = RegistroModelo(
        nombre_modelo="ML02_DriverClasificador",
        experimento="prueba",
        registrar_modelo=True,
    )

    run_id = registrar_sklearn(object(), config)

    assert run_id == "run-123"
    assert tags["registered_model_version"] == "7"


def test_verifica_version_mas_reciente_de_modelos_solicitados(monkeypatch) -> None:
    class ClienteFake:
        def __init__(self, tracking_uri: str) -> None:
            assert tracking_uri == "http://mlflow:5000"

        def search_model_versions(self, filtro: str):
            assert filtro == "name='ML02_DriverClasificador'"
            return [SimpleNamespace(version="1"), SimpleNamespace(version="3")]

    monkeypatch.setitem(sys.modules, "mlflow", SimpleNamespace(MlflowClient=ClienteFake))
    monkeypatch.setattr(mlflow_utils, "verificar_compatibilidad", lambda uri: None)

    versiones = verificar_modelos_registrados(
        "http://mlflow:5000",
        frozenset({"ML02_DriverClasificador"}),
    )

    assert versiones == {"ML02_DriverClasificador": "3"}


def test_reporta_modelos_faltantes_en_registry(monkeypatch) -> None:
    class ClienteFake:
        def __init__(self, tracking_uri: str) -> None:
            pass

        def search_model_versions(self, filtro: str):
            return []

    monkeypatch.setitem(sys.modules, "mlflow", SimpleNamespace(MlflowClient=ClienteFake))
    monkeypatch.setattr(mlflow_utils, "verificar_compatibilidad", lambda uri: None)

    with pytest.raises(RuntimeError, match="ML03_ClusteringEscuelas"):
        verificar_modelos_registrados(
            "http://mlflow:5000",
            frozenset({"ML03_ClusteringEscuelas"}),
        )


def test_reporta_version_invalida_con_el_modelo_afectado(monkeypatch) -> None:
    class ClienteFake:
        def __init__(self, tracking_uri: str) -> None:
            pass

        def search_model_versions(self, filtro: str):
            return [SimpleNamespace(version=None)]

    monkeypatch.setitem(sys.modules, "mlflow", SimpleNamespace(MlflowClient=ClienteFake))
    monkeypatch.setattr(mlflow_utils, "verificar_compatibilidad", lambda uri: None)

    with pytest.raises(RuntimeError, match="ML01_RegresionMatricula"):
        verificar_modelos_registrados(
            "http://mlflow:5000",
            frozenset({"ML01_RegresionMatricula"}),
        )


def _mlflow_con_carga(cargar) -> SimpleNamespace:
    """Doble de `mlflow` cuyo `pyfunc.load_model` delega en `cargar`."""
    return SimpleNamespace(
        set_tracking_uri=lambda uri: None,
        pyfunc=SimpleNamespace(load_model=cargar),
    )


def test_artefacto_descargable_pasa_cuando_el_modelo_carga(monkeypatch) -> None:
    pedidos: list[str] = []
    monkeypatch.setitem(
        sys.modules, "mlflow", _mlflow_con_carga(lambda uri: pedidos.append(uri) or object())
    )

    verificar_artefactos_descargables(
        "http://mlflow:5000",
        {"ML01_RegresionMatricula": "2", "ML02_DriverClasificador": "5"},
    )

    # Se carga por `models:/nombre/version`, la misma ruta que usa la API de la Célula 4.
    assert pedidos == ["models:/ML01_RegresionMatricula/2", "models:/ML02_DriverClasificador/5"]


def test_artefacto_ausente_reprueba_aunque_la_version_exista(monkeypatch) -> None:
    """El caso de BUG-041: la fila del Registry está `READY` pero el artefacto no llega.

    Es exactamente el estado en que `ML01_RegresionMatricula` v1 estuvo en verde desde el 18-ago:
    `verificar_modelos_registrados` la reportaba y ningún cliente podía cargarla.
    """

    def cargar(uri: str):
        raise RuntimeError('No such artifact: "MLmodel"')

    monkeypatch.setitem(sys.modules, "mlflow", _mlflow_con_carga(cargar))

    with pytest.raises(RuntimeError) as error:
        verificar_artefactos_descargables("http://mlflow:5000", {"ML01_RegresionMatricula": "1"})

    mensaje = str(error.value)
    assert "ML01_RegresionMatricula v1" in mensaje       # dice cuál falló
    assert "--serve-artifacts" in mensaje                # y por qué
    assert "BUG-041" in mensaje


def test_artefacto_reporta_todos_los_modelos_rotos_no_solo_el_primero(monkeypatch) -> None:
    def cargar(uri: str):
        raise RuntimeError("No such artifact")

    monkeypatch.setitem(sys.modules, "mlflow", _mlflow_con_carga(cargar))

    with pytest.raises(RuntimeError) as error:
        verificar_artefactos_descargables(
            "http://mlflow:5000",
            {"ML01_RegresionMatricula": "1", "ML03_ClusteringEscuelas": "4"},
        )

    # Un reporte parcial obligaría a arreglar y re-correr modelo por modelo.
    assert "ML01_RegresionMatricula v1" in str(error.value)
    assert "ML03_ClusteringEscuelas v4" in str(error.value)
