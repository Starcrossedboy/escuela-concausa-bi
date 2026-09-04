---
project: "FARO"
date: "2026-09-03"
author_human: "Karla Alejandra Monter Benitez"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "1 sesión — sync de rama + validación de US-411 + hallazgo y corrección de BUG-044"
touches: ["US-411", "BUG-020", "BUG-044", "REQ-004"]
tags: [devlog, celula-4, api, gold, backend]
---

# DevLog — 2026-09-03 — US-411: validación post-BUG-020 y descubrimiento de BUG-044

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/03_Architecture/API_Specification|API_Spec §3.3]] ·
[[vault/06_Quality_Testing/Bug_Register|Bug_Register (BUG-044)]]

## Contexto

Llegué a la sesión con una rama (`feat/karla-benitez-us413-admin-endpoints`) construida sobre un
`main` 557 commits atrasado — de antes de que el repo migrara la documentación a `vault/` y
cambiara a una rama fija por persona (`dev/{identidad}`, regla 8 del vault). Ese trabajo de US-413
se descarta: la auditoría del día (`Execution_Status.md`, 2026-09-03) ya lo confirma como "sin PR ni
commit" en `main`. Edgar reasignó la semana: cerrar US-411, cortar US-413/US-414.

## Qué se hizo

**1. Sync a la rama fija.** `dev/karla-monter` estaba 93 commits atrás; se sincronizó con
`git merge origin/main` (fast-forward, sin conflictos) y se empujó a `origin`.

**2. Validación de US-411 contra la URL pública** (`https://faro-api-eanzfglvyq-uc.a.run.app`),
para confirmar de primera mano lo que `Bug_Register.md` ya reportaba sobre BUG-020 (curado en prod
el 2026-08-29/30, reconfirmado 2026-09-02 por Juan Macías, pero el campo `status` de la tabla
seguía en `open`):
- `/escuelas`, `/municipios`, `/kpis` → 200, ya no 500.
- `order_by` fuera de whitelist → 422 (nunca construye SQL con texto libre).
- Ordenamiento con `SIN_DATO` al final confirmado (`indice_riesgo desc`).
- Entidad fuera de `SCOPE_ENTIDADES` (`cve_ent=99`) → lista vacía, nunca datos ajenos.
- `/series` reconfirmado fuera de alcance (sin cambios desde la Decisión 3 del 20-ago).

**3. BUG-044 (critical), encontrado durante la validación.** Sin `ciclo` explícito, `/escuelas` y
`/kpis` sumaban/listaban los ~3 ciclos materializados en `gold.fact_escuela_ciclo` a la vez:
`cve_ent=09` sin `ciclo` daba 19 456 escuelas vs. 6 378 con `ciclo=2024-2025` (razón ≈3); `/kpis`
sin filtro daba `matricula_total=20 638 574` (≈3× el real de ~7M para las 4 entidades). No es un
problema de alcance de entidades -- es la misma matrícula sumada tres veces. `obtener_escuela`
(detalle) tenía el mismo hueco de raíz: sin filtro de ciclo, `.first()` devolvía una fila cualquiera
entre los ciclos de una escuela.

**Fix:** `RepositorioGoldPostgres._ciclo_mas_reciente()` nuevo (`SELECT MAX(id_ciclo)`, el formato
`AAAA-AAAA` ordena lexicográficamente igual que cronológicamente); se usa como default en
`listar_escuelas`, `obtener_kpis` y `obtener_escuela` cuando `ciclo` es `None`.
`tests/fixtures_gold.py::RepositorioGoldFake` implementa el mismo default -- antes el fixture solo
tenía un `id_ciclo`, por lo que la suite rápida nunca pudo ejercitar este defecto; se agregó una
fila con la misma escuela (`09DPR0001A`) en un segundo ciclo (`2023-2024`) para que las pruebas de
regresión lo cubran de verdad, no por casualidad de datos.

