---
project: "FARO"
date: "2026-08-24"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "2h"
touches: ["US-311", "US-313", "BUG-010", "BUG-008", "REQ-003", "REQ-004", "DOC-GUION-E2E-V4"]
tags: [devlog, celula-3, e2e, ensayo]
---

# DevLog — 2026-08-24 — Guion de la verificación #4 del ensayo E2E y BUG-010

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Faltan **4 días** para el ensayo E2E del 28–29. Al leer sus siete verificaciones en el PLAN_MAESTRO,
la **#4 es de la Célula 3**: *«≥1 modelo sirviendo por API (ML-01) — `/predicciones` devuelve valor
(real o simulado, marcado)»*.

Un detalle del criterio que cambia el análisis: **admite datos simulados si están marcados**. O sea
que la falta de datos reales del Formato 911 —el bloqueo que veníamos arrastrando— **no impide pasar
esta verificación**. Lo que la impide es otra cosa.

## Hallazgo: BUG-010

`src/api/v1/predicciones.py` **sigue leyendo `src/api/mock_data.py`**, no `gold.predicciones`. Su
propio docstring lo anticipaba: *"al integrar MLflow (Célula 3) es un swap"*. Ese swap no se hizo.

`repositorio_gold.py` (US-411, Karla) sí lee Gold, pero cubre `/escuelas`, `/municipios` y `/kpis`;
**`/predicciones` quedó fuera**.

Consecuencia: hoy la verificación #4 **pasaría de forma engañosa**. El endpoint devolvería un valor
—cumpliendo la letra del criterio— pero sería un número escrito a mano, no la predicción de ML-01.

### Lo que el swap necesita, y un hueco que aparece al mirarlo

`gold.predicciones` y `gold.recomendaciones` ya están pobladas y verificadas. El mapeo a
`PrediccionOut` es directo salvo por un campo:

| Campo | Origen | ¿Existe? |
|---|---|---|
| `cct`, `id_ciclo`, `indice_riesgo`, `mlflow_run_id` | `gold.predicciones` | ✅ |
| `driver_dominante`, `recomendacion` | `gold.recomendaciones` | ✅ |
| **`cluster`** | **ML-03 (US-321, Estefany)** | ❌ **no existe** |

**`PrediccionOut.cluster` es un `StrictInt` obligatorio sin productor.** Mientras ML-03 no exista, el
swap no puede completar la respuesta sin inventar el valor. Se deja explícito en el registro que la
salida correcta es hacerlo opcional o declararlo ausente — **nunca rellenarlo con un entero
arbitrario**, por la misma regla de `SIN_DATO` que rige el resto del proyecto.

También queda anotado que el swap debe filtrar `grano = 'escuela'`: desde DEC-010 la tabla admite
filas a `municipio × nivel` que no corresponden a un CCT.

## Entregado

- **BUG-010** en [[06_Quality_Testing/Bug_Register]], severidad `high`, owner Célula 4, con el mapeo
  completo y el hueco de `cluster`.
- [[06_Quality_Testing/Guion_E2E_Verificacion_4]] — guion ejecutable del tramo de la C3.

### Por qué un guion y no sólo un aviso

El ensayo es en vivo y con criterio go/no-go. El tramo de la C3 funciona, pero **su ejecución tiene
tres trampas de ambiente que ya nos costaron tiempo** en sesiones previas:

1. `POSTGRES_HOST=db` es el hostname interno de Docker; desde el host hay que usar `localhost`. Lo
   mismo con `MLFLOW_TRACKING_URI`, que apunta a `http://mlflow:5000` mientras el servicio se publica
   en `localhost:5001`.
2. La app real publica su OpenAPI en `/api/v1/openapi.json`, **no en la raíz**: una verificación que
   consulte `/docs` falla aunque todo esté bien.
3. `docker compose up -d api` usa la imagen cacheada; hay que agregar `--build`.

Redescubrirlas en vivo, frente al profesor, sería el peor momento. El guion las deja escritas junto
a los comandos exactos.

El documento incluye además un **plan B**: si BUG-008 y BUG-010 no se resuelven, el tramo se puede
demostrar sin la API mostrando las dos tablas de Gold pobladas por el modelo. No cumple la
verificación como está redactada, pero evidencia que el modelo produce y publica — **conviene
acordarlo con el PO antes del 28, no durante**.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `06_Quality_Testing/Guion_E2E_Verificacion_4.md`,
  `06_Quality_Testing/Bug_Register.md`, `06_Quality_Testing/_index.md`
- **Decisiones autónomas del agente:**
  - Leer el criterio literal de la verificación #4 antes de asumir que los datos reales la
    bloqueaban. Resultó que no: el criterio admite simulado marcado.
  - Registrar el hallazgo como bug en vez de sólo mencionarlo, para que siga el mismo canal que
    BUG-005/006/007, que sí se movieron.
  - No implementar el swap: `src/api/` es de la Célula 4 y está fuera de mi alcance.
  - Documentar el plan B, porque un ensayo con go/no-go necesita una salida acordada de antemano.
- **Correcciones manuales:** revisión línea por línea de los comandos del guion contra lo ejecutado
  en sesiones previas, para no publicar un procedimiento que no se haya corrido de verdad.

## Seguridad / calidad

- [x] Sin secretos: el guion usa `<POSTGRES_PASSWORD>` como marcador, no un valor
- [x] `vault_lint` ✅ · `validate_pm_dashboard` ✅ · suite **298 passed, 4 skipped** sobre `main`
      (las 310 del PR #83 incluyen sus 12 pruebas del grano dual, aún sin mergear)
- [x] Sólo documentación de QA; ningún cambio de código

## Estado de mis historias

Las tres siguen en `in_progress` y **ninguna está bloqueada por trabajo mío**:

| Historia | Falta | De quién depende |
|---|---|---|
| US-311 | datos reales · registro en MLflow | C1 · C5 (BLOCK-001) |
| US-312 | ML-03 para cerrar AC-003.2 | Estefany (US-321) |
| US-313 | datos reales · contrato de la API | C1 · Christian (DEC-010) |

## Pendiente

- **BUG-008** sigue `open` con el `CMD` intacto. Cuatro días para el ensayo.
- **BUG-010**, nuevo, mismo horizonte.
- **PR #83** (grano dual DEC-010) sigue esperando revisión.
