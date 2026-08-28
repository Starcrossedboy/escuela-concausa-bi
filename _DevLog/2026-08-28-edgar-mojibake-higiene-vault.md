---
project: "FARO"
date: "2026-08-28"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "media — guardia de codificación, BUG-014 y limpieza de artefactos generados"
touches: ["BUG-005", "BUG-011", "BUG-014", "US-503", "US-004", "META-RULES", "REQ-007", "RISK-006"]
tags: [devlog, pm, gobernanza, ci, calidad]
---

# DevLog — 2026-08-28 — Guardia de codificación, BUG-014 y artefactos generados

→ [[_DevLog/_index|Volver al índice]] · [[_Meta/Vault_Rules]] · [[06_Quality_Testing/Bug_Register]]

## Contexto

Cuatro fricciones distintas venían costando merges y PRs, todas de la misma naturaleza: **el
entorno local de cada quien filtrándose al repositorio**. Ninguna es un defecto de producto, y por
eso ninguna tenía dueño; entre las cuatro llevaban consumidas varias horas de la semana previa al
ensayo E2E.

## 1 · Guardia contra la codificación rota

El PR #102 llegó reescribiendo las **227 filas** de `_DevLog/_index.md` con el texto doble
codificado: lo que debía decir «Descripción» decía otra cosa. Es texto UTF-8 que un editor en
locale de Windows guardó como si fuera cp1252. `vault_lint.py` no lo detectaba porque el archivo
resultante **sigue siendo UTF-8 válido** — solo está mal.

Es la tercera aparición de la misma familia: **BUG-005** (CRLF en los `.sh` rompiendo shebangs
dentro de contenedores) y **BUG-011** (`read_text()` sin `encoding` explícito, que solo corría con
`PYTHONUTF8=1`). Distinto mecanismo, misma causa: el locale del sistema.

**Lo primero que se descartó fue `.gitattributes`.** No sirve: para cuando el editor escribe, los
bytes ya son UTF-8 válido y Git no puede distinguirlos de un cambio legítimo. `working-tree-encoding`
es además un no-op cuando el destino ya es UTF-8. **No se puede prevenir desde Git; hay que
detectarlo.**

La detección quedó en `vault_lint.py`, que ya corre dentro del check **requerido**
`Calidad de codigo y vault`: un hallazgo reprueba el PR sin trabajo extra de nadie. Es una prueba de
ida y vuelta —codificar la línea en cp1252 y decodificarla como UTF-8— que solo tiene éxito, y da
algo distinto, cuando los bytes ya venían codificados dos veces.

**Se validó antes de integrarla**, con once casos: acentos correctos, `¿`, emoji, flechas, guiones
largos y comillas angulares **no** disparan; las líneas reales del PR #102 sí. Sobre `main` completo
da limpio, así que activarla no rompió nada existente. Corrida contra el `_index.md` de ese PR,
reporta las **112 líneas** afectadas con archivo y número de línea.

Para poder documentar el defecto sin dispararlo se omiten los bloques de código y existe el
marcador `vault-lint: permitir-mojibake`.

## 2 · BUG-014 — el gate que reprobaba su propia plantilla

