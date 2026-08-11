---
id: ENG-BRANCHING
title: "Branching Strategy"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
version: "1.0"
source_of_truth: true
traces_up: ["05_Engineering/Engineering_Workflow"]
traces_down: ["08_CICD_DevOps/CI_Quality_Gates"]
last_reviewed: "2026-08-01"
tags: [engineering, git, branching, workflow]
---

# Branching Strategy — Modelo de ramas

> Documento canónico sobre ramas, commits y Pull Requests.
> Complementa [[05_Engineering/Engineering_Workflow]] y se hace cumplir vía
> [[08_CICD_DevOps/CI_Quality_Gates]].
> → [[05_Engineering/_index|Volver a Engineering]]

## Principio rector

**`main` siempre debe estar desplegable.** Nadie escribe directamente en `main`; todo cambio entra por
Pull Request revisado y con los checks en verde. Esto materializa la regla 5 de
[[_Meta/Vault_Rules]].

## Modelo: rama por unidad de trabajo

Se trabaja con **ramas cortas de una sola unidad de trabajo**, no con ramas personales de larga vida.

> **Antipatrón a evitar:** que cada integrante mantenga *una* rama durante todo el proyecto. Cuando
> llega el momento de integrar, el conflicto es inmanejable. Una rama = una historia = pocos días.

### Convención de nombres

```
<tipo>/<nombre-corto>-<descripcion-en-kebab-case>
```

| Tipo | Cuándo se usa |
|---|---|
| `feat/` | Funcionalidad nueva |
| `fix/` | Corrección de un defecto |
| `chore/` | Mantenimiento, configuración, dependencias |
| `docs/` | Solo documentación o vault |
| `sec/` | Cambios de seguridad |

Ejemplos válidos: `feat/ana-extractor-fuente-a` · `fix/luis-timeout-api` · `docs/ana-adr-medallon`

Sin acentos ni caracteres especiales en los nombres de rama.

### Reglas de vida de la rama

1. **Una rama por unidad de trabajo** (una historia / un ID), nunca por persona ni por sprint.
2. **Vida máxima: 3-4 días.** Si tu rama lleva más de una semana abierta, el alcance era demasiado
   grande: divídela.
3. **Parte siempre de `main` actualizado**, nunca de otra rama de trabajo.
4. **Sincroniza a diario** con `git pull origin main`, aunque no hayas terminado.
5. **La rama se borra al mergear.** No se reutilizan ramas.

## Flujo completo

```bash
# 1. Partir de main actualizado
git checkout main && git pull origin main

# 2. Crear la rama
git checkout -b feat/<nombre>-<descripcion>

# 3. Trabajar con commits pequeños y frecuentes
git add <archivos-especificos>        # nunca 'git add .' a ciegas
git commit -m "feat(<scope>): <descripcion> (<ID>)"

# 4. Sincronizar con main antes de subir
git pull origin main

# 5. Subir y abrir PR
git push -u origin feat/<nombre>-<descripcion>
```

## Convención de commits

Formato **Conventional Commits**, con el **ID del artefacto** al final:

```
<tipo>(<scope>): <descripcion en presente> (<ID>)
```

Ejemplos:
- `feat(api): endpoint de consulta paginada (US-411)`
- `fix(silver): homologacion de catalogo duplicada (BUG-004)`
- `docs(vault): ADR de estrategia de modelado (ADR-007)`

Un commit sin ID no es rastreable y rompe la cadena de
[[02_Requirements/Traceability_Matrix]].

## Reglas del Pull Request

1. Usa `.github/PULL_REQUEST_TEMPLATE.md` — se carga solo. **Complétalo todo.**
2. Referencia el **ID** de la historia y del requisito.
3. **Mantén el PR pequeño.** Un PR de 40 archivos no se revisa: se aprueba a ciegas.
4. **No apruebas tu propio PR.** Requiere la aprobación del PM (los PR del propio PM se mergean con bypass de administrador).
5. **Todos los checks en verde** antes de mergear.
6. Cambios en seguridad, esquema de datos o CI/CD requieren aprobación explícita del dueño del área
   (regla 7 de [[_Meta/Vault_Rules]]).


## Aprobación de Pull Requests — compuerta única (PM)

