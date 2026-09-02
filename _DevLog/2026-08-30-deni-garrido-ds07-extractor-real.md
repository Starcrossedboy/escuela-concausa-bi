---
project: "FARO"
date: "2026-08-30"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "implementación y prueba real DS-07"
touches: ["DS-07", "US-113", "RISK-008"]
tags: [devlog, ds07, coneval, extractor, bronze, datos-reales]
---

# DS-07 — extractor real oficial CONEVAL

→ [[_DevLog/_index|Volver al índice]] · [[14_Data_Sources/DS-07_CONEVAL_Rezago_Social]]

## Implementación
- Parser basado en la estructura física medida por el probe oficial.
- IRS 2020: `IRS_entidades_mpios_2020.xlsx` / `Municipios`.
- Pobreza: `Concentrado_indicadores_de_pobreza_2020.xlsx` / `Concentrado municipal`.
- Encabezados multinivel Excel 5-6 serializados para Parquet sin aliases de negocio.
- Descarga restringida a HTTPS de CONEVAL, validación ZIP/path traversal y SHA-256.
- `openpyxl==3.1.5` registrado en requirements de Célula 1.
- 9 pruebas offline del extractor.

## Evidencia real
- IRS: 2469 municipios.
- Pobreza: 2469 municipios.
- Overlap: 2469.
- Pobreza 2020: 2466 numéricos y 3 ausencias oficiales.
- SHA IRS: `9191f6c16ec22452aa970a0fb9a5bbc5cde2057cf48eb81a68d66140289d1cfb`.
- SHA pobreza: `644d19a9ff6df37908df2f63117bac8ba2cb1f5389d97df03f62fc2c5118d975`.

La ficha DS-07 pasa a `in_review`. Los datos reales permanecen locales y no se versionan.

## Impacto
No se modifica Silver, Gold, cubos, Superset ni ML en esta fase. El siguiente paso es conformar los dos Bronze oficiales en `silver.rezago_municipio`.
