---
id: ENG-BRANCHING
title: "Branching Strategy"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
version: "2.0"
source_of_truth: true
traces_up: ["vault/05_Engineering/Engineering_Workflow"]
traces_down: ["vault/08_CICD_DevOps/CI_Quality_Gates"]
last_reviewed: "2026-09-01"
tags: [engineering, git, branching, workflow]
---

# Branching Strategy — Modelo de ramas

> Documento canónico sobre ramas, commits y Pull Requests.
> Complementa [[vault/05_Engineering/Engineering_Workflow]] y se hace cumplir vía
> [[vault/08_CICD_DevOps/CI_Quality_Gates]].
> → [[vault/05_Engineering/_index|Volver a Engineering]]

## Principio rector

**`main` es la única fuente de verdad y siempre debe estar desplegable.** Nadie escribe
directamente en `main`; todo cambio entra por Pull Request revisado y con los checks en verde.
Esto materializa la regla 5 de [[vault/_Meta/Vault_Rules]].

## Modelo: una rama fija por persona

Cada integrante trabaja **en una sola rama, permanente, que lleva su nombre**. No se abre una
rama por historia, ni por sprint, ni por tema. La rama nace una vez, se sincroniza con `main`
antes de cada cambio, y sigue viva después del merge.

```
dev/{identidad}
```

Una persona, una rama, para todo el proyecto. `dev/diana-alvarez` lleva sus extractores, sus
correcciones y su documentación: la rama dice **quién**, el commit dice **qué**.

> **Antipatrón a evitar:** abrir una rama nueva por cada historia. Multiplica las ramas por
> el número de tareas, deja decenas de ramas fusionadas sin borrar, y cada una arranca de un
> `main` distinto — que es exactamente como una misma persona termina con dos ramas gemelas
> para el mismo trabajo.

### La identidad

La identidad se construye **siempre igual**, y es la misma en todas partes:

```
{primer-nombre}-{apellido-paterno}
```

en minúsculas, ASCII sin acentos, kebab-case. **Se ignoran el segundo nombre y el apellido
materno.** Héctor Rafael Morales Marbán es `hector-morales` y nada más: no `hector-marban`,
no `hector-rafael`, no `hector`.

Esa identidad nombra la rama, firma el título del PR, encabeza el DevLog, da nombre al Agent
Context y apunta al plan de sprint. **No existe ninguna otra forma de nombrar a una persona.**

El padrón completo —las 21 identidades con su rama, su handle de GitHub y su alcance— vive en
un solo archivo: **`vault/_Meta/ownership.yml`**. Ahí se da de alta a quien entra, y de ahí lo
lee el CI. Si tu nombre no está ahí, tu PR no pasa.

### Reglas de vida de la rama

1. **Una rama por persona**, permanente, nunca por historia ni por sprint.
2. **La rama no se borra al mergear.** Se sincroniza y se sigue usando.
3. **Se sincroniza con `git merge origin/main`**, nunca con `rebase`: la historia de tu rama ya
   fue revisada en PRs anteriores y reescribirla invalida esas revisiones.
4. **Nunca `--force`** sobre tu rama. Es permanente y compartida con el historial de tus PRs.
5. **Sincroniza antes de empezar y otra vez antes de abrir el PR.** `main` se mueve varias veces
   al día; el CI reprueba un PR cuya rama no contenga el último `main`.

Sin acentos ni caracteres especiales en los nombres de rama.

## Flujo completo

```bash
# 1. Sincroniza. Siempre, antes de escribir una sola línea.
git checkout dev/<identidad>
git fetch origin
git merge origin/main

# 2. Trabaja con commits pequeños y frecuentes, dentro de tu alcance
git add <archivos-especificos>        # nunca 'git add .' a ciegas
git commit -m "feat(<scope>): <descripcion> (<ID>)"

# 3. Vuelve a sincronizar justo antes de abrir el PR
git fetch origin && git merge origin/main

# 4. Sube
git push origin dev/<identidad>

# 5. Abre el PR con el título estándar. Tras el merge, NO borres la rama: vuelve al paso 1.
```

