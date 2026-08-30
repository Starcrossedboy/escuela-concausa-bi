---
project: "FARO"
date: "2026-08-29"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — conectar el endpoint del agente al servicio RAG (BUG-025)"
touches: ["BUG-025", "US-304a", "US-305", "REQ-006", "REQ-004"]
tags: [devlog, celula-4, api, agente, seguridad, rag, bug]
---

# DevLog — 2026-08-29 — BUG-025: endpoint del agente conectado al servicio RAG real

→ [[_DevLog/_index|Volver al índice]] · [[06_Quality_Testing/Bug_Register|Bug Register · BUG-025]] · [[03_Architecture/API_Specification|API_Spec §3.5]]

## Contexto

Andrés (C3) pidió desatorar el agente: el endpoint desplegado `/agente/consulta`
(`src/api/v1/agente.py`, **artefacto C4**) seguía siendo el **stub** que respondía lo mismo a todo y
cuyo filtro por subcadena dejaba pasar la frase destructiva más obvia (**BUG-025**, `high`). La
lógica real del agente (`src/agente/servicio.py`, `guardrails.py`) ya existía pero **nunca se
invocaba desde la API**. Es un bug conjunto **C4 + C3**: el endpoint es nuestro, el LLM/ejecutor es de C3.

## Qué se hizo (parte C4)

- **Reescrito `src/api/v1/agente.py`** para delegar en `procesar_consulta(...)` de C3 (equivalente a
  `procesar_consulta_con_rag()` con el recuperador inyectable), aplicando los **guardarraíles reales**
  (`pregunta_en_alcance` + `preparar_sql_seguro`). Se elimina el stub y el filtro ingenuo.
- **Seam de inyección de dependencias (FastAPI)** para las 4 colaboraciones —`recuperar_contexto`
  (default = RAG ChromaDB de US-304b), `generar_sql`, `ejecutar_sql`, `redactar_respuesta`— con
  defaults que **degradan seguro** ("no configurado"): la app arranca y el CI corre sin LLM ni
  ChromaDB. Andrés/C5 las sobreescriben con `app.dependency_overrides` / implementaciones reales.
- **Degradación segura de errores**: cualquier fallo interno se traduce a un mensaje genérico, sin
  filtrar trazas, prompts ni SQL de error.
- **Importación a prueba de CI**: `recuperacion.py` ya protege `chromadb`/`sentence-transformers` con
  `try/except`; no se añade ninguna dependencia pesada a `requirements.txt`.
- **Pruebas**: `tests/test_agente_endpoint.py` (5 casos: fuera de alcance, no-stub, **SQL destructivo
  nunca se ejecuta**, happy-path por el seam, degradación sin fuga). Actualizado
  `test_agente_rechaza_escritura` en `test_api_contract.py` (codificaba el filtro del stub viejo;
  ahora prueba el rechazo real en la capa SQL). Suite total 617 passed / 5 skipped (solo fallan 3
  módulos GE de C1 por versión, ajenos).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos creados:** `tests/test_agente_endpoint.py`, este DevLog.
- **Modificados:** `src/api/v1/agente.py`, `tests/test_api_contract.py`, `_DevLog/_index.md`.
- **Decisión de diseño:** conectar el servicio real con un **seam DI** en vez de solo mitigar el
  guardarraíl, para desatorar a Andrés estructuralmente (elegido con el PO/Christian). Se usa
  `procesar_consulta` con `recuperar_contexto` inyectable (generaliza `procesar_consulta_con_rag`)
  para que el retriever también sea sustituible y las pruebas no dependan de ChromaDB.
- **Hallazgo:** la protección contra escritura NO está en el filtro de lenguaje natural (una frase
  como «borra la tabla de predicciones» es *en alcance* porque menciona "predicciones"), sino en la
  **capa SQL** (`preparar_sql_seguro` solo admite `SELECT/WITH` sobre `gold.`). El test lo verifica.
- **Revisión manual:** revisado línea por línea; foco en no ejecutar SQL de escritura y en no filtrar detalle.

## Seguridad / calidad
- [x] El SQL de escritura generado se rechaza y el ejecutor nunca se invoca (prueba dedicada)
- [x] Errores internos degradan a mensaje genérico (sin trazas/prompt/SQL)
- [x] Sin nuevas dependencias en requirements.txt; import a prueba de CI
- [x] DevLog enlaza a los IDs afectados (BUG-025, US-304a, US-305, REQ-006, REQ-004)

## Bloqueantes / avisos a otros owners
- **Andrés (C3):** proveer las implementaciones reales de `generar_sql` (LLM text-to-SQL) y
  `redactar_respuesta` (LLM), sobreescribiendo `get_generar_sql`/`get_redactar_respuesta`. El seam
  ya está listo; con eso BUG-025 se cierra al 100%.
- **C4/US-404 (yo) + C5 (Luis):** `ejecutar_sql` read-only sobre Gold (rol de solo lectura) — es
  sensible (ejecutar SQL generado), se diseña en el hardening US-404.
- **C5 (Luis):** para que el demo desplegado haga RAG real, añadir `chromadb`/`sentence-transformers`
  (+ cliente LLM) a la imagen de la API; si no, el endpoint degrada con mensaje seguro.
- **Edgar (owner de `06_Quality_Testing/Bug_Register.md` y matriz):** actualizar **BUG-025** a
  *parcialmente resuelto* (mitigado por C4: endpoint conectado + guardarraíl + seam; pendiente C3/C5).
  No edité el registro por no ser artefacto propio.
