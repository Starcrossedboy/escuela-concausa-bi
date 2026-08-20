---
id: DS-01
title: "DS-01 · SEP Formato 911"
owner: "Diana Aracely Alvarez Varela"
status: draft
traces_up: ["01_Product/PRD", "12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, hecho-central]
---

# DS-01 · SEP Formato 911

> → [[14_Data_Sources/_index]] · Prueba de descarga real **PENDIENTE** (Semana 1)

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
  distribución. Es la vía que habilita el **target real multi-año** por `DEC-005` sin reconstruir años
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

## 9. Prueba de descarga real — **PENDIENTE** (Semana 1)
- [ ] Archivo descargado físicamente (o API llamada)
- [ ] Abierto y con datos utilizables
- [ ] Registros contados: `______`
- [ ] Esquema verificado (columnas y tipos)
- [ ] Llave confirmada: CCT presente y válido
- [ ] **Serie SNIEE municipio×nivel descargada** (≥2 años; habilita el target real de `DEC-005`) para las
  4 entidades de `SCOPE_ENTIDADES`
- [ ] **Intento de 2º ciclo crudo del 911** (2023-2024 / 2022-2023) con mapeo de esquema entre ciclos
  (ver §10) — si aterriza antes del gate S4, sube la granularidad del target a escuela
- **Responsable:** Diana Aracely Alvarez Varela · **Fecha:** ______

> Trazas: [[10_Risk_Governance/Decision_Log]] (`DEC-005`) · [[10_Risk_Governance/Risk_Register]] (RISK-007)
> · [[02_Requirements/User_Stories]] (US-104)

## 10. Riesgos conocidos
- Cambios de esquema entre ciclos (columnas que se renombran o desaparecen).
- Codificación/acentos inconsistentes en campos de texto.
- Posible desfase de publicación del ciclo más reciente.
- CCT con formato heterogéneo entre entregas (ceros a la izquierda).
