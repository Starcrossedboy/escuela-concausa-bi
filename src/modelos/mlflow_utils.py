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
    verificar_compatibilidad(config.tracking_uri)

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
            version = mlflow.register_model(info.model_uri, config.nombre_modelo)
            numero_version = getattr(version, "version", None)
            if numero_version is None:
                raise RuntimeError(
                    f"MLflow no confirmó una versión para {config.nombre_modelo!r}."
                )
            mlflow.set_tag("registered_model_version", str(numero_version))
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


def verificar_modelos_registrados(
    tracking_uri: str,
    nombres_modelos: frozenset[str] = NOMBRES_MODELOS_CANONICOS,
) -> dict[str, str]:
    """Confirma que cada modelo solicitado tenga al menos una versión en el Registry."""
    for nombre in nombres_modelos:
        validar_nombre_modelo(nombre)
    verificar_compatibilidad(tracking_uri)

    try:
        from mlflow import MlflowClient
    except ImportError as exc:  # pragma: no cover - depende del ambiente de C3
        raise RuntimeError("Instala mlflow para verificar el Model Registry.") from exc

    cliente = MlflowClient(tracking_uri=tracking_uri)
    versiones: dict[str, str] = {}
    faltantes: list[str] = []
    for nombre in sorted(nombres_modelos):
        encontradas = list(cliente.search_model_versions(f"name='{nombre}'"))
        if not encontradas:
            faltantes.append(nombre)
            continue
        try:
            versiones[nombre] = str(max(int(version.version) for version in encontradas))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"MLflow devolvió una versión inválida para {nombre!r}."
            ) from exc

    if faltantes:
        raise RuntimeError(f"Modelos sin versión en MLflow Registry: {', '.join(faltantes)}.")
    return versiones


def verificar_artefactos_descargables(
    tracking_uri: str,
    versiones: Mapping[str, str],
) -> None:
    """Confirma que cada versión registrada se pueda **cargar de vuelta**, no sólo que exista.

    Una fila en el Model Registry no prueba que el modelo esté ahí. Si el servidor de MLflow no
    corre con `--serve-artifacts`, su `--default-artifact-root` es una ruta **dentro del
    contenedor** (`/mlflow/artifacts`): las métricas viajan por la API REST y se guardan bien,
    pero los artefactos se resuelven contra el sistema de archivos del **cliente**. Escribir
    falla con `OSError: Read-only file system: '/mlflow'` y leer devuelve
    `No such artifact: 'MLmodel'` — mientras la versión sigue apareciendo `READY` en la UI y en
    `search_model_versions`.

    Ese hueco dejó `ML01_RegresionMatricula` versión 1 en verde desde el 18-ago sin que ningún
    cliente pudiera cargarla (**BUG-041**). AC-003.4 pide que el modelo *llegue* al registry, y la
    única prueba de eso es traerlo de vuelta — que es, además, exactamente lo que hace la API de
    la Célula 4 al servir inferencia.

    Se usa `pyfunc` a propósito: no depende del sabor con que se guardó el modelo y es la misma
    ruta de carga que usa quien lo consume.

    Args:
        tracking_uri: URI de tracking de MLflow.
        versiones: mapa `{nombre_modelo: version}`, tal como lo devuelve
            `verificar_modelos_registrados`.

    Raises:
        RuntimeError: si alguna versión no se puede cargar, nombrando el modelo y la causa probable.
    """
    try:
        import mlflow
    except ImportError as exc:  # pragma: no cover - depende del ambiente de C3
        raise RuntimeError("Instala mlflow para verificar el Model Registry.") from exc

    mlflow.set_tracking_uri(tracking_uri)

    fallidos: list[str] = []
    for nombre, version in sorted(versiones.items()):
        try:
            mlflow.pyfunc.load_model(f"models:/{nombre}/{version}")
        except Exception as exc:  # noqa: BLE001 - cualquier fallo aquí significa modelo inservible
            fallidos.append(f"{nombre} v{version} ({type(exc).__name__}: {str(exc)[:120]})")

    if fallidos:
        raise RuntimeError(
            "Hay versiones en el Registry que NO se pueden cargar: "
            + "; ".join(fallidos)
            + ".\nLa fila existe pero el artefacto no llega al cliente. Causa más común "
            "(BUG-041): el servidor de MLflow no corre con `--serve-artifacts`, así que su "
            "raíz de artefactos es una ruta interna del contenedor y ningún cliente puede "
            "leerla ni escribirla. Lo define `docker-compose.yml` (Célula 5)."
        )
