---
id: DOC-A11Y
title: "Accessibility"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
tags: [ux, accessibility, a11y]
---

# Accessibility — FARO

> Requisitos mínimos de accesibilidad. **Sin gate automatizado todavía** — se verifican a mano
> (Marina García, 2026-09-03: no hay "lighthouse" en `.github/` ni en
> [[vault/08_CICD_DevOps/CI_Quality_Gates]]; este documento lo daba por hecho).
> → [[vault/04_UX_Design/_index]]

## Checklist
- [ ] Contraste AA (texto ≥ 4.5:1)
- [ ] Navegable por teclado
- [ ] Roles/labels ARIA en controles
- [ ] `alt` en imágenes significativas
- [ ] Focus visible
- [ ] Respeta `prefers-reduced-motion`

## Meta objetivo (no bloqueante — sin CI que lo mida)
- Lighthouse Accessibility ≥ 0.9. Aspiracional hasta que exista el gate; verificar a mano con
  Lighthouse en el navegador antes de la demo.
