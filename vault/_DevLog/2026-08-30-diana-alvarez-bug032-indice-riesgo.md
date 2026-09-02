---
project: "FARO"
date: "2026-08-30"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~15 min"
touches: ["BUG-032"]
tags: [devlog, docs, data-model, bug032]
---

# BUG-032 — Corrige contradicción sobre dónde vive `indice_riesgo`

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

**Contexto.** Héctor Rafael Morales Marbán (C3) reportó BUG-032 el 29-ago al cerrar los
pendientes de `DOC-INDICE-RIESGO`: `Data_Model.md` se contradecía sobre dónde vive
`indice_riesgo`. La línea 181 (§4.5) lo describe correctamente como columna propia de
`gold.predicciones` (float[0,1], derivada en `src/modelos/riesgo.py`) — lo implementado y lo
que consume la API (`src/api/schemas.py` declara `indice_riesgo: StrictFloat | None`). Pero la
nota de la línea 313 (§5.3) afirmaba que vivía "en la columna `valor`". Quien siguiera §5.3
consultaría `valor` esperando `[0,1]` y recibiría la variación cruda, hoy en alumnos absolutos.

**Fix.** Se corrige la nota de la línea 313 de `Data_Model.md` para que diga que `indice_riesgo`
es su propia columna (no vive en `valor`), consistente con la línea 181. `Bug_Register.md`:
BUG-032 pasa de `open` a `fixed`.

## Cómo se probó

python vault/_Meta/scripts/vault_lint.py .
→ Vault limpio (6 huérfanos informativos, no bloqueantes — no relacionados con este cambio)

pytest tests/ -q
→ 643 passed, 5 skipped, 1 warning (requirió `pip install -r requirements.txt` primero;
faltaba `slowapi`/`limits` del endurecimiento de Christian, US-404 — no relacionado con este fix)

## Archivos tocados

- `vault/03_Architecture/Data_Model.md` (nota de la línea 313)
- `vault/06_Quality_Testing/Bug_Register.md` (estado de BUG-032)