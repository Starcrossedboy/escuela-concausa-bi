---
id: DEVLOG-2026-09-01-EDGAR-CORONEL-RAMA-FIJA
title: "DevLog — Rama fija por persona y consolidación del vault"
owner: "Edgar Edmundo Coronel Navarrete"
status: filed
version: "1.0"
traces_up: ["vault/02_Requirements/User_Stories", "vault/05_Engineering/Branching_Strategy"]
traces_down: ["vault/_Meta/ownership.yml", "vault/_Meta/scripts/check_ownership.py", "tests/test_check_ownership.py"]
last_reviewed: "2026-09-01"
tags: [devlog, gobernanza, git, ramas, vault, us001, celula-po]
---

# DevLog — 2026-09-01 — Edgar Edmundo Coronel Navarrete

**Historia:** `US-001` · Crear el repositorio nuevo y adaptar el vault
**Requisito:** `REQ-007` · Trabajo en equipo, Git y documentación
**Rama:** `dev/edgar-coronel`
**Herramienta de IA usada:** Claude Code / opus-5, en modo par de trabajo

## Qué se pidió

Auditar la metodología de trabajo del repositorio y reestructurarla alrededor de `main` como fuente
única de verdad: una rama fija y permanente por persona, sincronización obligatoria antes del PR,
un padrón de identidades sin variantes, una matriz de permisos por rol, la documentación de consulta
consolidada bajo un solo directorio, y las reglas armonizadas entre todos los documentos que las
declaran.

## Qué generó la IA

**Auditoría.** Recorrido de los 5 archivos de agente de la raíz, `vault/_Meta/`, `vault/05_Engineering/`,
los 21 planes de sprint y los 21 Agent Contexts, cotejando cada regla contra las demás. Salieron 14
contradicciones entre documentos marcados `source_of_truth: true`, entre ellas: rama por unidad de
trabajo contra rama por persona, `merge` contra `rebase` + `--force-with-lease`, una compuerta de
aprobación contra dos, y el ID del commit obligatorio en un documento y opcional en otro.

**Causa raíz del error H-09.** Los Agent Contexts nombran a cada persona por su apellido paterno en el
nombre del archivo, mientras que la convención de rama escrita **dentro de ese mismo archivo** usaba el
apellido materno. Dos llaves para la misma persona, en el mismo párrafo, replicadas 21 veces.

**Reestructuración.**

- `vault/_Meta/ownership.yml`: fuente única con las 21 identidades, su rama, su handle de GitHub
  verificado contra la API y su alcance 🟢/🟡. Los 21 Agent Contexts derivan su alcance de aquí.
- `vault/_Meta/scripts/check_ownership.py`: verifica en cada PR la identidad del autor, que la rama
  sea `dev/{identidad}`, que el título siga el estándar y esté firmado por su autor, y que ningún
  archivo tocado salga de su alcance. Sin dependencias externas, como `vault_lint.py`.
- `tests/test_check_ownership.py` (`TEST-014`): 25 casos, incluidos los alias históricos que ya no
  resuelven a ninguna rama.
- Gates nuevos en `quality_gate.yml`: sincronía con `main` (G10) y propiedad (G11), además del de
  plantilla que ya existía (G9).
- Las 19 carpetas de documentación quedan bajo `vault/`. Se repararon los cuatro puntos de ruptura
  del CI (los tres scripts de `_Meta`, `src/modelos/evaluar.py` y `tests/test_evaluar.py`), los
  `paths:` de los dos workflows del tablero, `.gitattributes` (`merge=union` del índice de DevLog),
  `.graphifyignore`, `.gitignore` y 3,017 referencias en 474 archivos.

## Qué revisé yo

- El padrón completo, persona por persona: los 21 colaboradores de GitHub corresponden exactamente a
  los 21 integrantes, sin cuentas sobrantes ni faltantes. Dos handles arrastran el mismo error H-09
  que las ramas (`ImanolRuiz00` usa el segundo nombre, `juanmmayen98-pixel` el apellido materno), así
  que el gate resuelve la identidad desde el padrón y nunca la infiere del handle.
- La regla de emparejado de rutas: `src/ingesta/**` no debe cubrir `src/ingesta_vieja/`. Cubierto por
  prueba.
- El alcance de `src/frontend/**`, que estaba en verde para cuatro personas de tres células sin
  protocolo de coordinación: queda con un dueño (Célula 2) y en amarillo para los otros tres.
- Los métodos de merge del repositorio: `squash` y `rebase` siguen habilitados y **hay que apagarlos
  antes de crear las ramas**. Un squash deja el commit de `main` fuera de la ascendencia de la rama
  fija, y a partir de ahí cada PR de esa persona repite conflictos ya resueltos.
- Que ningún plan de sprint ni Agent Context conserve la nomenclatura anterior: barrido en verde.

## Pruebas ejecutadas

```
python3 vault/_Meta/scripts/vault_lint.py .          ✅ Vault limpio
python3 -m pytest tests/ -q                          ✅ 749 passed, 5 skipped
ruff check .                                         ✅ All checks passed
bash .github/scripts/probar_verificar_plantilla.sh   ✅ TODOS CORRECTOS
python3 vault/_Meta/scripts/generate_pm_dashboard.py .   ✅ 91 US, 21 personas, 8 fuentes
python3 vault/_Meta/scripts/validate_pm_dashboard.py .   ✅ TEST-002 válido
```

Los seis modos de fallo del gate se probaron uno a uno: rama gemela, handle fuera del padrón, título
firmado por otra persona, título fuera de estándar, y los dos casos correctos.

## IDs tocados

`US-001` · `REQ-007` · `TEST-014` · `ENG-BRANCHING` · `DOC-WORKFLOW` · `META-RULES` · `DOC-PRCHECK`
· `DOC-CLAUDE` · `DOC-AGENTS` · `DOC-GEMINI` · los 21 `AGENTCTX-*` y los 21 `SPRINT-*`

## Siguiente paso recomendado

Apagar `squash` y `rebase` en Settings → General → Pull Requests, publicar la regla de `dev/*`
(bloquear force-push y borrado), marcar `quality-checks` como check requerido, y dar de alta las 21
ramas fijas desde `main`.
