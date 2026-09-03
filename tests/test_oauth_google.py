"""Pruebas del cierre e2e de OAuth2 con Google (US-402) — `state` CSRF y `RealGoogleVerifier`.

Todo offline y sin credenciales reales:

- El `state` anti-CSRF se ejercita con el `TestClient` (cookie de primera parte + parámetro).
- `RealGoogleVerifier` se prueba contra un Google falso: se genera una llave RSA en memoria, se
  firma un `id_token` real y se sustituyen `httpx.post` (token endpoint) y `httpx.get` (JWKS). Así
  se valida la verificación de firma, `aud`, `iss`, `exp` y `email_verified` sin salir a la red.

Historias: US-402 (OAuth2/JWT) y US-405 (login del frontend, que depende de este flujo).
"""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwk as josejwk
from jose import jwt

from src.api.app import API_PREFIX, app
from src.api.config import get_settings
from src.api.security import google as gmod
from src.api.security.deps import get_google_verifier
from src.api.security.google import (
    GoogleIdentity,
    GoogleNotConfigured,
    RealGoogleVerifier,
    limpiar_cache_jwks,
)
from src.api.security.jwt import AuthError, create_state_token, verify_state_token

CLIENT_ID = "cliente-de-prueba.apps.googleusercontent.com"
KID = "kid-de-prueba"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _iniciar_login(client: TestClient) -> str:
    """Ejecuta `GET /auth/login` y devuelve el `state`; la cookie queda en el cliente."""
    r = client.get(f"{API_PREFIX}/auth/login", follow_redirects=False)
    assert r.status_code == 302
    return parse_qs(urlparse(r.headers["location"]).query)["state"][0]


def _pem(privada: rsa.RSAPrivateKey) -> str:
    """Serializa una llave RSA a PEM PKCS8 sin cifrar (lo que espera `jose`)."""
    return privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


class _VerifierFalso:
    def verify(self, code: str) -> GoogleIdentity:
        return GoogleIdentity(sub="google-1", email="persona@faro.mx")


# --------------------------------------------------------------------------- #
# `state` anti-CSRF (token firmado + cookie de primera parte)
# --------------------------------------------------------------------------- #


def test_state_token_roundtrip() -> None:
    claims = verify_state_token(create_state_token())
    assert claims["type"] == "state"
    assert claims["nonce"]  # nonce aleatorio: dos states nunca son iguales


def test_dos_states_son_distintos() -> None:
    assert create_state_token() != create_state_token()


def test_un_access_token_no_vale_como_state() -> None:
    from src.api.schemas import Rol
    from src.api.security.jwt import create_access_token

    with pytest.raises(AuthError):
        verify_state_token(create_access_token(sub="u1", role=Rol.ciudadano))


def test_login_pone_cookie_httponly_con_el_state(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/auth/login", follow_redirects=False)
    assert r.status_code == 302
    cookie = r.headers["set-cookie"]
    assert "faro_oauth_state=" in cookie
    assert "HttpOnly" in cookie
    assert "samesite=lax" in cookie.lower()
    # El valor de la cookie es exactamente el `state` que viaja a Google.
    state = parse_qs(urlparse(r.headers["location"]).query)["state"][0]
    assert state in cookie
    assert state != "faro"  # ya no es la constante que había antes del cierre de US-402


def test_callback_sin_state_da_401(client: TestClient) -> None:
    app.dependency_overrides[get_google_verifier] = lambda: _VerifierFalso()
    try:
        _iniciar_login(client)  # aunque exista la cookie, falta el parámetro
        r = client.get(f"{API_PREFIX}/auth/callback", params={"code": "x"})
        assert r.status_code == 401
        assert r.json()["error"] == "unauthorized"
    finally:
        app.dependency_overrides.clear()


def test_callback_sin_cookie_da_401(client: TestClient) -> None:
    """Un `state` válido y bien firmado NO basta: sin la cookie que lo acompaña, es CSRF."""
    app.dependency_overrides[get_google_verifier] = lambda: _VerifierFalso()
    try:
        r = client.get(
            f"{API_PREFIX}/auth/callback",
            params={"code": "x", "state": create_state_token()},
        )
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_callback_con_state_que_no_coincide_da_401(client: TestClient) -> None:
    app.dependency_overrides[get_google_verifier] = lambda: _VerifierFalso()
    try:
        _iniciar_login(client)  # deja UNA cookie...
        ajeno = create_state_token()  # ...y llega OTRO state, también válido por sí mismo
        r = client.get(f"{API_PREFIX}/auth/callback", params={"code": "x", "state": ajeno})
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_callback_borra_la_cookie_del_state(client: TestClient) -> None:
    """El `state` es de un solo uso: tras el canje la cookie se elimina."""
    app.dependency_overrides[get_google_verifier] = lambda: _VerifierFalso()
    try:
        state = _iniciar_login(client)
        r = client.get(f"{API_PREFIX}/auth/callback", params={"code": "x", "state": state})
        assert r.status_code == 200
        assert 'faro_oauth_state=""' in r.headers.get("set-cookie", "") or "Max-Age=0" in r.headers.get(
            "set-cookie", ""
        )
    finally:
        app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# `RealGoogleVerifier` contra un Google falso
# --------------------------------------------------------------------------- #


@pytest.fixture
def google_falso(monkeypatch: pytest.MonkeyPatch):
    """Llave RSA en memoria + `httpx.post`/`httpx.get` sustituidos por un Google de mentiras.

    Devuelve una función `emitir(**claims)` que fija el `id_token` que "devolverá" Google.
    """
    get_settings.cache_clear()
    limpiar_cache_jwks()
    monkeypatch.setenv("GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secreto-de-prueba")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://testserver/api/v1/auth/callback")

    pem_privado = _pem(rsa.generate_private_key(public_exponent=65537, key_size=2048))

    publica_jwk = josejwk.construct(pem_privado, "RS256").public_key().to_dict()
    publica_jwk = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in publica_jwk.items()}
    publica_jwk["kid"] = KID
    jwks = {"keys": [publica_jwk]}

    estado: dict[str, Any] = {"id_token": None, "status": 200}

    class _Resp:
        def __init__(self, payload: Any, status_code: int = 200) -> None:
            self._payload = payload
            self.status_code = status_code

        def json(self) -> Any:
            return self._payload

        def raise_for_status(self) -> None:
            if self.status_code != 200:
                raise RuntimeError("http")

    monkeypatch.setattr(gmod.httpx, "get", lambda *a, **k: _Resp(jwks))
    monkeypatch.setattr(
        gmod.httpx,
        "post",
        lambda *a, **k: _Resp({"id_token": estado["id_token"]}, estado["status"]),
    )

    def emitir(**extra: Any) -> None:
        ahora = int(time.time())
        claims = {
            "iss": "https://accounts.google.com",
            "aud": CLIENT_ID,
            "sub": "google-sub-1",
            "email": "persona@faro.mx",
            "email_verified": True,
            "iat": ahora,
            "exp": ahora + 600,
        }
        claims.update(extra)
        estado["id_token"] = jwt.encode(
            claims, pem_privado, algorithm="RS256", headers={"kid": KID}
        )

    emitir.estado = estado  # type: ignore[attr-defined]
    yield emitir
    get_settings.cache_clear()
    limpiar_cache_jwks()


