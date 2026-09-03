---
id: DOC-SECREVIEW
title: "Security Review Checklist"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [security, checklist]
---

# Security Review Checklist — FARO

> Ejecutar antes de cada deploy a producción (y en PRs sensibles). En Claude Code: `/security-review`.
> → [[vault/07_Security/_index]]

## Checklist
- [ ] Auth aplicada en todos los endpoints no públicos (401 sin token)
- [ ] Autorización por recurso (sin IDOR): la escritura valida propiedad
- [ ] Validación/sanitización de input (inyección, path traversal, XSS)
- [ ] Sin secretos hardcodeados; escaneo de secretos en verde
- [ ] `npm audit` / SCA sin vulnerabilidades high/critical
- [ ] Sin fuga de info en errores (no stack traces en prod)
- [ ] Rate limiting en endpoints sensibles
- [ ] Reglas de datos probadas
- [ ] Dependencias actualizadas; sin paquetes abandonados críticos
- [ ] Logs sin datos personales

## Resultado
| Fecha | Revisor | Veredicto (🟢/🟡/🔴) | Hallazgos |
|---|---|---|---|
| 2026-09-02 | Christian Ruiz (TL C4) | 🟡 | Superficie de auth (US-402/403/404): `SEC-002` resuelto; `SEC-003`…`SEC-006` aceptados. Detalle en [[vault/07_Security/Security_Review_US402_US403_US404]] |