> **Política vigente desde 2026-08-09 (DEC-003).** Antes eran dos compuertas
> (Tech Lead + PM); la doble aprobación resultó un cuello de botella en Sprint 1, así que ahora
> **el PM es el único aprobador obligatorio.** El ruleset exige **1 aprobación** con *Require review
> from Code Owners*, y CODEOWNERS deja al PM como único dueño (`* @edgarcoroneln`).

Todo PR requiere **una** aprobación: la del PM (proceso + trazabilidad). El **Tech Lead del área sigue
revisando la corrección técnica**, pero de forma **no bloqueante** (se le solicita como revisor de
apoyo; su aprobación no es obligatoria para el merge). Los **PR del propio PM** se mergean con
**bypass de administrador**, porque nadie puede aprobar su propio PR.

### Revisión técnica de apoyo — Tech Lead del área (recomendada, no bloqueante)

El Tech Lead evalúa **si el trabajo está bien hecho**: el código resuelve la historia, no rompe otras
piezas ni introduce deuda evidente, sigue las convenciones del área y las pruebas cubren lo que deben.
Se le solicita con *Reviewers* en el PR.

### Aprobación obligatoria — Edgar Edmundo Coronel Navarrete (PM / PO)

**Checklist de aprobación del PM.** El PM aprueba si, y solo si, se cumple TODO:

| # | Verificación | Cómo se comprueba |
|---|---|---|
| 1 | **Sin errores** — todos los checks de CI en verde | Pestaña *Checks* del PR |
| 2 | **Plantilla completa** — ninguna sección vacía ni casilla sin marcar | Cuerpo del PR |
| 3 | **IDs presentes** — historia y requisito referenciados | Sección *IDs relacionados* |
| 4 | **DevLog registrado** si se usó IA | Enlace en el PR + archivo en `_DevLog/` |
| 5 | **Definition of Filed** cumplida | Frontmatter, `_index.md`, matriz |
| 6 | **Avance actualizado** en la matriz de trazabilidad | [[02_Requirements/Traceability_Matrix]] |
| 7 | **Revisión técnica de apoyo** considerada (si el Tech Lead comentó) | Hilos del PR resueltos |
| 8 | **Sin secretos ni datos pesados** | Gate de CI + revisión del diff |
| 9 | **README actualizado** si cambia instalación o uso | Diff del PR |

**Si algo falla, el PM solicita cambios (*Request changes*) señalando el punto exacto.** No se aprueba
"con observaciones": o cumple, o vuelve al autor.

> **Por qué compuerta única:** en Sprint 1 la doble aprobación obligatoria bloqueó PR listos que
> esperaban una 2ª firma. Con una sola compuerta (PM) el merge no se detiene; la revisión técnica del
> Tech Lead se conserva como apoyo no bloqueante. El PM es responsable de que ningún artefacto entre a
> `main` sin trazabilidad. Ver DEC-003.

## Protección de `main` (configuración obligatoria)

En GitHub → **Settings → Branches → Add branch protection rule**:

- Pattern: `main`
- ✅ Require a pull request before merging (**1 aprobación**: el PM, ver DEC-003)
- ✅ Require review from Code Owners (con CODEOWNERS = `* @edgarcoroneln`, la aprobación debe ser del PM)
- ✅ Require status checks to pass → seleccionar el job de CI
- ✅ Require branches to be up to date before merging
- ✅ Bypass: rol **Repository admin** (para que el PM mergee sus propios PR, que no puede autoaprobar)

> **Nota de plan:** las ramas protegidas están disponibles gratis en repositorios **públicos**. En
> repositorios privados requieren GitHub Pro, Team o Enterprise.

## Resolución de conflictos

```bash
git checkout main && git pull origin main
git checkout <tu-rama>
git merge main            # resuelve los conflictos aquí, en tu rama
# ... resolver, probar que sigue funcionando ...
git add . && git commit -m "chore: merge main y resolucion de conflictos"
git push
```

**Nunca fuerces un push** (`--force`) sobre una rama compartida.

## Si rompes `main`

1. Avisa de inmediato en el canal del equipo.
2. Se revierte con `git revert <sha>` (no `reset`, porque la historia es compartida).
3. Se registra el incidente en [[10_Risk_Governance/Incident_Log]].
