---
project: "FARO"
date: "2026-08-29"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "Sonnet 5"
session_duration: "larga — revisión de 15 PRs, resolución de dos conflictos y cierre del registro de bugs"
touches: ["BUG-026", "BUG-027", "BUG-028", "BUG-012", "BUG-014", "BUG-020", "US-004", "US-212", "US-221", "US-325", "ADR-007", "RPT-VAULT-FIX-2026-08-29", "REQ-002", "REQ-003", "REQ-007"]
tags: [devlog, pm, qa, bugs, vault, governance]
---

# DevLog — 2026-08-29 — Cierre de BUG-026/027, alta de BUG-028 y plan de corrección del vault

→ [[_DevLog/_index|Volver al índice]] · [[06_Quality_Testing/Bug_Register]] ·
[[13_Reports/Vault_Correcciones_2026-08-29]]

## Qué se hizo

Revisión de los 15 PRs abiertos para decidir orden de aprobación. Salieron tres cosas: dos
conflictos que no eran conflictos, un defecto silencioso que nadie había reportado, y cinco
incumplimientos de reglas del vault que ninguna herramienta detecta.

## Registro de bugs

**BUG-026 → `fixed`.** El PR #129 de Diana Alvarez lo cierra con un fixture aditivo de 4 ciclos
sobre las CCT del catálogo. Marina García lo validó **corriéndolo**: 1→3 ciclos en
`gold.features_escuela`, 60 de 60 CCT cruzando `dim_escuela`, y `publicar_gold.py --desde-gold`
entrenando ML-01 con MAE 12.2252 en vez de reventar. Con esto US-212 pasa a 95%.

Queda anotado lo que **no** cierra: la guarda automática propuesta —aserción dbt de solape mínimo y
de ciclos mínimos— sigue pendiente. Sin ella, un fixture futuro puede volver a divergir sin que CI
lo note.

**BUG-027 → `superseded`.** No se corrige la ruta porque los archivos desaparecen: Manuel Serranía
ratificó una sola implementación por KPI y los cinco `kpi_*.sql` se borran. Lo que **sí** sobrevive
del reporte de Marina es la causa de que CI no lo viera —`test_kpis_us221.py` codifica `SQL_DIR` a
mano y nunca lee el `sql_ref`—, y de ahí nace la guarda antiduplicación del follow-up de US-221.

**BUG-028 → alta y `fixed` en el mismo movimiento.** `cargar_features()` leía el CSV sin `dtype`,
así que pandas se comía el cero inicial de `cve_mun` (`"09001"` → `9001`) y el join contra
`dim_municipio` fallaba en silencio para las 9 entidades cuya clave INEGI empieza en cero, **CDMX
incluida**.

## Lo que vale registrar de cómo apareció BUG-028

No lo encontró una persona: lo encontró una guarda escrita quince minutos antes.

El PR #127 falló la invariante que Héctor Morales escribió en el #124 —que la agregación de DEC-007
dé lo mismo venga `cve_mun` de las features o de la dimensión— con 230 filas contra 315.
Investigando esa diferencia se agregó a `generar_fixture_dim.py` una guarda de coherencia entre la
entidad que codifica el CCT y la que declara `cve_mun`. Reventó en la primera corrida:

```
ValueError: 09DCT0000G: `cve_mun` '9001' contradice la entidad '09' del CCT.
```

**Y Diana lo había previsto.** Su comentario en `tests/conftest.py` describe el defecto palabra por
palabra. Pero el `dtype` quedó sólo en el fixture de pruebas; el lector de producción seguía sin él.
Los tests veían la clave bien formada y el pipeline real no.

La lección que quiero que quede: una hipótesis correcta escrita en un comentario no protege nada si
la corrección se aplica del lado equivocado. Cuando alguien documente un riesgo de tipos, la
pregunta siguiente es **cuántos lectores tiene ese archivo**.

## Los dos conflictos que no lo eran

Los PRs #124 y #127 reportaron conflicto en `_DevLog/_index.md`. Ninguno lo tenía. `.gitattributes`
declara `merge=union` en ese archivo precisamente porque cada PR le agrega una fila, pero **GitHub
no aplica los merge drivers al calcular mergeabilidad en la web**: reporta conflicto en un archivo
que `git` resuelve solo, y el editor web nunca lo cierra. Los dos se resolvieron con
`git merge origin/main` en local, sin intervención manual.

Va al plan de corrección como V-04b, porque volverá a pasar.

## Plan de corrección del vault

Cinco hallazgos de gobernanza en [[13_Reports/Vault_Correcciones_2026-08-29]], con dueño y fecha.
Tres comparten patrón: **la regla existe y está bien escrita, y la herramienta que debía hacerla
cumplir no la cubre.**

- **V-01** — `vault_lint` detecta mojibake pero no latin-1 crudo. Cuarto incidente de codificación
  en una semana; el del PR #102 pasó los cuatro checks en verde.
- **V-02** — Colisión de ID: el PR #87 declara un segundo `ADR-007`. Regla 3 violada, y el linter no
  lo ve. ADR-008 queda reservado.
- **V-03** — `Execution_Status` con filas desactualizadas, y el criterio de cierre por ruta HTTP
  ambiguo: se acota explícitamente a rutas de la API, no a tableros de Superset.
- **V-04** — Higiene: fila duplicada en el índice de DevLogs, procedimiento de conflicto sin
  documentar, deriva de columnas en el registro de bugs.
- **V-05** — BUG-012 sigue sin dueño y los siete pasos de Marina son el único runbook que existe.

## Uso de IA

Claude Code condujo la revisión de los 15 PRs, la resolución de los dos merges, el diagnóstico de
BUG-028 y la redacción de este registro. Verifiqué línea por línea los cambios a
`Bug_Register.md` y el plan de corrección antes de abrir el PR. No se pegaron datos reales ni
credenciales en los prompts.

## Pendiente

- Ratificar [[03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula]] — destraba el 5%
  restante de US-212, DB-04 y BUG-017.
- [[06_Quality_Testing/Bug_Register#BUG-020]] — único riesgo vivo para la casilla 6 del ensayo E2E.
- Ejecutar V-01 a V-05.
