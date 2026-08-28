"""Autenticación `/auth/*` (§3.2) — OAuth2 con Google + JWT propio (US-402).

- `GET  /auth/login`    → 302 a la pantalla de consentimiento de Google.
- `GET  /auth/callback` → canjea el `code` por la identidad (vía verificador) y emite el par de JWT.
- `POST /auth/refresh`  → valida el refresh token y emite un par nuevo (re-resolviendo el rol).
- `GET  /auth/me`       → devuelve el usuario del access token (protegido por `get_current_user`).

Nota: el enforcement por rol de los endpoints de datos/admin es **US-403** (RBAC), aquí solo se
autentica. La verificación real contra Google queda tras `RealGoogleVerifier` (pendiente de
credenciales de la Célula 5); los tests usan un verificador falso.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from src.api.schemas import RefreshIn, TokenPair, UserOut
from src.api.security.deps import get_current_user, get_google_verifier
from src.api.security.google import GoogleNotConfigured, GoogleVerifier
from src.api.security.jwt import AuthError, create_token_pair, verify_refresh_token
from src.api.security.roles import resolve_role

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.get("/login", status_code=status.HTTP_302_FOUND)
def login() -> RedirectResponse:
    """Inicia OAuth2 con Google redirigiendo a la pantalla de consentimiento.

    Nota de seguridad: el `state` debe ser un valor aleatorio ligado a la sesión para prevenir CSRF;
    su generación/almacenamiento se cierra al integrar el flujo e2e con credenciales reales (US-402).
    """
    from src.api.security.google import build_authorization_url

    return RedirectResponse(
        url=build_authorization_url(state="faro"),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/callback", response_model=TokenPair)
def callback(
    code: str,
    verifier: GoogleVerifier = Depends(get_google_verifier),
) -> TokenPair:
    """Callback de Google: valida el `code`, resuelve el rol y emite el par de JWT."""
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
    return create_token_pair(sub=identity.sub, role=role, email=identity.email)


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
    return create_token_pair(sub=claims["sub"], role=role, email=email)


@router.get("/me", response_model=UserOut)
def me(user: UserOut = Depends(get_current_user)) -> UserOut:
    """Devuelve el usuario autenticado (requiere access token válido; 401 en caso contrario)."""
    return user
