---
id: DS-06
title: "DS-06 · CONAGUA SINA"
owner: "Emilio Galnares Ruiz"
status: draft
traces_up: ["01_Product/PRD", "12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, driver-d5, ingesta-continua]
---

# DS-06 · CONAGUA SINA (Sistema Nacional de Información del Agua)

> → [[14_Data_Sources/_index]] · Prueba de descarga real **PENDIENTE** (Semana 1)
> **Ingesta continua #3** (diaria).

## 1. Identificación
- **Nombre oficial:** SINA — Sistema Nacional de Información del Agua.
- **Institución responsable:** CONAGUA (Comisión Nacional del Agua).
- **Qué aporta al proyecto:** disponibilidad hídrica, nivel de presas y estrés hídrico regional.

## 2. Acceso
- **URL de descarga / API:** PENDIENTE-CONFIRMAR (portal esperado: SINA / CONAGUA).
- **Formato:** CSV / API.
- **Tamaño aproximado:** PENDIENTE-CONFIRMAR.

## 3. Frecuencia real de actualización
- **Diaria.** → satisface el requisito de ingesta continua.

## 4. Cobertura geográfica y temporal
- **Geográfica:** **Regional** (por región hidrológica / presa, no por municipio directo).
- **Temporal:** serie histórica por estación/presa; confirmar profundidad en la prueba de descarga.

## 5. Esquema esperado (confirmar en prueba de descarga)
| Campo | Tipo | Nota |
|---|---|---|
| `id_estacion` / `id_presa` | str | Identificador del punto |
| `region_hidrologica` | str | Región |
| `latitud` | float | Georreferencia |
| `longitud` | float | Georreferencia |
| `indicador` | str | Nivel / almacenamiento / disponibilidad |
| `valor` | float | Medición |
| `fecha` | date | Marca temporal diaria |

## 6. Llave de unión
- **Geoespacial / regional**: se asocia a municipios por región hidrológica o por cercanía (lat/lon).
  Donde no aplica → **`SIN_DATO`**. No hay CCT ni clave INEGI directa.

## 7. Driver que alimenta
- **D5 · Estrés hídrico regional** (parcial).

## 8. Licencia de uso
- Términos de Libre Uso MX (CONAGUA) — **confirmar** en la ficha oficial.

## 9. Prueba de descarga real — PENDIENTE (Semana 1)
- [x] Fuente identificada y accesible: https://sisuar.imta.mx/aplicacion/vista/presa/presas.php
      (IMTA, con datos oficiales de CONAGUA)
- [x] Datos utilizables — confirmado
- [x] Registros contados: listado principal con múltiples presas a nivel nacional
      (filtrable por Organismo de Cuenca y Estado); cada presa tiene su propia serie
      histórica de "Vol. de almacenamiento (hm3)" por año (ej. presa 118 - Der. Jocoqui:
      2 registros, años 2017-2018).
- [x] Esquema verificado:
      - Listado general: Nombre Oficial, Corriente, Altura de cortina (m),
        Capacidad al NAME (hm3), Capacidad al NAMO (hm3), Estado, Año Término
      - Detalle por presa: Presa, Año, Vol. de almacenamiento (hm3) — SERIE DE TIEMPO
        confirmada (no es un valor fijo)
- [x] Llave confirmada: nombre/ID de presa + Estado (texto). NO trae clave INEGI de
      municipio directa; requiere mapeo posterior (Estado → municipio vía otra fuente,
      o geoespacial con lat/lon del catálogo de datos.gob.mx).
- **Responsable:** Emilio Galnares Ruiz · **Fecha:** 16/08/2026

## 10. Riesgos conocidos (actualizado)
- No hay descarga CSV/API directa: los datos están en tablas web (HTML), se requiere
  automatizar la consulta (scraping) en US-122a para extraer el histórico completo.
- La granularidad temporal varía por presa (algunas solo tienen 2 años, otras podrían
  tener series más largas) — se debe confirmar rango real al construir el extractor.
- Llave de unión a municipio no es directa (ver sección 6); requiere regla de cruce.
