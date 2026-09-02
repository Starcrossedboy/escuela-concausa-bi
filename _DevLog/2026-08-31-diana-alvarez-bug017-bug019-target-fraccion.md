---
project: "FARO"
date: "2026-08-31"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "claude-sonnet-5"
session_duration: "~1h"
touches: ["US-104", "US-311", "US-313", "REQ-003"]
tags: [devlog, dbt, gold, bug017, bug019, adr-007, target]
---

# BUG-017/BUG-019 — `target_variacion_matricula` pasa a fracción (ADR-007)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

[[03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula|ADR-007]] se ratificó el
2026-08-29 (fracción, no alumnos absolutos), pero el código de `features_escuela.sql` seguía sin
actualizarse — confirmado directo contra el SQL real antes de tocar nada. BUG-017 y BUG-019
seguían `open` en el registro.

Cambio en la CTE `base` de `dbt/models/gold/features_escuela.sql`: de
`matricula_total - matricula_ciclo_anterior` (alumnos absolutos) a
`(matricula_total::double precision / matricula_ciclo_anterior) - 1.0` (fracción), mismo patrón
que ya usa `src/modelos/target_hibrido.py::variacion_desde_serie` (C3). Dos detalles que exige
el ADR y que no son solo "quitar el `-`":

- **Cast a `double precision` antes de dividir.** `matricula_total`/`matricula_ciclo_anterior`
  son `integer` (`silver/matricula.sql`) — sin el cast, `300/285` trunca a `1` en vez de dar
  `1.0526...`, y `(300/285) - 1.0` da `0.0` silenciosamente en vez de `0.0526`. Verificado a mano
  con una consulta real en Postgres antes de escribir el fix.
- **`matricula_ciclo_anterior = 0` se rechaza explícito**, sin `nullif`. El ADR es explícito:
  "no un `NULLIF` silencioso que produzca `SIN_DATO` invisible" — la división nativa de Postgres
  truena (`ERROR: division by zero`) si aparece, igual que `variacion_desde_serie` hace
  `raise ValueError`. Verificado real en Postgres que el `ERROR` se dispara con un `0` de prueba
  y que la fracción sale correcta sin él.

Se declaró la unidad explícitamente por primera vez en `src/modelos/contrato.py` y en
`Data_Model.md` §5.3 (ofrecido por Diana, ya escrito en el ADR).

## Cómo se probó

$ dbt run --select features_escuela+ --full-refresh

Done. (sin error de división por cero — ninguna escuela real tiene matrícula previa 0)

$ dbt test --select features_escuela

PASS=18 ERROR=1 (el ERROR es el hueco ya conocido de DS-07/CONEVAL contra dim_municipio,
documentado desde el 29-ago en US-325, no relacionado con este cambio)
incluye PASS: features_escuela_target_variacion_escala (test nuevo)
incluye PASS: not_null_features_escuela_target_variacion_matricula

$ pytest

643 passed, 5 skipped


Test nuevo: `dbt/tests/features_escuela_target_variacion_escala.sql` — falla si la mediana de
`|target_variacion_matricula|` supera 1.0, mismo umbral que `MEDIANA_MAXIMA_FRACCION` en
`src/modelos/riesgo.py::verificar_escala_variacion()`. Protege en Gold, antes de que el dato
llegue a ML, contra una regresión futura de vuelta a alumnos absolutos.

## Archivos tocados

- `dbt/models/gold/features_escuela.sql`
- `dbt/tests/features_escuela_target_variacion_escala.sql` (nuevo)
- `src/modelos/contrato.py`
- `03_Architecture/Data_Model.md`
- `06_Quality_Testing/Bug_Register.md` (BUG-017, BUG-019 → fixed)

## Pendiente

- **C3 (Andrés González):** regenerar las 45 249 filas de `gold.predicciones` (quedaron
  saturadas con la unidad vieja) y reentrenar ML-01 — el MAE deja de leerse en alumnos y pasa a
  fracción.
- `src/modelos/riesgo.py::verificar_escala_variacion()` cita a BUG-017 en su docstring como causa
  conocida — vale que C3 lo actualice cuando toque ese archivo, no es bloqueante.
