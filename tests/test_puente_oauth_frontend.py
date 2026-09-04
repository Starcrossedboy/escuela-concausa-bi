"""Puente OAuth → frontend: `?redirect=`, código de un solo uso y `/auth/exchange` (US-405).

Cubre la pieza que faltaba entre la API y FARO Web: el callback ya no deja el `TokenPair` como
JSON en el navegador, sino que redirige al front con un código corto que este canjea desde el
servidor. Ver `src/api/security/codigos_login.py` y ADR-010.

Lo que se prueba, en orden de importancia:

- **La allowlist del `redirect`** — es lo que impide un open redirect en el flujo de login.
- **Que el token NO viaje por la URL** — el motivo entero del diseño.
- **Un solo uso y expiración** del código.
- Que el rol se re-resuelva al canjear, en vez de confiar en el guardado.
"""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from src.api.app import API_PREFIX, app
from src.api.config import get_settings
from src.api.schemas import Rol
from src.api.security.codigos_login import (
    AlmacenMemoria,
    IdentidadSesion,
    get_almacen_codigos,
)
from src.api.security.deps import get_google_verifier
from src.api.security.google import GoogleIdentity
from src.api.security.jwt import verify_access_token

FRONT = "http://localhost:8501"


class _VerifierFalso:
    def verify(self, code: str) -> GoogleIdentity:
        return GoogleIdentity(sub="google-1", email="persona@faro.mx", name="Persona de Prueba")


@pytest.fixture
def almacen() -> AlmacenMemoria:
    return AlmacenMemoria()


@pytest.fixture
def client(almacen: AlmacenMemoria) -> TestClient:
    """Cliente con el verificador y el almacén sustituidos (nada de Google ni de Postgres)."""
    app.dependency_overrides[get_google_verifier] = lambda: _VerifierFalso()
    app.dependency_overrides[get_almacen_codigos] = lambda: almacen
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client: TestClient, redirect: str | None = None) -> str:
    params = {"redirect": redirect} if redirect else {}
    r = client.get(f"{API_PREFIX}/auth/login", params=params, follow_redirects=False)
    assert r.status_code == 302
    return parse_qs(urlparse(r.headers["location"]).query)["state"][0]


# --------------------------------------------------------------------------- #
# Allowlist del `redirect` — lo que impide un open redirect
# --------------------------------------------------------------------------- #


def test_redirect_permitido_es_aceptado(client: TestClient) -> None:
    assert _login(client, FRONT)  # no lanza => 302 a Google


def test_redirect_no_permitido_da_400(client: TestClient) -> None:
    r = client.get(
        f"{API_PREFIX}/auth/login",
        params={"redirect": "https://evil.example.com/robar"},
        follow_redirects=False,
    )
    assert r.status_code == 400


def test_redirect_por_prefijo_no_cuela(client: TestClient) -> None:
    """`http://localhost:8501.evil.tld` NO debe pasar: la comparación es exacta, no `startswith`."""
    r = client.get(
        f"{API_PREFIX}/auth/login",
        params={"redirect": f"{FRONT}.evil.tld"},
        follow_redirects=False,
    )
    assert r.status_code == 400


def test_sin_redirect_el_callback_sigue_devolviendo_json(client: TestClient) -> None:
    """Compatibilidad: los clientes que no son navegador siguen recibiendo el TokenPair."""
    state = _login(client)
    r = client.get(f"{API_PREFIX}/auth/callback", params={"code": "ok", "state": state})
    assert r.status_code == 200
    assert "access_token" in r.json()


# --------------------------------------------------------------------------- #
# El callback redirige con el código, y el token NO va en la URL
# --------------------------------------------------------------------------- #


def _callback_con_redirect(client: TestClient) -> str:
    """Completa login → callback con redirect y devuelve el `code_faro` de la URL de vuelta."""
    state = _login(client, FRONT)
    r = client.get(
        f"{API_PREFIX}/auth/callback",
        params={"code": "ok", "state": state},
        follow_redirects=False,
    )
    assert r.status_code == 302
    destino = urlparse(r.headers["location"])
    assert f"{destino.scheme}://{destino.netloc}" == FRONT
    return parse_qs(destino.query)["code_faro"][0]


def test_callback_redirige_al_front_con_codigo(client: TestClient) -> None:
    assert len(_callback_con_redirect(client)) >= 16


