---
id: DOC-CODESTD
title: "Coding Standards"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
tags: [engineering, standards, lint]
---

# Coding Standards — FARO

> → [[vault/05_Engineering/_index]]

## Estilo
- Linter/formatter: <ESLint+Prettier / Ruff / etc.> — configuración en el repo.
- Naming, estructura de carpetas, límites de tamaño de función/archivo.

## Reglas mínimas de lint (bloqueantes en CI)
- `no-unused-vars`: error
- `no-undef`: error
- `no-console`: warn (prohibido en prod)

## Manejo de errores y logging
- Logger central; sin `console.log` en producción.
- Sin exponer stack traces al cliente ([[vault/07_Security/Security_Model]]).

## Comentarios
- Explicar el "por qué", no el "qué". Sin TODO sin ticket.
