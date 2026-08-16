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