## Convención de commits

Formato **Conventional Commits**, con el **ID del artefacto** al final:

```
<tipo>(<scope>): <descripcion en presente> (<ID>)
```

Tipos: `feat` · `fix` · `chore` · `docs` · `test` · `refactor` · `style` · `sec`

Ejemplos:
- `feat(api): endpoint de consulta paginada (US-411)`
- `fix(silver): homologacion de catalogo duplicada (BUG-004)`
- `docs(vault): ADR de estrategia de modelado (ADR-007)`

**El ID es obligatorio en todo commit.** Se usa el de la historia (`US-###`) y, cuando el cambio
no nace de una historia, el del artefacto que lo origina (`BUG-`, `ADR-`, `SEC-`, `TEST-`). Un
commit sin ID no es rastreable y rompe la cadena de
[[vault/02_Requirements/Traceability_Matrix]].

Como la rama ya no lleva el tipo de trabajo, **el tipo vive aquí**: es el commit el que
distingue una funcionalidad de una corrección.

## Título del Pull Request

```
[Nombre Apellido] - <descripción concisa> (<ID>) - [sync|CI|DoF|DevLog]
```

```
[Diana Alvarez] - Extractor de CEMABE con reintentos (US-113) - [sync|CI|DoF|DevLog]
```

El nombre es el de tu identidad. Los cuatro tokens finales son tu declaración de que
sincronizaste con `main`, el CI está verde, cumples Definition of Filed y escribiste tu DevLog.
**El CI valida el formato y que la firma corresponda al autor:** un PR firmado con el nombre de
otra persona se reprueba solo.

## Reglas del Pull Request

1. Usa `.github/PULL_REQUEST_TEMPLATE.md` — se carga solo. **Complétalo todo.**
2. Referencia el **ID** de la historia y del requisito.
3. **Mantén el PR pequeño.** Un PR de 40 archivos no se revisa: se aprueba a ciegas.
4. **Solo tocas archivos de tu alcance.** El tuyo está en tu Agent Context y en
   `vault/_Meta/ownership.yml`. Para cambiar algo ajeno, pídeselo a su dueño. Un cambio
   **transversal** —un renombre que cruza todo el repositorio, una migración estructural—
   se declara en el PR y pide revisión de cada dueño afectado; el check lo marcará en rojo
   y esa es la señal de que necesita esas revisiones, no de que esté mal.
5. **No apruebas tu propio PR.** Requiere la aprobación del PM (los PR del propio PM se mergean
   con bypass de administrador).
6. **Todos los checks en verde** antes de mergear.
7. Cambios en seguridad, esquema de datos o CI/CD requieren aprobación explícita del dueño del
   área (regla 7 de [[vault/_Meta/Vault_Rules]]).
8. **Al mergear no se borra la rama.**

## Aprobación de Pull Requests — compuerta única (PM)

Todo PR requiere **una** aprobación: la del PM (proceso + trazabilidad). El ruleset exige
**1 aprobación** con *Require review from Code Owners*, y CODEOWNERS deja al PM como único dueño
(`* @edgarcoroneln`). El **Tech Lead del área revisa la corrección técnica** de forma **no
bloqueante**: se le solicita como revisor de apoyo y su aprobación no es obligatoria para el
merge. Los **PR del propio PM** se mergean con **bypass de administrador**, porque nadie puede
aprobar su propio PR. Ver DEC-003.

### Revisión técnica de apoyo — Tech Lead del área (recomendada, no bloqueante)

El Tech Lead evalúa **si el trabajo está bien hecho**: el código resuelve la historia, no rompe otras
piezas ni introduce deuda evidente, sigue las convenciones del área y las pruebas cubren lo que deben.
Se le solicita con *Reviewers* en el PR.

### Aprobación obligatoria — Edgar Edmundo Coronel Navarrete (PM / PO)

