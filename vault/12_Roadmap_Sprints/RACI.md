---
id: DOC-RACI
title: "RACI de entregables — FARO"
owner: "Edgar Edmundo Coronel Navarrete"
status: in_review
source_of_truth: true
traces_up: ["vault/12_Roadmap_Sprints/PLAN_MAESTRO", "vault/02_Requirements/User_Stories"]
traces_down: ["vault/13_Reports/PM_Dashboard_Spec"]
last_reviewed: "2026-08-05"
tags: [roadmap, raci, governance, dashboard]
---

# RACI de entregables — FARO

> Responsabilidades a nivel de entregable. La asignación de cada historia permanece en
> [[vault/02_Requirements/User_Stories]]. → [[vault/12_Roadmap_Sprints/_index]]

## Claves

- **R:** Responsible — ejecuta.
- **A:** Accountable — responde por la aceptación final.
- **C:** Consulted — participa antes de decidir.
- **I:** Informed — recibe el resultado.

| Entregable | R | A | C | I | Fecha gate |
|---|---|---|---|---|---|
| Gobierno, requisitos y trazabilidad | PO | Edgar Edmundo Coronel Navarrete | Tech Leads | Equipo | 2026-08-09 |
| Fuentes, Bronze, Silver y Gold | Célula 1 | Diana Aracely Alvarez Varela | Células 2, 3 y 4 | PO · Célula 5 | 2026-08-23 |
| Dashboards y experiencia BI | Célula 2 | Manuel Alejandro Serranía Reinada | Células 1, 3 y 4 | PO | 2026-08-30 |
| Modelos ML y agente | Célula 3 | Andrés González Habib | Células 1 y 4 | PO · Célula 2 | 2026-09-06 |
| API, autenticación y seguridad | Célula 4 | Christian Imanol Ruiz Hurtado | Células 1 y 3 | PO · Célula 2 | 2026-08-30 |
| Contenedores, CI/CD y GCP | Célula 5 | Luis Téllez Domínguez | Todos los Tech Leads | PO · Equipo | 2026-09-08 |
| Demo, pitch y plan de contingencia | PO | Edgar Edmundo Coronel Navarrete | Tech Leads | Equipo | 2026-09-08 |

## Regla de escalamiento

Un entregable bloqueado por más de 24 horas se registra en
[[vault/10_Risk_Governance/Blocker_Register]]. Una decisión que cambie alcance, seguridad, esquema o CI/CD
requiere aprobación humana y registro en [[vault/10_Risk_Governance/Decision_Log]] o un ADR.
