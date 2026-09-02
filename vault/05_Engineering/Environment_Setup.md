---
id: DOC-ENVSETUP
title: "Environment Setup"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
tags: [engineering, setup]
---

# Environment Setup — FARO

> → [[vault/05_Engineering/_index]] · secretos en [[vault/07_Security/Secrets_Policy]]

> **Documento canónico de setup: [[vault/00_Start_Here/Developer_Onboarding]].** Esta nota es complementaria
> (variables y comandos rápidos); no se duplica aquí el paso a paso del onboarding (regla 1 del vault).

## Requisitos
- Python 3.11 · Airflow · dbt · Postgres · Superset · MLflow · FastAPI · Docker · GCP

## Instalación
```bash
git clone https://github.com/edgarcoroneln/escuela-concausa-bi
# instalar deps
# copiar .env.example → .env y rellenar (NUNCA commitear .env)
```

## Variables de entorno
Todas documentadas en `.env.example`. Ninguna con valor real en el repo.

## Comandos comunes
| Acción | Comando |
|---|---|
| Dev | `docker compose up -d` |
| Test | `pytest tests/ -q` |
| Lint | `python vault/_Meta/scripts/vault_lint.py .` |
| Build | `docker compose build` |
