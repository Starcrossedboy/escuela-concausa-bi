---
project: "FARO"
date: "2026-08-29"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión única: correcciones a mi reporte del 28-ago y revisión ejecutada del PR #129"
touches: ["US-212", "REQ-001", "REQ-002", "REQ-003", "BUG-015", "BUG-017", "BUG-026", "BUG-027", "ADR-007", "DEC-006", "US-104", "US-113", "US-313", "US-221"]
tags: [devlog, bi, qa, revision, celula-2]
---

# DevLog — 2026-08-29 — Correcciones al reporte del 28-ago y revisión del PR #129

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

Tres respuestas al reporte del 28-ago (Diana, Héctor y el PM) traen una corrección de fondo, una
precisión de causa raíz y dos decisiones de proceso. Esta sesión las aplica y revisa el PR que
desbloquea US-212.

## Corrección: cité el commit equivocado como fix de BUG-015

Escribí que `4f22bd8` (22:45) arreglaba el error de sklearn que Diana dejó abierto. **No es así.**
Héctor lo señaló y el PM lo verificó en el historial: `4f22bd8` fue su primer intento, evaluaba la
cobertura de drivers de forma **global** y no funcionó — Diana volvió a correr después de ese commit
y obtuvo el mismo error. El que sirvió es **`f906a7d` (23:04)**, que la evalúa **por ventana**:
`d6_aire` tenía datos globalmente pero estaba vacío en el tramo de entrenamiento.

Lo que más me importa de esta corrección no es la precisión bibliográfica, es lo que Héctor explicó
mejor que yo: **tal como lo redacté, Diana concluiría que su segundo fallo no debió ocurrir y
acabaría dudando de su ambiente en vez de confiar en él.** Un reporte que hace desconfiar de un
ambiente sano cuesta más que el defecto que reporta. Corregido en el DevLog del 28-ago —como nota
explícita, sin borrar la versión original— y en la matriz.

Donde escribí *"probablemente pasa"* ya hay certeza: Héctor verificó la cadena completa sobre `main`
con el target real, **F1 0.633 y 78 de 80 predicciones con recomendación**.

## Precisión de la causa de BUG-026 (Diana)

Mi encuadre —"dos fixtures y cada uno resuelve la mitad"— sugiere que el histórico era candidato a
tapar el hueco. No lo es, y por una razón más de fondo que el solape: **`silver.matricula` nunca lee
de `bronze.formato911_historico`**; ese camino termina en `gold.matricula_municipio_nivel` (DEC-007)
y no toca el grano escuela. El hueco real es aritmético, en la tabla que sí está en el linaje: 2
ciclos crudos, `con_target` sacrifica el primero como referencia del `LAG`, y `ventanas_posibles()`
exige 3 con target — luego hacen falta **4 crudos**. El solape sigue importando, pero es la
consecuencia (el arreglo aparente falla en silencio), no la causa. Incorporado a la sección de
BUG-026.

## Revisión del PR #129 — ejecutada, no leída

| Qué | Antes | Con PR #129 |
|---|---|---|
| Ciclos crudos en `bronze.formato911_2024_2025` | 2 | **4** |
| Ciclos en `gold.features_escuela` | 1 | **3** (2022-2023 … 2024-2025) |
| CCT que cruzan con `gold.dim_escuela` | — | **60 de 60** |
| `publicar_gold.py --desde-gold` | `ValueError` por 1 ciclo | **entrena ML-01, MAE 12.2252** |

Generador **reproducible** (mismo MD5 al regenerar) y carga **idempotente**. `dbt run --threads 1
--full-refresh`: 22 modelos OK, único fallo `silver.agua_region` por CONAGUA no ingerida — el error
esperado y correcto. La corrida se detiene ahora en la guarda de BUG-017, no por falta de ciclos,
exactamente como Diana reportó. **Aprobado.**

Observación menor, no bloqueante: el panel queda desbalanceado (60 escuelas en 2022-2023, 30 en
2023-2024, 55 en 2024-2025). Con 1 ventana funciona; para 2 o más conviene emparejar la cobertura.

## ADR-007 — de solicitante a ratificadora

Héctor incorporó a la dueña de los tableros a la ratificación (PR #128) y dejó escrito que usar mi
área como argumento para descartar la alternativa B sin sentarme en la mesa era un defecto de su
artefacto. La mesa la convoca el PM hoy.

**Argumento que aporta Héctor y que conviene llevar:** DEC-006, ratificada por Manuel el 13-ago, dice
*"escuela en riesgo = `indice_riesgo ≥ 0.6` ↔ pérdida de ~5 % de matrícula"*. Ese "~5 %" **es una
fracción**. El umbral de DB-03/DB-04 ya presupone la unidad que ADR-007 propone, así que la
alternativa A no es una opción nueva: es **reabrir DEC-006**. No estoy pidiendo entrar a una decisión
nueva, estoy defendiendo una que el equipo ya tomó y que la unidad actual contradice en silencio.

## Decisiones de proceso recibidas

- **El gate de URL pública no aplica a US-212** (PM). Se escribió para rutas HTTP de la API, por la
  asimetría entre US-411 y US-412. Un tablero cierra con evidencia de código más capa de datos
  validada. El PM hará explícito ese límite en `Execution_Status.md`.
- **BUG-027 pasa a `superseded`** y no se arregla: Manuel decidió borrar los `kpi_*.sql` y remapear
  las tarjetas a los datasets canónicos, así que corregir los `sql_ref` sería trabajo sobre archivos
  que van a desaparecer. Sobrevive el hallazgo de por qué CI no lo veía —el test codifica `SQL_DIR` a
  mano y nunca lee `sql_ref`—, del que nace la guarda antiduplicación pedida a Oscar. El PM marca el
  registro; no lo toco para no duplicar.

## Nota sobre una medición que no se pudo replicar

Héctor no pudo reproducir la intersección de CCT (59/60 y 3/30) porque comparó contra su mock, no
contra el catálogo real. La medición se hizo con `psql` contra `gold.dim_escuela` en la base local
con los fixtures cargados; los conteos de ciclos sí los confirmó él. Queda anotado por si alguien
más intenta replicarla: hay que cargar `bronze.cct` antes.

## Verificación

| Qué | Resultado |
|---|---|
| PR #129 de punta a punta | ✅ verificado en Postgres local |
| `pytest tests/ -q` | ✅ ver salida en el PR |
| `vault_lint.py` | ✅ Vault limpio |

## Pendientes

1. **US-214a** sigue sin arrancar, por decisión de la autora.
2. Mesa de ADR-007 — llevar el argumento de DEC-006.
3. BUG-012 (runbook del pipeline local) sigue abierto sin avance.

## Uso de IA

Claude Code (Opus 5) para aplicar las correcciones y ejecutar la revisión del PR #129. Todo lo que
este DevLog afirma del PR se corrió en la base local antes de escribirlo: carga del fixture, `dbt
run`, conteos y `publicar_gold.py --desde-gold`.
