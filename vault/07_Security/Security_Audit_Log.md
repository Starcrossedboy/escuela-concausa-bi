---
id: DOC-SECLOG
title: "Security Audit Log"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
tags: [security, audit, log]
---

# Security Audit Log — FARO

> Registro único de hallazgos de seguridad. Detalle con [[vault/_Templates/Security_Finding_template]].
> → [[vault/07_Security/_index]]

| SEC | Título | Severidad | Estado | Encontrado | Remediación (PR) | Verificado |
|---|---|---|---|---|---|---|
| SEC-001 | | high | open | 2026-08-01 | | ☐ |
| SEC-002 | `state` de OAuth constante (`faro`): el callback no estaba protegido contra login CSRF | high | resolved | 2026-09-02 | `state` firmado de un solo uso + cookie `HttpOnly` (US-402) | ☑ |
| SEC-003 | Rate limiting en memoria por proceso: con varias instancias el límite efectivo se multiplica | medium | accepted_risk | 2026-09-02 | Follow-up: backend compartido (Redis) o límite en el balanceador — C5 | ☐ |
| SEC-004 | JWT propios con HS256 (simétrico): quien lea el secreto puede **emitir** tokens | medium | accepted_risk | 2026-09-02 | Follow-up: migrar a RS256 con llaves en Secret Manager | ☐ |
| SEC-005 | Refresh tokens sin rotación ni revocación (vigencia 7 días) | medium | accepted_risk | 2026-09-02 | Follow-up: rotación en cada canje + lista de revocación | ☐ |
| SEC-006 | `AUTH_LECTURA_PUBLICA=true` en el entorno desplegado: la lectura no exige sesión | low | accepted_risk | 2026-09-02 | Decisión de demo; se apaga por configuración cuando el login e2e esté validado — C5 | ☐ |

## Estados
open → mitigating → resolved (o accepted_risk con firma del owner).

> `SEC-002`…`SEC-006` los levantó y firmó Christian Ruiz (dueño de `vault/07_Security/**`) en
> [[vault/07_Security/Security_Review_US402_US403_US404]] — revisión humana explícita de la regla 7
> para el cierre de US-402, US-403 y US-404.
