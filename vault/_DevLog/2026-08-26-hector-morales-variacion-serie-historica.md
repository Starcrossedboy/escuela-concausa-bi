---
project: "FARO"
date: "2026-08-26"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "3h"
touches: ["US-311", "US-313", "DEC-007", "RISK-007", "TEST-009", "BUG-008", "BUG-010", "SPRINT-HECTOR-RAFAEL-MORALES-MA"]
tags: [devlog, celula-3, ml, dec-007]
---

# DevLog — 2026-08-26 — Variación desde la serie histórica: última pieza de DEC-007

→ [[vault/_DevLog/_index|Volver al índice]]

## Lo que encontré al validar

Tres cosas dirigidas a mí que no había visto:

1. **La serie que esperaba `unir_target()` ya existe.** Diana lo anotó en su DevLog del 23:
   `gold.matricula_municipio_nivel` está mergeada, alimentada por `silver.matricula_historica` y
   `src/ingesta/extractor_formato911_historico.py`. **La cadena multi-ciclo del 911 está
   construida** — RISK-007 quedó mitigado a nivel de datos.
2. **BUG-010 está cerrado** (PR #95, Juan Macías). `/predicciones/*` ya lee Gold vía
   `RepositorioModelos`, y adoptó la recomendación de dejar `PrediccionOut.cluster` opcional en vez
   de rellenarlo con un entero arbitrario.
3. **Edgar señaló que mi tabla de seguimiento nunca se había actualizado**, con cuatro PRs
   mergeados. Tenía razón.

## Lo entregado

### `variacion_desde_serie()` — la pieza que faltaba

`gold.matricula_municipio_nivel` publica **matrícula absoluta** por `municipio × nivel × ciclo`,
pero el objetivo de ML-01 es la **variación proporcional** contra el ciclo anterior. Esa conversión
no existía en ningún lado: era el último eslabón de DEC-007.

Diana ya había hecho su parte del encaje —alias `ciclo → id_ciclo` y `nivel` en mayúsculas para
coincidir con `dim_escuela`—, citando `target_hibrido.py` en sus comentarios.

**Dos reglas que evitan contaminar el objetivo:**

- **Sólo se compara contra el ciclo inmediatamente anterior.** Si un grupo aparece en 2019-2020 y en
  2021-2022 pero no en 2020-2021, comparar los extremos mediría dos años como si fuera uno. Esa
  fila no se emite.
- **Un grupo que aparece o desaparece no genera variación.** Un `municipio × nivel` que deja de
  reportarse **no cayó −100 %**. Publicar esa caída enseñaría al modelo a predecir bajas
  administrativas en vez de pérdida de matrícula — el mismo riesgo que señalé a Diana el 21 de
  agosto para el grano escuela, que aplica igual aquí.

Se rechaza además una matrícula previa de cero, que daría un infinito, y la serie con duplicados por
grupo y ciclo.

**9 pruebas nuevas** (TEST-009 pasa de 18 a 27 casos), incluida una de circuito completo:
serie histórica → variación → `unir_target()` → partición temporal.

### Tabla de seguimiento actualizada

Con el respaldo de cada porcentaje, qué está mergeado y qué falta, y de quién depende cada bloqueo.
No estaba actualizada desde el inicio del proyecto; Edgar lo pidió explícitamente.

### Guion del ensayo, con una trampa nueva

`/api/v1/predicciones/{cct}` usa `CICLO_DEFAULT = "2024-2025"`, pero `publicar_gold` escribe el
ciclo más reciente del fixture: **`2023-2024`**. **Sin `?ciclo=2023-2024` explícito el endpoint
responde 404 aunque el dato esté ahí.**

No es un defecto del código de Juan —con datos reales del 911 el default sí coincide, porque su
ciclo más nuevo es 2024-2025—, pero en el ensayo del 28 haría fallar la verificación #4 por una
razón trivial. Queda documentado con el `curl` exacto.

También se actualizó el estado de los prerrequisitos: **queda un solo bloqueo, BUG-008.**

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/target_hibrido.py`, `tests/test_target_hibrido.py`,
  `vault/06_Quality_Testing/Guion_E2E_Verificacion_4.md`,
  `vault/12_Roadmap_Sprints/Sprints/3-hector-rafael-morales-marban.md`
- **Decisiones autónomas del agente:**
  - Exigir que el ciclo previo sea el **inmediatamente anterior**, no simplemente el anterior
    disponible: un hueco de ciclos produciría una variación de dos años disfrazada de una.
  - Omitir los grupos sin ciclo previo en vez de emitirlos con variación cero o nula.
  - Rechazar matrícula previa cero en vez de dejar pasar un infinito al entrenamiento.
  - Verificar el estado real de BUG-010 leyendo el código, no sólo el registro: el swap resultó
    completo para `/predicciones` y `/batch`, y `/explicacion` sigue en mock por una razón
    documentada (SHAP no tiene fuente en Gold).
- **Correcciones manuales:** revisión línea por línea. Una sospecha propia resultó infundada y vale
  anotarla: parecía que el endpoint validaba el CCT contra la lista simulada, pero `_buscar_escuela`
  sólo se usa en `/explicacion`; `prediccion()` consulta Gold y devuelve 404 únicamente si no hay
  fila. Se comprobó leyendo el cuerpo de la función antes de reportarlo.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Suite completa **369 passed, 5 skipped** · `ruff` limpio en archivos propios · `vault_lint` ✅

## Estado y pendientes

Con esto, **todo el circuito de DEC-007 está construido de punta a punta**: extractor multi-ciclo
(C1) → serie agregada (C1) → variación (C3) → objetivo del agregado → partición temporal →
entrenamiento → publicación a Gold → API.

Lo único que falta para que las métricas dejen de ser sintéticas es **correr dbt con datos cargados**.

- **BUG-008 sigue `open`** desde el 21 de agosto, con el `CMD` intacto. **Es el último bloqueo de la
  verificación #4** y el ensayo es en 2 días.
- AC-003.2 sigue esperando ML-03 (US-321).
- AC-003.4 sigue esperando el `--serve-artifacts` de la Célula 5.
