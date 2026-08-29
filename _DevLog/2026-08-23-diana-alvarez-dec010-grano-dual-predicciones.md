---
project: "FARO"
date: "2026-08-23"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "corta -- revisión de PR #56 y registro de decisión de esquema"
touches: ["DEC-010", "DEC-007", "REQ-003", "US-311", "US-313"]
tags: [devlog]
---

# DevLog — 2026-08-23 — DEC-010: grano dual en gold.predicciones (PR #56)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

Diana pidió revisar el PR #56 (Héctor Rafael Morales Marbán, "target híbrido de dos niveles",
implementación de DEC-007/RISK-007). El PR tiene dos pendientes dirigidos a Diana:

1. **La serie SNIEE que Héctor esperaba para `unir_target()` ya existe.** Su propio commit
   `d711fc3` ("feat(gold): matricula_municipio_nivel, agregado municipio x nivel x ciclo para
   unir_target()", RISK-007/DEC-007) ya está mergeado a `main` desde el PR #68, con datos reales
   materializados hoy mismo (72 filas). DEC-007 nunca exigía la serie pública SNIEE en sí — su
   propio texto dice que "es la misma fuente DS-01 en otra distribución (agregada)" — así que
   `matricula_historica`/`matricula_municipio_nivel` (construida con `formato911_historico`)
   cumple el requisito sin desviarse de la decisión. Esto desbloquea el gate del 30-ago de
   inmediato, no hasta esa fecha. Se preparó un comentario para avisarle a Héctor en el PR.

2. **Decisión de contrato**: `gold.predicciones` tiene grano `cct × ciclo × modelo`; con ML-01
   prediciendo a veces a `municipio × nivel` (DEC-007), Héctor preguntó si repartir el valor a
   cada escuela del grupo o si la tabla admite ambos granos, junto con Imanol Ruiz Hurtado (C4,
   dueño de `PrediccionOut`). Diana decidió **admitir ambos granos**, consistente con el principio
   ya aplicado en DEC-008/DEC-009 esta misma semana: nunca inventar un dato a un nivel que no se
   midió. Registrada como **DEC-010**.

## Decisión

`gold.predicciones` agrega un discriminador `grano` (`escuela` | `municipio_nivel`) y las
columnas `cve_mun`+`nivel` como llaves alternativas a `cct` — exactamente una de las dos debe
estar poblada según `grano`. `gold.recomendaciones` no cambia: se mantiene siempre a grano
escuela (el carácter prescriptivo no se agrega).

La forma exacta del contrato de la API (`PrediccionOut`) queda **pendiente de que Imanol Ruiz
Hurtado (Tech Lead Célula 4) la confirme** — la parte de esquema Gold es de Diana (regla 7), pero
el tipo que expone la API es co-propiedad de C4. Se le etiquetó en el comentario del PR.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude (Cowork), claude-sonnet-5
- **Archivos creados/modificados:**
  - `10_Risk_Governance/Decision_Log.md` (nueva fila DEC-010)
  - `03_Architecture/Data_Model.md` (§4.5 — grano dual + nota de diseño)
  - `02_Requirements/Traceability_Matrix.md` (fila REQ-003 — evidencia DEC-010)
  - `_DevLog/_index.md` (fila nueva)
  - `_DevLog/2026-08-23-diana-alvarez-dec010-grano-dual-predicciones.md` (este archivo)
- **Decisiones autónomas del agente:** ninguna de fondo — el agente investigó la conexión entre
  PR #56 y el trabajo de RISK-007/DEC-007 ya mergeado (no era obvia, requirió revisar el `git log`)
  y propuso la opción "ambos granos" con su razonamiento, pero la decisión final y el alcance
  exacto (qué queda pendiente de Imanol) los confirmó Diana.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** revisar PR #56 (Héctor) y su pregunta pendiente para Diana.

## Seguridad / calidad
- [ ] Pendiente: `python _Meta/scripts/vault_lint.py .` y `pytest tests/ -q` (Diana, antes del PR)
- [x] Cambio de esquema (regla 7) — revisión humana explícita de Diana (Tech Lead Célula 1); la
      parte de API queda explícitamente marcada como pendiente de Imanol, no se le impone

## Próximos pasos
- Diana: commitear, pushear y abrir PR con estos cambios.
- Diana: publicar el comentario en PR #56 avisando de `gold.matricula_municipio_nivel` y
  proponiendo el grano dual, etiquetando a Imanol Ruiz Hurtado.
- Imanol: confirmar o ajustar la forma de `PrediccionOut` para el grano dual.
- Héctor: actualizar sus referencias de "DEC-005" a "DEC-007" en el PR #56 (colisión ya resuelta
  por Edgar, pendiente de reflejarse en sus artefactos).