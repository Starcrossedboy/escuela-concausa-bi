"""Flujo OAuth2 con Google, desacoplado para poder probar sin credenciales (US-402).

- `build_authorization_url(state)` — construye la URL de consentimiento de Google (pura, testeable).
- `GoogleVerifier` (Protocol) — canjea el `code` del callback por la identidad del usuario.
- `RealGoogleVerifier` — implementación real; **pendiente de credenciales** (las provee la Célula 5).
  Mientras no haya `GOOGLE_CLIENT_ID`, lanza `GoogleNotConfigured`.

Los tests inyectan un verificador falso vía `app.dependency_overrides`, así que el contrato del
callback queda probado sin tocar Google ni manejar secretos reales.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from urllib.parse import urlencode

from src.api.config import get_settings


@dataclass(frozen=True)
class GoogleIdentity:
    """Identidad mínima que necesitamos de Google para emitir nuestros JWT."""

    sub: str
    email: str


class GoogleNotConfigured(RuntimeError):
    """Se intentó usar el flujo de Google sin credenciales configuradas."""


@runtime_checkable
class GoogleVerifier(Protocol):
    def verify(self, code: str) -> GoogleIdentity:  # pragma: no cover - interfaz
        ...


def build_authorization_url(state: str) -> str:
    """Construye la URL de consentimiento de Google (OpenID Connect: openid+email+profile)."""
    s = get_settings()
    params = {
        "client_id": s.google_client_id,
        "redirect_uri": s.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{s.google_authorization_endpoint}?{urlencode(params)}"


class RealGoogleVerifier:
    """Canjea el `code` por un `id_token` de Google y lo verifica.

    Implementación pendiente hasta tener credenciales y el flujo e2e (US-402, Célula 5). Cuando se
    complete, debe: (1) intercambiar `code` en el token endpoint usando client_id/secret; (2) validar
    el `id_token` (firma con JWKS de Google, `aud`==client_id, `iss`, `exp`); (3) devolver sub/email.
    """

    def verify(self, code: str) -> GoogleIdentity:
        s = get_settings()
        if not s.google_client_id:
            raise GoogleNotConfigured("Faltan las credenciales OAuth de Google.")
        raise NotImplementedError(
            "Verificación real de Google pendiente de credenciales/e2e (US-402)."
        )
