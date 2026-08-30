---
project: "FARO"
date: "2026-08-29"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1h"
touches: ["US-502", "US-504", "REQ-005", "SEC-CREDENTIALS-POLICY", "SEC-THREAT-MODEL"]
tags: [devlog, security, docs, cis-controls, devops]
---

# DevLog — 2026-08-29 — Workstream documental de seguridad (CIS + US IDs + generate-keys)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

Limpieza de **deuda documental de seguridad** en los artefactos de los que soy owner
(sin GCP, sin costo). Motivada por el plan de Célula 5 mientras el PR #144 (Fase 2)
espera revisión del PM. Se respetó el ownership por frontmatter: sólo se tocaron los
archivos cuyo `owner` soy yo.

**1. `07_Security/Credentials_Policy.md` (owner: Luis) → v1.1**
- Corregido el mapeo **CIS Controls v8**: **5.3** ya no se etiqueta como "políticas de
  complejidad de passwords" (error); su nombre real es **"Disable Dormant Accounts"**.
  La guía de longitud (≥14 chars) se re-atribuyó a **5.2 (Use Unique Passwords)**, que
  es donde vive en v8. El **6.5** se corrigió de "gestión centralizada" a su nombre real
  **"Require MFA for Administrative Access"** (lo centralizado es 5.6 / 6.7).
- Agregado `JWT_SECRET_KEY` a la lista de "Output del script".

**2. `07_Security/Threat_Model.md` (owner: Luis, co: Christian) → v1.0.1 (patch)**
- Reconciliados los **US IDs** del roadmap con el catálogo real de Célula 5
  (US-501..505): antes usaba IDs cruzados (US-503/504/505) y el **fantasma US-601**.
  Ahora: Secret Manager / red / audit → **US-504 (Fase 1 ✅)**; auth de UIs admin
  (MLflow/ChromaDB vía IAP), WAF y edge → **US-505 (Fases 3-4)**.
- Corregido tech stale para GCP: "nginx reverse proxy" / "self-signed" →
  **Cloud Load Balancing + Cloud Armor + certificados administrados** (coherente con DEC-5).
- Cita CIS 5.3→5.2 en la mitigación M4. Versión patch para **no pisar** la 1.1 reservada
  a Christian en el change log.

**3. `scripts/generate-keys.py`**
- **Eliminada la dependencia de `cryptography`**: la Fernet key ahora se genera con
  stdlib (`base64.urlsafe_b64encode(secrets.token_bytes(32))`, formato idéntico al de
  `Fernet.generate_key()`). Ahora corre en cualquier host sin instalar paquetes.
- **Agregado `JWT_SECRET_KEY`** (`secrets.token_urlsafe(48)`) al output, que antes
  faltaba (por eso en Fase 0 el `.env` se creó a mano con stdlib).
- Docstring/mensajes CIS corregidos a 5.2.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code / claude-opus-4-8
- **Archivos creados/modificados:**
  - `07_Security/Credentials_Policy.md` (v1.1)
  - `07_Security/Threat_Model.md` (v1.0.1)
  - `scripts/generate-keys.py`
  - `_DevLog/2026-08-29-luis-tellez-security-docs-cis-usids-genkeys.md` (este)
  - `_DevLog/_index.md` (fila)
  - `02_Requirements/Traceability_Matrix.md` (evidencia en REQ-005)
- **Decisiones autónomas del agente:** versión patch (1.0.1) en Threat_Model para no
  colisionar con la 1.1 reservada; Fernet key con stdlib en vez de `cryptography`;
  US IDs mapeados a las Fases vigentes del plan de despliegue.
- **Correcciones manuales:** —
- **Verificación:** `python3 _Meta/scripts/vault_lint.py .` → `✅ Vault limpio`;
  `python3 -m py_compile scripts/generate-keys.py` OK; el script ejecuta y emite las
  7 claves (incluida `JWT_SECRET_KEY`) en el host (Python 3.9.6), sin `cryptography`.

## Seguridad / calidad
- [x] Sin secretos hardcodeados (el script sólo genera; nada se versiona)
- [x] `vault_lint` verde
- [x] DevLog enlaza a los IDs afectados
- [ ] Tests: N/A (cambios documentales + script de generación validado a mano)

## Fuera de alcance (handoff)
- **`07_Security/Security_Model.md` y `Compliance.md`** son `owner: Edgar Coronel (PM)`
  y siguen como plantillas con placeholders. Requieren decisiones que sólo el PM puede
  tomar (mecanismo de auth definitivo, base legal de privacidad, licencias de las 8
  fuentes, atribuciones). **Handoff abierto al PM** (chip de sesión).
- Otras citas CIS imprecisas en las mitigaciones del Threat_Model (M1 "5.4",
  M2 "12.4", M5 "3.12") → auditoría CIS completa a coordinar con **Christian** (co-owner
  y security lead).

## Nota de gobernanza
Regla 7 del vault: los cambios de seguridad requieren **revisión humana explícita**.
Este PR va al PM (Edgar) como compuerta; Christian queda notificado como co-owner del
Threat_Model.