Lo detectó **Marina García** revalidando US-212 (PR #103). El check buscaba el token de casilla sin
marcar en **todo el cuerpo del PR**, no solo en ítems de lista: bastaba mencionar esa sintaxis
dentro de una explicación —aunque fuera entre backticks— para reprobar. Y como la plantilla oficial
trae las casillas de aprobación del PM sin marcar (le toca marcarlas a él al revisar), **la
plantilla del repositorio no podía pasar su propio gate**, lo que empujaba a los autores a borrar el
bloque de aprobación o a marcarlo ellos mismos.

Peor aún, el workflow no escuchaba el evento `edited`: como lee el cuerpo desde el *payload* del
evento, **un cuerpo corregido después del push se quedaba en rojo para siempre**. Costó los PR
**#73, #78, #79, #84, #88, #94, #98 y #105** — ocho, y en varios se resolvió con un commit vacío
para forzar un `synchronize`.

Tres cambios:

1. El patrón se acota a casillas reales de lista.
2. La sección de aprobación se recorta antes de evaluar: es del PM, no del autor.
3. Se agrega `edited` a los disparadores.

**La lógica se extrajo del YAML a `.github/scripts/verificar_plantilla_pr.sh`** para poder probarla.
`probar_verificar_plantilla.sh` la ejercita con cinco casos —incluida la plantilla oficial— contra el
script real, no contra una copia que se desincronice. Los cinco pasan.

## 3 · Dos artefactos generados que ensuciaban los diffs

- **`.obsidian/graph.json`** era estado del editor versionado: cambia con solo abrir el vault.
  Deja de rastrearse y pasa a `.gitignore`.
- **`graphify-out/`** no se toca. Se revisó y **está versionado a propósito**: es el mapa que
  consultan los agentes y que [[AGENTS]] referencia. El problema real era otro —regenerarlo en
  local produce diffs de decenas de miles de líneas que chocan con el bot que lo mantiene— y se
  resolvió documentándolo en [[_Meta/Vault_Rules]], no ignorando los archivos.

## 4 · El formateo de tablas de Obsidian

`Execution_Status.md` apareció una vez con **112 líneas modificadas** y, con `git diff -w`, un solo
cambio real: la fila de guiones del encabezado. Un formateador de tablas del editor lo reescribe al
abrirlo. Basta para abortar un `git merge` y bloquear el PR de otra persona. **No es corregible
desde el repositorio** —los plugins del editor no se versionan— así que quedó documentado en las
reglas del vault, junto con cómo detectarlo (`git diff -w`) y cómo descartarlo.

## Uso de IA

- **Archivos modificados:** `_Meta/scripts/vault_lint.py`, `_Meta/Vault_Rules.md`,
  `.github/workflows/quality_gate.yml`, `.github/scripts/verificar_plantilla_pr.sh` (nuevo),
  `.github/scripts/probar_verificar_plantilla.sh` (nuevo), `.gitignore`,
  `06_Quality_Testing/Bug_Register.md`, `_DevLog/_index.md`, este archivo.
- **Decisiones autónomas del agente:** ninguna de fondo. El agente propuso primero
  `.gitattributes` para el problema de codificación y `.gitignore` para `graphify-out/`;
  **ambas propuestas resultaron equivocadas al verificarlas** y se corrigieron antes de escribir
  código (ver más abajo).
- **Correcciones manuales:** tres, todas del agente sobre sí mismo tras verificar contra el
  repositorio.
  1. `.gitattributes` **no puede** prevenir el mojibake: los bytes ya son UTF-8 válido cuando el
     editor los escribe. Se movió a detección en el linter.
  2. `graphify-out/` **no debe** ignorarse: `Vault_Rules.md` lo documenta como decisión deliberada
     y `update-project-graph.yml` lo commitea. Se cambió por documentación.
  3. La evidencia de BUG-014 apuntaba primero a un script fuera del repositorio. Se extrajo la
     lógica a `.github/scripts/` para que la prueba sea reproducible por cualquiera.

## Seguridad / calidad

- [x] `python _Meta/scripts/vault_lint.py .` — Vault limpio
- [x] `python _Meta/scripts/generate_pm_dashboard.py .` — 91 US, 21 personas, 8 fuentes
- [x] `python _Meta/scripts/validate_pm_dashboard.py .` — TEST-002 válido
- [x] `pytest tests/ -q` — **467 pasan**, 5 omitidas
- [x] `bash .github/scripts/probar_verificar_plantilla.sh` — 5 de 5
- [x] `ruff` sobre `vault_lint.py`: los 2 hallazgos son **preexistentes**, verificado con `git stash`
- [x] Ninguna credencial ni dato real en el diff

## Regla 7 — revisión declarada

Este PR **toca CI/CD** (`.github/workflows/quality_gate.yml` y dos scripts nuevos en
`.github/scripts/`), así que cae bajo la regla 7 del vault. **Se solicita la revisión de Luis
Téllez (Tech Lead C5)**, dueño del área y dueño registrado de BUG-014, además de la aprobación del
PM bajo DEC-003.

## Próximos pasos

- **`vault_lint.py` solo cubre `.md`.** Los `.txt` de `requirements/` y los `.yaml` de la capa
  semántica quedan fuera; si aparece un caso ahí, ampliar `find_md`.
- **Cinco ramas locales `pr-*`** de resoluciones de conflictos pasadas no son ancestros de `main`.
  Revisarlas una por una antes de borrarlas.
