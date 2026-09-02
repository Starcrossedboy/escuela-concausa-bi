---
id: DOC-BRANCHPROT
title: "Branch Protection"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [engineering, git, security, enforcement]
traces_up: [REQ-007, US-523a, DEC-003]
traces_down: [".github/CODEOWNERS"]
---

# Branch Protection — FARO

> Convierte las reglas de workflow en **enforcement técnico**.
> Está implementado como **ruleset** `main` (GitHub → Settings → Rules → Rulesets), no
> como el *branch protection* clásico. Contrastado contra la API el 26-ago-2026.
> → [[vault/05_Engineering/_index]]

## Estado real de las reglas en `main`

| Regla | Estado | Nota |
|---|---|---|
| Require a pull request before merging | ✅ activa | `required_approving_review_count = 1` |
| Require review from Code Owners | ✅ activa | es lo que hace vinculante a `.github/CODEOWNERS` |
| Require status checks to pass | ✅ activa | **solo dos** son requeridos, ver abajo |
| Require branches to be up to date | ✅ activa | `strict_required_status_checks_policy = true` |
| Extra approval for unattributed changes | ✅ activa | |
| Block force pushes | ✅ activa | regla `non_fast_forward` |
| Block deletions | ✅ activa | regla `deletion` |
| Dismiss stale approvals on new commits | ❌ **apagada** | deliberado, ver §Por qué |
| Require conversation resolution | ❌ apagada | |
| Require approval of the most recent push | ❌ apagada | |
| Do not allow bypassing (incluye admins) | ❌ **apagada** | el rol *admin* tiene bypass `always`, deliberado |

**Método de merge permitido: solo `merge` (Create a merge commit).** `squash` y `rebase` están
apagados, y `Automatically delete head branches` también.

> **Por qué solo merge commit.** Un *squash* comprime el trabajo en un commit nuevo que **no es
> ancestro** de la rama de origen. Como las ramas `dev/*` son permanentes y se siguen usando,
> quedarían divergentes para siempre: cada PR posterior de esa persona volvería a arrastrar
> conflictos ya resueltos. Y borrar la rama al mergear obliga a recrearla desviada de `main`.

### Checks requeridos

Solo estos dos bloquean el merge:

- `Calidad de codigo y vault`
- `Generar y validar tablero PM`

`quality-checks` y `Contrato dbt (parse)` corren en cada PR pero **no son requeridos**: un
rojo en ellos no impide mergear. Es intencional — `quality-checks` valida la plantilla del
PR, no el código.

## Por qué el admin conserva el bypass

No es un descuido: es el mecanismo que hace viable **DEC-003 (compuerta única)**.

El PM es el único revisor obligatorio del repositorio, y GitHub **no permite que nadie
apruebe su propio PR**. Sin el bypass, ningún PR del PM podría mergearse nunca. Se usa
exclusivamente para eso, y cada uso queda registrado en el historial del merge.

Por la misma razón, `dismiss_stale_reviews_on_push` está **apagado** a propósito: permite
que el PM resuelva un conflicto en la rama de un compañero —cosa frecuente, porque `main`
se mueve varias veces al día— sin invalidar la aprobación que ya había dado.

## CODEOWNERS — compuerta única

Por **DEC-003**, el repositorio opera con un solo revisor obligatorio. `.github/CODEOWNERS`
asigna al PM (`@edgarcoroneln`) como dueño de todo el árbol, y como el ruleset exige
*Require review from Code Owners*, esa aprobación tiene que ser la suya.

```text
*                           @edgarcoroneln
```

Los Tech Leads siguen haciendo revisión técnica de su área, pero se les solicita como
revisores manualmente y **no bloquean** el merge.

## Verificación

Los 17 "saltos" a `main` del proyecto anterior se evitan aquí: sin esta configuración las
reglas son solo texto. El ruleset está `active` sobre la rama por omisión.

Para contrastar este documento contra la configuración viva:

```bash
gh api repos/{owner}/{repo}/rulesets --jq '.[0].id' | xargs -I{} gh api repos/{owner}/{repo}/rulesets/{}
```

Si algo de la tabla de arriba deja de coincidir, **gana la API** y hay que corregir este
documento — es `source_of_truth` sobre la intención, no sobre el estado.
