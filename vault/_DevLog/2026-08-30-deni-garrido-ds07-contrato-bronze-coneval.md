---
project: "FARO"
date: "2026-08-30"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "diagnóstico y diseño de corrección raíz DS-07"
touches: ["DS-07", "DOC-DATAMODEL", "US-113", "RISK-008"]
tags: [devlog, ds07, coneval, bronze, data-model, fuentes-oficiales]
---

# DS-07 — contrato Bronze para IRS y Pobreza Municipal oficiales de CONEVAL

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/14_Data_Sources/DS-07_CONEVAL_Rezago_Social]] · [[vault/03_Architecture/Data_Model]]

## Contexto

Edgar Coronel solicitó cerrar DS-07 con datos reales porque la tabla Bronze usada en local seguía siendo una muestra de prueba, reduciendo la cobertura municipal de D1 y permitiendo que pruebas de integridad pasaran contra un universo artificialmente pequeño.

La revisión contra fuentes oficiales de CONEVAL confirmó que DS-07 no corresponde a un único archivo: el Índice de Rezago Social (IRS) municipal y la Medición de Pobreza Municipal son productos oficiales separados. El contrato anterior de `bronze.coneval` mezclaba semánticamente ambos productos.

## Decisión preparada para revisión humana

- Mantener **DS-07** como una sola fuente lógica institucional (CONEVAL).
- Aterrizar cada producto oficial 1:1 en Bronze: `bronze.coneval_irs_<aaaa>` y `bronze.coneval_pobreza_<aaaa>`.
- Conformar ambos únicamente en `silver.rezago_municipio` por clave INEGI + período.
- Mantener intacto el contrato downstream de Silver/Gold para no afectar cubos, BI ni ML.
- Eliminar en la implementación posterior la dependencia de datos de prueba (`coneval_v2`) y el período inventado por placeholder una vez que el período provenga del producto oficial.
- Usar únicamente URLs institucionales de `www.coneval.org.mx`.

## Alcance de esta sesión

Esta sesión modifica únicamente documentación de arquitectura/fuente y deja preparado el contrato. **No** implementa todavía extractor, sources dbt ni cambios de esquema físico. Por regla 7 del vault, el cambio canónico de Data Model requiere revisión humana explícita antes de merge.

La ficha DS-07 permanece `draft`: no se marcará `in_review` hasta ejecutar y documentar la prueba de descarga real de ambos productos.

## Fuentes oficiales confirmadas

- IRS: `https://www.coneval.org.mx/Medicion/Documents/IRS_2020/IRS_ent_mun_2000_2020.zip`
- Pobreza municipal: `https://www.coneval.org.mx/Medicion/Documents/Pobreza_municipal/2020/Concentrado_indicadores_de_pobreza_2020.zip`

## Impacto

- Bronze: cambio documental del contrato DS-07 (dos artefactos físicos bajo una fuente lógica).
- Silver: sin cambio implementado todavía; diseño mantiene `silver.rezago_municipio`.
- Gold/cubos/Superset/ML: **sin cambios** en esta fase.
- US-113: la corrección de DS-07 permitirá posteriormente repetir runtime con D1 sobre cobertura real.

## Validaciones previstas antes del push

- `python vault/_Meta/scripts/vault_lint.py .`
- `git diff --check`
- revisión del diff completo
- revisión humana explícita del cambio de schema antes de merge
