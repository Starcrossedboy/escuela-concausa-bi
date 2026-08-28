"""Emisión y validación de JWT propios (US-402).

Decisiones (ver `03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt.md`):
- **access token**: vida corta (15 min por defecto), viaja en `Authorization: Bearer`.
- **refresh token**: vida larga (7 días), se canjea en `POST /auth/refresh`.
- Ambos llevan el claim `type` (`access`|`refresh`) para que un refresh no se use como access ni
  viceversa.
- **Endurecimiento contra confusión de algoritmo**: `decode` recibe SIEMPRE una lista explícita de
  algoritmos permitidos; nunca se confía en el `alg` del encabezado del token entrante.

Firma HS256 (simétrica) por ahora; el ADR documenta la migración a RS256 en producción.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.api.config import get_settings
from src.api.schemas import Rol, TokenPair

TIPO_ACCESS = "access"
TIPO_REFRESH = "refresh"


class AuthError(Exception):
    """Error de autenticación (token ausente, inválido, expirado o de tipo incorrecto).

    No lleva detalle sensible: la capa HTTP lo traduce a un 401 uniforme sin filtrar la causa real.
    """


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(payload: dict[str, Any]) -> str:
    s = get_settings()
    return jwt.encode(payload, s.jwt_secret_key, algorithm=s.jwt_algorithm)


def _decode(token: str) -> dict[str, Any]:
    """Decodifica validando firma y expiración, restringiendo el algoritmo al configurado."""
    s = get_settings()
    try:
        # algorithms explícito => no se acepta el `alg` que venga en el token (anti-confusión).
        return jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
    except JWTError as exc:
        raise AuthError("token inválido o expirado") from exc


def create_access_token(sub: str, role: Rol | str, email: str = "") -> str:
    """Emite un access token de vida corta con los claims `sub`, `role`, `email`, `type`, `iat`, `exp`."""
    s = get_settings()
    ahora = _now()
    exp = ahora + timedelta(minutes=s.access_token_expire_minutes)
    return _encode(
        {
            "sub": sub,
            "role": Rol(role).value,
            "email": email,
            "type": TIPO_ACCESS,
            "iat": int(ahora.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )


def create_refresh_token(sub: str, email: str = "") -> str:
    """Emite un refresh token de vida larga.

    Lleva `sub` y `email` (no el rol): al refrescar se **re-resuelve** el rol con la política vigente,
    de modo que un cambio de permisos surta efecto sin re-login.
    """
    s = get_settings()
    ahora = _now()
    exp = ahora + timedelta(days=s.refresh_token_expire_days)
    return _encode(
        {
            "sub": sub,
            "email": email,
            "type": TIPO_REFRESH,
            "iat": int(ahora.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )


def create_token_pair(sub: str, role: Rol | str, email: str = "") -> TokenPair:
    """Crea el par access+refresh que devuelven `/auth/callback` y `/auth/refresh`."""
    s = get_settings()
    return TokenPair(
        access_token=create_access_token(sub, role, email),
        refresh_token=create_refresh_token(sub, email),
        token_type="bearer",
        expires_in=s.access_token_expire_minutes * 60,
    )


def verify_access_token(token: str) -> dict[str, Any]:
    """Valida un access token y devuelve sus claims. Lanza `AuthError` si no es de tipo access."""
    claims = _decode(token)
    if claims.get("type") != TIPO_ACCESS:
        raise AuthError("se esperaba un access token")
    return claims


def verify_refresh_token(token: str) -> dict[str, Any]:
    """Valida un refresh token y devuelve sus claims. Lanza `AuthError` si no es de tipo refresh."""
    claims = _decode(token)
    if claims.get("type") != TIPO_REFRESH:
        raise AuthError("se esperaba un refresh token")
    return claims
