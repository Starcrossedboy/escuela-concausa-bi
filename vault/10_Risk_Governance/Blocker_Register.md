---
id: DOC-BLOCKERREG
title: "Blocker Register — FARO"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
traces_up: ["vault/12_Roadmap_Sprints/Execution_Status"]
traces_down: ["vault/13_Reports/PM_Dashboard_Spec"]
last_reviewed: "2026-08-05"
tags: [blockers, dependencies, governance, dashboard]
---

# Blocker Register — FARO

> Registro único de impedimentos actuales. Un riesgo es algo que podría ocurrir; un bloqueo ya está
> impidiendo avanzar. → [[vault/10_Risk_Governance/_index]]

| BLOCK | US | Proveedor | Consumidor | Descripción | Desde | Alternativa | Dueño | Estado |
|---|---|---|---|---|---|---|---|---|
| BLOCK-001 | US-311 | Célula 5 (infra MLflow) | Célula 3 (Héctor, Andrés, Estefany) | `docker/mlflow.Dockerfile` corre `mlflow==2.8.0` contra el cliente `3.15.1`: las corridas se ven en la UI pero el modelo **nunca llega al registry** → **AC-003.4 no cumplido**. Frena US-302/303 (Andrés), US-321 (Estefany) y US-313. **Fix mergeado (PR #45, MLflow→3.15.1); falta que C3 re-corra y confirme el registry end-to-end.** | 2026-08-18 | Entrenar y ver métricas en la UI sin registrar en el registry (no cierra AC-003.4) | Luis Téllez Domínguez | mitigating |

## Convención

- Estado: `open` → `mitigating` → `resolved`.
- Todo bloqueo abierto debe apuntar a una `US-###` y tener dueño.
- A las 24 horas se escala al Tech Lead; a las 48 horas, al PO.
- Al resolverse se conserva la fila como historial y se enlaza la evidencia.
