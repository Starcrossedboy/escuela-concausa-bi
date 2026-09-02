---
id: DOC-TESTSTRAT
title: "Test Strategy"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
traces_up: ["PRD#6"]
tags: [qa, strategy]
---

# Test Strategy — FARO

> → [[vault/06_Quality_Testing/_index]]

## Pirámide de pruebas
| Nivel | Herramienta | Dueño | Corre en |
|---|---|---|---|
| Unit | <Jest/pytest/Vitest> | dev del módulo | CI (cada PR) |
| Integración | <emulador/testcontainers> | dev backend | CI |
| E2E | <Playwright/Cypress> | QA | CI (nightly) |
| Manual / físico | guiones | QA | pre-release |
| Seguridad | ver [[vault/07_Security/_index]] | security owner | CI + pre-release |

## Cobertura mínima
- Rutas críticas / API: ≥ 80%
- Todo `REQ-###` tiene al menos un `TEST-###` (verificable en la matriz).

## Trazabilidad
Cada test declara `traces_up` al `REQ`/`US` que valida. Sin test = requisito no Done.

## Gestión de bugs
Todo defecto → `BUG-###` en [[vault/06_Quality_Testing/Bug_Register]] + test de regresión.
