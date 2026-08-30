---
id: RPT-VAULT-FIX-2026-08-29
title: "Plan de corrección del vault — hallazgos de la revisión de PRs del 29-ago"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: false
traces_up:
  - "12_Roadmap_Sprints/Execution_Status"
  - "06_Quality_Testing/Bug_Register"
  - "_Meta/Vault_Rules"
traces_down:
  - "03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula"
  - "02_Requirements/Traceability_Matrix"
last_reviewed: "2026-08-29"
tags: [report, vault, governance, follow-up, deuda-tecnica]
---

# Plan de corrección del vault — 29 de agosto de 2026

> Hallazgos de gobernanza detectados al revisar los 15 PRs abiertos del 29-ago. **No son defectos
> de producto**: son incumplimientos de las reglas del vault y huecos en las herramientas que las
> hacen cumplir. Cada uno tiene dueño y fecha.
> → [[_Meta/Vault_Rules]] · [[06_Quality_Testing/Bug_Register]] · [[12_Roadmap_Sprints/Execution_Status]]

## Por qué existe este documento

Dos de los cinco hallazgos comparten el mismo patrón: **una regla del vault existe, está bien
escrita, y la herramienta que debía hacerla cumplir no la cubre**. El linter revisa mojibake pero no
latin-1 crudo, y `merge=union` protege el índice de DevLogs en `git` pero GitHub lo ignora. La regla
sin verificación automática es una recomendación, y este equipo ya demostró que las recomendaciones
se saltan bajo presión de entrega.

El tercero (V-02) parecía del mismo tipo y **no lo es**: ahí la herramienta funciona y lo que falló
fue dejar una rama tres días sin actualizar, de modo que su último check describe un repositorio que
ya no existe. Se corrigió esta entrada al verificarlo, en vez de dejar el diagnóstico cómodo.

---

## V-01 · `vault_lint` no detecta latin-1 crudo

**Severidad: alta · Dueño: Edgar Coronel (PM) · Antes del: 30-ago**

