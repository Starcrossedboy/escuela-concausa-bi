---
title: "Fix errores de importación en dag_anual y dag_censal_estatico (US-102)"
author: "Diana Aracely Alvarez Varela"
date: "2026-08-16"
tags: [devlog, us-102, dags, bugfix]
---

# 2026-08-16 — Fix errores de importación en DAGs de Airflow

Al levantar el stack completo de Airflow (post PR #34/#35, US-502/US-503) para validar `dim_tiempo` de US-103, encontré dos errores de importación en DAGs ya mergeados a main (PR #29, US-102):
- `dag_anual.py`: faltaba `start_date`.
- `dag_censal_estatico.py`: preset de `schedule` no soportado por el parser de cron de Airflow.

Confirmado con `docker compose exec airflow-webserver airflow dags list-import-errors` antes y después del fix, y en la UI de Airflow (6/6 DAGs, 0 failed tras el fix).

Como estos bugs son de código ya en main y fuera del alcance de US-103, los separé a su propia rama `fix/diana-varela-us102-dag-import-errors` y PR independiente, para no mezclar historias.

## Uso de IA
Usé Claude para: diagnosticar la causa raíz de ambos errores a partir del traceback de Airflow, redactar el fix mínimo en cada DAG, y guiarme en el flujo de git para separar los cambios en una rama y PR nuevos.

Revisé línea por línea ambos diffs antes de comitear — son cambios de 3 líneas por archivo (insertions/deletions), fáciles de verificar contra la documentación de Airflow (`start_date` requerido, formato cron de 5 partes). No se pegaron datos reales ni credenciales en los prompts.