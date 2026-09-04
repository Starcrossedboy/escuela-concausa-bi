"""Pruebas del cliente del guest token de Superset para el embebido (US-206)."""

from __future__ import annotations

import httpx
import pytest

from src.frontend.superset_client import (
    SUPERSET_URL,
    SupersetDeshabilitado,
    TableroEmbebido,
    tableros_embebidos,
    url_con_filtros,
)


def _cliente_fake(handler) -> httpx.Client:
    transporte = httpx.MockTransport(handler)
    return httpx.Client(base_url=SUPERSET_URL, transport=transporte)


@pytest.fixture(autouse=True)
def _password_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fija credenciales para las pruebas (el .env no se carga en el CI/test)."""
    monkeypatch.setattr("src.frontend.superset_client.ADMIN_PASS", "test-password")


def test_devuelve_los_dashboards_con_iframe_firmado() -> None:
    peticiones: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        peticiones.append(request.url.path)
        if request.url.path == "/api/v1/security/login":
            return httpx.Response(200, json={"access_token": "admin-token"})
        if request.url.path == "/api/v1/dashboard/":
            slug = request.url.params["q"]
            valor = "db01-ejecutivo" if "db01" in slug else "db02-mapa-riesgo"
            return httpx.Response(200, json={"result": [{"uuid": f"uuid-{valor}"}]})
        if request.url.path == "/api/v1/security/guest_token/":
            body = request.read().decode()
            assert '"type":"dashboard"' in body
            return httpx.Response(200, json={"token": "guest-token"})
        return httpx.Response(404, json={})

    cliente = _cliente_fake(handler)
    tableros = tableros_embebidos(rol="ciudadano", cliente=cliente)

    assert isinstance(tableros, list)
    assert len(tableros) == 10  # los 10 dashboards DB-01…DB-10
    for t in tableros:
        assert isinstance(t, TableroEmbebido)
        assert t.slug
        assert "guest_token=guest-token" in t.iframe_url
        assert t.iframe_url.startswith(SUPERSET_URL)
    assert "/api/v1/security/guest_token/" in peticiones


def test_rechaza_guest_token_deshabilitado_en_config() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/security/login":
            return httpx.Response(200, json={"access_token": "admin-token"})
        if request.url.path == "/api/v1/dashboard/":
            return httpx.Response(200, json={"result": [{"uuid": "uuid-abc"}]})
        if request.url.path == "/api/v1/security/guest_token/":
            return httpx.Response(401, json={"msg": "No guest token"})
        return httpx.Response(404, json={})

    cliente = _cliente_fake(handler)
    with pytest.raises(SupersetDeshabilitado, match="GUEST_ROLE_NAME"):
        tableros_embebidos(rol="ciudadano", cliente=cliente)


def test_no_renderiza_tablero_si_no_hay_slug_resuelto() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/security/login":
            return httpx.Response(200, json={"access_token": "admin-token"})
        if request.url.path == "/api/v1/dashboard/":
            return httpx.Response(200, json={"result": []})  # ningún uuid resuelto
        return httpx.Response(404, json={})

    cliente = _cliente_fake(handler)
    with pytest.raises(Exception, match="UUIDs de dashboards"):
        tableros_embebidos(rol="analista", cliente=cliente)


def test_falla_claramente_si_no_hay_password_de_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.frontend.superset_client.ADMIN_PASS", "")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "x"})

    cliente = _cliente_fake(handler)
    with pytest.raises(Exception, match="SUPERSET_ADMIN_PASSWORD no está definido"):
        tableros_embebidos(rol="ciudadano", cliente=cliente)


def test_url_con_filtros_sin_filtros_no_anade_nada() -> None:
    url = f"{SUPERSET_URL}/superset/dashboard/db01-ejecutivo/?standalone=true&guest_token=t"
    assert url_con_filtros(url, ciclo="", entidad="", nivel="") == url


def test_url_con_filtros_agrega_ciclo_entidad_y_nivel() -> None:
    url = f"{SUPERSET_URL}/superset/dashboard/db01/?standalone=true&guest_token=t"
    resultado = url_con_filtros(url, ciclo="2024-2025", entidad="09", nivel="Primaria")

    assert "guest_token=t" in resultado
    assert "filters=2024-2025" in resultado
    assert "entidad=09" in resultado
    assert "nivel=Primaria" in resultado
    assert "native_filters=!()" in resultado


def test_url_con_filtros_escapa_valores_con_caracteres_especiales() -> None:
    url = "http://superset/superset/dashboard/db01/?standalone=true"
    resultado = url_con_filtros(url, ciclo="2024-2025", entidad="09 Distrito A", nivel="")
    # El espacio en la entidad debe quedar percent-codificado.
    assert "entidad=09%20Distrito%20A" in resultado
