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
| BLOCK-004 | US-222/US-223/US-224 | Célula 1 (Diana — Bronze real) | Célula 2 (Oscar — `gold.cubo_pipeline`/DB-10, validación real de US-222/US-223 en PR #192, capturas reales de US-224) | Nadie del equipo salvo Diana tiene un ambiente local con **Bronze real** cargado (reportado por Edgar 2026-09-03) — bloquea validar con datos reales `gold.cubo_pipeline` (DB-10) y `gold.cubo_completitud` (DB-07, BUG-029 de Oscar, no bloqueante por sí solo pero también espera números reales). No es falta de scripts: es que descargar+cargar a mano toma horas y solo Diana lo ha hecho. | 2026-09-03 | Camino A (reproducir la carga real) **automatizado** en [[vault/14_Data_Sources/DS-01_Formato_911]] §11 — un solo comando (`python -m src.ingesta.reproducir_bronze_real`), verificado en vivo de punta a punta 2026-09-03 (385,204 filas DS-02 + ~1.37M filas DS-01 histórico), disponible ya para cualquiera sin esperar a Diana. Camino B (restaurar el dump de Bronze de Diana, minutos en vez de horas) documentado en la misma sección — dump ya generado 2026-09-03 (33 MB), pendiente solo de que Diana lo comparta por Teams. | Diana Aracely Alvarez Varela | mitigating |

## Convención

- Estado: `open` → `mitigating` → `resolved`.
- Todo bloqueo abierto debe apuntar a una `US-###` y tener dueño.
- A las 24 horas se escala al Tech Lead; a las 48 horas, al PO.
- Al resolverse se conserva la fila como historial y se enlaza la evidencia.
