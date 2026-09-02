---

project: "FARO"
date: "2026-08-10"
author_human: "Deni Garrido Fragoso"
agent: "Codex"
model: "GPT-5"
session_duration: "2h"
touches: ["DOC-ONBOARD"]
tags: [devlog, onboarding, celula-1]
------------------------------------

# DevLog — 2026-08-10 — Onboarding y ambiente local

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

* Se preparó el ambiente local con Python 3.11, Docker Desktop y dbt.
* Se creó `.venv` y `.env`, ambos ignorados por Git.
* Se ejecutaron las pruebas base.
* Se agregó a Deni Garrido Fragoso a la lista de integrantes que completaron onboarding.

## 🤖 Sesión de IA

* **Agente / modelo:** Codex / GPT-5
* **Archivos creados/modificados:**

  * `vault/00_Start_Here/Developer_Onboarding.md`
  * `vault/_DevLog/2026-08-10-deni-garrido-onboarding.md`
  * `vault/_DevLog/_index.md`
* **Decisiones autónomas del agente:** usar una carpeta local fuera de OneDrive y no instalar Airflow directamente en Windows.
* **Correcciones manuales:** Deni revisó los comandos y configuró personalmente las variables privadas.
* **Prompt inicial:** acompañamiento para comprender y completar el onboarding de GitHub.

## Seguridad / calidad

* [x] Sin secretos hardcodeados.
* [x] `pytest tests/ -q`: 5 pruebas aprobadas.
* [x] `python -m pip check`: sin dependencias rotas.
* [x] DevLog enlaza a `DOC-ONBOARD`.
* [ ] `vault_lint.py`: bloqueado por problemas preexistentes y por inspeccionar `.venv`.

## Bloqueantes

* No existe un archivo Docker Compose en `main`.
* El linter reporta errores preexistentes y archivos Markdown dentro de `.venv`.

## Próximos pasos

* Crear el commit, hacer push y abrir el PR de práctica.
* Solicitar las dos aprobaciones.
