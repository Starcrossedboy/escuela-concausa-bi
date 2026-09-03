"""Flujo OAuth2 con Google, desacoplado para poder probar sin credenciales (US-402).

- `build_authorization_url(state)` — construye la URL de consentimiento de Google (pura, testeable).
- `GoogleVerifier` (Protocol) — canjea el `code` del callback por la identidad del usuario.
- `RealGoogleVerifier` — implementación real: intercambia el `code` en el *token endpoint* y
  **verifica el `id_token`** contra el JWKS público de Google (firma RS256, `aud`, `iss`, `exp`).
  Sin `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` lanza `GoogleNotConfigured`.

Los tests inyectan un verificador falso vía `app.dependency_overrides`, así que el contrato del
callback queda probado sin tocar Google ni manejar secretos reales.

Nota de seguridad: este módulo **nunca** registra ni devuelve el `code`, el `client_secret` ni el
`id_token`. Cualquier fallo del intercambio se convierte en un `ValueError` genérico que la capa HTTP
traduce a un 401 uniforme (§5 del contrato).
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt

from src.api.config import get_settings

_logger = logging.getLogger("faro.api.google")

# Google rota sus llaves de firma con poca frecuencia; 1 h de caché evita una llamada por login sin
# quedarse con llaves viejas. Ante un `kid` desconocido se refresca de inmediato (ver _jwk_para_kid).
_JWKS_TTL_SEGUNDOS = 3600

# Único algoritmo aceptado para el `id_token`. Explícito: nunca se confía en el `alg` del token.
_ALGORITMOS_ID_TOKEN = ["RS256"]


@dataclass(frozen=True)
class GoogleIdentity:
    """Identidad mínima que necesitamos de Google para emitir nuestros JWT.

    `name` es el nombre para mostrar (claim `name` del `id_token`, scope `profile`). Es **opcional**:
    si el perfil no lo expone queda vacío y el front cae a `email`. Nunca se usa para autorizar.
    """

    sub: str
    email: str
    name: str = ""


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


# --------------------------------------------------------------------------- #
# Caché del JWKS de Google
# --------------------------------------------------------------------------- #

_jwks_cache: dict[str, Any] | None = None
_jwks_expira_en: float = 0.0
_jwks_lock = threading.Lock()


def _descargar_jwks() -> dict[str, Any]:
    """Descarga el JWKS público de Google. Lanza `ValueError` si no se puede obtener."""
    s = get_settings()
    try:
        respuesta = httpx.get(s.google_jwks_uri, timeout=s.google_http_timeout_s)
        respuesta.raise_for_status()
        return respuesta.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ValueError("no se pudo obtener el JWKS de Google") from exc


def _jwks(forzar: bool = False) -> dict[str, Any]:
    """Devuelve el JWKS cacheado, refrescándolo si expiró o si `forzar` es True."""
    global _jwks_cache, _jwks_expira_en
    with _jwks_lock:
        if forzar or _jwks_cache is None or time.monotonic() >= _jwks_expira_en:
            _jwks_cache = _descargar_jwks()
            _jwks_expira_en = time.monotonic() + _JWKS_TTL_SEGUNDOS
        return _jwks_cache


def limpiar_cache_jwks() -> None:
    """Invalida la caché del JWKS. Pensado para las pruebas, que no deben compartir estado."""
    global _jwks_cache, _jwks_expira_en
    with _jwks_lock:
        _jwks_cache = None
        _jwks_expira_en = 0.0


def _jwk_para_kid(kid: str) -> dict[str, Any]:
    """Busca la llave pública del `kid` del token; si no está, refresca el JWKS una vez."""
    for forzar in (False, True):
        for llave in _jwks(forzar=forzar).get("keys", []):
            if llave.get("kid") == kid:
                return llave
    raise ValueError("el id_token viene firmado con una llave desconocida")


class RealGoogleVerifier:
    """Canjea el `code` por un `id_token` de Google y lo verifica.

    Pasos (OpenID Connect, *authorization code flow*):

    1. **Intercambio**: `POST` al *token endpoint* con `code`, `client_id`, `client_secret`,
       `redirect_uri` y `grant_type=authorization_code`. El `redirect_uri` debe ser byte a byte el
       registrado en la consola de Google o el intercambio falla (`redirect_uri_mismatch`).
    2. **Verificación del `id_token`**: firma RS256 contra la llave del JWKS que corresponde al `kid`
       del encabezado, `aud == client_id`, `iss` en la lista de emisores de Google y `exp` vigente.
       Se pasa una lista explícita de algoritmos: no se confía en el `alg` del token entrante.
    3. **Identidad**: se exige `sub`, `email` y `email_verified == true`. Un correo sin verificar no
       sirve para resolver el rol (`security/roles.py` decide por correo).
    """

    def verify(self, code: str) -> GoogleIdentity:
        s = get_settings()
        if not s.google_configurado:
            raise GoogleNotConfigured("Faltan las credenciales OAuth de Google.")

        id_token = self._intercambiar_code(code)
        claims = self._verificar_id_token(id_token)

        sub = claims.get("sub")
        email = claims.get("email", "")
        if not sub or not email:
            raise ValueError("el id_token no trae sub/email")
        if claims.get("email_verified") is not True:
            raise ValueError("el correo de Google no esta verificado")
        return GoogleIdentity(sub=str(sub), email=str(email), name=str(claims.get("name") or ""))

    def _intercambiar_code(self, code: str) -> str:
        """Canjea el `code` por el `id_token`. Nunca registra el `code` ni el `client_secret`."""
        s = get_settings()
        try:
            respuesta = httpx.post(
                s.google_token_endpoint,
                data={
                    "code": code,
                    "client_id": s.google_client_id,
                    "client_secret": s.google_client_secret,
                    "redirect_uri": s.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=s.google_http_timeout_s,
            )
        except httpx.HTTPError as exc:
            _logger.warning("Fallo de red al canjear el code con Google: %s", type(exc).__name__)
            raise ValueError("no se pudo contactar a Google") from exc

        if respuesta.status_code != 200:
            # El cuerpo de Google puede traer detalle del cliente OAuth: se queda en el log interno.
            _logger.warning(
                "Google rechazo el intercambio del code (HTTP %s)", respuesta.status_code
            )
            raise ValueError("Google rechazo el codigo de autorizacion")

        try:
            id_token = respuesta.json().get("id_token")
        except ValueError as exc:
            raise ValueError("respuesta inesperada del token endpoint") from exc
        if not id_token:
            raise ValueError("la respuesta de Google no trae id_token")
        return str(id_token)

    def _verificar_id_token(self, id_token: str) -> dict[str, Any]:
        """Valida firma, `aud`, `iss` y `exp` del `id_token` contra el JWKS de Google."""
        s = get_settings()
        try:
            kid = jwt.get_unverified_header(id_token).get("kid")
        except JWTError as exc:
            raise ValueError("id_token malformado") from exc
        if not kid:
            raise ValueError("el id_token no declara kid")

        llave = _jwk_para_kid(str(kid))
        try:
            return jwt.decode(
                id_token,
                llave,
                algorithms=_ALGORITMOS_ID_TOKEN,
                audience=s.google_client_id,
                issuer=tuple(s.google_issuer_list),
            )
        except JWTError as exc:
            _logger.warning("id_token de Google invalido: %s", type(exc).__name__)
            raise ValueError("id_token invalido") from exc