def test_la_url_de_vuelta_no_lleva_tokens(client: TestClient) -> None:
    """El motivo entero del diseño: nada parecido a un JWT en la barra de direcciones."""
    state = _login(client, FRONT)
    r = client.get(
        f"{API_PREFIX}/auth/callback",
        params={"code": "ok", "state": state},
        follow_redirects=False,
    )
    url = r.headers["location"]
    assert "access_token" not in url
    assert "refresh_token" not in url
    assert "eyJ" not in url  # los JWT en base64url siempre empiezan así


def test_el_codigo_no_es_un_jwt_ni_lleva_datos(client: TestClient) -> None:
    """El código es opaco: no transporta identidad, solo apunta a ella en el almacén."""
    codigo = _callback_con_redirect(client)
    assert "." not in codigo  # un JWT tiene tres partes separadas por puntos
    assert "persona@faro.mx" not in codigo


# --------------------------------------------------------------------------- #
# Canje
# --------------------------------------------------------------------------- #


def test_exchange_devuelve_la_sesion(client: TestClient) -> None:
    codigo = _callback_con_redirect(client)
    r = client.post(f"{API_PREFIX}/auth/exchange", json={"code": codigo})
    assert r.status_code == 200
    claims = verify_access_token(r.json()["access_token"])
    assert claims["sub"] == "google-1"
    assert claims["name"] == "Persona de Prueba"
    assert claims["role"] == "ciudadano"


def test_el_codigo_es_de_un_solo_uso(client: TestClient) -> None:
    codigo = _callback_con_redirect(client)
    assert client.post(f"{API_PREFIX}/auth/exchange", json={"code": codigo}).status_code == 200
    segundo = client.post(f"{API_PREFIX}/auth/exchange", json={"code": codigo})
    assert segundo.status_code == 401


def test_codigo_inventado_da_401_sin_fuga(client: TestClient) -> None:
    r = client.post(f"{API_PREFIX}/auth/exchange", json={"code": "x" * 40})
    assert r.status_code == 401
    cuerpo = r.json()
    assert cuerpo["error"] == "unauthorized"
    assert {"error", "message", "request_id"} == cuerpo.keys()


def test_exchange_rechaza_campos_extra(client: TestClient) -> None:
    """Validación estricta de US-404: un campo desconocido en el cuerpo es 422."""
    r = client.post(f"{API_PREFIX}/auth/exchange", json={"code": "x" * 40, "rol": "analista"})
    assert r.status_code == 422


def test_el_rol_se_reresuelve_al_canjear(
    client: TestClient, almacen: AlmacenMemoria, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No se confía en el rol guardado: si la política cambió entre el callback y el canje, manda
    la política vigente. Aquí el correo entra a la allowlist justo antes del canje."""
    codigo = almacen.guardar(
        IdentidadSesion(sub="u1", email="jefa@faro.mx", name="Jefa", role=Rol.ciudadano)
    )
    get_settings.cache_clear()
    monkeypatch.setenv("ANALISTA_EMAILS", "jefa@faro.mx")
    try:
        r = client.post(f"{API_PREFIX}/auth/exchange", json={"code": codigo})
        assert r.status_code == 200
        assert verify_access_token(r.json()["access_token"])["role"] == "analista"
    finally:
        get_settings.cache_clear()


# --------------------------------------------------------------------------- #
# El almacén en memoria (contrato compartido con el de Postgres)
# --------------------------------------------------------------------------- #


def test_almacen_no_guarda_el_codigo_en_claro(almacen: AlmacenMemoria) -> None:
    """Se guarda el SHA-256: quien lea el almacén no puede canjear nada."""
    codigo = almacen.guardar(
        IdentidadSesion(sub="u1", email="a@b.mx", name="A", role=Rol.ciudadano)
    )
    assert codigo not in almacen._filas


def test_almacen_codigo_expirado_no_sirve(
    almacen: AlmacenMemoria, monkeypatch: pytest.MonkeyPatch
) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("LOGIN_CODE_EXPIRE_SEGUNDOS", "0")
    try:
        codigo = almacen.guardar(
            IdentidadSesion(sub="u1", email="a@b.mx", name="A", role=Rol.ciudadano)
        )
        assert almacen.canjear(codigo) is None
    finally:
        get_settings.cache_clear()


def test_dos_codigos_nunca_coinciden(almacen: AlmacenMemoria) -> None:
    identidad = IdentidadSesion(sub="u1", email="a@b.mx", name="A", role=Rol.ciudadano)
    assert almacen.guardar(identidad) != almacen.guardar(identidad)
