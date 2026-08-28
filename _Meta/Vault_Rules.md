---
id: META-RULES
title: "Vault Rules"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
version: "1.1"
source_of_truth: true
last_reviewed: "2026-08-28"
tags: [meta, rules, governance]
---

# Vault Rules — Reglas no negociables

> → [[_Meta/_index|Volver a _Meta]]

## Las 7 reglas

1. **Un tema, un archivo canónico.** Si algo se documenta en dos lugares, uno es el canónico y el
   otro solo enlaza a él. Prohibido duplicar PRD, DevLog, dashboards, etc.

2. **Todo artefacto lleva frontmatter completo** con `id`, `owner`, `status`, y (cuando aplica)
   `traces_up` / `traces_down`. Sin frontmatter = no está terminado.

3. **Todo artefacto tiene un ID único** según [[_Meta/Naming_Conventions]]. Los IDs nunca se reciclan.

4. **Nada vive en la raíz de una carpeta sin estar en su `_index.md` (MOC).** Ver
   [[_Meta/Definition_of_Filed]].

5. **Cambios al código pasan por PR**, nunca push directo a la rama protegida. Ver
   [[05_Engineering/Engineering_Workflow]].

6. **Toda sesión con IA genera una entrada de DevLog** antes del push. Ver [[_DevLog/_index]].

7. **Cambios de seguridad, schema o CI/CD requieren revisión humana explícita** del dueño del área.

## Estados válidos (`status`)

`draft` → `in_review` → `approved` → `done` → `archived`

## Roles de propiedad

| Rol | Responsabilidad |
|---|---|
| **PM / Owner del vault** | Integridad del vault, matriz de trazabilidad, releases |
| **Área owner** | Dueño de una carpeta (p.ej. Security, CI/CD) |
| **Contribuidor** | Trabaja dentro de su scope (ver su `Agent_Context`) |
| **Revisor** | Aprueba PRs; no puede aprobar el propio |

## Higiene periódica (mensual)

- Correr `_Meta/scripts/vault_lint.py`.
- Revisar documentos con `last_reviewed` > 90 días.
- Cerrar o archivar riesgos/bugs/incidentes resueltos.

## Excepciones al linter

- **`graphify-out/`** queda **fuera del alcance de `vault_lint.py`** (se excluye en `find_md`). Es
  **salida generada y regenerable** por Graphify, no un artefacto del vault: aplicarle *Definition of
  Filed* (frontmatter, `_index`, no-huérfano) sería incorrecto conceptualmente y frágil, porque se
  sobrescribe en cada corrida. **Sí se versiona a propósito** (`graph.json`, `GRAPH_REPORT.md`,
  `graph.html`): es el mapa que consultan los LLMs y que [[AGENTS]] referencia explícitamente; lo que
  no se versiona (`cache/`, `cost.json`, `*.tmp`) ya está en `.gitignore`.

  > **No regeneres el grafo en local.** Lo mantiene el workflow `update-project-graph.yml`, que
  > corre al empujar a `main` y commitea `graph.json` y `GRAPH_REPORT.md` con la cuenta del bot.
  > Correr `graphify .` en tu máquina reescribe los ocho archivos y produce diffs de **decenas de
  > miles de líneas** que chocan con el bot y bloquean merges ajenos. Si aparecen cambios de
  > `graphify-out/` en tu `git status` sin que los buscaras, descártalos con
  > `git restore graphify-out/`.

## Codificación de los archivos del vault

**Todo `.md` se guarda en UTF-8.** `vault_lint.py` lo verifica y **reprueba el PR** si encuentra
texto de codificación rota — el patrón que convierte `Descripción` en su versión doble-codificada.

La detección es una prueba de ida y vuelta: si una línea puede codificarse en cp1252 y ese
resultado decodifica como UTF-8 válido dando algo distinto, los bytes ya eran UTF-8 y se
escribieron dos veces. Los acentos correctos, los emoji, las flechas y las comillas angulares no la
disparan.

**Si te reprueba**, no intentes corregir a mano carácter por carácter: recupera el archivo con
`git checkout origin/main -- <ruta>`, vuelve a aplicar tu cambio y guarda con el editor en UTF-8
(en VS Code, el indicador de codificación está en la barra inferior derecha).

Para documentar el defecto sin dispararlo, muestra el ejemplo dentro de un bloque de código
—se omiten— o agrega el marcador `vault-lint: permitir-mojibake` en la línea.

Es la misma familia de **BUG-005** (CRLF de Windows en los `.sh`) y **BUG-011** (`read_text()` sin
`encoding` explícito): el locale del sistema filtrándose a un archivo del repositorio. La tercera
aparición —el PR #102, con 227 líneas de `_DevLog/_index.md` reescritas— motivó esta regla.

### Si editas el vault con Obsidian

Apaga el **formateo automático de tablas** (lo traen plugins como *Advanced Tables*). Al abrir un
documento reescribe cada fila para alinear las columnas: el contenido no cambia, pero el diff sí.
`12_Roadmap_Sprints/Execution_Status.md` apareció una vez con **112 líneas modificadas** sin un solo
cambio real, y eso basta para abortar un `git merge` y bloquear el PR de otra persona.

Si ya te pasó, compruébalo con `git diff -w <archivo>`: si sale vacío o casi, era solo espaciado y
puedes descartarlo con `git restore <archivo>`.
