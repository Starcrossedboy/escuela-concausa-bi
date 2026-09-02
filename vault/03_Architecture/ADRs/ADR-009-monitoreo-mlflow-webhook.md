---
id: ADR-009
title: "ADR-009: Monitoreo de runs de MLflow con alertas por webhook generico"
owner: "Edgar Ulises Jiménez López"
status: proposed
version: "1.0"
traces_up: ["vault/02_Requirements/Requirements_Detailed", "vault/02_Requirements/User_Stories"]
traces_down: ["scripts/mlflow_monitor.py", "common_alerting/webhook.py", "common_alerting/airflow_callbacks.py", "dags/mlflow_monitor_dag.py"]
last_reviewed: "2026-08-31"
tags: [adr, devops, monitoreo, mlflow, alertas, celula-5]
---

# ADR-009: Monitoreo de runs de MLflow con alertas por webhook genérico

> Relacionado con: `US-524b` · Monitoreo, logs y alertas de Airflow y jobs ML
> Requisito: `REQ-005` · Deploy GCP
>
> **Nota de numeración:** este documento se creó directamente como `ADR-009`. El número `ADR-008`
> ya está tomado por la decisión de contenerización de Airflow/SQLAlchemy de `US-522b` (renombrada
> desde `ADR-007` para evitar colisión con el `ADR-007` de Héctor Morales, unidad del target de ML-01).

## Contexto

FARO entrena y registra tres modelos (ML-01, ML-02, ML-03) vía MLflow, orquestados por Airflow. Hasta
ahora, si un run de entrenamiento fallaba o una métrica clave se degradaba silenciosamente (por ejemplo,
un MAE que se dispara o un F1 que cae por debajo del umbral aceptado), **nadie se enteraba hasta que
alguien revisaba manualmente el tracking server**. Esto es inaceptable para un pipeline que alimenta
predicciones consumidas por la API y los tableros de Superset.

Se requiere un mecanismo de monitoreo que:
1. Revise el run más reciente de un experimento de MLflow.
2. Detecte dos condiciones de alerta: **(a)** el run terminó con `status == FAILED`, o **(b)** una
   métrica configurada está fuera de un rango aceptable (por debajo de un mínimo o por encima de un
   máximo).
3. Notifique el hallazgo a un canal humano (Slack o Discord) sin bloquear la ejecución del DAG si el
   webhook falla.
4. No rompa el **parseo** del DAG (`dag import errors` en Airflow) si el paquete `mlflow` no está
   instalado en el ambiente del *scheduler*.

## Decisión

1. **Reutilizar el módulo `common_alerting/webhook.py`** ya existente (usado por otros DAGs vía
   `airflow_callbacks.py`) en vez de crear un cliente de notificación nuevo. El webhook soporta
   formato Slack o Discord vía la variable `ALERT_WEBHOOK_TYPE`, y si `ALERT_WEBHOOK_URL` no está
   configurada, la función retorna sin error (no rompe el flujo).

2. **Import diferido de `mlflow`**: el módulo `scripts/mlflow_monitor.py` **no importa `mlflow` a
   nivel de módulo**. El `import mlflow` ocurre dentro de la función `main()`, que es la que
   efectivamente se ejecuta como tarea de Airflow (`PythonOperator`/`@task`). Esto significa que:
   - El *scheduler* puede parsear el DAG (`dags/mlflow_monitor_dag.py`) sin tener `mlflow` instalado,
     evitando que un DAG roto bloquee la carga de **todos** los demás DAGs del mismo `dag_bag`.
   - Solo el *worker* que ejecuta la tarea necesita el paquete `mlflow` en su entorno.
   - Se agregó una prueba de regresión explícita (`test_mlflow_no_se_importa_a_nivel_de_modulo`) que
     falla si alguien reintroduce el import a nivel de módulo en el futuro.

3. **Umbrales configurables por variables de entorno** (`MLFLOW_METRIC_NAME`, `MLFLOW_METRIC_MIN`,
   `MLFLOW_METRIC_MAX`) en vez de hardcodearlos, para que cada experimento (ML-01, ML-02, ML-03) pueda
   reusar el mismo script con distintos umbrales sin duplicar código.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Usar los *alerts* nativos de MLflow (feature de MLflow >= 2.x) | Requiere un tracking server con esa función habilitada y acoplaría el monitoreo a una versión específica de MLflow; el equipo ya usa un tracking server local/compartido sin esa configuración |
| Servicio de alertas dedicado (PagerDuty, Opsgenie) | Sobre-ingeniería para el tamaño del equipo y el sprint; agrega una dependencia de pago/cuenta externa sin beneficio claro sobre un webhook a Slack/Discord que el equipo ya usa |
| Importar `mlflow` a nivel de módulo en el DAG | Simplifica el código pero **rompe el parseo del DAG completo** si el *scheduler* no tiene `mlflow` instalado (riesgo real, ya observado en otros DAGs del repo) |

## Consecuencias

**Positivas**
- El monitoreo es reutilizable para los tres modelos con solo cambiar variables de entorno.
- Ningún DAG se cae por falta de `mlflow` en el scheduler.
- La alerta nunca propaga una excepción no controlada hacia Airflow (un fallo de red o de webhook se
  loguea, no tumba la tarea).

**Negativas / deuda aceptada**
- El monitoreo solo revisa el **último run** de un experimento; no hay agregación histórica ni
  dashboard de tendencia de métricas (posible mejora futura, fuera de alcance de `US-524b`).
- Depende de que `MLFLOW_TRACKING_URI` apunte a un servidor accesible desde el *worker*; si el
  servidor está caído, el script reporta esa falla como parte del run, no la distingue de un fallo de
  entrenamiento real.

## Estado

`proposed` — pendiente de revisión por Luis Téllez Domínguez (Tech Lead, Célula 5).
