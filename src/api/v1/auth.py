"""Autenticación `/auth/*` (§3.2).

**Stub del contrato (US-401):** devuelve ejemplos válidos de `TokenPair`/`UserOut` para que los
clientes mockeen el flujo. El OAuth2 real con Google y la emisión/validación de JWT son **US-402**;
aquí no se firma ni verifica ningún token.
"""
from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from src.api.schemas import RefreshIn, Rol, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["Autenticación"])

_TOKEN_EJEMPLO = TokenPair(
    access_token="mock.access.jwt",
    refresh_token="mock.refresh.jwt",
    token_type="bearer",
    expires_in=900,
)


@router.get("/login", status_code=status.HTTP_302_FOUND)
def login() -> RedirectResponse:
    """Inicia OAuth2 con Google (US-402). En el stub redirige a un destino de ejemplo."""
    return RedirectResponse(
        url="https://accounts.google.com/o/oauth2/v2/auth?client_id=MOCK",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/callback", response_model=TokenPair)
def callback(code: str) -> TokenPair:
    """Callback de Google: canjea `code` por el par de tokens (mock)."""
    return _TOKEN_EJEMPLO


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn) -> TokenPair:
    """Canjea un refresh token válido por un nuevo par (mock)."""
    return _TOKEN_EJEMPLO


@router.get("/me", response_model=UserOut)
def me() -> UserOut:
    """Devuelve el usuario del token en sesión (rol mínimo: ciudadano)."""
    return UserOut(sub="mock-user-001", email="ciudadano@example.mx", role=Rol.ciudadano)
