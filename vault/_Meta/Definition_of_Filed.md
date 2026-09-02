---
id: META-FILED
title: "Definition of Filed"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [meta, intake, process]
---

# Definition of Filed — Intake de "cosas nuevas reportadas"

> Cualquier cosa nueva (bug, hallazgo de seguridad, decisión, auditoría, requisito, incidente)
> **no cuenta como reportada** hasta cumplir esta checklist.
> → [[vault/_Meta/_index|Volver a _Meta]]

## Checklist de "Filed" ✅

- [ ] Tiene un **ID** según [[vault/_Meta/Naming_Conventions]]
- [ ] Vive en su **carpeta correcta** (no en la raíz del repo ni suelto)
- [ ] Tiene **frontmatter** con `owner` y `status`
- [ ] Enlaza a su **origen** (`traces_up`) y a lo que lo resolverá (`traces_down`) si aplica
- [ ] Está listado en el **`_index.md` (MOC)** de su carpeta
- [ ] Si afecta un requisito: su fila en [[vault/02_Requirements/Traceability_Matrix]] fue actualizada
- [ ] Si nació de una sesión de IA: hay entrada en [[vault/_DevLog/_index]]

## Flujo de intake por tipo

| Reporte nuevo | Carpeta destino | Registro obligatorio |
|---|---|---|
| Bug | `vault/06_Quality_Testing` | [[vault/06_Quality_Testing/Bug_Register]] |
| Hallazgo de seguridad | `vault/07_Security` | [[vault/07_Security/Security_Audit_Log]] |
| Riesgo | `vault/10_Risk_Governance` | [[vault/10_Risk_Governance/Risk_Register]] |
| Bloqueo operativo | `vault/10_Risk_Governance` | [[vault/10_Risk_Governance/Blocker_Register]] |
| Decisión técnica mayor | `vault/03_Architecture/ADRs` | nuevo ADR |
| Decisión de proceso | `vault/10_Risk_Governance` | [[vault/10_Risk_Governance/Decision_Log]] |
| Incidente en prod | `vault/10_Risk_Governance` + `vault/11_Operations` | [[vault/10_Risk_Governance/Incident_Log]] + post-mortem |
| Requisito nuevo | `vault/02_Requirements` | matriz + `_index` |
| Reporte ejecutivo | `vault/13_Reports` | fechado, sin duplicar dashboards |

> **Anti-patrón prohibido:** dejar archivos `.txt`, PDFs sueltos o "notas" en la raíz del repo.
> Si algo no encaja en ninguna carpeta, es señal de que falta una carpeta — discútelo con el PM.
