---
project: "FARO"
date: "2026-08-14"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "3h"
touches: ["US-313", "REQ-003", "TEST-006", "DOC-PUBLICACION-GOLD", "DEC-005", "MOC-MLMODELS"]
tags: [devlog, celula-3, ml, gold, batch]
---

# DevLog — 2026-08-14 — Publicación de predicciones y recomendaciones a Gold (US-313)

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Job batch de US-313: escribe `gold.predicciones` y `gold.recomendaciones`, las tablas que alimentan
DB-06, DB-09 y los endpoints de inferencia de la Célula 4.

- `src/modelos/publicar_gold.py` — contratos Pydantic de ambas tablas, catálogo prescriptivo,
  derivación de prioridad, DDL y escritura **idempotente por UPSERT**.
- `tests/test_publicar_gold.py` — 18 casos ([[vault/15_ML_Models/Publicacion_Gold|TEST-006]]).
- [[vault/15_ML_Models/Publicacion_Gold]] — documento del job, en `in_review`.

Se adelanta: US-313 es de S5 y estamos en S2. Se pudo porque **DEC-005/006 cerró la ambigüedad del
contrato** y porque ya existe `docker-compose.yml` con Postgres.

### Verificación contra Postgres real

No sólo con SQLite: se levantó el `docker-compose.yml` del equipo y se corrió el job **dos veces**.

```
gold.predicciones: 80 filas publicadas (upsert idempotente)   ← corrida 1
gold.predicciones: 80 filas publicadas (upsert idempotente)   ← corrida 2

SELECT COUNT(*), COUNT(DISTINCT cct) FROM gold.predicciones;  →  80 | 80
```

El esquema quedó con la PK compuesta `(cct, id_ciclo, modelo)` y `probabilidad` nullable. El
contenedor se bajó al terminar.

### Decisiones

**UPSERT en vez de borrar la partición.** El job es idempotente sin ejecutar `DELETE` ni `TRUNCATE`:
tras reentrenar, la corrida siguiente actualiza `valor`, `indice_riesgo` y `mlflow_run_id` en su
sitio. El código es dialecto-aware (PostgreSQL y SQLite), así que las pruebas ejercitan la misma
ruta que corre en producción.

**No se publica `gold.recomendaciones`.** `driver_dominante` es salida de ML-02 (US-302, Andrés) y
no existe todavía. `construir_recomendaciones()` lo **recibe como argumento en vez de calcularlo**:
cuando ML-02 aterrice es conectar su salida. Antes de inventar un driver, no se publica la fila —
una recomendación prescriptiva con driver inventado es peor que ninguna, porque es justo el dato
con el que alguien asignaría presupuesto.

**El catálogo prescriptivo se reutilizó, no se inventó.** Es literalmente el que la Célula 4 ya usa
en `src/api/mock_data.py`. Hoy queda duplicado en dos módulos, así que se añadió
`test_catalogo_coincide_con_el_de_la_api`, que falla si divergen.

**La prioridad no introduce umbrales nuevos:** reutiliza las anclas ya ratificadas de
`DOC-INDICE-RIESGO` (0.60 confirmado por Manuel en el PR #27, 0.30 de matrícula estable).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `src/modelos/publicar_gold.py`, `tests/test_publicar_gold.py`,
  `vault/15_ML_Models/Publicacion_Gold.md`, `vault/15_ML_Models/_index.md`,
  `vault/06_Quality_Testing/Automated/_index.md`
- **Decisiones autónomas del agente:**
  - UPSERT dialecto-aware en lugar de borrar-e-insertar, para no ejecutar `DELETE` y poder probar
    con SQLite la misma ruta que corre en Postgres.
  - Recibir el driver dominante como argumento en vez de inventarlo o dejar la función a medias.
  - Reutilizar el catálogo de la C4 y vigilarlo con una prueba anti-deriva.
  - Derivar la prioridad de las anclas ya ratificadas en vez de proponer umbrales nuevos.
  - Validar cada fila construida contra su contrato Pydantic antes de escribir.
- **Correcciones manuales:** revisión línea por línea. Ruff señaló un import sin usar
  (`COLUMNA_TARGET`) y una variable desempacada sin usar (`tabla_reco`); ambos corregidos. Se
  verificó a mano contra Postgres que la idempotencia fuera real y no sólo un supuesto de las
  pruebas.
- **Prompt inicial:** validar el repositorio y avanzar con US-313.

## Higiene del vault

`vault_lint` marcó un ID duplicado: apareció `vault/15_ML_Models/ML01_Entrenamiento 2.md`, copia local
**no versionada** y byte a byte idéntica al original (duplicación típica de Finder/iCloud). Se
eliminó; no era trabajo de nadie.

## Seguridad / calidad

- [x] Sin secretos hardcodeados — la URL de conexión sale de `DATABASE_URL` o `--url`
- [x] Tests agregados (TEST-006) — 18 casos; suite completa **83 passed, 4 skipped**
- [x] DevLog enlaza a los IDs afectados
- [x] `ruff check` limpio en los archivos propios
- [x] `vault_lint.py` ✅ · `validate_pm_dashboard.py` ✅
- [x] Sin `DELETE`, `UPDATE` ni `DROP` sueltos: sólo `INSERT … ON CONFLICT DO UPDATE` sobre la PK
- [x] Sin datos reales: se publica desde el fixture sintético

## Bloqueantes

- **ML-02** (US-302, Andrés): sin él, `gold.recomendaciones` no se puede poblar.
- **`gold.features_escuela`** (US-104, Diana, vence **23 ago**): las predicciones publicadas salen
  del fixture sintético.

## Riesgos abiertos

- **`Data_Model.md` línea 255** conserva la redacción anterior a DEC-005: dice que `indice_riesgo`
  vive en la columna `valor`, lo que contradice el §4.5 nuevo, donde ya tiene columna propia. Es de
  la Célula 1.
- **Evidencia desactualizada de US-311** en `Execution_Status`: sigue diciendo "falta el modelo
  entrenado + MAE/RMSE + MLflow" con fecha del 11 de agosto, anterior al merge del PR #28.
- **Catálogo prescriptivo duplicado** entre `src/modelos` y `src/api/mock_data.py`.
- Siguen abiertos: la duplicación de partición temporal (PR #8 vs #12) y la divergencia de
  cobertura parcial con ADR-003.

## Próximos pasos

- US-312: la evaluación es lo único que queda de mis tres historias sin arrancar.
- Conectar ML-02 a `construir_recomendaciones()` cuando Andrés lo entregue.
- Re-ejecutar todo el pipeline con features reales tras US-104.
