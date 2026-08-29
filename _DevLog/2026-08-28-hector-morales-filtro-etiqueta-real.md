---
project: "FARO"
date: "2026-08-28"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["BUG-016", "BUG-018", "BUG-020", "US-302", "US-313", "REQ-003", "TEST-006"]
tags: [devlog, celula-3, ml, bug, revision]
---

# DevLog — 2026-08-28 — La etiqueta real manda; revisión de BUG-018

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Se mergearon #111 (mío), #113 (`driver_dominante` real de C1) y #115. Andrés pidió revisión de #116
por paridad con el patrón de ML-01.

## Un hueco que abrió el merge de #113

Mi `filtrar_con_driver_observado()` apartaba las filas mirando si **el valor** del driver era no
nulo. C1 elige driver dominante con una regla más estricta: valor no nulo **y** `dN_cobertura = 'OK'`.

Una fila con dato pero cobertura `SIN_DATO` tiene `driver_dominante` en NULL, **sobrevivía a mi
filtro** y moría después en `validar_target_ml02` con "contiene etiquetas nulas". En el fixture las
dos condiciones coinciden siempre, así que ninguna prueba lo veía; pero el SQL de C1 contempla esa
divergencia explícitamente —por algo la comprueba—, y el Gold real es quien decide.

El arreglo no es replicar la lógica de cobertura de C1, que sería duplicar una regla ajena que puede
cambiar. Es más simple: **cuando la columna real existe, ella es la autoridad**, y basta mirar dónde
quedó NULL. Sin ella —fixtures, o Gold anterior a US-302— se cae al criterio del proxy.

Inferir lo que otro ya calculó fue el error de origen.

## Revisión de #116 (Andrés)

**El arreglo es correcto y es un port fiel del patrón de ML-01.** Verifiqué la cadena completa
combinando su rama con la mía, sobre el target **real**:

```
apartadas por etiqueta nula: 12
ML-01 excluyó: ('d5_agua', 'd6_aire')
ML-02 excluyó: ('d5_agua', 'd6_aire')  (target: driver_dominante)
F1 0.633 · 78 recomendaciones de 80 predicciones
```

Cubrió además `calcular_shap_kernel` con `feature_names_in_`, que yo no había mencionado y hacía
falta.

**Lo que encontré vale la pena decirlo:** él reporta "454 aprobadas, 51 omitidas"; en mi ambiente su
misma rama da **500 aprobadas, 5 omitidas**. Las 46 de diferencia son pruebas que su ambiente omite
por dependencias ausentes — y **entre ellas está la de SHAP**, justo código que él tocó. Su cambio es
correcto, pero su propia corrida no lo comprobó. Aquí sí, y pasa.

Dos diferencias menores con ML-01, ninguna bloqueante:

1. **ML-02 no imprime nada.** ML-01 avisa en consola qué drivers quedaron fuera, global y por
   ventana. ML-02 lo guarda en el resultado pero no lo dice. Es justo lo que hizo diagnosticable
   BUG-015: sin ese aviso, un F1 bajo se ve como un modelo malo y no como dos drivers faltantes.
2. **`excluidos_por_ventana` es `None` por defecto**, no `{}`. Un consumidor que haga `in` sobre él
   revienta con `TypeError`. En ML-01 quedó como `field(default_factory=dict)` tras la revisión de
   Edgar.

## BUG-020 — la URL pública sirve, los datos no

Al reanudar la verificación E2E, que llevaba semanas bloqueada por BUG-008: ese sí quedó arreglado
—18 rutas vivas— pero **toda ruta que toca base de datos responde 500**. Con token, sin token o con
token basura, siempre 500 y nunca 401, así que revienta antes de validar auth. `/health` responde 200.

Es `critical`: sin esto no hay demo E2E ni el punto de rúbrica de URL pública. Los logs de Cloud Run
son de C4/C5.

## Verificación

Suite **500 passed, 5 skipped**. Ruff limpio en `src/modelos/` y en la prueba tocada. `vault_lint`
limpio. **2 pruebas nuevas**: la divergencia etiqueta-real vs valor observado, y el respaldo de que
sin la columna real se sigue cayendo al proxy.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/publicar_gold.py`, `tests/test_publicar_gold.py`,
  `06_Quality_Testing/Bug_Register.md`, `02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:**
  - Usar la columna real como autoridad en vez de replicar la regla de cobertura de C1, que es suya
    y puede cambiar.
  - Correr la rama de Andrés en mi ambiente antes de opinar, en vez de confiar en su conteo.
  - Verificar la cadena completa combinando ambas ramas, para poder decirle a Diana si sirve.
- **Correcciones manuales:** revisión línea por línea.

## Pendiente

1. **BUG-020** con C4/C5. Es lo que más pesa para el 9 de septiembre.
2. **ADR-007** sin ratificar: el `indice_riesgo` del grano escuela sigue sin significar nada.
3. Mergear #116 y que Diana reanude el E2E con Gold real.
