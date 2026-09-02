---
id: META-ADOPT
title: "Adoption Guide"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
tags: [meta, onboarding, adoption]
---

# Adoption Guide — Cómo adoptar este vault en un proyecto

> → [[vault/_Meta/_index|Volver a _Meta]]

## Paso a paso

1. **Copia** la carpeta del vault a tu repo (o a un repo de documentación aparte).
2. **Reemplaza los placeholders** en todos los archivos:
   - `FARO`, `Edgar Edmundo Coronel Navarrete`, `https://github.com/edgarcoroneln/escuela-concausa-bi`, `Python 3.11 · Airflow · dbt · Postgres · Superset · MLflow · FastAPI · Docker · GCP`, `2026-08-01`, `Edgar Edmundo Coronel Navarrete`
   ```bash
   grep -rl "FARO" . | xargs sed -i '' 's/FARO/MiProyecto/g'
   ```
3. **Define el equipo** en [[vault/00_Start_Here/Developer_Onboarding]] y crea un
   `vault/09_AI_Governance/Agent_Contexts/{nombre}.md` por persona (usa la plantilla).
4. **Escribe el PRD** en [[vault/01_Product/PRD]] (usa [[vault/_Templates/PRD_template]]).
5. **Deriva requisitos** en [[vault/02_Requirements/Requirements_General]] y `Requirements_Detailed`,
   y siembra la [[vault/02_Requirements/Traceability_Matrix]].
6. **Configura enforcement:**
   - La plantilla de PR vive en `.github/PULL_REQUEST_TEMPLATE.md` y GitHub la carga sola
   - Implementa los gates de [[vault/08_CICD_DevOps/CI_Quality_Gates]] en tu `ci.yml`
   - Activa branch protection según [[vault/05_Engineering/Branch_Protection]]
7. **Configura CLAUDE.md / AGENTS.md** del repo apuntando a este vault y a los Agent Contexts.
8. **Corre el linter** [[vault/_Meta/Link_Hygiene]] para validar que todo enlaza.

## Checklist de "vault listo"

- [ ] Sin placeholders `{{...}}` restantes
- [ ] PRD aprobado
- [ ] Al menos 1 REQ con cadena completa en la matriz (ejemplo de referencia)
- [ ] PR template + CI gates + branch protection activos
- [ ] Un Agent Context por contribuidor
- [ ] `vault_lint.py` sin errores
