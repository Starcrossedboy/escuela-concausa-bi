---
project: "FARO"
date: "2026-08-07"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "deepseek-v4-flash-free"
session_duration: "sesión única: US-201 portafolio de dashboards y catálogo de KPIs"
touches: ["US-201", "REQ-002", "DOC-SCREENSPECS", "DOC-TRACE-MATRIX", "PRD"]
tags: [devlog, dashboards, kpis, celula-2]
---

# DevLog — 2026-08-07 — US-201: portafolio de 10 dashboards y catálogo de KPIs

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- **US-201 (S1) completa.** `vault/04_UX_Design/Screen_Specs.md` pasó de plantilla a **portafolio canónico**:
  - §1 Principios de diseño (filtros globales AC-002.2, `SIN_DATO` explícito, grano CCT).
  - §2 Arquitectura de información de DB-01…DB-10: propósito, audiencia, cubo Gold e historia.
  - §3 Árbol de navegación de FARO Web en mermaid + navegación cruzada (drill-downs).
  - §4 Catálogo de **14 KPIs** (KPI-01…KPI-14) con fórmula SQL sobre `gold.fact_escuela_ciclo` + dims
    y el cubo que los materializa.
  - §5 Filtros globales (ciclo, entidad, nivel) · §6 Trazabilidad.
- **Ratificación del catálogo DB** (P8 del DevLog del PM): nota "pendiente" de `PRD.md §12` →
  ratificada por Manuel (TL C2) con enlace al portafolio.
- **Cierre:** fila REQ-002 en Traceability_Matrix (columna DevLog), `vault/04_UX_Design/_index.md`,
  seguimiento §9 del plan de sprint (US-201 → 🔵 En revisión, 100%).

## 🤖 Sesión de IA

- **Agente / modelo:** OpenCode / deepseek-v4-flash-free
- **Archivos creados/modificados:**
  - `vault/04_UX_Design/Screen_Specs.md` (reescrito)
  - `vault/01_Product/PRD.md` (§12 ratificación)
  - `vault/02_Requirements/Traceability_Matrix.md` (fila REQ-002)
  - `vault/04_UX_Design/_index.md` (descripción de Screen_Specs)
  - `vault/12_Roadmap_Sprints/Sprints/2-manuel-alejandro-serrania-reinada.md` (§9 seguimiento)
- **Decisiones autónomas del agente:**
  - Fórmulas SQL definidas sobre el esquema canónico (fact+dims) con el cubo anotado por KPI,
    siguiendo el Data_Model; umbral de riesgo fijado en 0.6 (revisable por el negocio).
  - KPI-14 (contexto socioeconómico) añadido para sostener DB-04, que no tenía KPI propio.
- **Correcciones manuales:** ninguna (pendiente de revisión línea por línea antes del merge).
- **Prompt inicial:** plan de US-201 acordado en sesión (archivo destino, nivel de fórmulas,
  ratificación del catálogo).

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [ ] Tests agregados/actualizados (N/A — historia de documentación de diseño; `pytest tests/` verificado en verde)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

- Ninguno.

## Próximos pasos

- Revisión del PR por Edgar (PM) — compuerta técnica y de proceso.
- US-201 → ✅ en la tabla §9 del plan tras el merge.
- US-202 (S3): conectar Superset a Gold, datasets virtuales y capa semántica.
