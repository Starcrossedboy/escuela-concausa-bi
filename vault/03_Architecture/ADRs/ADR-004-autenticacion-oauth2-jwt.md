---
id: ADR-004
title: "ADR-004 — Autenticación: OAuth2 con Google + JWT propio (access/refresh)"
owner: "Christian Imanol Ruiz Hurtado"
status: proposed
traces_up: ["REQ-004", "vault/02_Requirements/User_Stories", "vault/03_Architecture/API_Specification"]
traces_down: ["US-402", "US-403", "vault/07_Security/Security_Model"]
supersedes: []
date: "2026-08-17"
tags: [architecture, adr, security, auth, oauth2, jwt, celula-4]
---

# ADR-004 — Autenticación: OAuth2 con Google + JWT propio (access/refresh)

→ [[vault/03_Architecture/ADRs/_index|Volver a ADRs]] · [[vault/03_Architecture/API_Specification|API_Spec §2]] · [[vault/07_Security/Security_Model|Security Model]]

## Contexto

REQ-004 exige autenticación OAuth2/JWT y RBAC de 2 roles (`ciudadano`, `analista`). El contrato
([[vault/03_Architecture/API_Specification]] §2) ya fija el flujo: login con Google, la API emite **JWT
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

## RBAC — enforcement por rol (US-403)

Sobre `get_current_user` (US-402) se añaden **dos dependencias reutilizables** en
`src/api/security/rbac.py`:

- **`require_role(*roles)`** — exige que el usuario autenticado tenga alguno de los roles; si no,
  **403** con la forma uniforme `ErrorOut`. Sin sesión → **401** (lo emite `get_current_user` antes).
- **`require_lectura`** — protege la lectura según un **interruptor híbrido** `AUTH_LECTURA_PUBLICA`.

**Dónde se aplica:** a nivel de `include_router` en `src/api/v1/__init__.py`, **no** dentro de los
routers de otras células (gold/predicciones son de US-411/US-412). Así el RBAC queda centralizado en
artefactos de Célula 4 sin invadir código ajeno, y se refleja como `security: bearerAuth` por path en
el OpenAPI publicado.

**Matriz de acceso:**

| Endpoints | Rol exigido |
|---|---|
| `GET /health`, `/version`, `/auth/*` | público (probes de Cloud Run y flujo de login) |
| `GET /escuelas*`, `/municipios*`, `/kpis`, `/predicciones/*`, `POST /agente/consulta` | **lectura** (`require_lectura`) |
| `POST /admin/pipeline/run`, `GET /admin/export`, `GET /admin/metrics` | **`analista`** siempre |

**Interruptor híbrido `AUTH_LECTURA_PUBLICA` (decisión con el PO, 2026-08-26):**

- `true` (default) → la lectura es **pública**: la URL viva de la demo (crítica en la rúbrica) no
  depende del login Google, que hoy está **bloqueado** por credenciales pendientes de Célula 5.
- `false` → la lectura exige sesión de **cualquier** rol (mínimo `ciudadano`; `analista` también pasa).
- **El admin nunca se relaja:** siempre `analista`, independiente del flag.
- Al aterrizar credenciales de Google (C5), se pone `AUTH_LECTURA_PUBLICA=false` y la lectura pasa a
  exigir `ciudadano` **sin re-tocar código** — solo variable de entorno.

Pruebas: `tests/test_rbac.py` (matriz 401/403/200 en admin y ambas ramas del flag en lectura).

## Hardening de la API (US-404)

Endurecimiento de la superficie HTTP, configurable por entorno (`config.py`):

- **Rate limiting** por `(IP, path)`, `RATE_LIMIT_DEFAULT` (default `120/minute`). Se implementa con
  el **motor `limits`** (dependencia de `slowapi`) en un middleware propio que devuelve el `ErrorOut`
  429 uniforme. **No** se usa `SlowAPIMiddleware`: su resolución de ruta no reconoce los routers
  incluidos de esta versión de FastAPI (`_IncludedRouter`) y eximiría todo. Es **en memoria por
  proceso** → sirve para 1 instancia/demo; **follow-up:** backend compartido (Redis) para Cloud Run
  multi-instancia.
- **CORS** con orígenes configurables (`CORS_ORIGINS`, CSV); default = frontends locales. C5 añade
  los orígenes reales de despliegue. Métodos/headers acotados (`GET/POST/OPTIONS`, `Authorization`/
  `Content-Type`).
- **Validación estricta de entrada**: los request bodies heredan de `EntradaEstricta`
  (`extra="forbid"`) → un campo desconocido es 422, no se ignora en silencio. Se refleja como
  `additionalProperties: false` en el OpenAPI publicado.
- **Errores sin fuga**: el handler 500 registra el detalle real en logs (`faro.api`) y devuelve un
  mensaje genérico; ningún 4xx/5xx expone trazas, SQL ni configuración interna.

Pruebas: `tests/test_hardening.py` (CORS, 429 con `ErrorOut`, 422 por campo extra, 500 sin fuga).

### Ejecutor SQL read-only del agente (BUG-025)

La colaboración `ejecutar_sql` del seam del agente se implementa en `src/api/ejecutor_gold.py`
(`ejecutar_sql_read_only`), con **defensa en profundidad**:

1. **Rol PostgreSQL con solo `SELECT` sobre `gold.*`** — DSN `DATABASE_URL_READ_ONLY`, distinto de la
   conexión general; es la barrera real (aunque todo lo demás fallara, la BD rechaza escritura).
2. `SET TRANSACTION READ ONLY` por conexión.
3. `statement_timeout` (`AGENTE_SQL_TIMEOUT_MS`, default 30 s).
4. Revalidación con `validar_sql_lectura()` antes de tocar la BD (redundante, a propósito).

Se cablea (`app.dependency_overrides[get_ejecutar_sql]`) **solo si** `DATABASE_URL_READ_ONLY` está
definido; sin él el agente usa el default seguro del seam y CI/local no tocan Postgres. La ejecución
real es integración (US-422, Eloisa). Config por patrón `Settings` (minúsculas, sin `os.getenv` suelto).

**Pendiente de Célula 5:** crear el rol `faro_agente_readonly` (`GRANT SELECT ON ALL TABLES IN SCHEMA
gold`), el secreto en Secret Manager y el `--set-secrets=DATABASE_URL_READ_ONLY=...` en Cloud Run.

**Follow-ups de hardening (documentados aquí):** migración a **RS256** (llaves RSA en Secret Manager,
**C5**) manteniendo `jwt_algorithm` configurable; **rotación/revocación de refresh** con un store
(Postgres/Redis); rate limiting distribuido (Redis).

## Consecuencias

- US-403 construye `require_role(...)` sobre `get_current_user` de este ADR.
- Requiere de terceros: credenciales OAuth de Google + secreto en Secret Manager (**Célula 5**) y la
  **política de rol** definitiva (**Edgar/PO**).
- `vault/07_Security/Security_Model.md` (owner: Edgar) debe actualizar su sección de Autenticación para
  reflejar este mecanismo; se solicita en el PR (no se edita aquí por no ser artefacto propio).
