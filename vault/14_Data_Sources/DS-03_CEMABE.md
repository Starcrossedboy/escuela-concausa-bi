---
id: DS-03
title: "DS-03 · SEP CEMABE"
owner: "Deni Garrido Fragoso"
status: draft
traces_up: ["vault/01_Product/PRD", "vault/12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, driver-d3, driver-d4]
---

# DS-03 · SEP CEMABE (Censo de Escuelas, Maestros y Alumnos de Educación Básica y Especial)

> → [[vault/14_Data_Sources/_index]] · Prueba de descarga real **PENDIENTE** (Semana 1)

## 1. Identificación
- **Nombre oficial:** CEMABE — Censo de Escuelas, Maestros y Alumnos de Educación Básica y Especial.
- **Institución responsable:** INEGI en coordinación con SEP.
- **Qué aporta al proyecto:** **infraestructura por escuela** (agua, drenaje, electricidad, sanitarios,
  internet, computadoras). Es la "joya escondida": datos **a nivel escuela** que alimentan dos drivers
  nacionales.

## 2. Acceso
- **URL de descarga:** PENDIENTE-CONFIRMAR (portal esperado: INEGI / SEP).
- **Formato:** CSV.
- **Tamaño aproximado:** PENDIENTE-CONFIRMAR.

## 3. Frecuencia real de actualización
- **Censo único 2013** (no se actualiza periódicamente). Se trata como snapshot estructural.

## 4. Cobertura geográfica y temporal
- **Geográfica:** Nacional · nivel escuela.
- **Temporal:** levantamiento **2013**.

## 5. Esquema esperado (confirmar en prueba de descarga)
| Columna | Tipo | Nota |
|---|---|---|
| `cct` | str (10) | Llave escuela |
| `agua_red` | bool/str | Disponibilidad de agua |
| `drenaje` | bool/str | Drenaje |
| `electricidad` | bool/str | Energía eléctrica |
| `sanitarios` | int/bool | Servicios sanitarios |
| `internet` | bool/str | Conexión a internet |
| `computadoras` | int | Equipos de cómputo |

## 6. Llave de unión
- **CCT** (escuela). Deriva **clave INEGI de 5 dígitos** para agregados municipales.

## 7. Driver que alimenta
- **D3 · Infraestructura escolar** (agua, drenaje, luz, sanitarios).
- **D4 · Conectividad digital** (internet / computadoras).

## 8. Licencia de uso
- Términos de Libre Uso MX (INEGI) — **confirmar** en la ficha oficial.

## 9. Prueba de descarga real — **PENDIENTE** (Semana 1)
- [ ] Archivo descargado físicamente
- [ ] Abierto y con datos utilizables
- [ ] Registros contados: `______`
- [ ] Esquema verificado (columnas y tipos)
- [ ] Llave confirmada: CCT presente y cruzable con DS-02
- **Responsable:** Deni Garrido Fragoso · **Fecha:** ______

## 10. Riesgos conocidos
- **Antigüedad (2013):** la infraestructura pudo cambiar; documentar como limitación temporal.
- Cobertura de educación básica/especial (no media superior).
- CCT que ya no existen en el catálogo actual (DS-02) → filas huérfanas.
- Campos booleanos codificados de forma heterogénea (1/0, Sí/No, texto).
