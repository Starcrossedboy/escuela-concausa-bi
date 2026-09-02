---
project: "FARO"
date: "2026-08-30"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "probe automatizado de esquema físico DS-07"
touches: ["DS-07", "US-113", "RISK-008"]
tags: [devlog, ds07, coneval, schema-probe, datos-reales]
---

# DS-07 — probe del esquema físico real de CONEVAL

→ [[_DevLog/_index|Volver al índice]] · [[14_Data_Sources/DS-07_CONEVAL_Rezago_Social]]

## Motivo

La primera ejecución del extractor real descargó desde CONEVAL pero el detector defensivo no
reconoció la tabla IRS. No se relajó el contrato a ciegas: este probe registra únicamente
metadatos físicos y tokens de encabezado para adaptar el parser al archivo oficial real.

> Este DevLog **no contiene filas municipales ni valores de indicadores**. Solo URLs, hashes,
> nombres de archivo/hoja, dimensiones y tokens detectados en encabezados.

## IRS

- URL solicitada: `https://www.coneval.org.mx/Medicion/Documents/IRS_2020/IRS_ent_mun_2000_2020.zip`
- URL final: `https://www.coneval.org.mx/Medicion/Documents/IRS_2020/IRS_ent_mun_2000_2020.zip`
- SHA-256: `9191f6c16ec22452aa970a0fb9a5bbc5cde2057cf48eb81a68d66140289d1cfb`
- Bytes: `2614158`

### Miembros del ZIP

- `IRS_entidades_mpios_2000.xlsx` · `.xlsx` · 543391 bytes
  - Hoja `Estados`: 2458 × 17; merged ranges=8
    - fila 5: `Clave entidad | Entidad federativa | Población total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
  - Hoja `Municipios`: 2454 × 19; merged ranges=10
    - fila 5: `Clave entidad | Entidad
federativa | Clave municipio | Municipio | Población total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
- `IRS_entidades_mpios_2005.xlsx` · `.xlsx` · 542647 bytes
  - Hoja `Estados`: 2458 × 17; merged ranges=8
    - fila 5: `Clave entidad | Entidad federativa | Población total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
  - Hoja `Municipios`: 2465 × 19; merged ranges=11
    - fila 5: `Clave entidad | Entidad 
federativa | Clave municipio | Municipio | Población 
total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
- `IRS_entidades_mpios_2010.xlsx` · `.xlsx` · 542164 bytes
  - Hoja `Estados`: 2458 × 17; merged ranges=8
    - fila 5: `Clave entidad | Entidad federativa | Población total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
  - Hoja `Municipios`: 2467 × 19; merged ranges=13
    - fila 5: `Clave entidad | Entidad 
federativa | Clave municipio | Municipio | Población 
total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
- `IRS_entidades_mpios_2015.xlsx` · `.xlsx` · 517182 bytes
  - Hoja `Estados`: 2457 × 17; merged ranges=8
    - fila 5: `Clave entidad | Entidad federativa | Población total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
  - Hoja `Municipios`: 2457 × 19; merged ranges=11
    - fila 5: `Clave entidad | Entidad 
federativa | Clave municipio | Municipio | Población 
total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
- `IRS_entidades_mpios_2020.xlsx` · `.xlsx` · 551499 bytes
  - Hoja `Estados`: 2458 × 17; merged ranges=8
    - fila 5: `Clave entidad | Entidad federativa | Población total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`
  - Hoja `Municipios`: 2484 × 19; merged ranges=11
    - fila 5: `Clave entidad | Entidad
federativa | Clave municipio | Municipio | Población total | Indicadores de rezago social (porcentaje) | Índice de rezago social | Grado de rezago social`
    - fila 6: `Población de 15 años o más analfabeta | Población de 6 a 14 años que no asiste a la escuela | Población de 15 años y más con educación básica incompleta | Población sin derechohabiencia a servicios de salud`

## Pobreza

- URL solicitada: `https://www.coneval.org.mx/Medicion/Documents/Pobreza_municipal/2020/Concentrado_indicadores_de_pobreza_2020.zip`
- URL final: `https://www.coneval.org.mx/Medicion/Documents/Pobreza_municipal/2020/Concentrado_indicadores_de_pobreza_2020.zip`
- SHA-256: `644d19a9ff6df37908df2f63117bac8ba2cb1f5389d97df03f62fc2c5118d975`
- Bytes: `4401534`

### Miembros del ZIP

- `Concentrado_indicadores_de_pobreza_2020.xlsx` · `.xlsx` · 5017971 bytes
  - Hoja `Concentrado municipal`: 2494 × 147; merged ranges=39
    - fila 5: `Clave de entidad | Entidad federativa | Clave de municipio | Municipio | Población 2010*
(leer nota al final del cuadro) | Población 2015*
(leer nota al final del cuadro) | Población 2020*
(leer nota al final del cuadro) | Pobreza | Pobreza extrema | Pobreza moderada | Vulnerables por carencia social | Rezago educativo | Carencia por acceso a los servicios de salud | Carencia por acceso a la seguridad social | Carencia por calidad y espacios de la vivienda | Carencia por acceso a los servicios básicos en la vivienda | Carencia por acceso a la alimentación | Población con al menos una carencia social | Población con tres o más carencias sociales`
    - fila 6: `Porcentaje
2010 | Porcentaje
2015 | Porcentaje
2020 | Personas
2010 | Personas
2015 | Personas
2020 | Carencias promedio
2010 | Carencias promedio
2015 | Carencias promedio
2020`
    - fila 10: `2067 | 2015`
    - fila 11: `2010 | 1970`
    - fila 17: `2078 | 2047`
    - fila 30: `2016 | 2077 | 2040`
    - fila 37: `2017 | 1916 | 1944 | 2072`
  - Hoja `Concentrado estatal`: 2467 × 145; merged ranges=27
    - fila 5: `Clave de entidad | Entidad federativa | Población 2010*
(leer nota al final del cuadro) | Población 2015*
(leer nota al final del cuadro) | Población 2020*
(leer nota al final del cuadro) | Pobreza | Pobreza extrema | Pobreza moderada | Vulnerables por carencia social | Rezago educativo | Carencia por acceso a los servicios de salud | Carencia por acceso a la seguridad social | Carencia por calidad y espacios de la vivienda | Carencia por acceso a los servicios básicos en la vivienda | Carencia por acceso a la alimentación | Población con al menos una carencia social | Población con tres o más carencias sociales`
    - fila 6: `Porcentaje
2010 | Porcentaje
2015 | Porcentaje
2020 | Personas
2010 | Personas
2015 | Personas
2020 | Carencias promedio
2010 | Carencias promedio
2015 | Carencias promedio
2020`

