"""Autenticación `/auth/*` (§3.2) — OAuth2 con Google + JWT propio (US-402).

- `GET  /auth/login`    → 302 a la pantalla de consentimiento de Google, con `state` anti-CSRF.
- `GET  /auth/callback` → valida el `state`, canjea el `code` por la identidad (vía verificador) y
  emite el par de JWT.
- `POST /auth/refresh`  → valida el refresh token y emite un par nuevo (re-resolviendo el rol).
- `GET  /auth/me`       → devuelve el usuario del access token (protegido por `get_current_user`).

Nota: el enforcement por rol de los endpoints de datos/admin es **US-403** (RBAC), aquí solo se
autentica.

**Protección CSRF del callback (US-402).** El `state` es un JWT propio de vida corta
(`create_state_token`) que viaja por dos canales independientes: el parámetro `state` de la URL de
Google y una cookie `HttpOnly` de primera parte. El callback exige que ambos existan, coincidan y
que el token sea válido. Un tercero puede inducir al navegador a llamar al callback, pero no puede
leer ni fabricar la cookie, así que el ataque muere ahí. Se eligió un `state` **firmado** en vez de
uno guardado en memoria porque Cloud Run corre varias instancias sin estado compartido: un `state`
en RAM se perdería entre la ida y la vuelta.
"""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from src.api.config import get_settings
from src.api.schemas import RefreshIn, TokenPair, UserOut
from src.api.security.deps import get_current_user, get_google_verifier
from src.api.security.google import (
    GoogleNotConfigured,
    GoogleVerifier,
    build_authorization_url,
)
from src.api.security.jwt import (
    AuthError,
    create_state_token,
    create_token_pair,
    verify_refresh_token,
    verify_state_token,
)
from src.api.security.roles import resolve_role

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Cookie de primera parte que sostiene la mitad "secreta" del `state`. `SameSite=Lax` es lo correcto
# aquí: la vuelta de Google es una navegación GET de nivel superior, así que la cookie SÍ se envía,
# pero no acompaña a peticiones cross-site incrustadas.
COOKIE_STATE = "faro_oauth_state"


@router.get("/login", status_code=status.HTTP_302_FOUND)
def login() -> RedirectResponse:
    """Inicia OAuth2 con Google redirigiendo a la pantalla de consentimiento.

    Genera el `state` anti-CSRF, lo manda a Google en la URL y guarda el mismo valor en una cookie
    `HttpOnly` para poder compararlos al volver.
    """
    s = get_settings()
    state = create_state_token()
    respuesta = RedirectResponse(
        url=build_authorization_url(state),
        status_code=status.HTTP_302_FOUND,
    )
    respuesta.set_cookie(
        key=COOKIE_STATE,
        value=state,
        max_age=s.oauth_state_expire_minutes * 60,
        httponly=True,  # inaccesible a JavaScript: ni XSS ni un tercero pueden leerla
        secure=s.cookies_seguras,  # en local es http://, donde `Secure` impediría guardarla
        samesite="lax",  # se envía en la navegación de vuelta de Google, no en peticiones incrustadas
        path="/",
    )
    return respuesta


def _validar_state(request: Request, state: str | None) -> None:
    """Verifica el `state` del callback: presente, firmado, vigente y **igual** al de la cookie.

    Cualquier fallo se traduce a un 401 uniforme, sin decir cuál de las tres condiciones falló: el
    mensaje detallado solo ayudaría a quien esté probando el ataque.
    """
    cookie = request.cookies.get(COOKIE_STATE)
    if not state or not cookie or not secrets.compare_digest(state, cookie):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="No se pudo verificar el origen de la petición."
        )
    try:
        verify_state_token(state)
    except AuthError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="No se pudo verificar el origen de la petición."
        ) from exc


@router.get("/callback", response_model=TokenPair)
def callback(
    request: Request,
    response: Response,
    code: str,
    state: str | None = None,
    verifier: GoogleVerifier = Depends(get_google_verifier),
) -> TokenPair:
    """Callback de Google: valida el `state`, canjea el `code`, resuelve el rol y emite los JWT."""
    _validar_state(request, state)
    # El `state` es de un solo uso: se borra la cookie apenas se valida, pase lo que pase después.
    response.delete_cookie(COOKIE_STATE, path="/")

    try:
        identity = verifier.verify(code)
    except GoogleNotConfigured as exc:
        # Config del servidor incompleta: error interno, sin filtrar detalle al cliente.
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth no configurada."
        ) from exc
    except (ValueError, RuntimeError) as exc:
        # `code` inválido / no verificable => 401.
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="No se pudo verificar la identidad."
        ) from exc
    role = resolve_role(identity.email)
    return create_token_pair(
        sub=identity.sub, role=role, email=identity.email, name=identity.name
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn) -> TokenPair:
    """Canjea un refresh token válido por un par nuevo, re-resolviendo el rol con la política vigente."""
    try:
        claims = verify_refresh_token(body.refresh_token)
    except AuthError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado."
        ) from exc
    email = claims.get("email", "")
    role = resolve_role(email)
    # El `name` viaja tambien en el refresh: al renovar no hay id_token de Google que reconsultar.
    return create_token_pair(
        sub=claims["sub"], role=role, email=email, name=claims.get("name", "")
    )


@router.get("/me", response_model=UserOut)
def me(user: UserOut = Depends(get_current_user)) -> UserOut:
    """Devuelve el usuario autenticado (requiere access token válido; 401 en caso contrario)."""
    return user
