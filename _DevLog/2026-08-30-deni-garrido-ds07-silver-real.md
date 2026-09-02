---
project: "FARO"
date: "2026-08-30"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "conformación DS-07 Bronze Postgres → Silver real"
touches: ["DS-07", "US-113", "RISK-008", "US-111"]
tags: [devlog, ds07, coneval, bronze, silver, postgres, datos-reales]
---

# DS-07 — Bronze Postgres y Silver real CONEVAL

→ [[_DevLog/_index|Volver al índice]] · [[14_Data_Sources/DS-07_CONEVAL_Rezago_Social]]

## Cambio

- Se elimina `coneval_v2` como source dbt canónico.
- Se declaran `bronze.coneval_irs_2020` y `bronze.coneval_pobreza_2020`.
- Se agrega cargador Postgres específico para los Parquet reales de DS-07; no reutiliza el
  contrato sintético de `cargar_bronze_fixture.py`.
- Los encabezados oficiales largos se representan en Postgres con identificadores técnicos
  SHA-1 cortos y determinísticos para evitar colisiones por el límite de 63 bytes; el encabezado
  original queda preservado en COMMENT ON COLUMN y manifiesto local.
- `silver.rezago_municipio` conforma ambos productos por clave INEGI + período.
- Se elimina `coneval_periodo_medicion` de `dbt_project.yml`.
- El período 2020 viaja como metadato técnico `_periodo_medicion` desde el extractor oficial.
- Gold, cubos, Superset y ML no se modifican.

## Regla de ausencia

Los `n.d.` oficiales de Pobreza 2020 se preservan en Bronze y se traducen en Silver a
`pobreza_pct = NULL` + `pobreza_pct_cobertura = SIN_DATO`, nunca a cero.

## Evidencia runtime

- `silver.rezago_municipio`: **2469 filas / 2469 municipios**.
- Período 2020: 2469 filas.
- IRS: 2469 `OK`, 0 `SIN_DATO`.
- Pobreza: 2466 `OK`, **3 `SIN_DATO` oficiales**.
- Pobreza fuera de [0,100]: 0.
- Claves municipales inválidas: 0.


## Validaciones

- tests unitarios extractor + loader real
- `dbt parse --no-partial-parse`
- `dbt compile --select rezago_municipio`
- `dbt run --select rezago_municipio`
- `dbt test --select rezago_municipio`
- auditoría SQL nacional con expectativas exactas
- suite completa `pytest tests/ -q`
- `vault_lint.py`
- `git diff --check`

