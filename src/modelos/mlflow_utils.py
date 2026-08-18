"""Utilidades comunes de registro MLflow para Célula 3 (US-303)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

NOMBRES_MODELOS_CANONICOS = frozenset(
    {
        "ML01_RegresionMatricula",
        "ML02_DriverClasificador",
        "ML03_ClusteringEscuelas",
    }
)


@dataclass(frozen=True)
class RegistroModelo:
    """Configuracion para registrar un modelo en MLflow."""

    nombre_modelo: str
    experimento: str
    tracking_uri: str = "sqlite:///mlflow.db"
    artifact_path: str = "modelo"
    registrar_modelo: bool = False
    parametros: Mapping[str, Any] = field(default_factory=dict)
    metricas: Mapping[str, float] = field(default_factory=dict)


def validar_nombre_modelo(nombre_modelo: str) -> None:
    """Falla si el modelo no usa el nombre acordado en `ML_Strategy` §7."""
    if nombre_modelo not in NOMBRES_MODELOS_CANONICOS:
        esperados = ", ".join(sorted(NOMBRES_MODELOS_CANONICOS))
        raise ValueError(f"Nombre de modelo no canonico: {nombre_modelo!r}. Esperado uno de: {esperados}.")


def registrar_sklearn(modelo: Any, config: RegistroModelo) -> str:
    """Registra un modelo compatible con scikit-learn en MLflow.

    El import de MLflow es diferido para que el entrenamiento y las pruebas unitarias puedan correr
    en ambientes que solo instalaron `requirements.txt`.

    Returns:
        `run_id` de la corrida MLflow, que despues se persiste en `gold.predicciones.mlflow_run_id`.
    """
    validar_nombre_modelo(config.nombre_modelo)

    try:
        import mlflow
    except ImportError as exc:  # pragma: no cover - depende del ambiente de C3
        raise RuntimeError("Instala mlflow para registrar modelos de Célula 3.") from exc

    mlflow.set_tracking_uri(config.tracking_uri)
    mlflow.set_experiment(config.experimento)

    with mlflow.start_run(run_name=config.nombre_modelo) as run:
        if config.parametros:
            mlflow.log_params(dict(config.parametros))
        if config.metricas:
            mlflow.log_metrics(dict(config.metricas))
        info = mlflow.sklearn.log_model(modelo, name=config.artifact_path)
        if config.registrar_modelo:
            mlflow.register_model(info.model_uri, config.nombre_modelo)
        return run.info.run_id


def version_del_servidor(tracking_uri: str, timeout: float = 10.0) -> str | None:
    """Consulta la versión del servidor MLflow. `None` si no es un servidor HTTP o no responde.

    El servidor expone `GET /version` en texto plano (p. ej. `"2.8.0"`).
    """
    if not tracking_uri.startswith(("http://", "https://")):
        return None  # backends locales (sqlite:///, file:) no tienen servidor que consultar
    import requests

    try:
        respuesta = requests.get(f"{tracking_uri.rstrip('/')}/version", timeout=timeout)
        respuesta.raise_for_status()
        return respuesta.text.strip()
    except Exception:  # noqa: BLE001 - la incompatibilidad no debe tapar el error real de entrenar
        return None


def version_del_cliente() -> str | None:
    """Versión de MLflow instalada localmente. `None` si no está instalado."""
    try:
        import mlflow
    except ImportError:
        return None
    return mlflow.__version__


def verificar_compatibilidad(tracking_uri: str, version_cliente: str | None = None) -> None:
    """Falla temprano y con un mensaje accionable si cliente y servidor no son compatibles.

    Un cliente MLflow 3.x contra un servidor 2.x **registra métricas pero pierde los modelos**:
    `log_model()` llama `/api/2.0/mlflow/logged-models`, que no existe en 2.x, y responde 404. El
    síntoma es confuso —la corrida aparece en la UI, sin artefactos ni versión en el registry— y
    bloquea AC-003.4 sin que sea evidente por qué.

    Esta verificación convierte ese 404 tardío en un error inmediato que dice qué hacer.

    Args:
        tracking_uri: URI de tracking. Los backends locales (`sqlite:///`, `file:`) se omiten.
        version_cliente: versión a comparar. Por defecto, la instalada. Se inyecta desde las
            pruebas para que corran en el CI, que sólo instala `requirements.txt` y no trae MLflow.

    Raises:
        RuntimeError: si las versiones mayores de cliente y servidor difieren.
    """
    servidor = version_del_servidor(tracking_uri)
    if servidor is None:
        return

    cliente = version_cliente or version_del_cliente()
    if cliente is None:
        return  # sin cliente instalado no hay nada que registrar ni que comparar

    if servidor.split(".")[0] != cliente.split(".")[0]:
        raise RuntimeError(
            f"MLflow incompatible: servidor {servidor} vs cliente {cliente} en {tracking_uri}.\n"
            "Con versiones mayores distintas las métricas sí se registran, pero los MODELOS no: "
            "`log_model()` falla con 404 y el registry queda vacío (AC-003.4 sin cumplir).\n"
            "Alinea las versiones: el servidor lo define `docker/mlflow.Dockerfile` (Célula 5) y "
            "el cliente `requirements/celula-3.txt`."
        )
