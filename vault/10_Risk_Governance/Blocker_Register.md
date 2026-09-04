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
| BLOCK-001 | US-311 | Célula 5 (infra MLflow) | Célula 3 (Héctor, Andrés, Estefany) | `docker/mlflow.Dockerfile` corre `mlflow==2.8.0` contra el cliente `3.15.1`: las corridas se ven en la UI pero el modelo **nunca llega al registry** → **AC-003.4 no cumplido**. Frena US-302/303 (Andrés), US-321 (Estefany) y US-313. **Fix mergeado (PR #45, MLflow→3.15.1); falta que C3 re-corra y confirme el registry end-to-end.** · **2026-09-03 · C3 re-corrió y confirmó (Héctor):** el desajuste de versiones que originó este bloqueo **sí estaba resuelto** (servidor 3.15.1 = cliente 3.15.1), pero destapó una segunda causa — la raíz de artefactos apuntaba a `/mlflow/artifacts`, ruta interna del contenedor, así que `log_model()` fallaba y `register_model()` dejaba la versión `READY` sin artefacto (**BUG-043**). Se corrige con `MLFLOW_ARTIFACT_ROOT=mlflow-artifacts:/` en el `.env`, **sin tocar archivos de C5**. **AC-003.4 CUMPLIDO**: ML-01 v4, ML-02 v2 y ML-03 v2 registrados y con **carga verificada** por `verificar_registry`, no sólo presentes en el Registry | 2026-08-18 | Entrenar y ver métricas en la UI sin registrar en el registry (no cierra AC-003.4) | Luis Téllez Domínguez | resolved |
| BLOCK-004 | US-222/US-223/US-224 | Célula 1 (Diana — Bronze real) | Célula 2 (Oscar — `gold.cubo_pipeline`/DB-10, validación real de US-222/US-223 en PR #192, capturas reales de US-224) | Nadie del equipo salvo Diana tiene un ambiente local con **Bronze real** cargado (reportado por Edgar 2026-09-03) — bloquea validar con datos reales `gold.cubo_pipeline` (DB-10) y `gold.cubo_completitud` (DB-07, BUG-029 de Oscar, no bloqueante por sí solo pero también espera números reales). No es falta de scripts: es que descargar+cargar a mano toma horas y solo Diana lo ha hecho. · **2026-09-03 · Diana compartió el dump por Teams** (canal general, además de mandárselo directo a Luis Téllez para RISK-001) — Camino B queda disponible para cualquiera. · **2026-09-03 (tarde) · Oscar Quiroz — verificación de punta a punta.** Restauré ese dump (Camino B) + corrí `extractor_coneval.py`/`cargar_bronze_coneval_real.py` (flujo real de Deni Garrido) para poblar `bronze.coneval_irs_2020`/`coneval_pobreza_2020` con datos oficiales. `dbt run` completo: **22 de 24 modelos materializaron** — `dim_municipio` (el que bloqueaba en cascada) ya construye, y con él `gold.cubo_completitud`, `cubo_matricula`, `cubo_riesgo_territorial`, `cubo_driver`, `cubo_escuela_360`, `cubo_pivot`, `cubo_recomendaciones`, `cubo_comparador_municipio`. Sync a Superset: **9 de 10 tableros (DB-01…DB-09) registrados con datos reales**, capturas tomadas y en el manual (`Manual_Usuario_Dashboards.md`). El bloqueador de *ambiente* (que nadie salvo Diana tuviera Bronze real) queda **resuelto y confirmado independientemente**. **Queda un blocker nuevo, aislado y distinto, sin relación con este:** `gold.cubo_pipeline` (solo DB-10) referencia `bronze.conagua_presas` (CONAGUA/DS-06), que no existe — dependencia de **Emilio Galnares**, no de Diana/Deni; requiere seguimiento aparte. Aparte, `gold.predicciones`/`gold.recomendaciones` (mock de ML-01/02) tienen CCT que no cruzan con el catálogo real de 77,712 escuelas — todo KPI de predicción/recomendación en las 9 capturas muestra SIN_DATO por eso, no por error. | 2026-09-03 | Camino A (reproducir la carga real) **automatizado** en [[vault/14_Data_Sources/DS-01_Formato_911]] §11 — un solo comando (`python -m src.ingesta.reproducir_bronze_real`), verificado en vivo de punta a punta 2026-09-03 (385,204 filas DS-02 + ~1.37M filas DS-01 histórico), disponible ya para cualquiera sin esperar a Diana. Camino B (restaurar el dump de Bronze de Diana, compartido por Teams) **verificado exitoso 2026-09-03** por Oscar Quiroz de punta a punta, combinado con el extractor real de CONEVAL de Deni Garrido. | Diana Aracely Alvarez Varela | resolved |

## Convención

- Estado: `open` → `mitigating` → `resolved`.
- Todo bloqueo abierto debe apuntar a una `US-###` y tener dueño.
- A las 24 horas se escala al Tech Lead; a las 48 horas, al PO.
- Al resolverse se conserva la fila como historial y se enlaza la evidencia.
