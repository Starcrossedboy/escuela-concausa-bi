---
id: DOC-TRACE-MATRIX
title: "Matriz de Trazabilidad — FARO"
owner: "Edgar Edmundo Coronel Navarrete"
status: in_review
version: "1.0"
source_of_truth: true
traces_up: ["02_Requirements/Requirements_Detailed", "02_Requirements/User_Stories"]
last_reviewed: "2026-08-03"
tags: [requirements, traceability, matrix]
---

# ⭐ Matriz de Trazabilidad — FARO

> **Vista única del estado del proyecto** (historia **US-004**, PM). Cierra el ciclo:
> REQ → AC → US → Fuentes → Modelos → Arquitectura → Test → DevLog → Release.
> → [[02_Requirements/_index]] · [[02_Requirements/Requirements_Detailed]] · [[02_Requirements/User_Stories]]

## Cómo se mantiene

- **El PM la actualiza en cada standup** (semanas 1–3 los jueves; semanas 4–6 L-Mi-V).
- Las columnas **Test**, **DevLog** y **Release** nacen **vacías (⬜)** y se llenan conforme avanza la
  ejecución.
- **Regla dura:** una fila con **Test o DevLog en ⬜ NO está Done.** La planeación puede estar completa,
  pero el REQ solo pasa a 🟢 cuando tiene prueba verde, DevLog y quedó en un release.
- Nuevo `REQ-###` → fila nueva. Cambios de alcance → PR con aviso al dueño del REQ.

---

## Matriz

