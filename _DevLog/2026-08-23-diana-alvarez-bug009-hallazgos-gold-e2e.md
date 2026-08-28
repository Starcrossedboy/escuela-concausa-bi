---
project: "FARO"
date: "2026-08-23"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "media -- materialización de Gold para ensayo E2E + fix de vault corrupto"
touches: ["BUG-009", "BUG-008", "DOC-BUGREG", "US-111", "US-411"]
tags: [devlog]
---

# DevLog — 2026-08-23 — Hallazgos reales de BUG-009 (materialización Gold para ensayo E2E de Héctor) + fix de conflicto sin resolver en Bug_Register.md

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

En PR #70 (Héctor Rafael Morales Marbán, mergeado), quedó un comentario dirigido a Diana: para
que el ensayo E2E del 28-29 de agosto tenga qué mostrar, hacía falta un `dbt build` real con datos
contra la base del docker-compose local — ese día `gold` solo tenía las dos tablas propias de
Héctor (`dim_driver` y otra).

Se confirmó primero que el ensayo corre contra el docker-compose local de Diana (no un ambiente
compartido), que el servicio `db` ya estaba sano, y que el override de `generate_schema_name`
(`dbt/macros/generate_schema_name.sql`) ya garantiza que los modelos silver/gold aterrizan en
esquemas literales (`silver.*`, `gold.*`), sin importar el `schema` del target del perfil dbt
(`dbt_diana`).

Al intentar un `dbt build` completo se confirmó BUG-009 en la práctica, no solo en compilación: los
identifiers placeholder usados hasta ahora (`cct_test`, `conapo_test`, etc., para builds acotados
con `--select`) no son tablas reales — al correr sin acotar, dbt sí las consulta y truena con
`relation "bronze.cct_test" does not exist`. Se investigaron las tablas reales en `bronze` vía
`psql` y se armó un build acotado (`--select` a los modelos silver + gold que alimentan
`dim_escuela`, `dim_municipio`, `dim_tiempo`, `fact_escuela_ciclo`, `features_escuela`,
`matricula_municipio_nivel`, excluyendo `agua_region` por no tener datos ingeridos de CONAGUA
todavía) con los valores reales encontrados — ver detalle completo en la actualización agregada a
BUG-009 en `Bug_Register.md`.

Resultado: `dbt build` completó 14 modelos y 126 tests en verde, y las 6 tablas Gold objetivo
quedaron con datos reales (60/10/2/25/25/72 filas respectivamente). Se avisó a Héctor por comentario
en PR #70.

## Fix adicional: conflicto de merge sin resolver en Bug_Register.md

Al ir a documentar los hallazgos de BUG-009, se encontró que `06_Quality_Testing/Bug_Register.md`
tenía marcadores de conflicto de git (`<<<<<<< HEAD` / `=======` / `>>>>>>> origin/main`) comiteados
literalmente en `main`, sin resolver — quedaron ahí en los commits de Edgar que renumeraron
BUG-008→BUG-009 (`c3af546`/`3b407d8`) para resolver la colisión de esa misma sesión. La tabla
resumen del archivo estaba bien (por eso no se notó antes), pero el detalle de las secciones
BUG-008 y BUG-009 estaba roto. `vault_lint.py` no lo detectó porque solo valida wikilinks, no
integridad de contenido — es un gap de la herramienta, no urgente de cerrar ahora.

Se resolvió en el mismo PR, quedándose con el contenido correcto de cada sección (el que ya
coincidía con la tabla resumen: BUG-008 = contenedor de la API, BUG-009 = fuentes Bronze sin
identifier).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude (Cowork), claude-sonnet-5
- **Archivos creados/modificados:**
  - `06_Quality_Testing/Bug_Register.md` (fix de conflicto sin resolver + actualización de BUG-009
    con hallazgos reales)
  - `_DevLog/_index.md` (fila nueva)
  - `_DevLog/2026-08-23-diana-alvarez-bug009-hallazgos-gold-e2e.md` (este archivo)
- **Decisiones autónomas del agente:** ninguna de fondo. El agente investigó y propuso los valores
  reales (tablas/columnas bronze, y el criterio para preferir `coneval_v2` sobre `coneval_test`),
  pero el año de `coneval_periodo_medicion` quedó explícitamente sin confirmar — es un valor de
  negocio que no le corresponde inventar al agente, se documentó como pendiente para Deni.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** continuar con la materialización de Gold que pedía Héctor en PR #70, y
  documentar los hallazgos de BUG-009 y el problema de `coneval_periodo_medicion`.

## Seguridad / calidad
- [x] `python _Meta/scripts/vault_lint.py .` da Vault limpio (5 huérfanos preexistentes,
      informacional, no bloqueante)
- [x] `pytest tests/ -q` en verde — 268 passed, 4 skipped, 1 warning
- [x] No se tocó código de producción — solo documentación/gobernanza (`Bug_Register.md`) y datos
      locales de dbt (build contra el compose local, no un ambiente compartido)
- [x] No se subieron credenciales — la contraseña del perfil dbt local nunca se pegó en ningún
      archivo del repo

## Próximos pasos
- Diana: commitear, pushear y abrir PR con estos cambios.
- Pendiente de Deni (US-111/DS-07): confirmar el año real de `coneval_periodo_medicion` (se usó
  `2020` como placeholder solo para el ensayo E2E).
- Pendiente de Edgar: decidir el reparto para que los valores reales encontrados (o los que
  correspondan) queden como default permanente en `dbt/models/sources.yml`, cerrando BUG-009.
- Pendiente de quien materialice `bronze.conagua`: `agua_region` sigue sin datos reales ingeridos.