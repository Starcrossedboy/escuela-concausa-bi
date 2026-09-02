---
project: "FARO"
date: "2026-08-25"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "ox-alpha"
type: devlog
session_duration: "~1h"
touches: ["US-203", "US-212", "BUG-011", "REQ-002", "PR-84", "US-113"]
tags: [devlog, superset, sync, windows, celula-2]
---

# 2026-08-25 — Manuel Serranía · BUG-011 (encoding Windows) + guardia de charts homónimos + review US-212

## Contexto

Marina García del Buey entregó US-212 (PR #84: DB-03/DB-04 declarativos sobre el motor de
US-203) y en la revisión reportó **tres defectos de mi script** `sync_semantic_layer.py`
(no tocó el archivo porque es mío). Esta sesión atiende los dos de código y el de docs,
y cierra el review del PR #84.

## Qué se hizo

### 1. BUG-011 — lectura cp1252 en Windows (reporte de Marina)

`_read_yaml()` y `_read_sql()` leían con `path.read_text()` sin `encoding`: en Windows Python
usa el locale (cp1252) y truena con `UnicodeDecodeError` ante cualquier acento de
`metrics_*.yaml`. El workaround era correr todo con `PYTHONUTF8=1`. Fix: `encoding="utf-8"`
explícito en las **3** lecturas (las 2 de `_read_yaml`, incluida la ruta del parser manual, y
la de `_read_sql` que Marina no había mencionado). Registrado como **BUG-011** en
[[vault/06_Quality_Testing/Bug_Register]] — misma familia que BUG-005.

### 2. Guardia anti-homónimos en `ensure_chart()` (hallazgo principal de Marina)

El script identificaba charts por `slice_name` **global**: tres charts de DB-03 se llamaban
igual que los de DB-01 ("KPI-01 · Matrícula total", etc.) y el sync repuntaba los charts de
DB-01 a los datasets nuevos con un log verde de "actualizado". Opción elegida: **no** prefijar
el slug al nombre visible (propuesta original de Marina) sino comparar el `datasource_id` del
candidato contra el dataset objetivo: solo se actualiza si apunta al MISMO dataset; si el
homónimo vive en otro dataset, se crea chart nuevo y se avisa con `⚠` en el log. Sin renombres,
sin migración, DB-01/DB-02 intactos.

### 3. Doc fix (`Superset_Setup_US202.md` §2)

La guía mandaba cargar `docker/gold_mock.sql`, que no existe. El archivo real es
`superset/mock/gold_ml_outputs_mock.sql`; sección reescrita apuntando a `superset/mock/`.

### 4. Review del PR #84 (Marina · US-212)

Diff completo leído (2 YAML de tableros, mock estrella, metrics yaml). Verificación:

- Los 24 charts referencian métricas que existen en `metrics_db03_db04.yaml` y datasets cuyo
  nombre coincide con el stem del SQL semántico ✓
- Regla SIN_DATO respetada end-to-end: mock con cobertura deliberadamente parcial, banderas
  como fuente de verdad, NULL ≠ false ✓
- Higiene del mock: datos 100% sintéticos, idempotente (`IF NOT EXISTS` + `ON CONFLICT`),
  vive en `superset/mock/`, no toca `dbt/` ✓
- `gold.geo_municipio` incluido solo para que `db02_coropletico.sql` no aborte el sync en
  lote — justificado y documentado en el propio archivo; se aprueba tal cual ✓
- Filtro global `cct` en DB-03: soportado por `_filtros_nativos` del motor (US-203); sin
  conflicto con US-214a (misma dueña) ✓
- Renombres de llaves YAML (`kpis_propuestos`→`kpis_canonicos`,
  `grano_canonico_actual`→`grano_ratificado_en`) no rompen tests: solo
  `test_semantic_db05_db08.py` aserta esas llaves y es del archivo db05/db08 ✓

**Veredicto: approve**, con la condición ya documentada por ella de revalidar números contra
los cubos reales cuando US-113 (PR #81) se mergeé.

### 5. Confirmación US-113 (pregunta del equipo)

US-113 **sí fue iniciada**: dueño Deni Garrido Fragoso (C1, Plan Maestro), PR #81 abierto con
los 8 cubos + ~30 data tests. Estaba detenido esperando DEC-009 (granos canónicos), que ya
está en main desde el 2026-08-23 → el PR puede avanzar. Lo que dice Marina es cierto sobre
main (los cubos aún no están), no sobre la existencia del trabajo.

## Verificación

- `python superset/sync_semantic_layer.py --help` importa sin error tras los cambios ✅
- `_read_yaml` parsea `metrics_db01_db02.yaml` (6 datasets, acentos intactos) ✅
- Suite completa: **298 passed, 4 skipped** ✅ · `vault_lint.py` ✅ Vault limpio

## Notas / riesgos

- BUG-011 queda `fixed` con test de regresión **pendiente de validar en Windows** (el fallo
  es específico de ese SO; quien tenga Windows corre el sync sin `PYTHONUTF8=1`).
- La guardia de homónimos depende de que la lista de `/api/v1/chart/` traiga
  `datasource_id`; si alguna versión no lo trae, el código cae al detalle por id.
- `metrics_db05_db08.yaml` conserva las llaves viejas (`kpis_propuestos`) — fuera de alcance,
  pero convendrá alinear cuando se cierre el PR de Monserrat.
- Mi instancia local de Superset sigue teniendo los charts de DB-01/02 con nombres planos:
  con la guardia, el próximo sync los encuentra por dataset y los actualiza en sitio.