La guarda anti-mojibake de [[06_Quality_Testing/Bug_Register#BUG-014]] busca secuencias
doble-codificadas (`Ã³`). No detecta el caso inverso: un byte latin-1 **que no es UTF-8 válido**.

Caso real, PR #102, en `11_Operations/_index.md`:

```
| [[11_Operations/Alertas_Monitoreo_US524a]] | Pol\xedtica de alertas ...
```

Los cuatro checks pasaron en verde. Se detectó a mano con `iconv -f UTF-8 -t UTF-8`.

**Es el cuarto incidente de codificación en una semana** — BUG-005, BUG-011, el mojibake previo del
PR #102 y ahora este. El patrón es Windows escribiendo con el locale del sistema, y el equipo ya
tiene el antecedente encima: si se le pasa a quien acaba de ser corregido por lo mismo, el problema
no es la persona.

**Acción:** agregar a `_Meta/scripts/vault_lint.py` una validación de decodificación UTF-8 estricta
sobre todo archivo de texto versionado, con el número de línea y el byte ofensor en el mensaje.
Registrar como BUG con su prueba de regresión, igual que se hizo con BUG-014.

---

## V-02 · Colisión de ID en ADR-007

**Severidad: alta · Dueño: Edgar Ulises Jiménez (C5) · Bloquea el PR #87**

El PR #87 introduce `ADR-007-contenerizacion-airflow-sqlalchemy.md` con `id: ADR-007`, pero ese ID
ya lo ocupa [[03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula]] — que además está en
**ratificación activa** con cinco personas en la mesa.

Viola la **regla 3** (*"Todo artefacto tiene un ID único. Los IDs nunca se reciclan"*) y rompe la
trazabilidad en la práctica: cualquier `traces_up: ["ADR-007"]` queda ambiguo.

**Acciones:**

1. Renombrar a **ADR-008** en los tres lugares: nombre de archivo, campo `id:` del frontmatter y
   título del documento. Actualizar `03_Architecture/ADRs/_index.md`.
2. **ADR-008 queda reservado** a su nombre desde hoy, anotado en el índice de ADRs, para que nadie
   lo tome mientras corrige.
3. **El linter sí funciona; el check estaba viejo.** `vault_lint` detecta la colisión y la reporta
   como bloqueante (`❌ IDs duplicados (1): ADR-007`). Lo verifiqué al mergear `main` en la rama del
   PR #87. No saltó antes porque su última corrida de CI fue el **26-ago** y el ADR-007 de Héctor
   nació el **28-ago**: la colisión no existía cuando el check se ejecutó, y la rama no se ha
   tocado desde entonces.

   Esto **no** es un hueco de herramienta como V-01 — es una consecuencia de dejar una rama sin
   actualizar. Pero merece una regla: **un PR con checks de más de 24 horas no se mergea sin
   revalidar**, porque el verde que muestra puede describir un mundo que ya no existe.

---

## V-03 · `Execution_Status.md` desactualizado y con un criterio ambiguo

**Severidad: media · Dueño: Edgar Coronel (PM) · Antes del: 30-ago**

### V-03a · Filas que contradicen el estado real

`US-221` sigue diciendo *"PR #106 abierto"* cuando se mergeó en `7754b90`. Reportado por Manuel
Serranía. Pasa a `done`, anotando que el follow-up antiduplicación de las tarjetas KPI se sigue
aparte y **absorbe BUG-027**.

Actualizar también, conforme se mergean: `US-213`, `US-303`, `US-321`, `US-325`, `US-522b`,
`US-524a`.

### V-03b · El criterio de cierre por ruta HTTP es ambiguo

La regla adoptada el 28-ago dice que *"las historias cuyo entregable es una ruta HTTP no cierran
mientras esa ruta no responda en el despliegue que se va a demostrar"*. Marina García preguntó, con
razón, si un tablero de Superset cuenta como superficie desplegada — la diferencia para ella era
medio sprint.

**Resolución del PM:** el criterio **aplica sólo a rutas HTTP de la API**. Un tablero de Superset
cierra con evidencia de código más capa de datos validada, y **no** queda condicionado al despliegue
de C5.

**Acción:** hacer explícito ese límite en el texto de la regla. Una regla que necesita interpretarse
caso por caso no es un criterio de cierre, y la pregunta se volvería a hacer.

---

## V-04 · Higiene de `_DevLog/_index.md` y del registro de bugs

**Severidad: baja · Dueño: Edgar Coronel (PM) · Antes del: 02-sep**

### V-04a · Fila duplicada en el índice de DevLogs

`2026-08-22-deni-garrido-us112-silver-gold` aparece **dos veces**. Es el efecto secundario esperado
de `merge=union` cuando alguien resuelve un conflicto a mano y reinserta su fila. Eliminar la
duplicada.

### V-04b · GitHub ignora `merge=union` — documentarlo

`.gitattributes` declara `_DevLog/_index.md merge=union` precisamente porque cada PR le agrega una
fila. Funciona en `git`, pero **la interfaz web de GitHub no aplica los merge drivers** al calcular
mergeabilidad: reporta conflicto en un archivo que localmente se resuelve solo, y el editor web
**nunca lo cierra**. Ya costó tiempo en los PRs #124 y #127.

**Acción:** documentar el procedimiento en `_Meta/Vault_Rules.md` — *ante conflicto en
`_DevLog/_index.md`, resolver con `git merge origin/main` en local, nunca con el editor web*.

### V-04c · Deriva de columnas en `Bug_Register.md`

La tabla declara 7 columnas. Nueve filas no las respetan: BUG-010, 015, 016, 017, 018, 019, 020, 023
traen una columna extra (`ver detalle`), y BUG-025 una de menos. Preexistente. Normalizar en una
pasada, sin tocar el contenido.

---

## V-05 · BUG-012 sigue sin dueño

**Severidad: alta · Dueño: por asignar (C1) · Asignar en el standup del 30-ago**

No existe runbook para levantar el pipeline local. `dbt/README.md` sigue siendo el scaffold por
defecto de dbt, no hay `profiles.yml` ni se documenta dónde ponerlo. Los siete pasos verificados de
Marina García en su DevLog del 27-ago **son el único registro que existe**, y viven en un DevLog
personal, no en la documentación del proyecto.

Ya costó una tarde una vez. Con el ensayo E2E encima, es la clase de deuda que se cobra en el peor
momento.

**Acción:** asignar dueño en el standup y convertir los pasos de Marina en `dbt/README.md`.

---

## Resumen

| ID | Hallazgo | Sev. | Dueño | Fecha |
|---|---|---|---|---|
| V-01 | `vault_lint` no detecta latin-1 crudo | alta | Edgar Coronel | 30-ago |
| V-02 | Colisión de ID en ADR-007 (el linter sí la detecta; el check estaba viejo) | alta | Edgar Ulises Jiménez | bloquea PR #87 |
| V-03a | `Execution_Status` con filas desactualizadas | media | Edgar Coronel | 30-ago |
| V-03b | Criterio de cierre por ruta HTTP ambiguo | media | Edgar Coronel | 30-ago |
| V-04a | Fila duplicada en `_DevLog/_index.md` | baja | Edgar Coronel | 02-sep |
| V-04b | Procedimiento de conflicto no documentado | baja | Edgar Coronel | 02-sep |
| V-04c | Deriva de columnas en `Bug_Register` | baja | Edgar Coronel | 02-sep |
| V-05 | BUG-012 sin dueño | alta | por asignar (C1) | 30-ago |

**Fuera de este plan, con reloj propio:** la ratificación de
[[03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula]] —que destraba US-212, DB-04 y
BUG-017— y [[06_Quality_Testing/Bug_Register#BUG-020]], único riesgo vivo para la casilla 6 del
ensayo E2E.