**4. Documentación actualizada:** `API_Specification.md` §3.3 (comportamiento de `ciclo` por
default), `Bug_Register.md` (fila + sección de detalle de BUG-044) y `Traceability_Matrix.md`
(REQ-004, evidencia incremental de hoy). **No toqué `Execution_Status.md`**: no está en mi alcance
(`ownership.yml` no lo lista en mi verde/amarillo ni en `comunes` — a diferencia de `Bug_Register`
y la matriz, que sí lo son); `check_ownership.py` reprueba el PR si lo edito. Dejo abajo el texto
propuesto para que Edgar (PM) lo aplique.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-sonnet-5.
- **Archivos modificados:** `src/api/repositorio_gold.py`, `tests/fixtures_gold.py`,
  `tests/test_api_contract.py`, `vault/03_Architecture/API_Specification.md`,
  `vault/06_Quality_Testing/Bug_Register.md`, `vault/12_Roadmap_Sprints/Execution_Status.md`,
  `vault/02_Requirements/Traceability_Matrix.md`, este DevLog.
- **Decisiones autónomas del agente:** forma exacta de `_ciclo_mas_reciente()` (subconsulta
  `MAX(id_ciclo)` vs. traer todos los ciclos y ordenar en Python -- se eligió la subconsulta por
  ser una sola ida a la BD); diseño del fixture de regresión (reusar el mismo `cct` en dos ciclos
  en vez de una escuela nueva, para ejercitar la deduplicación real, no solo un filtro). La
  decisión de **fondo** -- arreglar BUG-044 ahora, dentro de este mismo cierre, en vez de solo
  registrarlo -- se presentó a Karla con la evidencia completa (curl + lectura de código) y ella
  la confirmó antes de tocar código.
- **Correcciones manuales:** ninguna sobre el código generado; Karla revisó el diagnóstico y el
  plan de fix antes de implementarlo.
- **Prompt inicial:** continuación de la sesión donde se sincronizó la rama; sin documento scratch.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Tests agregados/actualizados: `tests/test_api_contract.py` pasa de 29 a 32 casos (+3 de
  BUG-044). Suite completa `pytest tests/ -q`: **843 passed, 7 skipped** (antes 840/7, sin
  fallos nuevos).
- [x] DevLog enlaza a los IDs afectados (US-411, BUG-020, BUG-044, REQ-004)

## Bloqueantes / avisos a otros owners
- **BUG-020:** el campo `status` en `Bug_Register.md` seguía en `open` pese a dos verificaciones en
  vivo previas (08-29/30, 09-02); esta sesión aporta una tercera confirmación independiente.
  Recomendación a **Christian Ruiz / Luis Téllez**: voltear a `fixed`/`closed`.
- **BUG-044:** el fix vive en `dev/karla-monter`, **no en producción todavía**. Pendiente de
  **Luis Téllez (C5)** redesplegar `faro-api` con este merge. US-411 no se marca `done` en
  `Execution_Status.md` hasta reverificar `/escuelas` y `/kpis` contra la URL pública
  post-despliegue (mismo criterio DEC-012 ya aplicado a US-412/US-416).

## Texto propuesto para `Execution_Status.md` (fuera de mi alcance -- para Edgar)

Reemplazar la fila de `US-411` por:

> `| US-411 | in_review | 2026-08-20 | — | [[vault/_DevLog/2026-08-20-karla-monter-us411-endpoints-gold]] · PR #59 (Gold real) · PR #99 (BUG-008 resuelto). **BUG-020 verificado curado en prod 2026-09-03** (Karla Monter): `/escuelas` 200, `/municipios` 200, `/kpis` 200, `order_by` inválido → 422, entidad fuera de alcance → lista vacía, `/series` confirmado fuera de alcance. **Validación destapó BUG-044 (critical, fixed en código)**: sin `ciclo` explícito, `/escuelas`/`/kpis` sumaban los ~3 ciclos materializados a la vez (matrícula triplicada en prod: 20.6M vs ~7M reales). Fix en `dev/karla-monter` con 3 pruebas de regresión, **pendiente de desplegar** (C5) y reverificar contra la URL pública antes de cerrar — mismo criterio que DEC-012 | 2026-09-03 |`

## Próximos pasos
- Abrir el PR desde `dev/karla-monter` con el aviso de BUG-044 a Christian (Tech Lead C4) y a
  Luis Téllez (C5, para el redeploy).
- **Edgar (PM):** aplicar el texto propuesto arriba en `Execution_Status.md` (fuera de mi alcance).
- Tras el redeploy: reverificar `/escuelas` y `/kpis` sin `ciclo` contra la URL pública y, si
  coincide con `ciclo` explícito, cerrar US-411 de verdad en `Execution_Status.md`.
- US-413 y US-414 siguen cortadas (reasignación de Edgar, 2026-09-03).