**Checklist de aprobación del PM.** El PM aprueba si, y solo si, se cumple TODO:

| # | Verificación | Cómo se comprueba |
|---|---|---|
| 1 | **Sin errores** — todos los checks de CI en verde | Pestaña *Checks* del PR |
| 2 | **Rama y alcance correctos** — sale de `dev/{identidad}` y no invade archivos ajenos | Check `check_ownership.py` |
| 3 | **Rama sincronizada** con el último `main` | Check de sincronía |
| 4 | **Título en estándar** y firmado por su autor | Check `check_ownership.py` |
| 5 | **Plantilla completa** — ninguna sección vacía ni casilla sin marcar | Cuerpo del PR |
| 6 | **IDs presentes** — historia y requisito referenciados | Sección *IDs relacionados* |
| 7 | **DevLog registrado** si se usó IA | Enlace en el PR + archivo en `vault/_DevLog/` |
| 8 | **Definition of Filed** cumplida | Frontmatter, `_index.md`, matriz |
| 9 | **Avance actualizado** en la matriz de trazabilidad | [[vault/02_Requirements/Traceability_Matrix]] |
| 10 | **Sin secretos ni datos pesados** | Gate de CI + revisión del diff |
| 11 | **README actualizado** si cambia instalación o uso | Diff del PR |

**Si algo falla, el PM solicita cambios (*Request changes*) señalando el punto exacto.** No se aprueba
"con observaciones": o cumple, o vuelve al autor.

> **Al mergear, el PM no pulsa *Delete branch*.** Las ramas `dev/*` son permanentes: borrar una
> obliga a recrearla y la desvía de `main`.

## Protección de `main` (configuración obligatoria)

En GitHub → **Settings → Branches → Add branch protection rule**:

- Pattern: `main`
- ✅ Require a pull request before merging (**1 aprobación**: el PM, ver DEC-003)
- ✅ Require review from Code Owners (con CODEOWNERS = `* @edgarcoroneln`, la aprobación debe ser del PM)
- ✅ Require status checks to pass → `Calidad de codigo y vault`, `Generar y validar tablero PM`,
  `quality-checks`
- ✅ Require branches to be up to date before merging
- ✅ Bypass: rol **Repository admin** (para que el PM mergee sus propios PR, que no puede autoaprobar)

En **Settings → General → Pull Requests**:

- ✅ *Allow merge commits* — **el único método permitido**
- ❌ *Allow squash merging* — **apagado**
- ❌ *Allow rebase merging* — **apagado**
- ❌ *Automatically delete head branches* — **apagado**

> **Por qué solo merge commit.** Un *squash* comprime el trabajo en un commit nuevo que **no es
> ancestro** de la rama de origen. Como la rama es permanente y se sigue usando, quedaría
> divergente para siempre: cada PR posterior de esa persona volvería a arrastrar conflictos ya
> resueltos. Es el fallo más silencioso del modelo y el ajuste más importante de esta página.

Y una regla para `dev/*`:

- Pattern: `dev/*`
- ✅ Block force pushes
- ✅ Block deletions

> **Nota de plan:** las ramas protegidas están disponibles gratis en repositorios **públicos**. En
> repositorios privados requieren GitHub Pro, Team o Enterprise.

## Resolución de conflictos

```bash
git checkout dev/<identidad>
git fetch origin
git merge origin/main     # resuelve los conflictos aquí, en tu rama
# ... resolver, probar que sigue funcionando ...
git add <archivos-resueltos>
git commit -m "chore: merge de main y resolucion de conflictos (<ID>)"
git push origin dev/<identidad>
```

**Nunca fuerces un push** (`--force`) y **nunca uses `rebase`** sobre tu rama: es permanente, y su
historia sostiene las revisiones de tus PRs anteriores.

## Si rompes `main`

1. Avisa de inmediato en el canal del equipo.
2. Se revierte con `git revert <sha>` (no `reset`, porque la historia es compartida).
3. Se registra el incidente en [[vault/10_Risk_Governance/Incident_Log]].
