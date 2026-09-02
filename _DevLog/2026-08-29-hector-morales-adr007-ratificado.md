---
project: "FARO"
date: "2026-08-29"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "45min"
touches: ["ADR-007", "DEC-006", "BUG-017", "BUG-019", "BUG-032", "US-311", "US-313", "REQ-003"]
tags: [devlog, celula-3, adr, gobernanza]
---

# DevLog — 2026-08-29 — ADR-007 ratificado: se asienta la decisión y se aclara qué falta

→ [[_DevLog/_index|Volver al índice]]

## Lo que encontré al validar

La reunión ratificó ADR-007, pero **la decisión no existía en el repositorio**. Los cuatro lugares
donde debía estar:

| Dónde | Estado antes |
|---|---|
| `ADR-007` frontmatter | `status: proposed` |
| `03_Architecture/ADRs/_index.md` | `**proposed**` |
| `10_Risk_Governance/Decision_Log.md` | cero menciones |
| `features_escuela.sql:71` | sigue en diferencia absoluta |

Un acuerdo que sólo vive en la memoria de quienes asistieron no es un acuerdo para quien no estuvo.

## Lo que asenté

`ADR-007` pasa a **`accepted`** con fecha 29-ago, y el índice de ADRs con él. Añadí una tabla de
**qué falta para que la ratificación surta efecto**, porque ratificar no cambia el dato: mientras
`features_escuela.sql` siga calculando `matricula_total - matricula_ciclo_anterior`, mi
`verificar_escala_variacion()` seguirá deteniendo la publicación — correctamente.

El paso que bloquea a los otros tres es de Célula 1 y **hoy no tiene responsable asignado**.

### Por qué no lo puse en el `Decision_Log`

Su propio encabezado dice: *"Decisiones de proceso/producto (las técnicas van a
`03_Architecture/ADRs`)"*. Duplicarlo ahí violaría además la regla 1 del vault —un tema, un archivo
canónico—. Lo menciono porque yo mismo lo había propuesto antes de leer esa nota. Si el PM quiere una
referencia cruzada, es su archivo.

## `DOC-INDICE-RIESGO`: de tres preguntas abiertas a una

El documento listaba tres cosas por ratificar. Al revisarlas, **dos ya estaban cerradas por hechos**:

- **El umbral de −5 %** lo ratificó `DEC-006` el 13-ago. El documento seguía pidiéndolo 16 días
  después.
- **`indice_riesgo` vs variación cruda** se resolvió en la implementación: se publican **ambos**.

Queda **una sola**: el ancla `0.30` para escuela estable. La replanteé por lo que se ve en pantalla y
no por la sigmoide, que es como se puede decidir:

> ¿Una escuela que no pierde un solo alumno debe aparecer con **30 % de riesgo** en el tablero?

No es inocuo: mueve el punto medio de la escala — hoy un riesgo de `0.50` equivale a perder 3.4 %.
Firman Manuel Serranía y Marina García (es lo que muestran sus tableros) y Christian Ruiz (contrato
de la API). Mientras siga abierta, el documento se queda en `in_review`; no lo promoví.

Una coincidencia que vale registrar: **`DEC-006` ya presuponía la fracción** al definirse como
"pérdida de ~5 % de matrícula". Ratificar ADR-007 no fue una decisión nueva sino hacer explícito lo
que el equipo ya había supuesto en agosto.

## BUG-032 — `Data_Model.md` se contradice a sí mismo

Apareció al cerrar el punto 4.3. La línea 181 (§4.5) describe `valor` e `indice_riesgo` como columnas
distintas —que es lo implementado y lo que consume la API—, pero la nota de la **línea 313** dice que
`indice_riesgo` vive *"en la columna `valor`"*.

Quien siga §5.3 consultaría `valor` esperando un `[0,1]` y recibiría la variación cruda, hoy en
alumnos absolutos: `-20` donde espera `0.6`, sin que nada falle. Es el modo de falla de BUG-017 otra
vez. Archivo de Célula 1: registrado, no corregido.

## De paso

Mi venv local estaba desactualizado y la suite tronaba con `ModuleNotFoundError: limits`. **No era un
defecto del repo**: `slowapi` sí está en `requirements.txt` desde el hardening de Christian (#145) y
el CI de `main` está verde. Lo anoto porque mi primer impulso fue reportarlo como CI roto — verificar
antes de avisar evitó un falso positivo al equipo.

## Verificación

Suite **643 passed, 5 skipped**. Ruff y `vault_lint` limpios. Sin cambios de comportamiento: esto es
gobernanza y documentación.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `03_Architecture/ADRs/ADR-007-*`, `03_Architecture/ADRs/_index.md`,
  `15_ML_Models/Indice_Riesgo_ML01.md`, `src/modelos/riesgo.py` (nota de estatus),
  `06_Quality_Testing/Bug_Register.md`, `02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:**
  - No duplicar el acuerdo en el `Decision_Log`, contra lo que yo mismo había propuesto: el propio
    archivo dice que las decisiones técnicas van a los ADRs.
  - No registrar quiénes asistieron a la reunión: asiento el acuerdo, la asistencia la confirma el PM.
  - No promover `DOC-INDICE-RIESGO` a `approved`: el ancla `0.30` sigue abierta.
- **Correcciones manuales:** revisión línea por línea.

## Pendientes

1. **Célula 1 normaliza el target y reprocesa Gold.** Es el único eslabón entre la ratificación y que
   la demo muestre predicciones. Sin dueño asignado.
2. **Regenerar las 45 249 filas** ya publicadas con la unidad vieja, y reentrenar ML-01.
3. **Ancla `0.30`** — decisión de negocio.
4. **BUG-032** con Célula 1.
