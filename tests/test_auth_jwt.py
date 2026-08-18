"""Pruebas del núcleo de autenticación OAuth2/JWT (US-402).

Todo offline y sin secretos reales: usan el secreto de desarrollo por defecto y un verificador de
Google falso. Cubren: roundtrip de tokens, expiración, firma manipulada, tipo de token equivocado,
refresh, `get_current_user` (401), el callback de Google y la política de rol provisional.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from src.api.app import API_PREFIX, app
from src.api.config import get_settings
from src.api.schemas import Rol
from src.api.security import jwt as jwtmod
from src.api.security.deps import get_google_verifier
from src.api.security.google import GoogleIdentity

# --------------------------------------------------------------------------- #
# Núcleo JWT (funciones puras)
# --------------------------------------------------------------------------- #


def test_access_token_roundtrip() -> None:
    token = jwtmod.create_access_token(sub="u1", role=Rol.ciudadano, email="a@b.mx")
    claims = jwtmod.verify_access_token(token)
    assert claims["sub"] == "u1"
    assert claims["role"] == "ciudadano"
    assert claims["type"] == "access"


def test_refresh_token_roundtrip() -> None:
    token = jwtmod.create_refresh_token(sub="u1", email="a@b.mx")
    claims = jwtmod.verify_refresh_token(token)
    assert claims["type"] == "refresh"
    assert claims["email"] == "a@b.mx"


def test_no_se_cruzan_tipos_de_token() -> None:
    access = jwtmod.create_access_token(sub="u1", role=Rol.ciudadano)
    refresh = jwtmod.create_refresh_token(sub="u1")
    with pytest.raises(jwtmod.AuthError):
        jwtmod.verify_refresh_token(access)  # un access no vale como refresh
    with pytest.raises(jwtmod.AuthError):
        jwtmod.verify_access_token(refresh)  # ni viceversa


def test_token_expirado_es_rechazado() -> None:
    s = get_settings()
    pasado = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": "u1", "role": "ciudadano", "type": "access", "exp": int(pasado.timestamp())},
        s.jwt_secret_key,
        algorithm=s.jwt_algorithm,
    )
    with pytest.raises(jwtmod.AuthError):
        jwtmod.verify_access_token(token)


def test_firma_manipulada_es_rechazada() -> None:
    token = jwtmod.create_access_token(sub="u1", role=Rol.analista)
    manipulado = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    with pytest.raises(jwtmod.AuthError):
        jwtmod.verify_access_token(manipulado)


def test_token_firmado_con_otro_secreto_es_rechazado() -> None:
    ajeno = jwt.encode({"sub": "x", "role": "analista", "type": "access"}, "otro-secreto", algorithm="HS256")
    with pytest.raises(jwtmod.AuthError):
        jwtmod.verify_access_token(ajeno)


# --------------------------------------------------------------------------- #
# Política de rol (mínimo privilegio)
# --------------------------------------------------------------------------- #


def test_rol_por_defecto_es_ciudadano() -> None:
    from src.api.security.roles import resolve_role

    assert resolve_role("cualquiera@example.mx") == Rol.ciudadano


def test_rol_analista_solo_por_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("ANALISTA_EMAILS", "jefa@faro.mx, otro@faro.mx")
    try:
        from src.api.security.roles import resolve_role

        assert resolve_role("JEFA@faro.mx") == Rol.analista
        assert resolve_role("nadie@faro.mx") == Rol.ciudadano
    finally:
        get_settings.cache_clear()  # no contaminar otras pruebas


# --------------------------------------------------------------------------- #
# Endpoints /auth/* vía TestClient
# --------------------------------------------------------------------------- #


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_me_sin_token_da_401(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/auth/me")
    assert r.status_code == 401
    cuerpo = r.json()
    assert cuerpo["error"] == "unauthorized"
    assert {"error", "message", "request_id"} == cuerpo.keys()


def test_me_con_token_valido(client: TestClient) -> None:
    token = jwtmod.create_access_token(sub="u9", role=Rol.analista, email="ana@faro.mx")
    r = client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["sub"] == "u9"
    assert cuerpo["role"] == "analista"


def test_me_con_token_malformado_da_401(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401


def test_refresh_emite_par_nuevo(client: TestClient) -> None:
    refresh = jwtmod.create_refresh_token(sub="u1", email="a@b.mx")
    r = client.post(f"{API_PREFIX}/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer"
    # El nuevo access token es válido y trae rol ciudadano (email no está en la allowlist).
    claims = jwtmod.verify_access_token(cuerpo["access_token"])
    assert claims["role"] == "ciudadano"


def test_refresh_con_access_token_da_401(client: TestClient) -> None:
    access = jwtmod.create_access_token(sub="u1", role=Rol.ciudadano)
    r = client.post(f"{API_PREFIX}/auth/refresh", json={"refresh_token": access})
    assert r.status_code == 401


def test_login_redirige_a_google(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/auth/login", follow_redirects=False)
    assert r.status_code == 302
    assert "accounts.google.com" in r.headers["location"]


def test_callback_con_verificador_falso_emite_tokens(client: TestClient) -> None:
    class FakeVerifier:
        def verify(self, code: str) -> GoogleIdentity:
            return GoogleIdentity(sub="google-123", email="persona@faro.mx")

    app.dependency_overrides[get_google_verifier] = lambda: FakeVerifier()
    try:
        r = client.get(f"{API_PREFIX}/auth/callback", params={"code": "fake-code"})
        assert r.status_code == 200
        claims = jwtmod.verify_access_token(r.json()["access_token"])
        assert claims["sub"] == "google-123"
        assert claims["role"] == "ciudadano"  # mínimo privilegio por defecto
    finally:
        app.dependency_overrides.clear()
