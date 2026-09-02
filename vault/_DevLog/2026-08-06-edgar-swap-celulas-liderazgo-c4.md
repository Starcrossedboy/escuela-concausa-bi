---
project: "FARO"
date: "2026-08-06"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "re-aplicación del swap de células, liderazgo de C4 y pestañas del tablero"
touches: ["US-003", "US-004", "REQ-007", "US-CATALOG", "PLAN-MAESTRO", "DOC-ONBOARD", "RPT-PM-SPEC", "TEST-002"]
tags: [devlog, equipo, celulas, liderazgo, dashboard, governance]
---

# DevLog — 2026-08-06 — swap de células, liderazgo C4 y pestañas del tablero

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/12_Roadmap_Sprints/PLAN_MAESTRO|Plan Maestro]] · [[vault/13_Reports/_index|Tablero PM]]

## Contexto y diagnóstico

- Se detectó que el intercambio de célula de Eloisa/Oscar (commit `87cf678`, ya en `main`) había sido
  **revertido** por el commit `7eb2974 "restaura equipo en tablero PM"` en la rama de trabajo. Por eso
  Eloisa volvía a aparecer en Célula 2. No fue una edición fallida sino una regresión posterior.

## Qué se hizo

- **Item 1 — Eloisa ↔ Oscar (re-aplicado):** Eloisa → **Célula 4** (Desarrolladora jr · Pruebas de API,
  US-421/422/423); Oscar → **Célula 2** (Analista BI jr · Gráficos, mapas y KPIs, US-221…224). Body-swap
  por rename de planes de sprint y de sus Agent Contexts; catálogo, roster, calendario, onboarding e índices.
- **Item 2 — Liderazgo de Célula 4:** **Christian Imanol Ruiz Hurtado** pasa a **Tech Lead** (nivel Alto,
  US-401…404) y **Karla Alejandra Monter Benitez** a Desarrolladora backend (nivel Medio, US-411/413/414).
  Se conserva la distribución 4 Alto · 8 Medio · 9 Bajo y la convención "Tech Lead = Alto".
- Se actualizaron **16 Agent Contexts** de otras células que apuntaban a "Karla Monter (C4)" como contacto
  de backend/seguridad → ahora **Christian Ruiz (C4)**; también `RACI.md` (accountable de C4) y la tabla de
  células de `CLAUDE.md`.
- **Item 3:** todo regenerado con `generate_pm_dashboard.py` desde las fuentes canónicas.
- **Item 4:** se añadieron dos pestañas a `TABLERO_CONTROL_PM.template.html`, calculadas 100% desde el
  snapshot: **Plan general** (avance esperado vs. real por sprint, carga célula×sprint y cadena de
  dependencias entre células) y **Foco por sprint** (matriz células×sprint del trabajo urgente/relevante:
  🔴 bloqueada · ⏳ en riesgo por antigüedad · ⭐ historia del Tech Lead).
- **Ampliación (misma sesión):** se agregó la pestaña **Dependencias por US** (selección por célula →
  US/responsable, con entregable requerido, "recibe de/entrega a", revisor, cadena de valor entre
  células y bloqueos asociados; mismo modo de uso que "Plan por persona"). Se confirmaron los usuarios
  de GitHub de **Emilio Galnares Ruiz** (`Starcrossedboy`) y **Carlos Guillermo Mayorga Tapia**
  (`cmayorgat44`) en el onboarding (queda pendiente solo Oscar).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / opus-4-8.
- **Método:** script coordinado (misma técnica de body-swap de `87cf678`) con aserciones, y verificación
  con la red de seguridad del pipeline.
- **Decisiones autónomas:** intercambiar también el nivel Alto/Medio entre Christian y Karla (confirmado
  por el PO) para no romper la invariante "Tech Lead = Alto"; definir el foco de forma auto-derivada del
  estado (sin campos manuales nuevos).

## Verificación

- `generate_pm_dashboard.py` → 87 US, 21 personas, 8 fuentes.
- `validate_pm_dashboard.py` → ✅ TEST-002 válido.
- `vault_lint.py` → ✅ Vault limpio.
- Render de las dos pestañas verificado en navegador sin errores de consola.
- Snapshot: Eloisa (C4/US-421-423), Oscar (C2/US-221-224), Christian (C4/Alto/Tech Lead), Karla (C4/Medio);
  RACI accountable de C4 = Christian; sin referencias colgantes a archivos renombrados.

## Trazabilidad

- IDs sin reciclar: cada plan/Agent Context conserva su `SPRINT-*` / `AGENTCTX-*` por persona.
- `traces_up`/`traces_down` y wikilinks actualizados a las rutas renombradas (`4-eloisa…`, `2-oscar…`).
- No se tocó `main`; el cambio entra por PR.