def test_verifier_sin_credenciales_levanta_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    try:
        with pytest.raises(GoogleNotConfigured):
            RealGoogleVerifier().verify("code")
    finally:
        get_settings.cache_clear()


def test_verifier_devuelve_la_identidad(google_falso) -> None:
    google_falso()
    identidad = RealGoogleVerifier().verify("code-bueno")
    assert identidad.sub == "google-sub-1"
    assert identidad.email == "persona@faro.mx"


def test_verifier_rechaza_audiencia_ajena(google_falso) -> None:
    google_falso(aud="otro-cliente.apps.googleusercontent.com")
    with pytest.raises(ValueError):
        RealGoogleVerifier().verify("code")


def test_verifier_rechaza_emisor_ajeno(google_falso) -> None:
    google_falso(iss="https://evil.example.com")
    with pytest.raises(ValueError):
        RealGoogleVerifier().verify("code")


def test_verifier_rechaza_token_expirado(google_falso) -> None:
    ahora = int(time.time())
    google_falso(iat=ahora - 7200, exp=ahora - 3600)
    with pytest.raises(ValueError):
        RealGoogleVerifier().verify("code")


def test_verifier_rechaza_correo_no_verificado(google_falso) -> None:
    google_falso(email_verified=False)
    with pytest.raises(ValueError):
        RealGoogleVerifier().verify("code")


def test_verifier_rechaza_kid_desconocido(google_falso) -> None:
    """Un `id_token` firmado con una llave que no está en el JWKS no pasa (algorithm confusion)."""
    google_falso()
    pem = _pem(rsa.generate_private_key(public_exponent=65537, key_size=2048))
    ahora = int(time.time())
    google_falso.estado["id_token"] = jwt.encode(  # type: ignore[attr-defined]
        {
            "iss": "https://accounts.google.com",
            "aud": CLIENT_ID,
            "sub": "x",
            "email": "x@faro.mx",
            "email_verified": True,
            "iat": ahora,
            "exp": ahora + 600,
        },
        pem,
        algorithm="RS256",
        headers={"kid": "kid-que-no-existe"},
    )
    with pytest.raises(ValueError):
        RealGoogleVerifier().verify("code")


def test_verifier_traduce_rechazo_de_google_a_valueerror(google_falso) -> None:
    google_falso()
    google_falso.estado["status"] = 400  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        RealGoogleVerifier().verify("code-invalido")


def test_callback_con_verifier_real_y_google_falso(client: TestClient, google_falso) -> None:
    """E2E del contrato: /auth/login -> /auth/callback -> par de JWT con rol ciudadano."""
    google_falso()
    state = _iniciar_login(client)
    r = client.get(f"{API_PREFIX}/auth/callback", params={"code": "code-bueno", "state": state})
    assert r.status_code == 200
    from src.api.security.jwt import verify_access_token

    claims = verify_access_token(r.json()["access_token"])
    assert claims["sub"] == "google-sub-1"
    assert claims["role"] == "ciudadano"


def test_callback_con_code_invalido_da_401_sin_fuga(client: TestClient, google_falso) -> None:
    google_falso()
    google_falso.estado["status"] = 400  # type: ignore[attr-defined]
    state = _iniciar_login(client)
    r = client.get(f"{API_PREFIX}/auth/callback", params={"code": "malo", "state": state})
    assert r.status_code == 401
    cuerpo = r.json()
    assert cuerpo["error"] == "unauthorized"
    assert {"error", "message", "request_id"} == cuerpo.keys()
    # El mensaje no menciona Google, el code ni nada del intercambio.
    assert "google" not in cuerpo["message"].lower()
