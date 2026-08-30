---
id: DS-07
title: "DS-07 · CONEVAL Rezago Social"
owner: "Deni Garrido Fragoso"
status: draft
traces_up: ["01_Product/PRD", "12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, driver-d1]
---

# DS-07 · CONEVAL Rezago Social y Pobreza Municipal

> → [[14_Data_Sources/_index]] · Diseño y URLs oficiales confirmados; prueba de descarga real
> **PENDIENTE DE EJECUCIÓN** antes de pasar la ficha a `in_review`.

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

## 6. Esquema semántico esperado
### IRS
El producto oficial aporta, entre otros: entidad, municipio, población total, indicadores componentes de rezago, Índice de Rezago Social y Grado de Rezago Social.

Los nombres físicos exactos de hoja/columnas deben confirmarse en la prueba real; el extractor debe fallar explícitamente si no reconoce de forma inequívoca el contrato publicado.

### Pobreza municipal
El manual oficial de CONEVAL documenta, entre otras, variables `ent`, `cve_mun`, `pobtot`, `pobreza`, `pobreza_pob` e indicadores adicionales de pobreza/carencias.

Para FARO, `pobreza_pct` se deriva en Silver desde la variable oficial `pobreza`; Bronze conserva el nombre y valor originales.

## 7. Llave de unión y conformación Silver
- **Llave canónica FARO:** clave INEGI municipal de 5 dígitos.
- La homologación a 5 dígitos y el join entre IRS y pobreza son responsabilidad de `silver.rezago_municipio`.
- El período debe provenir de los datos/producto oficial; no debe inventarse mediante un placeholder silencioso.

El contrato downstream actual de `silver.rezago_municipio` se mantiene para no romper Gold: `cve_mun`, `entidad`, `municipio`, `periodo_medicion`, `indice_rezago_social`, `indice_rezago_social_cobertura`, `grado_rezago`, `pobreza_pct`, `pobreza_pct_cobertura` y metadatos.

## 8. Driver que alimenta
- **D1 · Pobreza y rezago social** (junto con DS-08 / CONAPO).

## 9. Prueba de descarga real — PENDIENTE DE EJECUCIÓN
Antes de cambiar `status: draft` → `in_review`:
- [ ] Descargar ambos ZIP directamente desde `www.coneval.org.mx`.
- [ ] Verificar HTTP/redirect final y archivo ZIP válido/no vacío.
- [ ] Registrar SHA-256 de cada ZIP.
- [ ] Identificar workbook(s), hoja(s) y fila(s) de encabezado reales.
- [ ] Contar registros municipales y contrastar cobertura nacional.
- [ ] Verificar clave municipal y duplicados.
- [ ] Confirmar períodos reales presentes.
- [ ] Confirmar columnas físicas IRS y pobreza.
- [ ] Generar Parquet Bronze 1:1 con metadatos.
- **Responsable:** Deni Garrido Fragoso.
- **Fecha de ejecución:** pendiente.

## 10. Riesgos conocidos
- Cambios de estructura, nombres de hoja o encabezados entre ediciones oficiales.
- Claves municipales leídas como numéricas y pérdida de ceros a la izquierda.
- Confundir IRS con medición multidimensional de pobreza; son productos oficiales distintos.
- Mezclar ambos productos dentro de Bronze violaría el landing 1:1 y ocultaría procedencia.
- `coneval_v2` / `coneval_test` son artefactos de desarrollo y no deben acreditarse como fuente oficial real para cerrar DS-07.
