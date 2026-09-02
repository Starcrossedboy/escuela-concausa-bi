---
id: META-NAMING
title: "Naming Conventions"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [meta, naming, ids]
---

# Naming Conventions — IDs, archivos, ramas y commits

> → [[vault/_Meta/_index|Volver a _Meta]]

## Prefijos de ID (globales, únicos, secuenciales)

| Prefijo | Artefacto | Vive en |
|---|---|---|
| `REQ-###` | Requisito (general o detallado) | [[vault/02_Requirements/Requirements_Detailed]] |
| `US-###` | User Story | [[vault/02_Requirements/User_Stories]] |
| `AC-###` | Criterio de aceptación | junto a su US |
| `ADR-###` | Decisión de arquitectura | `vault/03_Architecture/ADRs/` |
| `TASK-###` | Tarea de sprint | `vault/12_Roadmap_Sprints/Sprints/` |
| `TEST-###` | Caso de prueba | `vault/06_Quality_Testing/` |
| `BUG-###` | Defecto | [[vault/06_Quality_Testing/Bug_Register]] |
| `SEC-###` | Hallazgo de seguridad | [[vault/07_Security/Security_Audit_Log]] |
| `RISK-###` | Riesgo | [[vault/10_Risk_Governance/Risk_Register]] |
| `BLOCK-###` | Bloqueo activo | [[vault/10_Risk_Governance/Blocker_Register]] |
| `INC-###` | Incidente | [[vault/10_Risk_Governance/Incident_Log]] |
| `DEC-###` | Decisión (no arquitectónica) | [[vault/10_Risk_Governance/Decision_Log]] |

> Regla: los IDs **nunca se reutilizan**, aunque el artefacto se archive.

## Nombres de archivo

- Documentos: `Title_Case_With_Underscores.md`
- Fechados (DevLog, reportes): `YYYY-MM-DD-descripcion-kebab.md`
- Índices de carpeta: `_index.md`

## Ramas Git

Una sola forma, sin variantes ni prefijos de tipo:

```
dev/{identidad}
```

Una rama fija y permanente por persona, para todo el proyecto. El tipo de trabajo
(`feat`, `fix`, `chore`, `docs`, `sec`) **no va en la rama: va en el commit**, donde sí
distingue un cambio de otro. Ver [[vault/05_Engineering/Branching_Strategy]].

Ejemplos: `dev/diana-alvarez` · `dev/luis-tellez` · `dev/hector-morales`

Sin acentos ni caracteres especiales.

## Commits — Conventional Commits

```
<tipo>(<scope>): <descripción corta>

Tipos: feat · fix · chore · docs · test · refactor · style · sec
Ejemplo: feat(gold): cubo de matricula por municipio (US-113)
```

> **El ID es obligatorio en todo commit.** Se usa el de la historia (`US-###`) y, cuando el
> cambio no nace de una historia, el del artefacto que lo origina (`BUG-###`, `ADR-###`,
> `SEC-###`, `TEST-###`). Un commit sin ID rompe el ciclo de trazabilidad.

## Nombres de personas — la identidad canónica

Una sola identidad por persona, construida **siempre igual**:

```
{primer-nombre}-{apellido-paterno}
```

en minúsculas, ASCII sin acentos, kebab-case. **Se ignoran el segundo nombre y el apellido
materno**, que son justo las dos piezas que generan variantes de la misma persona.

| Nombre completo | Identidad |
|---|---|
| Héctor Rafael Morales Marbán | `hector-morales` |
| Christian Imanol Ruiz Hurtado | `christian-ruiz` |
| Diana Aracely Alvarez Varela | `diana-alvarez` |

Esa identidad es la misma en **todos** lados: la rama (`dev/{identidad}`), la firma del título
del PR, el nombre del DevLog (`YYYY-MM-DD-{identidad}-tema.md`), el Agent Context
(`{identidad}-agent-context.md`) y el enlace a su plan de sprint.

El padrón de las 21 identidades —con su rama, su handle de GitHub y su alcance— vive en un solo
archivo: **`vault/_Meta/ownership.yml`**. Es la fuente de verdad y la que lee el CI. Quien no
está ahí, no puede abrir un PR.
