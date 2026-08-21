---
id: DOC-RISKREG
title: "Risk Register"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
tags: [risk, register]
---

# Risk Register — FARO

> → [[10_Risk_Governance/_index]]

| RISK | Descripción | Prob. (1-5) | Impacto (1-5) | Respuesta | Mitigación | Disparador | Dueño | Estado | US relacionada | Fecha objetivo |
|---|---|---:|---:|---|---|---|---|---|---|---|
| RISK-001 | Sin URL pública viva al evaluar: techo de 6.0 | 3 | 5 | mitigar | Deploy temprano y healthcheck verificable en S1 | US-501 no tiene evidencia el 9 ago | Luis Téllez Domínguez | cerrado | US-501 | 2026-08-09 (URL viva) |
| RISK-002 | Una o más fuentes resultan inservibles | 4 | 4 | mitigar | 6/8 fuentes probadas con extractor real (DS-04/05 por Luis, PR #47; DS-01/02/03/07 vía DAG); **faltan DS-06 CONAGUA y DS-08 CONAPO** (Emilio, US-121a/122a en `planned`) | descarga, esquema o llave fallan | Diana Aracely Alvarez Varela | mitigando | US-121a, US-121b, US-122b | 2026-08-16 (fin S2) |
| RISK-003 | Participación concentrada o contribución no auditable | 3 | 3 | mitigar | PR, reviews y DevLogs; sin ranking de commits | persona sin evidencia durante 7 días | Edgar Edmundo Coronel Navarrete | abierto | US-004 | Continuo |
| RISK-004 | Retraso de Gold bloquea BI, ML y API | 4 | 5 | mitigar | Contratos, mocks y fixtures; escalamiento a 24 h | US-103/104 se desvía del gate S3 | Diana Aracely Alvarez Varela | cerrado | US-103, US-104, US-105 | 2026-08-19 (Gold entregado: dim/fact + features, PR #48/#52) |
| RISK-005 | Sobre-alcance geográfico o funcional | 3 | 4 | evitar | Respetar `SCOPE_ENTIDADES` y congelar alcance | nueva entidad/feature sin decisión registrada | Edgar Edmundo Coronel Navarrete | mitigando | — | Continuo |
| RISK-006 | El vault pierde trazabilidad con 21 contribuidores | 3 | 4 | mitigar | linter, steward, matriz y generador validado | link roto, ID duplicado o artefacto huérfano | Edgar Edmundo Coronel Navarrete | mitigando | US-004 | Continuo |
| RISK-007 | Formato 911 solo tiene el ciclo 2024-2025: sin ≥2 ciclos no hay `target_variacion_matricula` que predecir (ML sin objetivo real) | 4 | 5 | mitigar | **Target híbrido de dos niveles (DEC-007):** target real multi-año a nivel `municipio × nivel` con la serie SNIEE de la SEP (misma fuente DS-01, agregada) + features y driver dominante a nivel escuela con el 911 2024-2025. **En paralelo:** perseguir el 2º ciclo crudo del 911 (2023-2024/2022-2023) para subir la granularidad del target a escuela. **Contingencia:** índice compuesto de riesgo desde los 6 drivers marcado `SIN_DATO_REAL` | Ni la serie SNIEE ni un 2º ciclo confirmados antes del gate ML (S4) | Edgar Edmundo Coronel Navarrete | mitigando | US-104, US-311, US-313 | 2026-08-30 (gate S4) |

## Escala
Probabilidad e impacto usan escala 1 (mínimo) a 5 (máximo). Severidad = `Prob. × Impacto`.
Respuesta: evitar / mitigar / transferir / aceptar. Estado: abierto → mitigando → cerrado → aceptado.
Los riesgos de seguridad enlazan a [[07_Security/Threat_Model]].
