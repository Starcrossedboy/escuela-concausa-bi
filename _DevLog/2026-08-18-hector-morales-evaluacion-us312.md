---
project: "FARO"
date: "2026-08-18"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "2h"
touches: ["US-312", "REQ-003", "TEST-007", "DOC-EVALUACION-MODELOS", "MOC-06-AUTO"]
tags: [devlog, celula-3, ml, qa, metricas]
---

# DevLog — 2026-08-18 — Evaluación comparativa de modelos y análisis de error (US-312)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

US-312: tabla comparativa, curvas y análisis de error por entidad, en `06_Quality_Testing/`.

- `src/modelos/evaluar.py` — evalúa ML-01 y ML-02 sobre la misma partición temporal y **genera el
  documento del vault desde el código**.
- `tests/test_evaluar.py` — 13 casos ([[06_Quality_Testing/Automated/Evaluacion_Modelos|TEST-007]]).
- [[06_Quality_Testing/Automated/Evaluacion_Modelos]] — reporte generado, en `in_review`.

Se adelanta: US-312 es de S5 y estamos en S2/S3.

### La decisión de fondo

AC-003.2 pide métricas *"documentadas y **reproducibles**"*. Un documento escrito a mano cumple lo
primero y falla lo segundo en cuanto alguien reentrena. Por eso el reporte **se genera con
`python -m src.modelos.evaluar` y lleva un aviso de no editarlo a mano**, y hay una prueba que
verifica que regenerarlo produce el mismo archivo. Así las cifras del vault no pueden divergir de
las del pipeline.

### Las "curvas"

La historia pide curvas; se emiten como **tablas de datos por ventana**, no como imágenes:

- Una tabla es diffable — en un PR se ve qué métrica cambió y cuánto; un PNG sólo se ve distinto.
- El vault versiona texto; meter binarios regenerables contradice su higiene.
- La misma serie alimenta después los tableros de la Célula 2, que es donde la curva se dibuja.

`--figuras` renderiza los PNG en local para la demo, sin versionarlos.

### Resultados (datos sintéticos)

| Modelo | Métrica | Valor | Baseline | Mejora |
|---|---|---|---|---|
| ML-01 · regresión | MAE | 0.0141 ± 0.0012 | 0.0291 | +51.6 % |
| ML-02 · clasificación | F1 macro | 0.7945 ± 0.0241 | 0.0699 | ×10.6 |

Dos análisis que el reporte agrega y que no existían:

- **Error por entidad:** Jalisco (14) es la peor con MAE 0.0200, **+27.5 % sobre el global**. Un
  error global aceptable puede esconder una entidad donde el modelo falla, y las recomendaciones se
  emiten escuela por escuela.
- **Error contra cobertura de drivers:** responde si predecimos peor donde hay menos datos. Sobre el
  fixture no hay degradación clara, pero el análisis queda listo para los datos reales, que es
  cuando importa.

### Salvedades que el reporte declara explícitamente

- **ML-02 entrena contra `driver_dominante_proxy`**, no contra una etiqueta observada. Su F1 mide
  recuperar una etiqueta derivada de los propios drivers; la cifra sólo será significativa cuando
  Gold publique la etiqueta real.
- **ML-03 no existe** (US-321, Estefany). **AC-003.2 no queda cerrado** hasta que reporte Silhouette.
- **Los umbrales de ML-01 no son comparables**: `ML_Strategy` §5 los fija en alumnos absolutos
  (`MAE < 15`) mientras el contrato define el objetivo como variación.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `src/modelos/evaluar.py`, `tests/test_evaluar.py`,
  `06_Quality_Testing/Automated/Evaluacion_Modelos.md` (generado),
  `06_Quality_Testing/Automated/_index.md`
- **Decisiones autónomas del agente:**
  - Generar el documento del vault desde el código en vez de redactarlo, para que AC-003.2 sea
    verificable y no una promesa.
  - Emitir las curvas como tablas y dejar los PNG detrás de un flag sin versionar.
  - Agregar el cruce error × completitud de drivers, que la historia no pedía pero responde una
    pregunta que el PRD sí se hace.
  - Reportar `mejora sobre baseline` como única columna comparable entre modelos, porque MAE y F1
    no se comparan entre sí.
- **Correcciones manuales:** revisión línea por línea. Ruff detectó un import sin usar
  (`COLUMNA_CICLO`) y desorden de imports en las pruebas; ambos corregidos. Se verificó a mano que
  regenerar el reporte no produjera diff en disco, además de la prueba unitaria.
- **Prompt inicial:** avanzar con US-312 tras el merge del PR #41.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Pruebas agregadas (TEST-007) — 13 casos; suite completa **155 passed, 4 skipped**
- [x] `ruff` limpio en los archivos propios
- [x] `vault_lint.py` ✅ · reporte registrado en el `_index.md` de su carpeta
- [x] Sin datos reales: se evalúa contra el fixture sintético, y el reporte lo advierte arriba

## Bloqueantes y estado desactualizado

- **US-311 figura como `done`** en [[12_Roadmap_Sprints/Execution_Status]] citando el registro en
  MLflow, pero ese registro **no funciona**: `docker/mlflow.Dockerfile` sigue en `mlflow==2.8.0`
  contra el cliente `3.15.1`. Las métricas se registran, el modelo no. **AC-003.4 sin cumplir.**
- **US-313 no está registrada** y figura como `planned`, cuando se mergeó en el PR #41.
- **`gold.features_escuela`** (US-104, Diana): venció el 23 de agosto.
- **Formato 911 con un solo ciclo disponible**: sin dos ciclos no hay variación que predecir. Sigue
  sin dueño y es el riesgo mayor del proyecto.

## Próximos pasos

- Conectar ML-02 a `construir_recomendaciones()` para cerrar `gold.recomendaciones`.
- Consolidar el catálogo de recomendaciones, hoy en tres módulos.
- Regenerar este reporte en cuanto lleguen features reales.
