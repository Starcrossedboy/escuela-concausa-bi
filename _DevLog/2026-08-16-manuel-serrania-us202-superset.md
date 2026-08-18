---
id: DEVLOG-2026-08-16-MANUEL-US202
title: "DevLog — US-202 Setup Superset + BUG-003/004"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "~120 min"
status: done
date: "2026-08-17"
touches: ["US-202", "US-211a", "REQ-002", "BUG-003", "BUG-004", "DOC-SUPERSET-SETUP", "DOC-SCREENSPECS", "DOC-CUBESPEC-DB0304", "DOC-TRACE-MATRIX"]
traces_up: ["02_Requirements/User_Stories", "04_UX_Design/Screen_Specs", "04_UX_Design/Cube_Specs_DB03_DB04"]
tags: [devlog, superset, setup, semantic-layer, bug]
---

# DevLog — 2026-08-17 — US-02 Setup Superset (completado) + BUG-003/004

## Contexto

Sesión de trabajo en S3 (lunes 17-ago empieza oficialmente). Se creó la rama `feat/manuel-serrania-us202-superset` desde la rama del PR anterior (`feat/manuel-serrania-kpis-db03-ratificacion-join`). Se completó la documentación vault, el script de sincronización de la capa semántica de Superset, y se ejecutó el sync end-to-end en Docker local.

## Qué se hizo

### US-202 — Configurar Superset: conexión, datasets y capa semántica (100%)

1. **Script `superset/sync_semantic_layer.py`** — Idempotente, vía REST API de Superset, stdlib only. Funcionalidades:
   - Login JWT + CSRF token (con cookies para SameSite).
   - Crear/conectar a `faro_escuela_concausa_db` (Postgres).
   - Crear datasets virtuales desde `superset/semantic/*.sql` (DB-03, DB-04).
   - Aplicar métricas y dimensiones desde `metrics_db03_db04.yaml`.
   - Manejo de métricas sin `expresion` (solo `columnas`, ej. contexto_socioeconomico).
   - Reporte de creación/actualización/skipped.

2. **Doc vault `04_UX_Design/Superset_Setup_US202.md`** (DOC-SUPERSET-SETUP) — Cómo levantar ambiente, correr sync, verificar conexión, limitaciones conocidas (Gold no existe), workaround de psycopg2, Gold mock tables.

3. **Gold mock tables** — Tablas mínimas en `gold.*` para que Superset pueda validar los datasets virtuales. 1 fila dummy cada una. Serán reemplazadas cuando C1 entregue `gold.*` (US-112/113).

4. **Sync end-to-end ejecutado exitosamente:**
   - Conexión a Postgres: ✅ `faro_escuela_concausa_db` (id=1)
   - DB-03 (cubo_escuela_360): 6 métricas, 44 columnas
   - DB-04 (cubo_comparador_municipio): 14 métricas, 32 columnas
   - Métrica `contexto_socioeconomico` (columnas solas): ⚠ omitida (sin `expresion`)

5. **Actualizaciones vault:**
   - `04_UX_Design/_index.md` — Fila DOC-SUPERSET-SETUP.
   - `02_Requirements/Traceability_Matrix.md` — REQ-002: referencia a Superset Setup y DevLog US-202.
   - `12_Roadmap_Sprints/Sprints/2-manuel-alejandro-serrania-reinada.md` — US-202: 🟡 → 🔵 En revisión (100%).

### BUG-003 — sklearn faltante

Registrado en `06_Quality_Testing/Bug_Register.md`: `test_entrenar_ml01.py` y `test_entrenar_ml02.py` fallan con `ModuleNotFoundError: No module named 'sklearn'`. Severidad low, estado open, fuera de alcance C2 (dueño: C3 Andrés).

### BUG-004 — psycopg2 no incluido en imagen Superset

Registrado en `06_Quality_Testing/Bug_Register.md`: la imagen oficial `apache/superset:latest` no trae `psycopg2`. Conexión a PostgreSQL falla con 422. Severidad medium, estado open, dueño C3 (Edward Ruiz — US-522c). Workaround documentado: `pip install --target /app/.venv/lib/python3.10/site-packages psycopg2-binary`.

### Revisión de peticiones de Marina (US-211a)

Las tres peticiones de Marina ya estaban cubiertas:
- LEFT JOIN en DB-03: ✅ implementado (`db03_cubo_escuela_360.sql:87-91`).
- KPI-15…18: ✅ registrados en `Screen_Specs.md:140-143` + SQL en `Screen_Specs.md:340-420`.
- Convención `superset/semantic/`: ✅ alineada, nombres consistentes entre YAML y SQL.

## Sesión con IA

- Modelo: opencode/big-pickle
- Duración: ~120 min (2 sesiones: 16-ago setup + 17-ago ejecución)
- Se usó para: creación de script Python, documentación vault, ejecución de sync, registro de bugs, revisión de alineación con US-211a.
- Revisión manual: pendiente antes de commit/push.

## Seguridad y calidad

- No se subieron credenciales ni `.env` al repo.
- Script lee credenciales de variables de entorno (nunca hardcodeadas).
- `vault_lint.py` ✅ pass
- `pytest tests/test_semantic_db03_db04.py` ✅ 28 passed (antes 21+7 skipped; Gold mock habilitó los tests de YAML)

## Bloqueantes

| Bloqueante | Dueño | Impacto |
|---|---|---|
| Gold no existe (`dbt/` vacío, C1 US-112/113) | Diana (C1) | Preview real de datasets fallará hasta que C1 entregue `gold.*`. Mock tables permiten validación de esquema. Registrar en standup. |
| Predicciones no existen (C3 US-311 en progreso) | Andrés (C3) | Métricas de predicción/recomendación se agregan cuando ML-01/02/03 estén entrenados. |
| psycopg2 no persiste al reiniciar contenedor (BUG-004) | Edward (C3, US-522c) | Dockerfile custom o fix en superset-init.sh necesario para persistencia. |

## Próximos pasos

1. Commit + push de la rama `feat/manuel-serrania-us202-superset`.
2. Abrir PR → 1 aprobación del PM.
3. Avisar en standup S3 que la capa semántica está lista pero Gold bloquea la preview real.
