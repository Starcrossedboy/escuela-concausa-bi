"""Dependencias FastAPI de seguridad (US-402).

- `get_current_user` — extrae y valida el Bearer token; devuelve el `UserOut` autenticado o **401**
  uniforme. Es la base sobre la que US-403 construirá `require_role(...)`.
- `get_google_verifier` — proveedor del verificador de Google (los tests lo sobreescriben con un
  doble para no depender de credenciales).
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.schemas import Rol, UserOut
from src.api.security.google import GoogleVerifier, RealGoogleVerifier
from src.api.security.jwt import AuthError, verify_access_token

# auto_error=False => nosotros emitimos el 401 con el formato ErrorOut del contrato (§5).
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserOut:
    """Valida el access token del encabezado `Authorization` y devuelve el usuario.

    Lanza 401 (sin filtrar la causa) si falta el token, está malformado, expiró o fue manipulado.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Falta el token de acceso.")
    try:
        claims = verify_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado."
        ) from exc
    return UserOut(
        sub=claims["sub"],
        email=claims.get("email", ""),
        role=Rol(claims["role"]),
        name=claims.get("name", ""),
    )


def get_google_verifier() -> GoogleVerifier:
    """Proveedor del verificador de Google. Sobrescribible en tests vía dependency_overrides."""
    return RealGoogleVerifier()