| REQ | Criterios AC | User Stories | Fuentes DS | Modelos ML | Arquitectura | Test | DevLog | Release | Estado |
|---|---|---|---|---|---|---|---|---|---|
| [[02_Requirements/Requirements_Detailed\|REQ-001]] · Data Engineering | AC-001.1…AC-001.7 (7) | [[02_Requirements/User_Stories\|18 US]]: US-101–106, US-111–114, US-121a/b–124a/b | [[14_Data_Sources/_index\|DS-01…DS-08]] (las 8) | — (produce `features_escuela`) | [[03_Architecture/Data_Model\|Data_Model]] | ⬜ | [[_DevLog/2026-08-07-diana-alvarez-data-model-us101\|2026-08-07]] | ⬜ | 🟡 En progreso |
| [[02_Requirements/Requirements_Detailed\|REQ-002]] · Frontend BI | AC-002.1…AC-002.6 (6) | [[02_Requirements/User_Stories\|19 US]]: US-201–207, US-211a/b, US-212, US-213, US-214a/b, US-215a/b, US-221–224 | — (vía Gold) | ML-01/02/03 (consumidos en DB-06/09) | [[03_Architecture/Data_Model\|Data_Model]] (cubos) · [[03_Architecture/Frontend_Architecture\|FARO Web]] · [[04_UX_Design/Screen_Specs\|Screen_Specs]] (US-201) · [[04_UX_Design/Cube_Specs_DB03_DB04\|Cube_Specs DB-03/04]] (US-211a) | `test_semantic_db03_db04` ✅ (US-211a, 28 casos: SIN_DATO≠0, ML por JOIN, grano) | [[_DevLog/2026-08-07-manuel-serrania-us-201\|2026-08-07]] · US-201 · [[_DevLog/2026-08-13-manuel-serrania-screenspecs-cubos\|2026-08-13]] · [[_DevLog/2026-08-14-marina-garcia-cubos-db03-db04\|2026-08-14]] · US-211a | ⬜ | 🟡 En progreso |
| [[02_Requirements/Requirements_Detailed\|REQ-003]] · Modelos ML | AC-003.1…AC-003.6 (6) | [[02_Requirements/User_Stories\|10 US]]: US-301–303, US-311–313, US-321, US-322, US-324, US-325 (+apoyo US-412/415/416) | DS-01…08 (vía `features_escuela`) | [[15_ML_Models/_index\|ML-01, ML-02, ML-03]] | [[03_Architecture/Data_Model\|Data_Model]] · [[03_Architecture/API_Specification\|API_Spec]] | [[06_Quality_Testing/Automated/Particion_Temporal_ML01\|TEST-003 ✅]] (US-311, AC-003.3) · [[15_ML_Models/Indice_Riesgo_ML01\|TEST-004 ✅]] (US-311) · [[15_ML_Models/ML01_Entrenamiento\|TEST-005 ✅]] (ML-01 entrenado) | [[_DevLog/2026-08-08-hector-morales-fixture-particion-temporal\|2026-08-08]] · [[_DevLog/2026-08-11-hector-morales-indice-riesgo-ml01\|2026-08-11]] · [[_DevLog/2026-08-13-hector-morales-entrenamiento-ml01\|2026-08-13]] | ⬜ | 🟡 En progreso |
| [[02_Requirements/Requirements_Detailed\|REQ-004]] · Backend/API/Auth | AC-004.1…AC-004.6 (6) | [[02_Requirements/User_Stories\|14 US]]: US-401–405, US-411–416, US-421–423 | — | ML-01/02/03 (expuestos vía API) | [[03_Architecture/API_Specification\|API_Spec]] · [[03_Architecture/Data_Model\|Data_Model]] | `test_api_contract` ✅ (US-401, 18 casos) | [[_DevLog/2026-08-11-christian-ruiz-us401-contrato-api\|2026-08-11]] · US-401 | ⬜ | 🟡 En progreso |
| [[02_Requirements/Requirements_Detailed\|REQ-005]] · Deploy GCP | AC-005.1…AC-005.5 (5) | [[02_Requirements/User_Stories\|13 US]]: US-501, US-502, US-504, US-505, US-522a/b/c, US-524a/b/c, US-525a/b/c | — | — | [[08_CICD_DevOps/Cloud_Run_Deploy\|Cloud Run Deploy ✅]] | ⬜ | [[_DevLog/2026-08-09-luis-tellez-us501-cloud-run-deploy\|2026-08-09]] | ⬜ | 🟡 En progreso |
| [[02_Requirements/Requirements_Detailed\|REQ-006]] · Agente | AC-006.1…AC-006.4 (4) | [[02_Requirements/User_Stories\|4 US]]: US-304a, US-304b, US-305, US-323 | — (vía Gold) | — (RAG sobre Gold) | [[03_Architecture/API_Specification\|API_Spec]] (`/agente`) · [[03_Architecture/Data_Model\|Data_Model]] | ⬜ | ⬜ | ⬜ | 📋 Planeado |
| [[02_Requirements/Requirements_Detailed\|REQ-007]] · Equipo/Git/Docs | AC-007.1…AC-007.5 (5) | [[02_Requirements/User_Stories\|13 US]]: US-001–006, US-503, US-521a/b/c, US-523a/b/c | — | — | [[AGENTS\|AGENTS.md]] · [[_Meta/Vault_Rules\|vault]] · [[13_Reports/PM_Dashboard_Spec\|Tablero PM]] | [[06_Quality_Testing/Automated/_index\|TEST-002 ✅]] | [[_DevLog/2026-08-05-edgar-tablero-control-pm-v2\|2026-08-05]] · [[_DevLog/2026-08-06-edgar-directorio-github-codeowners\|2026-08-06]] · [[_DevLog/2026-08-12-alejandro-velazquez-mendoza\|2026-08-12]] | ⬜ | 🟡 En progreso |

---

## Leyenda de estado

- 📋 **Planeado** — cobertura de planeación completa (AC, US y arquitectura definidos); **ejecución no
  iniciada** (Test/DevLog/Release en ⬜).
- 🟡 **En progreso** — hay commits/PRs abiertos pero aún sin Test o DevLog completo.
- 🟢 **Done** — Test verde + DevLog + quedó en un Release.
- 🔴 **No iniciado** · ⚫ **Archivado/deprecado**.
- ⚠️ marca un **hueco de planeación** en alguna columna (ver abajo).

---

## Estado del proyecto

| Métrica | Valor |
|---|---|
| REQ totales | 7 |
| REQ con **planeación completa** (AC + US + arquitectura) | **6 / 7** |
| REQ con hueco de planeación | **1 / 7** (REQ-005: falta `System_Design.md`) |
| REQ **pendientes de ejecución** (sin Release completo) | **7 / 7** |
| REQ con Test | 1 / 7 |
| REQ con DevLog | 1 / 7 |
| REQ **Done** | 0 / 7 |
| Historias mapeadas | 91 / 91 (cobertura 7/7 módulos) |

> **Lectura:** la **planeación** está prácticamente cerrada (6 de 7 REQ con cobertura completa); la
> **ejecución** arrancó en REQ-007, pero aún hay 0 REQ Done. El único hueco es la **arquitectura de despliegue de
> REQ-005**, que se resolverá al escribir `03_Architecture/System_Design.md`.
