---
project: "FARO"
date: "2026-08-15"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "sesión única: ratificación LEFT JOIN, alta KPI-15..KPI-18 y convención superset/semantic (US-202)"
touches: ["US-201", "US-211a", "REQ-002", "DOC-SCREENSPECS", "DOC-CUBESPEC-DB0304", "DOC-TRACE-MATRIX"]
tags: [devlog, dashboards, kpis, celula-2]
---

# DevLog — 2026-08-15 — Ratificación LEFT JOIN DB-03, alta KPI-15..18 y convención `superset/semantic/`

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Marina García del Buey (C2) mergeó **US-211a**: el contrato semántico de los cubos de DB-03 y DB-04
([[04_UX_Design/Cube_Specs_DB03_DB04]]), el SQL de referencia y la capa semántica en `superset/semantic/`.
Su §8.3 me pedía tres cosas como owner del catálogo de KPIs (US-201) y de la convención de Superset
(US-202):

1. **Ratificar el `LEFT JOIN`** a las salidas de ML en el grano de escuela.
2. **Dar de alta KPI-15…KPI-18** en el catálogo canónico — DB-03 no tenía KPI propio (solo KPI-14 en DB-04)
   y AC-002.4 exige perfil, drivers, predicción y recomendación por CCT.
3. **Revisar la convención de carpeta `superset/semantic/`** y alinear los nombres de métricas con US-202.

## Decisiones tomadas (como Tech Lead C2)

1. **`LEFT JOIN` ratificado.** No cambia la regla R1 (las salidas de ML se leen siempre por JOIN,
   ratificada el 13-ago); solo fija el tipo de JOIN para el grano de escuela. Con JOIN interno, una
   escuela sin predicción desaparecería de su propia ficha — un nulo silencioso a nivel de fila, que
   viola P2/AC-002.6. Hoy `gold.predicciones` ni existe (llega en S4), así que el LEFT JOIN es
   obligatorio. La ficha muestra `cobertura_prediccion = 'SIN_DATO'` y "sin dato disponible".
2. **Alta de KPI-15…KPI-18** con los nombres y fórmulas propuestos por Marina en su §5.1, publicados
   como canónicos en `04_UX_Design/Screen_Specs.md` (regla 1: un tema, un archivo canónico).
3. **Convención `superset/semantic/` adoptada como está** y documentada en `superset/README.md` como
   estándar US-202: subcarpeta por contrato, `<tablero>_<cubo>.sql` + `metrics_<cubos>.yaml`, nombres
   de métricas en `snake_case` **idénticos a la fórmula del KPI canónico**, reglas no negociables
   (ML por JOIN, SIN_DATO ≠ 0, umbral 0.6, componentes aditivos, `NULLIF`).

## Qué se hizo

- **`04_UX_Design/Screen_Specs.md`** (catálogo canónico, US-201):
  - §4 nota de lectura: agregada la regla de **tipo de JOIN por grano** (interno en cubos agregados;
    `LEFT` en el grano de escuela), con referencia a DOC-CUBESPEC-DB0304 §2.2 y fecha de ratificación.
  - Catálogo: altas **KPI-15** (Perfil de matrícula), **KPI-16** (Perfil de drivers), **KPI-17**
    (Predicción, `LEFT JOIN gold.predicciones` ML-01 + semáforo 0.6) y **KPI-18** (Recomendación
    prescriptiva, `LEFT JOIN gold.recomendaciones`), cada uno con su sección SQL.
  - §2 fila DB-03: referencia a KPI-15…18. §6 Trazabilidad: agregado **AC-002.4** a `Sustenta AC`.
  - `last_reviewed` → 2026-08-15.
- **`superset/README.md`** (nuevo): convención canónica de la capa semántica US-202 (estructura de
  carpetas, naming de archivos y métricas, estructura del YAML, reglas no negociables, validación y
  responsables). Adopta la estructura que Marina propuso en US-211a.
- **DevLog** creado y registrado en `_DevLog/_index.md`.
- **`02_Requirements/Traceability_Matrix.md`**: celda DevLog de REQ-002 → referencia esta sesión.

## 🤖 Sesión de IA

- **Agente / modelo:** OpenCode / opencode/big-pickle
- **Archivos creados/modificados:**
  - `04_UX_Design/Screen_Specs.md`
  - `superset/README.md` (nuevo)
  - `_DevLog/2026-08-15-manuel-serrania-kpis-db03-ratificacion-join.md` (nuevo)
  - `_DevLog/_index.md`
  - `02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:** ninguna de fondo — los tres puntos (LEFT JOIN, KPI-15..18,
  convención) fueron decididos por el humano antes de tocar archivos. El agente solo redactó los SQL
  de los nuevos KPIs siguiendo el patrón de los existentes y el contrato de Marina.
- **Correcciones manuales:** revisión línea por línea del diff por Manuel antes del commit; sin cambios requeridos.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [ ] Tests agregados/actualizados (N/A — documentación de diseño; `pytest tests/` verificado en verde; el test de US-211a no se tocó)
- [x] DevLog enlaza a los IDs afectados
- [x] `python _Meta/scripts/vault_lint.py .` en verde

## Bloqueantes

- Ninguno.

## Próximos pasos

- Commit + push de la rama `feat/manuel-serrania-kpis-db03-ratificacion-join` (lo hace Manuel).
- Abrir PR → 1 aprobación del PM (compuerta única, DEC-003).
- US-202 (S3, arranca 17-ago): implementar la convención de capa semántica sobre los datos de Superset.
- Seguir a Marina en US-212 (construcción DB-03/DB-04) y a Monserrat en US-211b para que usen la convención.
