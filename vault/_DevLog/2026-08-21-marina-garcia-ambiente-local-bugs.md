---
project: "FARO"
date: "2026-08-21"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión de ambiente local: Docker arriba y 3 defectos reportados"
touches: ["BUG-005", "BUG-006", "BUG-007", "DOC-BUGREG", "US-502", "REQ-005"]
tags: [devlog, ambiente, docker, bugs, celula-2]
---

# DevLog — 2026-08-21 — Ambiente local completo y 3 defectos reportados

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

Al levantar por primera vez el stack de Docker para preparar US-212 aparecieron tres defectos que
**no son del ambiente de una sola persona**: dos están en `docker-compose.yml` y uno en la
configuración del repositorio. Se registran en [[vault/06_Quality_Testing/Bug_Register]] siguiendo el flujo
de intake de [[vault/_Meta/Definition_of_Filed]].

## Qué se hizo

### Ambiente local terminado

- `.venv` recreado con **Python 3.11.9** (antes 3.12.10, desalineado con el CI). `pytest tests/ -q`:
  **209 passed, 4 skipped**.
- `.env` creado desde la plantilla. Se reparó una URL de conexión que había quedado partida en dos
  renglones al pegar la contraseña, y se normalizaron 74 finales de línea de CRLF a LF.
- **7 servicios levantados**: `db`, `superset`, `airflow-webserver`, `airflow-scheduler` y `mlflow`
  en `healthy`; `api` y `chromadb` arriba y respondiendo, pero marcados `unhealthy` por BUG-006 y BUG-007.

### Defectos reportados

- **BUG-005 (high)** — Los seis `.sh` del repo están en LF, pero `.gitattributes` no tiene
  `*.sh text eol=lf`, así que con `core.autocrlf=true` se convierten a CRLF al hacer checkout en
  Windows. Superset falla con `$'\r': command not found` y MLflow con `no such file or directory`
  — engañoso: lo que no encuentra es el intérprete, porque el shebang quedó como `#!/bin/sh\r`.
  Mitigado en local con `core.autocrlf=input`, pero **le pasará a cualquiera en Windows**.
  Relacionado con el commit `51e047a`, que corrigió el síntoma en Superset sin atacar la causa.
- **BUG-006 (medium)** — El healthcheck de `api` usa `curl -f`, pero la imagen no trae `curl` ni
  `wget` (solo `python`). El contenedor queda `unhealthy` permanentemente aunque `/health`
  responda HTTP 200 (verificado).
- **BUG-007 (medium)** — El healthcheck de `chromadb` apunta a `/api/v1/heartbeat`, que responde
  **HTTP 410 Gone**; la ruta viva es `/api/v2/heartbeat` (verificado, HTTP 200). Arrastra además el
  problema de `curl` de BUG-006.

### Por qué importan aunque hoy no bloqueen

Ningún servicio depende del `healthy` de `api` ni de `chromadb`, así que el stack levanta igual. Pero
en la demo del 9 de septiembre se verían **dos servicios en rojo en la URL pública**, y basta con que
alguien agregue un `depends_on: condition: service_healthy` sobre ellos para que el stack deje de
levantar. BUG-005 sí es bloqueante para cualquier integrante en Windows.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:**
  - `vault/06_Quality_Testing/Bug_Register.md`
  - `vault/_DevLog/2026-08-21-marina-garcia-ambiente-local-bugs.md` (nuevo) · `vault/_DevLog/_index.md`
- **Fuera de alcance, no editado:** `docker-compose.yml` y `.gitattributes` (C5, Luis Téllez) y la
  imagen de `src/api` (C4, Christian Ruiz). **Se reporta, no se arregla.**
- **Manejo de secretos:** el agente no ejecutó `scripts/generate-keys.py` ni leyó valores del `.env`;
  solo contó placeholders y validó la estructura del archivo. Las credenciales nunca entraron al prompt.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] `pytest tests/ -q` → 209 passed, 4 skipped
- [x] `python vault/_Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

- **US-212 sigue bloqueada por US-113** (Deni Garrido, C1): `dbt/models/gold/` no tiene ningún
  `cubo_*.sql`. Vence el domingo 23.

## Próximos pasos

- C5 toma BUG-005, BUG-006 y BUG-007; C4 apoya en la imagen de la API.
- Congelar `requirements/celula-2.txt` ahora que Superset corre.
- US-212 en cuanto lleguen los cubos.
