---
project: "FARO"
date: "2026-08-14"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (claude.ai)"
model: "claude-sonnet-5"
session_duration: "~1h"
touches: ["US-102", "US-101"]
tags: [devlog]
---

# DevLog — 2026-08-14 — PR de US-102 y contrato indice_riesgo en gold.predicciones

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo
- Verificado que el PR #14 (US-521b) se mergeó a main; docker-compose.yml apareció pero solo
  con servicios db/api, sin airflow/superset/mlflow — bloqueo de US-102 sigue vigente
- Actualizada la rama de US-102 con los últimos cambios de main
- Confirmada URL real de Formato911 y comiteada (sesión anterior, referenciada aquí)
- Publicado PR #29 de US-102 (8/8 fuentes de datos en código, DAGs de Airflow)
- Actualizado vault/03_Architecture/Data_Model.md §4.5 para el cambio de contrato de gold.predicciones
  coordinado por Edgar Coronel Navarrete (DEC-005/006): indice_riesgo pasa a ser columna
  derivada propia, ya no reutiliza valor
- Corregido un commit que quedó por error directamente en main (detectado y revertido antes
  de hacer push, movido a la rama correcta con cherry-pick)
- Abierto PR de fix/diana-varela-datamodel-indice-riesgo

## 🤖 Sesión de IA
- **Agente / modelo:** Claude (claude.ai), claude-sonnet-5
- **Archivos creados/modificados:**
  - src/ingesta/extractor_formato911.py (URL confirmada)
  - vault/12_Roadmap_Sprints/Sprints/1-diana-aracely-alvarez-varela.md (estado de US-102)
  - vault/03_Architecture/Data_Model.md (§4.5 y nota de indice_riesgo)
- **Decisiones autónomas del agente:** verificar con find/grep la existencia real de
  docker-compose.yml y sus servicios antes de asumir que el bloqueo se había resuelto;
  detectar y corregir el commit hecho por error en main antes de hacer push
- **Correcciones manuales:** ninguna — cambios revisados y confirmados por Diana en cada paso
- **Prompt inicial:** continuación de sesión anterior de US-102, coordinación nueva recibida
  por Teams sobre contrato de gold.predicciones (DEC-005/006)

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] `python vault/_Meta/scripts/vault_lint.py .` → Vault limpio (verificado dos veces)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- docker-compose.yml en main no incluye airflow/superset/mlflow — mensaje actualizado
  pendiente de enviar a Edgar Coronel
- Falta que Edgar Coronel Navarrete registre DEC-005 en vault/10_Risk_Governance/Decision_Log.md

## Próximos pasos
- Enviar mensajes pendientes a Edgar Coronel (bloqueo Docker + avisos de contrato)
- Esperar revisión de Edgar en PR #29 (US-102) y en el PR de Data_Model.md
- Avisar a Andrés (C3) y Christian (C4) sobre el cambio de contrato, según pidió Edgar