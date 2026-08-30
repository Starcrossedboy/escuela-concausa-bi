---
id: DS-07
title: "DS-07 · CONEVAL Rezago Social"
owner: "Deni Garrido Fragoso"
status: in_review
traces_up: ["01_Product/PRD", "12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, driver-d1]
---

# DS-07 · CONEVAL Rezago Social y Pobreza Municipal

> → [[14_Data_Sources/_index]] · Descarga real oficial ejecutada y auditada; ficha en `in_review`.

## 1. Identificación
- **Institución responsable:** CONEVAL (Consejo Nacional de Evaluación de la Política de Desarrollo Social).
- **Fuente lógica FARO:** `DS-07`.
- **Productos oficiales que componen DS-07:**
  1. **Índice de Rezago Social (IRS)** a nivel entidad federativa y municipio.
  2. **Medición de Pobreza Municipal**.
- **Qué aporta al proyecto:** contexto socioeconómico municipal para D1 (pobreza y rezago social).

> **Regla de arquitectura:** estos dos productos no se fusionan en Bronze. CONEVAL los publica como
> artefactos físicos distintos y el modelo medallón exige landing crudo 1:1. Se conforman únicamente
> en `silver.rezago_municipio`.

## 2. Acceso oficial
### 2.1 Índice de Rezago Social
- **Página institucional:** `https://www.coneval.org.mx/Medicion/IRS/Paginas/Indice_de_Rezago_Social_2020_anexos.aspx`
- **Descarga directa oficial:** `https://www.coneval.org.mx/Medicion/Documents/IRS_2020/IRS_ent_mun_2000_2020.zip`
- **Períodos municipales publicados en el paquete:** 2000, 2005, 2010, 2015 y 2020.
- **Formato de distribución:** ZIP con archivo(s) tabular(es) de CONEVAL.

### 2.2 Pobreza municipal
- **Página institucional:** `https://www.coneval.org.mx/Medicion/Paginas/Pobreza-municipio-2010-2020.aspx`
- **Descarga directa oficial:** `https://www.coneval.org.mx/Medicion/Documents/Pobreza_municipal/2020/Concentrado_indicadores_de_pobreza_2020.zip`
- **Serie comparable municipal publicada:** 2010, 2015 y 2020.
- **Formato de distribución:** ZIP con XLSX oficial.

**Política de origen para FARO:** el extractor debe descargar únicamente desde `https://www.coneval.org.mx/`; no se aceptan mirrors, repositorios de terceros ni archivos sustitutos sin trazabilidad institucional.

## 3. Frecuencia real de actualización
- **IRS municipal:** periodicidad quinquenal en la serie publicada (2000, 2005, 2010, 2015, 2020).
- **Pobreza municipal:** disponibilidad municipal comparable 2010, 2015 y 2020.
- La cadencia operativa debe seguir la publicación oficial, no inferirse de un calendario fijo.

## 4. Cobertura geográfica y temporal
- **Geográfica:** nacional, desagregada a municipio/alcaldía.
- **Período común más reciente para conformación IRS + pobreza:** **2020**.
- Bronze conserva los períodos que entregue cada producto; Silver decide la conformación por `cve_mun + periodo_medicion`.

## 5. Contrato Bronze
DS-07 conserva dos artefactos crudos separados:

| Tabla lógica Bronze | Producto oficial | Regla |
|---|---|---|
| `bronze.coneval_irs_<aaaa>` | Índice de Rezago Social | Copia 1:1 + metadatos de ingesta |
| `bronze.coneval_pobreza_<aaaa>` | Medición de Pobreza Municipal | Copia 1:1 + metadatos de ingesta |

Metadatos obligatorios en ambos:
- `_ingested_at`
- `_source = DS-07_CONEVAL`
- `_source_url` con la URL oficial exacta descargada

No se realizan joins, renombres de negocio, cálculo de claves ni selección de métricas en Bronze.

## 6. Esquema físico confirmado en descarga real
### IRS 2020
- Workbook: `IRS_entidades_mpios_2020.xlsx`.
- Hoja: `Municipios`.
- Encabezado jerárquico: filas Excel 5-6 (`header=[4,5]` en pandas).
- Clave entidad: `Clave entidad`.
- Clave municipio: `Clave municipio`.
- Índice: `Índice de rezago social`.
- Grado: `Grado de rezago social`.

### Pobreza municipal
- Workbook: `Concentrado_indicadores_de_pobreza_2020.xlsx`.
- Hoja: `Concentrado municipal`.
- Encabezado jerárquico: filas Excel 5-6 (`header=[4,5]` en pandas).
- El concentrado conserva 2010, 2015 y 2020 en columnas.
- Pobreza 2020: `Pobreza | Porcentaje 2020`.
## 7. Llave de unión y conformación Silver
- **Llave canónica FARO:** clave INEGI municipal de 5 dígitos.
- La homologación a 5 dígitos y el join entre IRS y pobreza son responsabilidad de `silver.rezago_municipio`.
- El período debe provenir de los datos/producto oficial; no debe inventarse mediante un placeholder silencioso.

El contrato downstream actual de `silver.rezago_municipio` se mantiene para no romper Gold: `cve_mun`, `entidad`, `municipio`, `periodo_medicion`, `indice_rezago_social`, `indice_rezago_social_cobertura`, `grado_rezago`, `pobreza_pct`, `pobreza_pct_cobertura` y metadatos.

## 8. Driver que alimenta
- **D1 · Pobreza y rezago social** (junto con DS-08 / CONAPO).

## 9. Prueba de descarga real — EJECUTADA
- [x] Ambos ZIP descargados directamente desde `www.coneval.org.mx` por HTTPS.
- [x] ZIP y rutas internas validadas; sin redirects fuera del dominio oficial.
- [x] SHA-256 IRS: `9191f6c16ec22452aa970a0fb9a5bbc5cde2057cf48eb81a68d66140289d1cfb`.
- [x] SHA-256 pobreza: `644d19a9ff6df37908df2f63117bac8ba2cb1f5389d97df03f62fc2c5118d975`.
- [x] IRS: **2469 municipios únicos** de 2469.
- [x] Pobreza: **2469 municipios únicos** de 2469.
- [x] Overlap IRS/pobreza: **2469 municipios**.
- [x] IRS: 2469 índices y 2469 grados no nulos.
- [x] Pobreza 2020: 2466 numéricos; **3 ausencias oficiales** a preservar como `SIN_DATO`.
- [x] Bronze Parquet separado para IRS y pobreza con metadatos de ingesta.
- **Responsable:** Deni Garrido Fragoso.
- **Fecha:** 2026-08-30.
## 10. Riesgos conocidos
- Cambios de estructura, nombres de hoja o encabezados entre ediciones oficiales.
- Claves municipales leídas como numéricas y pérdida de ceros a la izquierda.
- Confundir IRS con medición multidimensional de pobreza; son productos oficiales distintos.
- Mezclar ambos productos dentro de Bronze violaría el landing 1:1 y ocultaría procedencia.
- `coneval_v2` / `coneval_test` son artefactos de desarrollo y no deben acreditarse como fuente oficial real para cerrar DS-07.
