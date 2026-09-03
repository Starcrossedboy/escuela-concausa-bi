"""Cliente del guest token de Superset para el embebido de dashboards (US-206).

El front habla directo con Superset: autentica con el usuario admin (login provider "db"),
resuelve el UUID de cada dashboard por slug, solicita un guest token por sesión con las RLS
del rol y devuelve la ``iframe_uri`` firmada de cada dashboard.

Historia: US-206. Ver vault/03_Architecture/Frontend_Architecture.md §4 y el patrón de
login de superset/sync_semantic_layer.py:login().
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

SUPERSET_URL = os.environ.get("SUPERSET_URL", "http://127.0.0.1:8088").rstrip("/")
ADMIN_USER = os.environ.get("SUPERSET_ADMIN_USERNAME", "faro_superset_admin")
ADMIN_PASS = os.environ.get("SUPERSET_ADMIN_PASSWORD", "")

# Catálogo de dashboards por slug. DB-07/DB-10 aún sin slug declarado (Oscar, US-222/223).
DASHBOARDS: tuple[dict[str, str], ...] = (
    {"id": "db01", "titulo": "Panel Ejecutivo", "slug": "db01-ejecutivo"},
    {"id": "db02", "titulo": "Mapa de Riesgo", "slug": "db02-mapa-riesgo"},
    {"id": "db03", "titulo": "Ficha de Escuela", "slug": "db03-ficha-escuela"},
    {"id": "db04", "titulo": "Comparador de Municipio", "slug": "db04-comparador-municipio"},
    {"id": "db05", "titulo": "Análisis de Driver", "slug": "db05-analisis-driver"},
    {"id": "db06", "titulo": "Predicciones", "slug": "db06-predicciones"},
    {"id": "db08", "titulo": "Explorador de Cubo", "slug": "db08-explorador-cubo"},
    {"id": "db09", "titulo": "Recomendaciones", "slug": "db09-recomendaciones"},
)

# RLS por rol. ciudadano ve solo su alcance público; analista ve todo.
RLS_CLAUSES: dict[str, list[dict[str, str]]] = {
    "ciudadano": [],
    "analista": [],
}


class SupersetDeshabilitado(Exception):
    """Superset no expone guest token (falta config de embedding del lado C5)."""


class SupersetError(Exception):
    """Fallo de autenticación o de solicitud del guest token a Superset."""


def _admin_token(cliente: httpx.Client) -> str:
    """Autentica contra `/api/v1/security/login` y devuelve el access_token (patrón C5)."""
    if not ADMIN_PASS:
        raise SupersetError(
            "SUPERSET_ADMIN_PASSWORD no está definido. Exporta las variables de .env."
        )
    resp = cliente.post(
        "/api/v1/security/login",
        json={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "provider": "db",
            "refresh": True,
        },
    )
    if resp.status_code != 200:
        raise SupersetError(
            f"No se pudo autenticar en Superset (HTTP {resp.status_code})."
        )
    token = resp.json().get("access_token", "")
    if not token:
        raise SupersetError("Superset no devolvió access_token.")
    return token


def _uuid_por_slug(cliente: httpx.Client, token: str) -> dict[str, str]:
    """Resuelve el UUID de cada dashboard consultando la API por slug."""
    cabeceras = {"Authorization": f"Bearer {token}"}
    resultado: dict[str, str] = {}
    for d in DASHBOARDS:
        slug = d["slug"]
        if not slug:
            continue
        resp = cliente.get(
            "/api/v1/dashboard/",
            params={"q": f'(filters:!((col:slug,opr:eq,value:{slug})))'},
            headers=cabeceras,
        )
        if resp.status_code != 200:
            continue
        items = resp.json().get("result", [])
        if items:
            resultado[slug] = items[0]["uuid"]
    return resultado


def _obtener_guest_token(
    cliente: httpx.Client, recursos: list[dict[str, Any]]
) -> dict[str, Any]:
    """POST `/api/v1/security/guest_token/` y devuelve {token, iframe_uri} por dashboard."""
    resp = cliente.post(
        "/api/v1/security/guest_token/",
        json={
            "user": {"username": "guest", "first_name": "FARO", "last_name": "Invitado"},
            "resources": recursos,
            "rls": [],
        },
    )
    if resp.status_code in (401, 403):
        raise SupersetDeshabilitado(
            "Superset rechazó el guest token (¿falta GUEST_ROLE_NAME / ENABLE_GUEST_EMBEDDING "
            "en la config del contenedor?). Habilítalo del lado de despliegue (C5)."
        )
    if resp.status_code != 200:
        raise SupersetError(
            f"Superset devolvió HTTP {resp.status_code} al pedir el guest token."
        )
    return resp.json()


@dataclass(frozen=True)
class TableroEmbebido:
    """Un dashboard embebido listo para renderizar en un iframe."""

    id: str
    titulo: str
    slug: str
    iframe_url: str


def url_con_filtros(iframe_url: str, ciclo: str, entidad: str, nivel: str) -> str:
    """Append de los filtros AC-002.2 a la URL del iframe (ciclo/entidad/nivel)."""
    import urllib.parse

    sep = "&" if "&" in iframe_url else "?"
    filtros = []
    if ciclo:
        filtros.append(f"native_filters=!()&filters={urllib.parse.quote(ciclo, safe='')}")
    if entidad:
        filtros.append(f"entidad={urllib.parse.quote(entidad, safe='')}")
    if nivel:
        filtros.append(f"nivel={urllib.parse.quote(nivel, safe='')}")
    return iframe_url + (sep + "&".join(filtros) if filtros else "")


def tableros_embebidos(rol: str = "ciudadano", cliente: httpx.Client | None = None) -> list[TableroEmbebido]:
    """Devuelve los dashboards con su iframe firmado para el rol, o lanza SupersetDeshabilitado.

    Sin token válido NO devuelve tableros: el llamador no renderiza ningún iframe (AC-002.1).
    ``cliente`` se inyecta para pruebas (mismo patrón DI del frontend); si viene None, se crea
    un httpx.Client contra SUPERSET_URL.
    """
    propio = cliente is None
    if cliente is None:
        cliente = httpx.Client(base_url=SUPERSET_URL, timeout=20.0)
    try:
        admin_token = _admin_token(cliente)
        uuids = _uuid_por_slug(cliente, admin_token)
        recursos = [
            {"type": "dashboard", "id": uuids[d["slug"]], "rls": RLS_CLAUSES.get(rol, [])}
            for d in DASHBOARDS
            if d["slug"] and d["slug"] in uuids
        ]
        if not recursos:
            raise SupersetError(
                "No se resolvieron UUIDs de dashboards en Superset "
                "(¿están publicados los slugs DB-01…DB-09?)."
            )
        payload = _obtener_guest_token(cliente, recursos)
        token = payload.get("token", "")
        if not token:
            raise SupersetDeshabilitado("Superset no devolvió token en el guest token.")
        return [
            TableroEmbebido(
                id=d["id"],
                titulo=d["titulo"],
                slug=d["slug"],
                iframe_url=(
                    f"{SUPERSET_URL}/superset/dashboard/{d['slug']}/"
                    f"?standalone=true&native_filters_key=1&guest_token={token}"
                ),
            )
            for d in DASHBOARDS
            if d["slug"] and d["slug"] in uuids
        ]
    finally:
        if propio:
            cliente.close()
