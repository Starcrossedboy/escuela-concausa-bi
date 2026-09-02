---
id: DOC-SECMODEL
title: "Security Model"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
source_of_truth: true
tags: [security, auth]
---

# Security Model — FARO

> Cómo se autentica, autoriza y protege la información. → [[vault/07_Security/_index]]

## Autenticación
- Mecanismo: <OAuth/JWT/Firebase Auth/...>
- Todos los endpoints no públicos exigen token válido (401 sin token).

## Autorización
- Cada escritura verifica **propiedad del recurso** (p.ej. `userId == req.user.uid`) → evita IDOR.
- Principio de mínimo privilegio en servicios y agentes IA.

## Datos
- Cifrado en tránsito (TLS) y en reposo según proveedor.
- Sin datos personales en URLs/logs. Sin stack traces al cliente.

## Acceso a producción
- Solo roles autorizados. Los agentes IA **no** tienen acceso directo a producción
  ([[vault/09_AI_Governance/AI_Agent_Governance]]).

## Reglas de datos (si aplica, p.ej. Firestore/DB rules)
- Probadas con tests automatizados (gate en CI).
