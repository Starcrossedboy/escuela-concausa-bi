---
project: "FARO"
date: "2026-08-21"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión única: cierre de US-211a y puesta al día del ambiente local"
touches: ["US-211a", "REQ-002", "DOC-CUBESPEC-DB0304", "DOC-TRACE-MATRIX", "SPRINT-MARINA-GARCIA-DEL-BUEY"]
tags: [devlog, bi, cubos, capa-semantica, cierre, celula-2]
---

# DevLog — 2026-08-21 — Cierre de US-211a al 100%

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

US-211a se entregó el 14 de agosto (PR #32) al **90%**: el contrato semántico, el SQL de referencia, la
capa semántica y las 28 pruebas estaban completos, pero quedaban dos respuestas ajenas registradas como
solicitudes formales en §8 del contrato. **Ambas llegaron**, así que la historia se puede cerrar al 100%
dentro de su sprint (S3, vence el domingo 23).

## Qué se hizo

### Cierre de la historia

- **`vault/04_UX_Design/Cube_Specs_DB03_DB04.md`**: `status` `in_review` → **`approved`**, `last_reviewed`
  → 2026-08-21. §2.2 y §8.3 marcadas como ratificadas, §8.1 como aceptada, §8.2 sigue abierta con nota
  de que no bloquea. §5.1 pasa de "propuesta" a "publicados por Manuel", señalando su catálogo como
  fuente canónica.
- **Plan de sprint §9**: US-211a → ✅ Terminado, 100%. El "Bloqueado por" de US-212 se acota a US-113.
- **`vault/02_Requirements/Traceability_Matrix.md`**: fila de REQ-002 con este DevLog.

### Verificación de alineación (lo que más importaba)

Se comparó línea por línea el catálogo de Manuel contra el contrato de Marina. **KPI-15…KPI-18
reproducen exactamente el SQL de §3.2**: mismo `CASE WHEN p.indice_riesgo IS NULL THEN NULL`, mismos
`LEFT JOIN` a `gold.predicciones` / `gold.recomendaciones`, mismo umbral 0.6 y mismas banderas
`cobertura_prediccion` / `cobertura_recomendacion`. **Cero divergencias**: el contrato y el catálogo
canónico dicen lo mismo, así que no hay riesgo de que DB-03 se construya contra dos definiciones.

Lo mismo con `Data_Model` §4.3: el grano quedó en `municipio × nivel × ciclo` con métricas aditivas,
que es literalmente lo que pedía §8.1.

### Ambiente local

- **`.venv` recreado con Python 3.11.9** (antes 3.12.10, desalineado con el CI). Suite completa:
  **209 passed, 4 skipped**.
- `requirements.txt` reinstalado — faltaba `python-jose` (US-402) y rompía la colección de pytest.
- Restaurada una edición local accidental que había partido en dos la línea 37 del plan de sprint.
- `.env` creado desde la plantilla; los valores los llena la humana (no pasan por el agente).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:**
  - `vault/04_UX_Design/Cube_Specs_DB03_DB04.md`
  - `vault/12_Roadmap_Sprints/Sprints/2-marina-garcia-del-buey.md`
  - `vault/02_Requirements/Traceability_Matrix.md`
  - `vault/_DevLog/2026-08-21-marina-garcia-cierre-us211a.md` (nuevo) · `vault/_DevLog/_index.md`
- **Decisiones autónomas del agente:** ninguna de alcance. No se tocó `Screen_Specs.md` (Manuel),
  `Data_Model.md` (Diana), `dbt/` (C1) ni `vault/_Meta/` (PM).
- **Manejo de secretos:** el agente **no** ejecutó `scripts/generate-keys.py` ni leyó el contenido de
  `.env`; solo contó placeholders pendientes. Las credenciales nunca entraron al prompt.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] `pytest tests/ -q` → 209 passed, 4 skipped
- [x] `python vault/_Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

- **US-212 está bloqueada por US-113** (Deni Garrido, C1): `dbt/models/gold/` no tiene ningún
  `cubo_*.sql`. La Célula 1 tiene el SQL de referencia desde el 14 de agosto. Vence el mismo domingo 23.

## Pendiente de coordinación (no editado por Marina)

- **Diana Alvarez (C1):** §8.2 — confirmar la codificación de `SIN_DATO` en `d1`…`d6`. No bloquea.
- **PM:** pasar US-211a de `in_review` a `done` en el tablero, y registrar en
  [[vault/10_Risk_Governance/Decision_Log]] el cambio de grano — la propia nota de Diana en `Data_Model` §4.3
  lo deja marcado como pendiente.
- **Reportado en su momento y aún abierto:** `vault/_Meta/scripts/vault_lint.py` truena con
  `UnicodeEncodeError` al imprimir en consolas Windows (cp1252). `vault/_Meta/**` es del PM.

## Próximos pasos

- **US-212 (S4):** construir DB-03 y DB-04 en cuanto C1 entregue los cubos.
- Levantar Docker con el `.env` completo y congelar `requirements/celula-2.txt`.
