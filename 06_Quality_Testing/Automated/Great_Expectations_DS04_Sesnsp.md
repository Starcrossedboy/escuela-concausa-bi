---
id: TEST-011
title: "Great Expectations — DS-04 SESNSP (Bronze)"
owner: "Luis Enrique García Vázquez"
status: implemented
traces_up: ["02_Requirements/User_Stories", "02_Requirements/Requirements_Detailed"]
tags: [qa, testing, great-expectations, celula-1, bronze, sesnsp]
---

# TEST-011 — Great Expectations DS-04 SESNSP (Bronze)

> Valida la tabla Bronze que produce `extractor_sesnsp.py` (`US-122b`) para
> [[02_Requirements/User_Stories|US-123b]]. Complementa
> [[06_Quality_Testing/Automated/Great_Expectations_DS05_Sinaica|TEST-010]] (DS-05), cerrando
> Great Expectations para ambas fuentes de la Célula 1 que le tocan a Luis.
> → [[06_Quality_Testing/Automated/_index]] · [[14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva]]

## Qué valida

| Ruta en repo | Comando | Corre en |
|---|---|---|
| `src/ingesta/validacion_sesnsp.py` | `python -m src.ingesta.validacion_sesnsp` | manual (aún no en CI/DAG) |

Sobre `sesnsp` (única tabla Bronze de esta fuente, ya agregada a nivel
municipio/año/mes/tipo de delito por el propio extractor — ver
`14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva.md` sección 10 para el porqué):

- **Nulos:** `cve_ent`, `cve_mun`, `anio`, `mes`, `tipo_delito`, `conteo`.
- **Tipos:** `anio`/`mes` enteros.
- **Formato de llave:** `cve_ent` ∈ `^\d{1,2}$`, `cve_mun` ∈ `^\d{1,3}$` (códigos crudos, sin
  padding — la homologación a 2/5 dígitos INEGI es trabajo de
  `dbt/macros/normalize_cve_ent.sql`/`normalize_cve_mun.sql`, no de Bronze).
- **Rangos físicos:** `anio` ∈ [2015, 2030], `mes` ∈ [1,12], `conteo` ≥ 0.
- **Catálogo válido:** `tipo_delito` contra la lista real confirmada en el corte de dic-2025.
- **Duplicados / llave:** `(cve_ent, cve_mun, anio, mes, tipo_delito)` único — esta expectativa
  **debe pasar siempre** porque el extractor ya agrega a ese grano exacto antes de escribir
  Bronze; si falla, es una regresión real en `extractor_sesnsp.py`, no un hallazgo de la fuente.

## Resultado real (12 553 440 filas de Bronze, corrido el 2026-08-24)

**14/15 expectativas en verde.** La única falla es un hallazgo real, no un bug de la suite:

| Columna | Valor | Ubicación |
|---|---|---|
| `conteo` | `-1` | CDMX (`cve_ent="9"`), municipio local `"006"`, sep-2017, tipo_delito "Otros delitos que atentan contra la libertad personal" |

Consistente con el riesgo ya documentado en la ficha DS-04: el archivo mensual de SESNSP puede
reescribir históricos, y una corrección retroactiva sobre un mes ya reportado puede llegar como
ajuste negativo. No se filtró ni se corrigió — Great Expectations lo deja visible en Data Docs
para que quien construya el driver D2 (inseguridad) decida cómo tratarlo (ej. `SIN_DATO` vs. 0
neto vs. ajuste absorbido en el mes).

## Cómo reproducir

```bash
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m src.ingesta.extractor_sesnsp    # ~380 MB, tarda varios minutos
.venv\Scripts\python.exe -m src.ingesta.validacion_sesnsp
# Data Docs en great_expectations/uncommitted/data_docs/local_site/index.html
```

## Cobertura automatizada (US-124b, `tests/test_validacion_sesnsp.py`)

`validar_sesnsp()` acepta un `df` y un `ge_context_dir` explícitos — permite correr esta suite en
`pytest` con datos sintéticos pequeños (esquema real, sin red, sin descargar los 380 MB del CSV
fuente ni tocar el `great_expectations/` real del repo). Los 4 casos reproducen a propósito el
mismo tipo de hallazgo que apareció en producción (conteo negativo por corrección retroactiva),
más tipo de delito fuera de catálogo y llave duplicada — cada uno demuestra que la suite SÍ
atrapa el problema, no solo que corre sin tronar. `tests/test_extractor_sesnsp.py` cubre además
la lógica de agregación (suma de subtipo/modalidad, derivación de `cve_mun`) sin red.

```bash
pytest tests/test_validacion_sesnsp.py tests/test_extractor_sesnsp.py -v
```

## Ver también

- `TEST-010` (DS-05) para el diseño general de estas suites (por qué Bronze no está tipado, cómo
  se estructura la validación con GE 1.21).
- `14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva.md` para la historia completa del bloqueo de
  SharePoint, la fuente alterna encontrada y las decisiones de agregación wide→long.
