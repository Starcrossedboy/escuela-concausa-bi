---
project: "FARO"
date: "2026-08-29"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["US-312", "US-321", "AC-003.2", "REQ-003", "TEST-007"]
tags: [devlog, celula-3, ml, evaluacion]
---

# DevLog — 2026-08-29 — ML-03 entra a la evaluación: AC-003.2 queda cubierto

→ [[_DevLog/_index|Volver al índice]]

## Por qué hoy

Andrés mergeó #133 y `src/modelos/entrenar_ml03.py` ya existe. Ése era **el único bloqueo de
US-312**: AC-003.2 exige que *cada* modelo reporte su métrica, y ML-03 no existía.

Al ir a integrarlo apareció que `evaluar.py` seguía publicando que ML-03 está *"aún sin
implementar"*. El artefacto del vault afirmaba algo que ya era falso — la misma familia de defecto
que Edgar me señaló ayer en §5.

## Lo que quedó

**ML-03 en la tabla comparativa y en la curva por ventana.** El parámetro es opcional, así que quien
evalúe sólo los supervisados no se rompe.

**ML-03 no finge una mejora sobre baseline.** Es no supervisado: su Silhouette mide separación de
grupos, no ventaja sobre un modelo tonto. Poner `0` lo haría parecer un modelo que no aporta, que es
una afirmación **distinta** a "no aplica". Va `NaN`, y `supera_baseline` devuelve `None` en vez de
`False`.

**La exclusión de ML-03 es parte del resultado, no limpieza previa.** Entrena sobre 107 de 400 filas:
293 quedan fuera porque KMeans no admite ausencias y **no se imputan**. Los grupos describen a las
escuelas con datos completos, no al universo, y el reporte lo dice.

## Lo que encontré y no venía en el encargo

El reporte enunciaba los umbrales en un párrafo y las cifras en otro, **sin decir nunca si se
cumplen**. Con ML-03 eso dejó de ser aceptable:

| modelo | metrica | valor | umbral | cumple |
|---|---|---|---|---|
| ML-01 | MAE | 0.0141 | < 0.03 | ✅ sí |
| ML-01 | RMSE | 0.0177 | < 0.05 | ✅ sí |
| ML-02 | F1 macro | 0.7945 | ≥ 0.6 | ✅ sí |
| ML-03 | Silhouette | 0.1086 | ≥ 0.3 | ❌ **no** |

**ML-03 no alcanza su umbral sobre el fixture.** Está evaluado y reporta su métrica —que es lo que
AC-003.2 pide— pero 0.1086 no llega a 0.30, y ahora el reporte lo afirma con un aviso, no lo deja en
una celda. Un modelo que no alcanza su umbral no puede presentarse como si lo hiciera.

Es un dato para Estefany, no un reproche: con 107 filas sintéticas y `k=2` el resultado no dice gran
cosa; hay que volver a mirarlo contra los datos reales de US-104.

## Verificación

Suite **595 passed, 5 skipped**. **6 pruebas nuevas.** La guarda de sincronía del reporte ahora
incluye ML-03, así que olvidar `python -m src.modelos.evaluar` sigue rompiendo el CI. Ruff limpio en
`src/modelos/`, `vault_lint` limpio.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/evaluar.py`, `tests/test_evaluar.py`,
  `06_Quality_Testing/Automated/Evaluacion_Modelos.md` (regenerado),
  `06_Quality_Testing/Automated/_index.md`, `02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:**
  - `NaN` y no `0` para el baseline de ML-03; y `supera_baseline` devuelve `None`.
  - Afirmar el cumplimiento de cada umbral en el reporte, en vez de enunciarlos por separado.
  - Publicar sólo el `k` elegido en la curva: `metricas` trae toda la búsqueda.
  - No editar `15_ML_Models/_index.md`, que es de Andrés (ver pendientes).
- **Correcciones manuales:** revisión línea por línea.

## Pendientes

1. **`15_ML_Models/_index.md` marca ML-01 y ML-03 como `pendiente`** y los dos ya entrenan. Es
   archivo de Andrés; se lo paso, no lo edito.
2. **ADR-007 sigue `proposed`**, sin registro en el `Decision_Log`.
3. **BUG-020** sin moverse: `/health` 200, `/predicciones` 500. Es la casilla 6 del ensayo de hoy.
4. **D5 sigue bloqueado**: #107 entró sin lat/lon ni serie de almacenamiento.
