#!/usr/bin/env python3
"""
scripts/mlflow_monitor.py
---------------------------
Script standalone (funciona con o sin Airflow) que:

  1. Se conecta a un servidor de MLflow Tracking.
  2. Busca el run más reciente de un experimento.
  3. Revisa si ese run:
       a) terminó con estado FAILED, y/o
       b) tiene una métrica clave fuera de un rango configurable.
  4. Si encuentra un problema, manda una alerta al MISMO webhook usado
     por los callbacks de Airflow (reusa `common_alerting/webhook.py`).

Por qué es un script standalone y no "solo un DAG":
- Se puede correr a mano para debug: `python mlflow_monitor.py --experiment X`.
- Se puede programar de dos formas distintas (ver sección 3 de la
  documentación en docs/monitoreo_alertas.md): con un DAG de Airflow que
  se autovigila, o con un cron plano dentro del contenedor. No queda
  atado a un solo orquestador.

Por qué se usa el cliente oficial `mlflow.tracking.MlflowClient` en vez
de pegarle directo a la REST API con `requests`:
- El cliente ya resuelve autenticación leyendo las variables de entorno
  estándar de MLflow (`MLFLOW_TRACKING_URI`, `MLFLOW_TRACKING_TOKEN`,
  `MLFLOW_TRACKING_USERNAME/PASSWORD`, etc.), así no reinventamos ese
  manejo a mano.
- Es la forma soportada oficialmente; si la REST API cambia de forma,
  el cliente absorbe el cambio en su próxima versión sin que tengamos
  que tocar este script.

--------------------------------------------------------------------
NOTA — Paso C, import diferido de `mlflow` (2026-08-31):
El import de `mlflow.tracking.MlflowClient` se movió de nivel de
módulo a DENTRO de las funciones que realmente lo usan
(`obtener_ultimo_run` y `main`).

Por qué: `dags/mlflow_monitor_dag.py` hace
`from scripts.mlflow_monitor import main` a nivel de módulo. Airflow
parsea (importa) TODOS los archivos de `dags/` de forma repetida y
frecuente, no solo cuando la task corre. Si `mlflow` no estuviera
instalado en el entorno del *scheduler* (por ejemplo si solo los
workers tienen esa dependencia pesada), un import a nivel de módulo
tumbaría el DAG completo con un ImportError visible en la UI de
Airflow, incluso si la task de monitoreo nunca llegó a ejecutarse.
Con el import diferido, `mlflow` solo se carga cuando la función que
lo necesita se invoca de verdad (es decir, cuando la task corre en un
worker que sí tiene la dependencia instalada).
--------------------------------------------------------------------

Ubicación sugerida en el repo: `scripts/mlflow_monitor.py`
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass

# NOTA (Paso C): el import de mlflow.tracking.MlflowClient se movió a
# nivel de función. Ver el bloque de notas más arriba para el detalle.

# Reutilizamos la misma función de envío de alertas que usan los
# callbacks de Airflow: un solo lugar sabe "cómo" mandar el mensaje.
from common_alerting.webhook import enviar_alerta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ConfiguracionMonitor:
    """Agrupa toda la configuración del monitor en un solo objeto tipado."""

    tracking_uri: str
    experimento: str
    metrica: str | None
    metrica_min: float | None
    metrica_max: float | None


def _a_float(valor: str | None) -> float | None:
    """Convierte a float de forma segura; retorna None si no vino nada."""
    if valor is None or valor == "":
        return None
    return float(valor)


def leer_configuracion(argv: list[str] | None = None) -> ConfiguracionMonitor:
    """
    Combina argumentos de línea de comandos con variables de entorno.

    Decisión: se admiten AMBAS fuentes de configuración.
    - CLI: cómodo para correr el script a mano durante debug.
    - Env vars: cómodo para Airflow/cron, donde es más simple definir
      variables en el contenedor/DAG que armar un comando largo.
    La CLI tiene prioridad si se pasa explícitamente; si no, cae al
    valor de la variable de entorno correspondiente.

    El parámetro `argv` existe para poder invocar `main()` desde Python
    (por ejemplo desde un PythonOperator de Airflow) pasando `argv=[]`
    y así evitar que argparse intente leer el `sys.argv` real del
    proceso de Airflow (que no tiene nada que ver con este script).
    """
    parser = argparse.ArgumentParser(
        description="Monitorea el último run de un experimento de MLflow."
    )
    parser.add_argument(
        "--tracking-uri",
        default=os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"),
        help="URI del servidor de MLflow Tracking.",
    )
    parser.add_argument(
        "--experiment",
        default=os.environ.get("MLFLOW_EXPERIMENT_NAME"),
        required=os.environ.get("MLFLOW_EXPERIMENT_NAME") is None,
        help="Nombre del experimento de MLflow a monitorear.",
    )
    parser.add_argument(
        "--metric",
        default=os.environ.get("MLFLOW_METRIC_NAME"),
        help="Nombre de la métrica clave a validar (opcional).",
    )
    parser.add_argument(
        "--metric-min",
        type=float,
        default=_a_float(os.environ.get("MLFLOW_METRIC_MIN")),
        help="Valor mínimo aceptable de la métrica (opcional).",
    )
    parser.add_argument(
        "--metric-max",
        type=float,
        default=_a_float(os.environ.get("MLFLOW_METRIC_MAX")),
        help="Valor máximo aceptable de la métrica (opcional).",
    )
    args = parser.parse_args(argv)

    return ConfiguracionMonitor(
        tracking_uri=args.tracking_uri,
        experimento=args.experiment,
        metrica=args.metric,
        metrica_min=args.metric_min,
        metrica_max=args.metric_max,
    )


def obtener_ultimo_run(client, nombre_experimento: str):
    """
    Retorna el run más reciente (por start_time) de un experimento.

    `client` es un `mlflow.tracking.MlflowClient`. No se anota el tipo
    en la firma a propósito (ver Paso C): anotar `client: MlflowClient`
    aquí obligaría a importar `mlflow` a nivel de módulo otra vez para
    que la anotación resuelva, deshaciendo el punto del import diferido.

    Se filtra y ordena del lado del SERVIDOR de MLflow
    (`order_by=["start_time DESC"]`, `max_results=1`) en vez de traer
    todos los runs y ordenar en Python: evita transferir datos que no
    vamos a usar, algo relevante si el experimento tiene miles de runs.
    """
    experimento = client.get_experiment_by_name(nombre_experimento)
    if experimento is None:
        raise ValueError(f"No existe el experimento '{nombre_experimento}' en MLflow.")

    runs = client.search_runs(
        experiment_ids=[experimento.experiment_id],
        order_by=["start_time DESC"],
        max_results=1,
    )
    if not runs:
        raise ValueError(f"El experimento '{nombre_experimento}' todavía no tiene runs.")

    return runs[0]


def evaluar_run(run, config: ConfiguracionMonitor) -> list[str]:
    """
    Evalúa el run contra las condiciones de alerta.

    Retorna una LISTA de problemas encontrados (puede tener 0, 1 o más
    elementos). Se devuelve una lista y no un simple booleano para poder
    reportar todos los problemas juntos en un único mensaje de alerta,
    en vez de mandar una alerta por cada condición que falle.

    Nota: esta función no necesita el import de `mlflow` en absoluto,
    solo opera sobre el objeto `run` ya obtenido (duck typing sobre
    `run.info` / `run.data.metrics`), por eso quedó sin cambios.
    """
    problemas: list[str] = []

    estado = run.info.status  # FINISHED, FAILED, KILLED, RUNNING, etc.
    if estado == "FAILED":
        problemas.append(f"El último run ({run.info.run_id}) terminó con estado FAILED.")

    if config.metrica:
        valor_metrica = run.data.metrics.get(config.metrica)
        if valor_metrica is None:
            problemas.append(
                f"El run ({run.info.run_id}) no registró la métrica '{config.metrica}'."
            )
        else:
            if config.metrica_min is not None and valor_metrica < config.metrica_min:
                problemas.append(
                    f"Métrica '{config.metrica}' = {valor_metrica}, por debajo del "
                    f"mínimo aceptable ({config.metrica_min})."
                )
            if config.metrica_max is not None and valor_metrica > config.metrica_max:
                problemas.append(
                    f"Métrica '{config.metrica}' = {valor_metrica}, por encima del "
                    f"máximo aceptable ({config.metrica_max})."
                )

    return problemas


def main(argv: list[str] | None = None) -> int:
    # Paso C: import diferido. Solo se carga `mlflow` cuando `main()`
    # se ejecuta de verdad (en el worker), no cuando Airflow simplemente
    # parsea el archivo del DAG que importa esta función.
    from mlflow.tracking import MlflowClient

    config = leer_configuracion(argv)
    client = MlflowClient(tracking_uri=config.tracking_uri)

    try:
        run = obtener_ultimo_run(client, config.experimento)
    except ValueError as error:
        # Un experimento inexistente o sin runs también merece alerta:
        # normalmente indica un typo en el nombre o que el pipeline de
        # entrenamiento ni siquiera llegó a correr.
        logger.error(str(error))
        enviar_alerta(
            titulo=f"🟠 MLflow: problema con el experimento '{config.experimento}'",
            texto=str(error),
        )
        return 0  # Ver nota sobre códigos de salida más abajo.

    problemas = evaluar_run(run, config)

    if problemas:
        detalle = "\n".join(f"- {p}" for p in problemas)
        enviar_alerta(
            titulo=f"🔴 MLflow: alerta en experimento '{config.experimento}'",
            texto=(
                f"*Run:* {run.info.run_id}\n"
                f"*Experimento:* {config.experimento}\n"
                f"*Problemas detectados:*\n{detalle}"
            ),
        )
        logger.warning("Se detectaron %d problema(s); alerta enviada.", len(problemas))
    else:
        logger.info("Run %s OK, sin problemas detectados.", run.info.run_id)

    # Decisión sobre el código de salida: el script retorna 0 (éxito)
    # AUNQUE haya mandado una alerta. La task de Airflow que ejecuta este
    # script representa "el chequeo corrió correctamente", no "el modelo
    # está sano". Si el script retornara 1 al detectar un problema, el
    # `on_failure_callback` de Airflow dispararía una SEGUNDA alerta
    # redundante (una del monitor avisando el problema real, y otra de
    # Airflow avisando que "la task de monitoreo falló"). Si tu equipo
    # prefiere que la task quede en rojo cuando hay alerta (por ejemplo
    # para verlo de un vistazo en el Grid de Airflow), cambiá el
    # `return 0` de este bloque por `return 1`.
    return 0


if __name__ == "__main__":
    sys.exit(main())
