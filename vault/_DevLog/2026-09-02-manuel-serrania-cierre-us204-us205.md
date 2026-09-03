---
project: "FARO"
date: "2026-09-02"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "1h"
touches: ["US-204", "US-205", "US-206", "REQ-002"]
tags: [devlog]
---

# DevLog — 2026-09-02 — Cierre documental US-204/US-205 + implementación US-206

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo
- **Plan de US-206** (embebido de los 10 dashboards + cierre US-204/205) redactado en la raíz del repo:
  `PLAN_US206_EMBEBIDO.md`. Contexto verificado, decisiones (guest token directo a Superset, sin endpoint
  nuevo en la API), tareas por día, dependencias C5/Oscar y riesgos.
- **Cierre documental de US-204** (DB-06/DB-09, PR #100): verificada la evidencia, el código ya estaba
  mergeado. Se confirma `done`; la validación con datos reales del mismo ciclo es follow-up de
  US-313/BUG-013 y no bloquea esta historia. `Execution_Status.md` actualizado (in_review → done).
- **Cierre documental de US-205** (repunteo a `gold.cubo_*`, PR #134): **corregido el bug de etiqueta**
  reportado por Edgar — la fila que decía `US-206 | done` contenía la evidencia de US-205. Reetiquetada
  a `US-205 | done`.
- **Implementación de US-206 (embebido de dashboards)**:
  - `src/frontend/superset_client.py` (nuevo): cliente del guest token — login admin contra
    `/api/v1/security/login`, resolución de UUID de cada dashboard por slug, `POST
    /api/v1/security/guest_token/` y `iframe_url` firmada por tablero. `tableros_embebidos()` acepta un
    `cliente` inyectado (patrón DI del frontend). Sin token válido NO devuelve tableros.
    **Catálogo completo DB-01…DB-10** (DB-07 `db07-calidad-cobertura` y DB-10 `db10-monitor-pipeline`
    se incorporaron tras el merge de Oscar en `main`).
  - `src/frontend/pages/1_Dashboards.py`: catálogo de 10 tableros, filtros globales AC-002.2
    (ciclo/entidad/nivel), iframes firmados y degradación explícita: si Superset no expone guest token
    (C5 pendiente) NO se muestra ningún tablero (AC-002.1).
  - `src/frontend/app.py`: tarjetas de acceso rápido (elimina `TODO(US-206)`).
  - `tests/test_frontend_superset_client.py` (nuevo): 7 casos con `httpx.MockTransport` (token ok,
    401→deshabilitado, sin UUID→error, password ausente→error) + `url_con_filtros` (sin filtros,
    ciclo/entidad/nivel, escape percent) para cubrir AC-002.2 a nivel de URL.
  - `tests/test_frontend_dashboards_streamlit.py` (nuevo, `importorskip`): prueba `render()` con un
    Superset HTTP simulado — con token válido dibuja los filtros; con 401 el guest token NO muestra
    tableros ni filtros (AC-002.1). Se omite en ejecución local porque `streamlit` no está instalado
    (igual que `test_frontend_chat_streamlit.py`).
  - Refactor: `url_con_filtros` movida de `pages/1_Dashboards.py` a `superset_client.py` para poder
    probarla sin el stack Streamlit.
- Verificación: `ruff check` limpio (src/frontend + tests) · `pytest` frontend 18 passed (7 de
  superset_client/url_con_filtros + agente + chat) · ownership `test_check_ownership.py` 40 passed.
  La prueba de `render()` (Streamlit) se omite localmente por falta de `streamlit`, igual que la del
  chat. Los 10 errores de colección del suite global son preexistentes (módulos externos como
  `limits`), ajenos a este cambio.

## 🤖 Sesión de IA
- **Agente / modelo:** OpenCode / opencode/big-pickle
- **Archivos creados/modificados:**
  - `PLAN_US206_EMBEBIDO.md` (nuevo, raíz)
  - `vault/12_Roadmap_Sprints/Execution_Status.md` (corrección US-204 done + reetiqueta US-205)
  - `src/frontend/superset_client.py` (nuevo)
  - `src/frontend/pages/1_Dashboards.py` (implementado)
  - `src/frontend/app.py` (navegación)
  - `tests/test_frontend_superset_client.py` (nuevo)
- **Decisiones autónomas del agente:** confirmar US-204 como `done` (el entregable es el tablero, cierra
  con código + capa de datos; la validación en vivo queda como follow-up de US-313); el guest token se
  pide **directo a Superset** (sin endpoint nuevo en la API); resolver el UUID del dashboard por slug
  porque el recurso del guest token requiere UUID, no slug. Dependencias de C5 (habilitar embedding) y
  Oscar (DB-07/DB-10) quedan declaradas como no bloqueantes del código.
- **Correcciones manuales:** — (ninguna)
- **Prompt inicial:** "¿Qué hemos hecho hasta ahora?" (recuperación de contexto de sesión previa)

## Seguridad / calidad
- [x] Sin secretos hardcodeados (credenciales vienen de env, nunca se loguean)
- [x] Tests agregados/actualizados — `tests/test_frontend_superset_client.py` (4 casos)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- Guest token de Superset NO habilitado (depende de C5/Luis Téllez) → en runtime el front degrada a
  mensaje sin tableros; el código del embebido queda listo.
- DB-07 y DB-10 sin slug declarado (depende de Oscar Quiroz, US-222/223) → 8 de 10 tableros hoy.

## Próximos pasos
1. Push de rama `dev/manuel-serrania` con cierre documental + código US-206 + tests.
2. Coordinar con Luis Téllez (habilitar `ENABLE_GUEST_EMBEDDING`/`GUEST_ROLE_NAME`) para validar el
   embebido en vivo (Sáb 5 pruebas compose).
3. Coordinar con Oscar para declarar DB-07/DB-10 y completar los 10 tableros.
4. Coordinar shell compartido con Marina/Andrés/Christian (todos tocan `src/frontend/**`).
