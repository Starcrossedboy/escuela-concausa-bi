---
id: ADR-004
title: "ADR-004 — Autenticación: OAuth2 con Google + JWT propio (access/refresh)"
owner: "Christian Imanol Ruiz Hurtado"
status: proposed
traces_up: ["REQ-004", "02_Requirements/User_Stories", "03_Architecture/API_Specification"]
traces_down: ["US-402", "US-403", "07_Security/Security_Model"]
supersedes: []
date: "2026-08-17"
tags: [architecture, adr, security, auth, oauth2, jwt, celula-4]
---

# ADR-004 — Autenticación: OAuth2 con Google + JWT propio (access/refresh)

→ [[03_Architecture/ADRs/_index|Volver a ADRs]] · [[03_Architecture/API_Specification|API_Spec §2]] · [[07_Security/Security_Model|Security Model]]

## Contexto

REQ-004 exige autenticación OAuth2/JWT y RBAC de 2 roles (`ciudadano`, `analista`). El contrato
([[03_Architecture/API_Specification]] §2) ya fija el flujo: login con Google, la API emite **JWT
propios** (access corto + refresh largo) y protege los endpoints. US-402 implementa la emisión y
validación de esos tokens; US-403 el enforcement por rol. Es el requisito de seguridad más delicado
del PRD, por lo que entra bajo la **regla 7 del vault** (revisión humana explícita de seguridad).

## Decisión

1. **Identidad federada con Google (OpenID Connect).** `GET /auth/login` redirige al consentimiento;
   `GET /auth/callback` canjea el `code` por la identidad (`sub`, `email`) y la API emite sus tokens.
   La verificación real contra Google se aísla tras una interfaz (`GoogleVerifier`) para poder probar
   sin credenciales y para no acoplar el resto del sistema al proveedor.
2. **JWT propios, dos tokens:**
   - **access** — 15 min, `Authorization: Bearer`, claims `sub`, `role`, `email`, `type=access`.
   - **refresh** — 7 días, se canjea en `POST /auth/refresh`; claims `sub`, `email`, `type=refresh`.
   - El claim `type` impide usar un refresh como access (y viceversa).
3. **Firma HS256 ahora, RS256 en producción.** Simétrica con `JWT_SECRET_KEY` para la demo; el paso a
   RS256 (llave privada firma, pública valida) se hace en el hardening (US-404) con gestión de llaves
   de la Célula 5.
4. **Endurecimiento contra confusión de algoritmo:** `decode` recibe **siempre** una lista explícita
   de algoritmos permitidos; nunca se confía en el `alg` del token entrante.
5. **Rol re-resuelto en cada refresh:** el refresh no lleva el rol; al refrescar se recalcula con la
   política vigente, de modo que un cambio de permisos surta efecto sin re-login.
6. **Política de rol de mínimo privilegio (PROVISIONAL):** por defecto todos `ciudadano`; `analista`
   solo por allowlist explícita (`ANALISTA_EMAILS`). **La política definitiva la decide Edgar/PO.**
7. **Guarda de arranque:** en `ENVIRONMENT=production` la app se niega a iniciar si el secreto JWT es
   el de desarrollo o mide <32 caracteres.

## Alternativas consideradas

| Opción | Pros | Contras |
|---|---|---|
| Sesión con cookie de servidor | Simple, revocación fácil | No encaja con API stateless + SPA/Streamlit + Cloud Run multi-instancia. Rechazada. |
| Solo access token (sin refresh) | Menos piezas | O el token es largo (inseguro) o el usuario re-login constante. Rechazada por el contrato. |
| **OAuth2 Google + JWT access/refresh** ✅ | Cumple el contrato, sin gestionar contraseñas, escalable y stateless | Complejidad de manejar dos tokens y su almacenamiento en el cliente. |
| `python-jose` vs `PyJWT` | jose lo indica el plan de sprint | jose arrastra CVEs de confusión de algoritmo; se mitiga con uso endurecido. **Evaluar PyJWT en US-404.** |

## Riesgos de seguridad y mitigaciones

- **Confusión de algoritmo (CVE de `python-jose`)** → algoritmos explícitos en `decode`; solo HS256;
  recomendación de evaluar PyJWT/RS256 en el hardening. `pip-audit` en CI vigila el paquete.
- **Fuga del secreto / secreto débil** → nunca en el repo (`.env` en `.gitignore`); guarda de arranque
  en producción; rotación por Secret Manager (Célula 5).
- **CSRF en el callback** → el `state` debe ser aleatorio y ligado a la sesión (se cierra en el e2e).
- **Robo del refresh (vida larga)** → vías HTTPS obligatorio; se contempla rotación/revocación en US-404.
- **Almacenamiento en el cliente (frontend US-405):** access en memoria; refresh en cookie `HttpOnly`
  `Secure` `SameSite` (no en `localStorage`). Se detalla al implementar US-405.
- **Fuga de detalles internos** → todos los fallos de auth devuelven un 401 uniforme (`ErrorOut`) sin
  causa; los NotImplemented/Config del servidor devuelven 500 genérico.

## Consecuencias

- US-403 construye `require_role(...)` sobre `get_current_user` de este ADR.
- Requiere de terceros: credenciales OAuth de Google + secreto en Secret Manager (**Célula 5**) y la
  **política de rol** definitiva (**Edgar/PO**).
- `07_Security/Security_Model.md` (owner: Edgar) debe actualizar su sección de Autenticación para
  reflejar este mecanismo; se solicita en el PR (no se edita aquí por no ser artefacto propio).
