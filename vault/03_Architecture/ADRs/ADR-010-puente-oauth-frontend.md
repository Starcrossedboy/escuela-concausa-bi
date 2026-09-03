---
id: ADR-010
title: "ADR-010 — Puente OAuth → frontend: código de un solo uso, no tokens en la URL"
owner: "Christian Imanol Ruiz Hurtado"
status: proposed
traces_up: ["REQ-004", "vault/03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt", "vault/03_Architecture/Frontend_Architecture"]
traces_down: ["US-405", "vault/07_Security/Security_Review_US402_US403_US404", "SEC-007"]
supersedes: []
date: "2026-09-03"
tags: [architecture, adr, security, auth, oauth2, frontend, streamlit, celula-4]
---

# ADR-010 — Puente OAuth → frontend: código de un solo uso, no tokens en la URL

→ [[vault/03_Architecture/ADRs/_index|Volver a ADRs]] · [[vault/03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt|ADR-004]] ·
[[vault/03_Architecture/API_Specification|API_Spec §2.1.2]] · [[vault/03_Architecture/Frontend_Architecture|Frontend_Architecture §3]]

## Contexto

`Frontend_Architecture.md` §3 dice que FARO Web *"redirige al `/auth/login` de la API y guarda el
access/refresh token en `st.session_state`"*. **Nunca se especificó el paso intermedio**: cómo llega
el token de vuelta al front.

Hoy el flujo termina en `/auth/callback`, que responde el `TokenPair` como **JSON en el navegador**.
Quien está ahí es el navegador, no el servidor de Streamlit: la persona ve un blob de JSON en
pantalla y el front nunca se entera de que hubo login. No es un defecto de US-402 —el flujo OAuth es
correcto y está probado— es una pieza de diseño que faltaba, y **bloqueaba US-405** por completo.

Restricción que descarta la solución habitual: **Streamlit no puede leer cookies del navegador** sin
un componente de terceros. Lo que sí puede leer es la query string (`st.query_params`) y hacer
peticiones HTTP desde su servidor.

## Decisión

`/auth/callback` **no manda el token al navegador**. Guarda la identidad recién verificada, genera un
**código opaco de un solo uso** y redirige al front con `?code_faro=<código>`. El servidor de
Streamlit lo canjea en `POST /auth/exchange` y recibe los tokens **en el cuerpo de la respuesta**.

```
navegador          API                         front (servidor)
    │  GET /auth/login?redirect=<front>         │
    │──────────────►│  (redirect validado contra allowlist)
    │  ... Google ...
    │  GET /auth/callback?code&state            │
    │──────────────►│  verifica id_token, guarda identidad,
    │               │  emite código de un solo uso
    │  ◄────302──── │  Location: <front>?code_faro=XXX
    │────────────────────────────────────────► │
    │                                          │  POST /auth/exchange {code}
    │               │◄─────────────────────────│
    │               │──── TokenPair (cuerpo) ─►│  → st.session_state
```

Cinco decisiones concretas:

1. **Por la URL viaja un código, nunca un token.** Es el punto entero. Una URL con el token dentro
   acaba en el historial del navegador, en los logs de cualquier proxy intermedio y en la cabecera
   `Referer` de la siguiente petición que haga la página.
2. **El `redirect` va dentro del `state` firmado**, no como parámetro suelto en el callback. Google
   nos devuelve el `state` intacto y su firma impide que nadie lo cambie por el camino.
3. **Allowlist estricta y comparación exacta** para el `redirect` (`FRONTEND_REDIRECT_URIS`). Un
   *open redirect* dentro del flujo de login es el vehículo clásico para desviar el código de
   autorización. La comparación no es por prefijo: un `startswith` deja pasar
   `https://faro.example.com.evil.tld` cuando la allowlist dice `https://faro.example.com`.
4. **Se guarda la identidad, no los tokens**, y del código solo su **SHA-256**. Así no hay
   credenciales en reposo, y quien lea la tabla no puede canjear nada. Los JWT se emiten al canjear,
   **re-resolviendo el rol** con la política vigente.
5. **El canje es atómico** (`DELETE ... RETURNING`). "Un solo uso" lo garantiza Postgres, no una
   comprobación en Python que dos peticiones simultáneas podrían esquivar.

Vida del código: **60 segundos**. Solo tiene que cubrir un redirect de navegador.

## Alternativas consideradas

| Opción | Por qué no |
|---|---|
| **Tokens en la query string del redirect** | Veinte minutos de trabajo y el token queda en el historial, en los logs del proxy y en el `Referer`. Es justo lo que ADR-004 §Almacenamiento dice que no hagamos. |
| **Cookies `HttpOnly` puestas por el callback** | Conceptualmente la mejor, pero **Streamlit no puede leerlas** sin un componente custom. Descartada por la herramienta, no por el diseño. |
| **Código firmado (JWT) sin almacén** | Sin estado, pero un JWT en la URL **es** una credencial: si se filtra dentro de su ventana sirve igual, y sin almacén no hay forma de forzar el "un solo uso". |
| **Pegado manual del token** | Cero código y cero riesgo, pero implica copiar un JSON a mano en una demo evaluada. |
| **Que el front implemente OAuth por su cuenta** | Duplica la lógica más delicada del proyecto en dos lenguajes y dos células, y contradice `Frontend_Architecture` §3. |

## Consecuencias

**Positivas.** US-405 se desbloquea sin exponer credenciales en URLs. El front no aprende a
interpretar JWT: pide la identidad a `/auth/me`, así que la fuente de verdad sigue siendo la API. El
rol se re-resuelve al canjear, así que un cambio de `ANALISTA_EMAILS` surte efecto sin re-login.

**Costos.** Un endpoint más (`POST /auth/exchange`), una tabla más (`auth.codigos_login`, fuera de
`gold`: no es un artefacto analítico) y una llamada HTTP extra en el login.

**Riesgo aceptado — `SEC-007`.** La tabla se crea de forma idempotente al arrancar, lo que exige que
el rol de la aplicación tenga permiso de `CREATE` sobre la base. Si no lo tiene —o la base no está
disponible— el almacén **degrada a memoria del proceso** y lo registra como `error` en el log. En
memoria el login **solo es correcto con una instancia**: con varias, el canje puede llegar a un
proceso que no emitió el código y el login falla de forma intermitente. Se eligió degradar en vez de
fallar porque un login caído del todo es peor que uno que funciona en la configuración actual (una
instancia), pero **hay que verificar el permiso en el despliegue** — es lo primero que se comprueba
tras el siguiente redeploy.

**No resuelto aquí.** El cierre de sesión sigue siendo local al navegador: no revoca el refresh token
del lado de la API. Eso es `SEC-005`, follow-up ya documentado en ADR-004.
