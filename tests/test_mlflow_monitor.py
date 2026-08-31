"""
tests/scripts/test_mlflow_monitor.py
---------------------------------------
Tests unitarios para scripts/mlflow_monitor.py.

Enfoque: se testea evaluar_run() de forma totalmente aislada, usando
objetos falsos (fakes) en vez de un servidor MLflow real. Ningún test
de este archivo importa mlflow.tracking.MlflowClient: eso es a
propósito, ya que confirma que la lógica de evaluar_run() no depende
en absoluto de tener `mlflow` instalado.

No se testea main() end-to-end aquí a propósito: eso requeriría un
servidor MLflow real o mockear la librería `mlflow` completa, lo cual
es un test de integración, no unitario. Si se quiere esa cobertura,
debería vivir en un archivo separado (ej. test_mlflow_monitor_integracion.py)
marcado con @pytest.mark.integration.
"""

import ast
import inspect

from scripts.mlflow_monitor import ConfiguracionMonitor, evaluar_run
import scripts.mlflow_monitor as mlflow_monitor_module


class _InfoFalsa:
    def __init__(self, run_id: str, status: str):
        self.run_id = run_id
        self.status = status


class _DataFalsa:
    def __init__(self, metrics: dict):
        self.metrics = metrics


class RunFalso:
    """Simula un objeto Run de MLflow, sin depender de la librería real."""

    def __init__(self, run_id: str, status: str, metrics: dict | None = None):
        self.info = _InfoFalsa(run_id, status)
        self.data = _DataFalsa(metrics or {})


def _config(
    metrica: str | None = None,
    metrica_min: float | None = None,
    metrica_max: float | None = None,
) -> ConfiguracionMonitor:
    return ConfiguracionMonitor(
        tracking_uri="http://localhost:5000",
        experimento="experimento-de-prueba",
        metrica=metrica,
        metrica_min=metrica_min,
        metrica_max=metrica_max,
    )


def test_run_finalizado_sin_metrica_configurada_no_reporta_problemas():
    run = RunFalso(run_id="run-1", status="FINISHED")
    problemas = evaluar_run(run, _config())
    assert problemas == []


def test_run_failed_reporta_problema():
    run = RunFalso(run_id="run-2", status="FAILED")
    problemas = evaluar_run(run, _config())
    assert len(problemas) == 1
    assert "FAILED" in problemas[0]
    assert "run-2" in problemas[0]


def test_metrica_faltante_reporta_problema():
    run = RunFalso(run_id="run-3", status="FINISHED", metrics={})
    problemas = evaluar_run(run, _config(metrica="accuracy"))
    assert len(problemas) == 1
    assert "no registró la métrica" in problemas[0]


def test_metrica_por_debajo_del_minimo_reporta_problema():
    run = RunFalso(run_id="run-4", status="FINISHED", metrics={"accuracy": 0.5})
    problemas = evaluar_run(run, _config(metrica="accuracy", metrica_min=0.8))
    assert len(problemas) == 1
    assert "por debajo del" in problemas[0]


def test_metrica_por_encima_del_maximo_reporta_problema():
    run = RunFalso(run_id="run-5", status="FINISHED", metrics={"error_rate": 0.9})
    problemas = evaluar_run(run, _config(metrica="error_rate", metrica_max=0.3))
    assert len(problemas) == 1
    assert "por encima del" in problemas[0]


def test_metrica_dentro_de_rango_no_reporta_problemas():
    run = RunFalso(run_id="run-6", status="FINISHED", metrics={"accuracy": 0.95})
    problemas = evaluar_run(
        run, _config(metrica="accuracy", metrica_min=0.8, metrica_max=1.0)
    )
    assert problemas == []


def test_run_failed_y_metrica_fuera_de_rango_reporta_ambos_problemas():
    """
    evaluar_run() debe acumular TODOS los problemas encontrados en una
    sola lista, no detenerse en el primero (así se manda un único
    mensaje de alerta con todo el detalle, en vez de varios mensajes).
    """
    run = RunFalso(run_id="run-7", status="FAILED", metrics={"accuracy": 0.1})
    problemas = evaluar_run(run, _config(metrica="accuracy", metrica_min=0.8))
    assert len(problemas) == 2


def test_mlflow_no_se_importa_a_nivel_de_modulo():
    """
    Test de "regresión de arquitectura" para el Paso C.

    En vez de simular la ausencia de `mlflow` en tiempo de ejecución
    (frágil: implica parchear el sistema de import y reimportar
    módulos), se analiza estáticamente el AST del archivo fuente y se
    confirma que ningún `import mlflow` / `from mlflow...` vive a nivel
    de módulo. Si alguien en el futuro revierte el Paso C (por ejemplo
    moviendo el import de vuelta arriba del archivo "por prolijidad"),
    este test debe fallar y avisar por qué es un problema.
    """
    codigo_fuente = inspect.getsource(mlflow_monitor_module)
    arbol = ast.parse(codigo_fuente)

    imports_de_mlflow_a_nivel_de_modulo = []
    for nodo in ast.iter_child_nodes(arbol):
        # Solo miramos nodos que son HIJOS DIRECTOS del módulo (nivel 0),
        # no los que están dentro de una función (esos son hijos de un
        # ast.FunctionDef, no del ast.Module).
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name == "mlflow" or alias.name.startswith("mlflow."):
                    imports_de_mlflow_a_nivel_de_modulo.append(alias.name)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module and (
                nodo.module == "mlflow" or nodo.module.startswith("mlflow.")
            ):
                imports_de_mlflow_a_nivel_de_modulo.append(nodo.module)

    assert imports_de_mlflow_a_nivel_de_modulo == [], (
        "Se encontró un import de mlflow a nivel de módulo: "
        f"{imports_de_mlflow_a_nivel_de_modulo}. Esto rompe el Paso C "
        "(import diferido) y puede tumbar el parseo del DAG en Airflow "
        "si mlflow no está instalado en el entorno del scheduler."
    )
