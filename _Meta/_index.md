---
id: MOC-META
title: "_Meta — Reglas y salud del vault"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
tags: [moc, meta]
---

# _Meta — Reglas del vault

> Cómo funciona el vault: convenciones, trazabilidad e higiene.
> → [[00_Start_Here/PROJECT_INDEX|Índice del Proyecto]]

| Documento | Propósito |
|---|---|
| [[_Meta/Vault_Rules]] | Reglas no negociables del vault |
| [[_Meta/Naming_Conventions]] | IDs, nombres de archivo, ramas y commits |
| [[_Meta/Traceability_Model]] | Cómo se conecta todo (frontmatter + matriz) |
| [[_Meta/Definition_of_Filed]] | Cuándo algo "nuevo reportado" se considera archivado |
| [[_Meta/Link_Hygiene]] | Evitar links rotos y huérfanos |
| [[_Meta/Adoption_Guide]] | Cómo adoptar el vault en un proyecto nuevo |
| `scripts/vault_lint.py` | Check automatizable de higiene (links, frontmatter, IDs) |
| `scripts/generate_pm_dashboard.py` | Genera el snapshot y HTML PM desde fuentes canónicas |
| `scripts/validate_pm_dashboard.py` | `TEST-002`: valida IDs, cobertura, estados y vistas del tablero |
| `scripts/collect_github_activity.py` | Recopila PR/CI agregado en Actions; no modifica estados de US |
* [[US-521b-guia-ambiente-local]] - Guía de ambiente local reproducible
