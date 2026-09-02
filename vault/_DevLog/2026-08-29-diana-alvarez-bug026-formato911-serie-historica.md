---
project: "FARO"
date: "2026-08-29"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~1h"
touches: ["BUG-026"]
tags: [devlog, bronze, fixtures, formato911, bug026, ml01]
---

# BUG-026 — Fixture de Formato 911 con 4 ciclos sobre las CCT del catálogo

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

**Contexto.** Marina García del Buey (C2) reportó BUG-026: ningún fixture del repo ejercita el
grano escuela multi-ciclo. `bronze_formato911_sample.csv` + `..._ciclo_anterior_sample.csv` dan
CCT coherentes con `gold.dim_escuela` pero solo 2 ciclos; `bronze_formato911_historico_sample.csv`
da 6 ciclos pero sobre un universo de CCT propio, disjunto de `bronze.cct` (3 de 30 coinciden).
`ventanas_posibles()` exige 3 ciclos con target ya calculado para admitir backtesting, así que
ML-01 y los bloques de predicción de DB-03 (AC-002.4) sólo eran verificables con datos reales en
el ambiente propio de C1.

**Diagnóstico más preciso.** El fixture `historico` no era la pieza que había que arreglar:
alimenta `bronze.formato911_historico` → `silver.matricula_historica` →
`gold.matricula_municipio_nivel` (el agregado municipio × nivel de DEC-007), una ruta separada que
`gold.features_escuela` no consume. `silver.matricula` (la fuente real de `features_escuela`) sólo
lee de `bronze.formato911`, que hoy trae 2 ciclos crudos; como `con_target` en
`features_escuela.sql` siempre excluye el primer ciclo observado de cada cct (es la referencia del
LAG), hacían falta 4 ciclos crudos en `bronze.formato911`, no en `formato911_historico`.

**Fix.** `tests/fixtures/generate_bronze_formato911_serie_historica_fixture.py`: reutiliza las 72
CCT de `bronze_formato911_sample.csv` tal cual (mismo patrón que ya usa
`..._ciclo_anterior_fixture.py`) y les agrega los ciclos 2021-2022 y 2022-2023, cargados en la
misma tabla `bronze.formato911_2024_2025`. Aditivo: no reemplaza ningún fixture existente ni toca
ningún modelo dbt.

## Cómo se probó

Verificado en un ambiente limpio (sin datos reales de por medio):
python tests/fixtures/generate_bronze_formato911_serie_historica_fixture.py

OK: ... (144 filas, 72 CCT x 2 ciclos nuevos)

python -m src.ingesta.cargar_bronze_fixture --fixture tests/fixtures/bronze_formato911_serie_historica_sample.csv --tabla formato911_2024_2025 --esquema formato911

dbt run --select matricula features_escuela+ --target dev --threads 1 --full-refresh

gold.features_escuela: 145 filas, 3 id_ciclo (2022-2023, 2023-2024, 2024-2025), 60/60 escuelas
cruzan con bronze.cct (100%)

python -m src.modelos.publicar_gold --desde-gold --solo-predicciones

ML-01 entrena (MAE 12.23); ya no truena por ciclos -- llega al siguiente guardarraíl real,
BUG-017/ADR-007 (unidades de target_variacion_matricula)


Confirmado además en el ambiente con datos reales (C1): `gold.features_escuela` sale con 136,046
filas y los mismos 3 `id_ciclo` (2022-2023/2023-2024/2024-2025) tras la reconstrucción.

`dbt test --select matricula features_escuela`: 23/25 en verde. Los 2 rojos son preexistentes y no
relacionados: `cubo_pipeline_rows_parity` (DS-06/CONAGUA sin ingerir) y el `relationships` de
`cve_mun` → `dim_municipio` (brecha de cobertura de DS-07, ya documentada en el DevLog de US-325).

`pytest tests/`: sin regresiones nuevas — los únicos rojos son los `KeyError: cve_mun` ya conocidos
de la dependencia con PR #124 (Héctor), no relacionados con este cambio.

## Archivos tocados

- `tests/fixtures/generate_bronze_formato911_serie_historica_fixture.py` (nuevo)
- `tests/fixtures/bronze_formato911_serie_historica_sample.csv` (generado)