---
id: DOC-WORKFLOW
title: "Engineering Workflow"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [engineering, git, workflow]
---

# Engineering Workflow — FARO

> Política de branching, PRs y colaboración. El detalle vive en
> [[vault/05_Engineering/Branching_Strategy]]. → [[vault/05_Engineering/_index]]

## Reglas de oro
| Regla | Detalle |
|---|---|
| `main` es la única fuente de verdad | Siempre desplegable; nunca push directo |
| **Merge solo por PR** | Prohibido push directo a la rama protegida |
| **Una rama fija por persona** | `dev/{primer-nombre}-{apellido-paterno}`, permanente, nunca se borra |
| Sincronizar antes de abrir el PR | `git merge origin/main` — nunca `rebase`, nunca `--force` |
| Solo archivos de tu alcance | 🟢/🟡 de tu Agent Context y de `vault/_Meta/ownership.yml` |
| 1 aprobación (PM) | El autor no aprueba su propio PR |
| CI verde antes de merge | Lint + tests + build + audit + propiedad + sincronía |
| DevLog antes del push | Toda sesión con IA |

## Flujo paso a paso
```bash
git checkout dev/tu-nombre-apellido
git fetch origin && git merge origin/main    # sincroniza SIEMPRE antes de trabajar
# trabajar; commits Conventional con el ID de la historia (US-###)
git fetch origin && git merge origin/main    # y otra vez antes de abrir el PR
git push origin dev/tu-nombre-apellido
# abrir PR con el template y el título estándar; solicitar al Tech Lead como apoyo
# atender review → merge cuando CI verde + 1 aprobación del PM
# tras el merge: NO borres la rama; vuelve al primer paso
```

## Archivos "hot-spot"
Los archivos tocados por varias personas tienen dueño designado en
`vault/_Meta/ownership.yml`, y el detalle por persona está en su `Agent_Context`
([[vault/09_AI_Governance/_index]]). Para modificar un archivo ajeno: pídeselo a su dueño y que
él lo lleve en su rama. El CI reprueba el PR que sale del alcance de su autor.

## Conflictos
```bash
git checkout dev/tu-nombre-apellido
git fetch origin
git merge origin/main
# resolver; probar que sigue funcionando; luego
git add <archivos-resueltos>
git commit -m "chore: merge de main y resolucion de conflictos (<ID>)"
git push origin dev/tu-nombre-apellido
```

Tu rama es permanente y su historia sostiene las revisiones de tus PRs anteriores: se sincroniza
con `merge`, **nunca con `rebase`**, y **nunca se empuja con `--force`**.

## Trazabilidad en el commit
Incluye el ID de la historia (`US-###`) o, cuando el cambio no nace de una historia, el del
artefacto que lo origina (`BUG-###`, `ADR-###`, `SEC-###`) para cerrar la cadena de
[[vault/02_Requirements/Traceability_Matrix]].
