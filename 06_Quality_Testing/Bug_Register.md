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
| BUG-003 | `sklearn` no instalado: `test_entrenar_ml01.py` y `test_entrenar_ml02.py` fallan con `ModuleNotFoundError` en colección de pytest | low | **not_a_bug** | US-311 / REQ-003 | ya resuelto en `main` desde 2026-08-13 (PR #28) — ver detalle | ambiente local desactualizado |
| BUG-004 | Imagen `apache/superset:latest` no incluye `psycopg2`: conexión a PostgreSQL falla con 422 al crear datasets virtuales | medium | open | US-202 | pendiente (**C5**, Edward Ruiz — US-522c) | — |
| BUG-005 | Scripts `.sh` se corrompen a CRLF en checkouts de Windows: `.gitattributes` no tiene regla `*.sh text eol=lf`, así que con `core.autocrlf=true` MLflow y Superset no arrancan (`$'': command not found`; en MLflow el shebang `#!/bin/sh` produce un engañoso `no such file or directory`) | high | fixed | US-502 / REQ-005 | PR #65 (Luis Téllez, **C5**) — agregado `*.sh text eol=lf` a `.gitattributes` | pendiente (validar en Windows) |
| BUG-006 | Healthcheck de `api` usa `curl -f` pero la imagen no incluye `curl` ni `wget` (solo `python`): el contenedor queda `unhealthy` de forma permanente aunque `/health` responda HTTP 200 | medium | fixed | US-502 / REQ-004 | PR #65 (Luis Téllez, **C5**) — removido healthcheck override de api, actualizado chromadb a /api/v2/heartbeat | pendiente (validar healthchecks) |
| BUG-007 | Healthcheck de `chromadb` apunta a `/api/v1/heartbeat`, que responde **HTTP 410 Gone** (endpoint retirado); la ruta viva es `/api/v2/heartbeat`. Además arrastra el mismo problema de `curl` de BUG-006 | medium | fixed | US-502 / REQ-006 | PR #65 (Luis Téllez, **C5**) — actualizado puerto MLflow en documentación (5000 → 5001) | validado |
| BUG-008 | 7 de 10 fuentes Bronze en `sources.yml` sin `identifier` por default: cualquier `dbt build`/`dbt run` completo puede fallar en compilación aunque el modelo probado no use esas fuentes | high | open | US-111 | pendiente (Edgar decide reparto) | — |

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

## BUG-003 — `sklearn` no instalado al correr pytest

| | |
|---|---|
| **Estado** | `not_a_bug` — el repositorio no tiene el defecto |
| **Reportado** | 2026-08-17 (commit `78ede8c`, US-202) |
| **Historia** | US-311 / REQ-003 |
| **Cerrado por** | Héctor Rafael Morales Marbán, 2026-08-17 |

### Diagnóstico

**No es un defecto del repositorio: es un ambiente local desactualizado.**

`scikit-learn>=1.5` ya está en `requirements.txt` desde el **13 de agosto**, cuatro días antes de
que se registrara este bug. Se agregó en el commit `5f0f04a` (PR #28) precisamente porque el CI
instala **sólo** `requirements.txt` y nunca los `requirements/celula-*.txt`, así que las pruebas de
`src/modelos/` fallaban en el runner.

### Evidencia

- `requirements.txt` contiene `scikit-learn>=1.5` (sección "Célula 3 - ML").
- El job **"Calidad de codigo y vault"** del CI hace `pip install -r requirements.txt` y luego
  `pytest tests/ -q`. Está **verde en `main`** en las corridas recientes: si faltara `sklearn`, la
  colección de pytest fallaría ahí primero.
- Cubre los **dos** archivos reportados: `entrenar_ml02.py` sólo necesita `sklearn` en imports de
  nivel superior (`shap` y `mlflow` son imports diferidos).

### Remediación para quien lo encuentre

No hay que tocar código, ni de la Célula 3 ni de nadie:

```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
```

Le pasa a cualquier ambiente virtual creado antes del 13 de agosto que no haya reinstalado
dependencias.

### Nota de alcance

Se preguntó si el fix correspondía a la Célula 3 por tocar `src/modelos/`. **No había fix de código
pendiente**, y la decisión de no tocar `src/modelos/` fuera del alcance propio fue la correcta.

## BUG-004 — Imagen `apache/superset:latest` no incluye `psycopg2`

- **Owner:** **Célula 5** (DevOps/Cloud) — Edward Ruiz (US-522c)
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
- pendiente (**C5**, Edward Ruiz — US-522c)

### Test de regresión
- pendiente

## BUG-008 — 7 fuentes Bronze en sources.yml sin identifier por default

- **Owner:** Edgar Edmundo Coronel Navarrete
- **Severidad:** high
- **Estado:** open
- **traces_up:** US-111
- **found_on:** 2026-08-21

### Descripción
Al validar `matricula_historica` (modelo nuevo y aislado, RISK-007/DEC-007) con `dbt build --select matricula_historica`, el build falló con `Required var 'bronze_cct_identifier' not found in config` — una fuente que el modelo ni siquiera consume. Causa: 7 de las 10 tablas Bronze declaradas en `dbt/models/sources.yml` no tienen un valor por default en su `identifier` (a diferencia de `formato911`, `formato911_historico` y `cemabe`, que sí lo tienen). Como dbt necesita renderizar el manifest completo del proyecto antes de ejecutar cualquier selección, cualquier `--select` falla si falta CUALQUIERA de las 7 vars, sin importar si el modelo seleccionado las usa.

Las 7 fuentes afectadas tocan varias historias distintas, sin un solo dueño:
- `bronze_cct_identifier` (DS-02 Catálogo CCT)
- `bronze_sesnsp_identifier`, `bronze_sinaica_observaciones_identifier`, `bronze_sinaica_estaciones_identifier` (DS-04/DS-05, Luis García)
- `bronze_coneval_identifier` (DS-07, Deni)
- `bronze_conagua_identifier`, `bronze_conapo_identifier` (DS-06/DS-08, Emilio)

`sources.yml` es de Deni (US-111).

### Pasos para reproducir
1. `cd dbt`
2. Correr cualquier `dbt build`/`dbt run`, con o sin `--select`, sin pasar las 7 vars por `--vars`.
3. Falla con `Compilation Error: Required var 'bronze_cct_identifier' not found in config` (o el nombre de la siguiente var sin default que encuentre).

### Resultado actual vs esperado
- **Actual:** `dbt build --select <modelo>` falla al renderizar fuentes que ese modelo no consume.
- **Esperado:** `dbt build --select <modelo>` sólo debería requerir las vars/fuentes que ese modelo realmente usa; o, alternativamente, las 7 fuentes deberían tener un valor por default como ya tienen `formato911`/`formato911_historico`/`cemabe`.

### Entorno
- dbt-core 1.12.0, dbt-postgres 1.11.0 (`requirements/celula-1.txt`)
- `dbt/models/sources.yml`

### Causa raíz
7 de los 10 `identifier` en `sources.yml` se declararon como `"{{ var('bronze_X_identifier') }}"` sin segundo argumento de default, a diferencia de los 3 que sí lo tienen (`"{{ var('bronze_formato911_identifier', 'formato911_2024_2025') }}"`, etc.).

### Fix
- pendiente — Edgar decide el reparto entre las historias/dueños involucrados; opción propuesta: agregar valor por default a las 7 (mismo patrón que `formato911`/`cemabe`).