---
id: DOC-DECLOG
title: "Decision Log"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
tags: [governance, decisions]
---

# Decision Log — FARO

> Decisiones de proceso/producto (las técnicas van a `03_Architecture/ADRs`).
> → [[10_Risk_Governance/_index]]

| DEC | Fecha | Decisión | Contexto | Dueño |
|---|---|---|---|---|
| DEC-001 | 2026-08-05 | El tablero PM es una proyección generada, no una fuente de verdad | Evitar duplicar US, responsables, riesgos y estados dentro del HTML | Edgar Edmundo Coronel Navarrete |
| DEC-002 | 2026-08-06 | Reducir temporalmente a una aprobación la protección del PR y restaurar dos aprobaciones el 2026-08-07 | Excepción operativa para agilizar el PR del tablero; no modifica la política canónica de doble compuerta | Edgar Edmundo Coronel Navarrete |
| DEC-003 | 2026-08-09 | **Cambio de política canónica: de doble compuerta (2 aprobaciones) a compuerta única (1 aprobación, el PM).** Ruleset `main` → `required_approving_review_count: 1`, `require_code_owner_review: true`; CODEOWNERS reducido a `* @edgarcoroneln`; se agrega bypass de administrador para que el PM pueda mergear sus propios PR (no puede autoaprobarlos). | La doble compuerta demostró ser un cuello de botella operativo en Sprint 1 (PR bloqueados esperando 2ª aprobación). El PM asume la revisión de proceso y técnica; los Tech Leads revisan de forma no bloqueante. Deja sin efecto la política de doble compuerta de [[05_Engineering/Branching_Strategy]]. | Edgar Edmundo Coronel Navarrete |
