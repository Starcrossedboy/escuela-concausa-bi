---
project: "FARO"
date: "2026-08-18"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "~1h30"
touches: ["US-101", "US-103", "US-111"]
tags: [devlog]
---

# DevLog — 2026-08-18 — Merge de US-111 (Silver, Deni) y validación real de dim_tiempo

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo
- Detectado que mi rama estaba **41 commits atrás de `main`**, y que faltaba jalar US-111
  (Deni Garrido Fragoso · PR #37, mergeado el 16 ago): los 8 modelos de `dbt/models/silver/`,
  macros de homologación (`normalize_cct`, `normalize_cve_ent`, `normalize_cve_mun`, etc.),
  51 data tests y `dbt/models/sources.yml`.
- Confirmado con el equipo (Deni/Edgar) antes de tocar nada. US-111 es historia de Deni
  (S2, REQ-001); mi rol es revisarla, no rehacerla.
- Hecho `git merge origin/main` sobre `feat/diana-varela-us103-gold-estrella`. **Un solo
  conflicto real**: `dbt/dbt_project.yml` — mi rama tenía `name/profile: 'faro_gold'`
  (solo capa gold), `main` tenía `name/profile: 'faro'` (solo capa silver, sin `+schema`).
  Se consolidó en un único proyecto `faro` con `silver` y `gold`, ambos con `+schema`
  explícito.
- **Bug real encontrado y corregido**: `gold/dim_tiempo.sql` leía `id_ciclo` de
  `silver.matricula`, pero el modelo de Deni entrega la columna como `ciclo` (no
  `id_ciclo`, que es como lo documenta Data_Model.md §5.1 `SilverMatricula`). Sin el merge
  real y sin correr `dbt run` de verdad, este bug hubiera pasado desapercibido hasta el
  freeze. Se corrigió con un alias (`ciclo as id_ciclo`) del lado de Gold (mi alcance), sin
  tocar el archivo de Deni.
- **Validado end-to-end** contra Postgres local (docker-compose) con un fixture anonimizado
  de `bronze.formato911` (`tests/fixtures/bronze_formato911_sample.csv`, 73 filas):
  - `dbt run --select matricula` → 72/72 filas
  - `dbt test --select matricula gold` → **11/11 en verde**
  - `dbt run --select gold` → `dim_tiempo` corre y da 2 filas (los 2 ciclos)
  - Las otras 6 fuentes de Silver siguen sin validar contra datos reales (mismo estado que
    dejó Deni: `dbt compile` limpio, sin `dbt run`/`dbt test`) — no se tocaron hoy.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude (Cowork), claude-sonnet-5
- **Archivos creados/modificados:**
  - `dbt/dbt_project.yml` (resolución del conflicto, proyecto único `faro`)
  - `dbt/macros/generate_schema_name.sql`
  - `dbt/models/gold/dim_tiempo.sql` (fix de columna `ciclo`→`id_ciclo`)
  - `src/ingesta/cargar_bronze_fixture.py`
  - `tests/fixtures/generate_bronze_formato911_fixture.py`
  - `tests/fixtures/bronze_formato911_sample.csv`
- **Decisiones autónomas del agente:** consolidar el nombre del proyecto dbt como `faro`
  (el de `main`/Deni); agregar `+schema: gold` (antes `gold` no tenía esquema propio) —
  cambio de comportamiento a confirmar con Manuel/Christian/Luis Téllez antes del PR;
  arreglar `dim_tiempo.sql` con un alias en vez de editar el archivo de Deni.
- **Correcciones manuales:** ninguna — revisado línea por línea antes de cada commit.
- **Prompt inicial:** continuación de sesión anterior (hallazgo de US-111 sin mergear).

## Seguridad / calidad
- [ ] `python _Meta/scripts/vault_lint.py .` — pendiente
- [x] Sin secretos hardcodeados
- [x] Validado con `dbt run` + `dbt test` reales (11/11), no solo `dbt compile`
- [x] DevLog enlaza a los IDs afectados (US-101, US-103, US-111)

## Bloqueantes
- `+schema: gold` es un cambio de comportamiento nuevo — pendiente confirmar con
  Manuel/Christian (C2/C4, consumen Gold) y Luis Téllez (C5, dueño del esquema Postgres)
  antes de abrir/actualizar el PR.
- El desajuste `ciclo` vs `id_ciclo` entre Data_Model.md y `silver.matricula` real sigue sin
  resolver de raíz — decidir con Deni/Edgar cuál es el nombre canónico.
- DS-02 (Catálogo CCT) sigue sin extractor — `silver.escuela` compila pero no corre.

## Próximos pasos
- Avisar a Manuel/Christian/Luis Téllez del cambio de esquema antes del push/PR.
- Coordinar con Deni la corrección de nomenclatura (`ciclo`/`id_ciclo`).
- Seguir con `dim_escuela` (bloqueado por DS-02) y `dim_municipio`.