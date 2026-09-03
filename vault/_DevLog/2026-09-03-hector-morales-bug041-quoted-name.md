---
project: "FARO"
date: "2026-09-03"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1 sesión — aplicar BUG-041 (parche de C5) y corregir un diagnóstico mío equivocado"
touches: ["BUG-041", "BUG-043", "BUG-013", "US-313", "US-311", "REQ-003"]
tags: [devlog, celula-3, ml, gold, bugfix, correccion]
---

# DevLog — 2026-09-03 — BUG-041 aplicado, y la causa raíz que publiqué ayer era falsa

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/06_Quality_Testing/Bug_Register|Bug Register]]
· [[vault/_DevLog/2026-09-02-luis-tellez-bug041-quoted-name-desde-gold|Diagnóstico de Luis]]

## Encargo

Luis Téllez (C5) pidió que C3 aplicara el parche de **BUG-041**: `src/modelos/**` es nuestro verde y
su rama reprobaría `check_ownership` si lo tocara él. Es el único bloqueante de **L1.3**, el paso que
quita el 404 de `/predicciones` en la URL pública y con eso el techo de 6.0 de RISK-001.

## Verifiqué antes de aplicar

Un parche que llega diagnosticado y validado por otro sigue siendo código que firmo yo. Comprobé las
dos afirmaciones por separado, contra el Postgres real:

| Afirmación de C5 | Resultado |
|---|---|
| `pd.read_sql_table` devuelve `quoted_name`, no `str` | ✅ confirmado — y también en **SQLite** |
| sklearn exige `type(x) is str` para poblar `feature_names_in_` | ✅ confirmado en 1.9.0: con `quoted_name` no lo puebla; con `str` puro sí |

Y reproduje el fallo completo, no sólo el mecanismo. Cargué los tres fixtures de Formato 911,
reconstruí Gold (**145 filas, 3 ciclos, D5 100 % `SIN_DATO`**) y corrí `publicar_gold --desde-gold`:

```
ValueError: X has 6 features, but HistGradientBoostingRegressor is expecting 5 features
ML-01 entrenado — MAE 0.0844
```

El mismo error y el mismo MAE que reportó Luis. Con el parche:

```
gold.predicciones     55 filas   ·  gold.recomendaciones  55 filas
ML-01 MAE 0.0844      ·  ML-02 F1 macro 0.6458
```

También las mismas cifras. **US-313 corre contra Gold real.**

## Lo que agregué: que el CI lo cace

El punto ciego que Luis identificó —los fixtures CSV dan `str` puro, así que la suite nunca vio el
defecto— seguía abierto después del parche. Tres pruebas nuevas lo cierran, y **usan SQLite**, que
entrega `quoted_name` igual que Postgres: corren en el CI sin base de datos.

Las validé al revés, que es la única forma de saber que sirven: **revertí el parche y las tres
reprobaron**, incluida la que reproduce el `ValueError` end-to-end. Luego lo restauré y pasaron.

## Corrección: lo que publiqué ayer sobre BUG-013 era falso

Ayer afirmé que `gold.features_escuela` salía con un solo ciclo porque `features_escuela.sql` §42
lee `{{ ref('matricula') }}` en vez de `matricula_historica`, y **le propuse a Diana cambiar ese
`ref`**. Está escrito en el Bug_Register y en la matriz de trazabilidad.

Es falso. Lo que pasó es que cargué **dos** de los **tres** fixtures de Formato 911 en Bronze:
faltaba `bronze_formato911_serie_historica_sample.csv`, el que BUG-026 creó justamente para dar
grano escuela multi-ciclo. Con los tres, Gold sale con 145 filas y 3 ciclos. `features_escuela`
nunca estuvo mal: **le atribuí a un modelo de C1 un defecto que era mío**.

Corregido en los dos artefactos, dejando el error visible en vez de borrarlo: alguien pudo leerlo, y
la propuesta a Diana habría sido trabajo inútil.

La parte útil es por qué me pasó. Reconstruí el pipeline leyendo el DevLog de Marina del 27-ago, que
dice *«cargar DOS fixtures en la MISMA tabla»* — cierto entonces, incompleto después de BUG-026.
**Un runbook que vive en un DevLog no se actualiza cuando cambia el repo.** Eso es exactamente el
costo de **BUG-012**, que sigue abierto, y esta vez lo pagué yo.

## Colisión de IDs: mi BUG-041 pasa a BUG-043

Ayer registré como **BUG-041** el defecto del Registry de MLflow (versiones `READY` sin artefacto).
Al sincronizar hoy, `main` ya traía **BUG-041** (el de Luis) y **BUG-042**. Por **DEC-013** —un ID
queda reservado sólo cuando está en su registro canónico en `main`, y ante colisión gana quien ya
está ahí— mi bug se renumera a **BUG-043**, en el registro, el DevLog de ayer, la matriz, los dos
módulos y las dos pruebas que lo citan. Sin huecos reciclados (regla 3).

**BUG-043 sigue abierto y sigue siendo de C5:** falta `--serve-artifacts` en `docker-compose.yml` y
recrear el experimento. No lo destraba este PR.

## Verificación

- Suite completa: **817 passed, 6 skipped**. **3 pruebas nuevas**, validadas revirtiendo el parche.
- `ruff check src/ tests/` → limpio · `vault_lint.py` → limpio · `check_ownership.py` → ✅
- `--desde-gold` end-to-end contra Postgres real: 55 + 55 filas publicadas.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/entrenar_ml01.py` (4 líneas + comentario),
  `tests/test_entrenar_ml01.py` (3 pruebas), `vault/06_Quality_Testing/Bug_Register.md`,
  `vault/02_Requirements/Traceability_Matrix.md`, `vault/15_ML_Models/ML01_Entrenamiento.md`,
  `vault/_DevLog/2026-09-02-hector-morales-registry-us311.md` y su índice (renumeración a BUG-043).
- **🔴 Fuera de alcance, ejecutado pero NO modificado:** `dbt/**` (C1) y `docker-compose.yml` (C5).
  El `profiles.yml` vive fuera del repositorio.
- **Decisiones autónomas del agente:** verificar el diagnóstico de C5 antes de aplicarlo en vez de
  confiar en él; usar SQLite en las pruebas al confirmar que también da `quoted_name`; validar los
  tests revirtiendo el parche; dejar visible el error de ayer en vez de reescribirlo.
- **No implementado a propósito:** el follow-up defensivo que Luis propone —pasar `drivers_usados`
  explícito a `construir_predicciones` en vez de depender de `feature_names_in_`— toca 6 llamadas en
  4 archivos, incluidos los de Andrés. Va aparte y con su visto bueno, no colado en un fix urgente.

## Pendientes

1. **Follow-up defensivo** (6 sitios con `getattr(modelo, "feature_names_in_", DRIVERS)`): el
   fallback silencioso es lo que convirtió un tipo de columna en un crash. Coordinar con Andrés.
2. **BUG-043 → C5:** `--serve-artifacts` y recrear el experimento de MLflow.
3. **BUG-012 → sigue abierto** y hoy me costó un diagnóstico equivocado. El runbook debería listar
   los **tres** fixtures.
4. **BUG-020** sigue abierto; L1.3 lo destraba parcialmente pero el 500 de la API es de C4.
