---
id: DOC-BUGREG
title: "Bug Register"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
tags: [qa, bugs]
---

# Bug Register — FARO

> Registro único de defectos. Detalle de cada uno con [[_Templates/Bug_template]].
> → [[06_Quality_Testing/_index]]

| BUG | Título | Severidad | Estado | US/REQ | Fix (PR) | Test regresión |
|---|---|---|---|---|---|---|
| BUG-001 | dag_anual.py: falta start_date | high | fixed | US-102 | fix/diana-varela-us102-dag-import-errors | manual (ver detalle) |
| BUG-002 | dag_censal_estatico.py: preset de cron no soportado | high | fixed | US-102 | fix/diana-varela-us102-dag-import-errors | manual (ver detalle) |

## Convención

- Severidad: critical / high / medium / low
- Estado: open → in_progress → fixed → closed (o wont_fix)
- Todo `fixed` requiere test de regresión antes de `closed`.

---

## BUG-001 — dag_anual.py: falta start_date

- **Owner:** Diana Aracely Alvarez Varela
- **Severidad:** high
- **Estado:** fixed
- **traces_up:** US-102
- **found_on:** 2026-08-16

### Descripción
Airflow no podía importar `dag_anual.py`: el DAG no tenía definido `start_date`, parámetro requerido por Airflow para poder programarse.

### Pasos para reproducir
1. Levantar el stack con `docker compose up`.
2. Ejecutar `docker compose exec airflow-webserver airflow dags list-import-errors`.
3. `dag_anual.py` aparece con error de importación.

### Resultado actual vs esperado
- **Actual:** DAG no cargaba, error de importación en la UI de Airflow.
- **Esperado:** DAG carga sin errores y aparece programable en la UI.

### Entorno
- Docker Compose local, servicios airflow-webserver / airflow-scheduler / airflow-init (PR #34, US-502).

### Causa raíz
Faltaba el argumento `start_date` en la definición del DAG.

### Fix
- **PR:** fix/diana-varela-us102-dag-import-errors
- **Test de regresión:** manual — `docker compose exec airflow-webserver airflow dags list-import-errors` ya no reporta `dag_anual.py`; confirmado en la UI de Airflow "6/6 DAGs, 0 failed".

---

## BUG-002 — dag_censal_estatico.py: preset de cron no soportado

- **Owner:** Diana Aracely Alvarez Varela
- **Severidad:** high
- **Estado:** fixed
- **traces_up:** US-102
- **found_on:** 2026-08-16

### Descripción
Airflow no podía importar `dag_censal_estatico.py`: usaba un preset de `schedule` no soportado por el parser de cron de Airflow (`cron_descriptor.Exception.FormatException: Expression only has 1 parts. At least 5 part are required`).

### Pasos para reproducir
1. Levantar el stack con `docker compose up`.
2. Ejecutar `docker compose exec airflow-webserver airflow dags list-import-errors`.
3. `dag_censal_estatico.py` aparece con error de importación.

### Resultado actual vs esperado
- **Actual:** DAG no cargaba; traceback de `cron_descriptor` al parsear el preset.
- **Esperado:** DAG carga sin errores, con una expresión cron válida de 5 partes (o el preset correcto soportado por Airflow).

### Entorno
- Docker Compose local, servicios airflow-webserver / airflow-scheduler / airflow-init (PR #34, US-502).

### Causa raíz
El `schedule` usaba un preset no reconocido por el parser de cron de Airflow.

### Fix
- **PR:** fix/diana-varela-us102-dag-import-errors
- **Test de regresión:** manual — `docker compose exec airflow-webserver airflow dags list-import-errors` ya no reporta `dag_censal_estatico.py`; confirmado en la UI de Airflow "6/6 DAGs, 0 failed".