---
id: DS-01
title: "DS-01 · SEP Formato 911"
owner: "Diana Aracely Alvarez Varela"
status: draft
traces_up: ["01_Product/PRD", "12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, hecho-central]
---

# DS-01 · SEP Formato 911

> → [[14_Data_Sources/_index]] · Prueba de descarga real — 911 crudo confirmado, **6 ciclos** (2019-2020 a 2024-2025), serie SNIEE municipio×nivel aún pendiente (ver §9/§9a)

## 1. Identificación
- **Nombre oficial:** Estadística Educativa — Formato 911.
- **Institución responsable:** SEP (Secretaría de Educación Pública), vía SIGED / datos.gob.mx.
- **Qué aporta al proyecto:** matrícula, docentes y grupos **por CCT y ciclo escolar**. Es el
  **hecho central** del proyecto (`fact_escuela_ciclo`). Unidad de observación = ESCUELA, nunca el
  alumno (privacidad por diseño).

## 2. Acceso
- **URL de descarga:** PENDIENTE-CONFIRMAR (portal esperado: SIGED / datos.gob.mx).
- **Formato:** CSV / XLSX.
- **Tamaño aproximado:** PENDIENTE-CONFIRMAR.
- **Distribución alterna — serie SNIEE:** la SEP publica esta **misma fuente ya agregada** a nivel
  `municipio × nivel` como serie **multi-año** (SNIEE / Sistema de Consulta de Estadística Educativa,
  planeacion.sep.gob.mx — URL PENDIENTE-CONFIRMAR). **No es una 9ª fuente**, es DS-01 en otra
  distribución. Es la vía que habilita el **target real multi-año** por `DEC-007` sin reconstruir años
  crudos del 911 (el 911 crudo aporta el desglose por escuela para features y driver dominante).

## 3. Frecuencia real de actualización
- **Anual**, por ciclo escolar (inicio de cursos).

## 4. Cobertura geográfica y temporal
- **Geográfica:** Nacional.
- **Temporal:** serie desde el ciclo **1990-91** (confirmar disponibilidad de años recientes en la
  prueba de descarga).

## 5. Esquema esperado (confirmar en prueba de descarga)
| Columna | Tipo | Nota |
|---|---|---|
| `cct` | str (10) | Clave de Centro de Trabajo — llave |
| `ciclo` | str | Ciclo escolar, p. ej. `2023-2024` |
| `entidad` | str (2) | Clave INEGI de entidad |
| `municipio` | str (3/5) | Clave de municipio |
| `nivel` | str | Nivel educativo |
| `alumnos_total` | int | Matrícula total |
| `docentes_total` | int | Plantilla docente |
| `grupos_total` | int | Número de grupos |

## 6. Llave de unión
- **CCT** (escuela). Deriva **clave INEGI de 5 dígitos** (entidad+municipio) para cruces municipales.

## 7. Driver que alimenta
- Ninguno directamente: **es el hecho central (matrícula)** sobre el que se calculan el riesgo y la
  variación. Todos los drivers se cruzan contra este hecho.

## 8. Licencia de uso
- Términos de Libre Uso MX (datos.gob.mx) — **confirmar** en la ficha oficial.

## 9. Prueba de descarga real — 6 ciclos cerrados (ver detalle 2026-08-22)
- [x] Archivo descargado físicamente — **6 ciclos reales** (2019-2020, 2020-2021, 2021-2022,
  2022-2023, 2023-2024, 2024-2025), ver DevLog 2026-08-21/22
- [x] Abierto y con datos utilizables
- [x] Registros contados: 230,424 / 228,852 / 228,804 / 229,691 / 231,534 / 231,913 filas
  (2019-2020 / 2020-2021 / 2021-2022 / 2022-2023 / 2023-2024 / 2024-2025) — 0 filas con
  `matricula_total` no numérico en ninguno de los 6
- [x] Esquema verificado (columnas y tipos) — los 6 parsean con `_parsear_ciclo` sin adivinar nada
- [x] Llave confirmada: CCT presente y válido (`clave_cct`/`clavecct` según ciclo, ver extractor) en
  los 6 ciclos
- [ ] **Serie SNIEE municipio×nivel descargada** (≥2 años; habilita el target real de `DEC-007`) para las
  4 entidades de `SCOPE_ENTIDADES` — **NO localizada, ver §9a**
- **Responsable:** Diana Aracely Alvarez Varela · **Fecha:** 2026-08-21/22

### 9a. Intento 2026-08-22 (a petición de Edgar) — resultado

- **2º ciclo crudo (2023-2024):** ~~el entorno cloud de esta sesión no tiene salida general a
  internet, pendiente reintentar desde una máquina con internet real~~ — **superado**: Diana
  descargó y validó los 6 ciclos completos (incluido 2023-2024) desde su propia máquina, ver §9.
- **Serie SNIEE municipio×nivel:** búsqueda razonablemente exhaustiva vía `WebSearch`/`WebFetch`
  sobre los 3 portales que esta misma ficha ya nombraba
  ([`planeacion.sep.gob.mx`](https://www.planeacion.sep.gob.mx/estadisticaeducativas.aspx),
  [`siged.sep.gob.mx`](https://siged.sep.gob.mx/SIGED/estadistica_educativa.html), `snie.sep.gob.mx`)
  más descubrimiento orgánico (Atlas de servicios educativos por estado, Principales Cifras,
  tabulados de INEGI). **No se encontró ninguna descarga pública a nivel municipio×nivel×ciclo.**
  Lo público y descargable en bloque que sí existe es a nivel **entidad** (serie histórica
  1990-91→2030-31,
  [`serie_historica_entidades_sep.xlsm`](https://www.planeacion.sep.gob.mx/Doc/estadistica_e_indicadores/serie_historica_entidades_sep.xlsm) /
  [`.zip`](https://www.planeacion.sep.gob.mx/Doc/estadistica_e_indicadores/serie_historica_entidades_sep.zip)).
  El Atlas por estado (ej.
  [Estado de México](https://planeacion.sep.gob.mx/Doc/Atlas_estados/estado_de_mexico.pdf)) sí
  desagrega por municipio, pero son indicadores de infraestructura/censo (agua, luz, internet,
  asistencia escolar por edad), **no matrícula por nivel educativo**. `snie.sep.gob.mx` no resolvió
  de forma estable (DNS/redirect). No se localizó ningún "sistema de consulta interactivo" con URL
  pública enlazada — si existe, probablemente requiere navegar un formulario/dropdown en vivo, no
  un archivo descargable, lo cual queda fuera del alcance de búsqueda automatizada.
  **Riesgo a escalar con Edgar/Célula 1: la premisa de `DEC-007`/`DOC-TARGET-HIBRIDO` de que la
  serie SNIEE es "la misma fuente DS-01 en otra distribución" pública y descargable puede no ser
  correcta — hasta ahora no se ha confirmado que exista en bloque a nivel municipio.** Alternativas
  a valorar: (a) solicitud directa a SEP/DGPPYEE, (b) navegación manual de algún sistema de consulta
  interactivo si existe, (c) aceptar el fallback ya previsto en `DOC-TARGET-HIBRIDO` §5 (índice
  compuesto `SIN_DATO_REAL`) si nada aterriza para el gate del 30 de agosto.

> Trazas: [[10_Risk_Governance/Decision_Log]] (`DEC-007`) · [[10_Risk_Governance/Risk_Register]] (RISK-007)
> · [[02_Requirements/User_Stories]] (US-104)

## 10. Riesgos conocidos
- Cambios de esquema entre ciclos (columnas que se renombran o desaparecen).
- Codificación/acentos inconsistentes en campos de texto.
- Posible desfase de publicación del ciclo más reciente.
- CCT con formato heterogéneo entre entregas (ceros a la izquierda).