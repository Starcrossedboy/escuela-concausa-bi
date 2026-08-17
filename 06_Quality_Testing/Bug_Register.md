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
| BUG-003 | `sklearn` no instalado: `test_entrenar_ml01.py` y `test_entrenar_ml02.py` fallan con `ModuleNotFoundError` en colección de pytest | low | open | US-311 / REQ-003 | pendiente (C3) | — |
| BUG-004 | Imagen `apache/superset:latest` no incluye `psycopg2`: conexión a PostgreSQL falla con 422 al crear datasets virtuales | medium | open | US-202 | pendiente (C3, Edward Ruiz — US-522c) | — |

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

---

## BUG-004 — Imagen `apache/superset:latest` no incluye `psycopg2`

- **Owner:** Célula 3 (DevOps/Cloud) — Edward Ruiz (US-522c)
- **Severidad:** medium
- **Estado:** open
- **traces_up:** US-202
- **found_on:** 2026-08-17

### Descripción
La imagen oficial `apache/superset:latest` no trae el driver `psycopg2` para PostgreSQL. Sin él, Superset no puede conectarse a la base de datos PostgreSQL y la creación de datasets virtuales vía API falla con HTTP 422 ("Connection failed, please check your connection settings").

### Pasos para reproducir
1. `docker compose up -d db superset`
2. Abrir Superset en http://127.0.0.1:8088
3. Ir a Data → Databases → Add → PostgreSQL
4. Configurar la conexión (host: `db`, puerto: `5432`, usuario, contraseña, base de datos)
5. Probar conexión → falla con 422

### Resultado actual vs esperado
- **Actual:** 422 "Connection failed" al intentar conectar Superset con PostgreSQL.
- **Esperado:** Conexión exitosa; Superset puede crear datasets virtuales sobre la base de datos.

### Entorno
- Docker Compose local, servicio `superset` (`apache/superset:latest`)
- PostgreSQL en servicio `db` (`postgres:15-alpine`)

### Causa raíz
La imagen oficial no incluye `psycopg2-binary` en su venv (`/app/.venv/`). Superset intenta usar SQLAlchemy para conectarse a PostgreSQL pero falla al importar el driver.

### Fix temporal (workaround)
```bash
docker exec -u root faro-superset pip install --target /app/.venv/lib/python3.10/site-packages psycopg2-binary
```
> **Nota:** se pierde al reiniciar el contenedor.

### Fix permanente (pendiente)
- Crear un Dockerfile custom que extienda `apache/superset` e instale `psycopg2-binary`, O
- Agregar la instalación a `docker/superset-init.sh` ejecutando como root antes de iniciar Superset.

### Fix (PR)
- pendiente (C3, Edward Ruiz — US-522c)

### Test de regresión
- pendiente