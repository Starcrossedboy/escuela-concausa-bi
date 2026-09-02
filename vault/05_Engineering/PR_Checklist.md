---
id: DOC-PRCHECK
title: "PR Checklist"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [engineering, pr, checklist]
---

# PR Checklist — FARO

> Verificar antes de solicitar review. La plantilla que GitHub carga sola al abrir el PR es
> `.github/PULL_REQUEST_TEMPLATE.md` — la única, y la que valida el CI.
> → [[vault/05_Engineering/_index]]

## Rama y sincronía (primero)
- [ ] Salgo de mi rama fija `dev/{identidad}` — la única que uso
- [ ] Hice `git merge origin/main` **antes** de abrir el PR
- [ ] Título en estándar: `[Nombre Apellido] - Descripción (ID) - [sync|CI|DoF|DevLog]`

## Colaboración IA
- [ ] DevLog creado con `author_human` y `agent`
- [ ] Solo archivos dentro de mi alcance (`vault/_Meta/ownership.yml`) — o cambio transversal
      declarado, con revisión pedida a cada dueño afectado
- [ ] Archivos compartidos coordinados y documentados

## Código
- [ ] Hace lo que dice el título; sin `console.log` ni código comentado
- [ ] Sin secretos hardcodeados; env nuevas en `.env.example`

## Pruebas
- [ ] ≥1 test para el comportamiento principal (TEST-###)
- [ ] Suite existente en verde

## Seguridad
- [ ] Endpoints con auth; escrituras verifican propiedad
- [ ] Sin fugas en errores; si toca seguridad/schema/CI → review del dueño

## Calidad / Trazabilidad
- [ ] Lint y build en verde
- [ ] Matriz de trazabilidad actualizada

## 🚫 Rechazo automático
1. Secretos hardcodeados
2. Build roto en CI
3. Push directo a main sin PR
4. PR sin descripción / sin ID de requisito
5. Rama distinta de `dev/{identidad}`
6. Rama sin el último `main`
7. Archivos fuera del alcance del autor
8. Título fuera de estándar o firmado por otra persona
