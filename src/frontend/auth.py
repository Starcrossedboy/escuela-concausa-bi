"""Sesión de FARO Web: login/logout con Google y guardas por rol (US-405).

El front **no reimplementa OAuth**. Manda a la persona a `/auth/login` de la API, que hace todo el
flujo con Google, y la recibe de vuelta con un **código de un solo uso** en la query string. Ese
código se canjea *desde el servidor de Streamlit* en `POST /auth/exchange`, y es ahí —en el cuerpo
de la respuesta, nunca en la URL— donde llegan los tokens.

Por qué así y no redirigiendo con el token puesto: una URL con el token dentro acaba en el
historial del navegador, en los logs de cualquier proxy intermedio y en la cabecera `Referer` de la
siguiente petición que haga la página. El código, en cambio, muere en el primer canje y expira en
60 segundos. Ver ADR-010 y `src/api/security/codigos_login.py`.

Contrato con la Célula 2 (acordado con Manuel Serranía): este módulo expone `current_user()`,
`login_button()`, `logout_button()` y `require_role()`. El objeto de sesión es un dict con las
claves **`sub`, `email`, `name`, `role`** — `role` es `"ciudadano"` o `"analista"`, que es lo que
indexa `RLS_CLAUSES` en `superset_client.py`. `name` puede venir vacío (no todo perfil de Google lo
expone), por eso `app.py` cae a `email`.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx
import streamlit as st

ROLES = ("ciudadano", "analista")

# La API. Mismo nombre de variable que ya usa `pages/3_Chat.py`, para no tener dos fuentes.
API_BASE_URL = os.environ.get("FARO_API_BASE_URL", "http://localhost:8000").rstrip("/")
# A dónde vuelve la API tras el login. Tiene que estar en la allowlist `FRONTEND_REDIRECT_URIS`
# de la API, o `/auth/login` responde 400 (eso es lo que impide un open redirect).
FRONTEND_URL = os.environ.get("FARO_FRONTEND_URL", "http://localhost:8501").rstrip("/")

# Segundos de espera al canjear. Corto a propósito: es una llamada local entre servicios y la
# persona está mirando una pantalla en blanco mientras tanto.
TIMEOUT_S = float(os.environ.get("FARO_API_TIMEOUT_S", "10"))

_PARAM_CODIGO = "code_faro"


class ErrorDeSesion(Exception):
    """El canje del código falló. El mensaje es apto para mostrarse tal cual."""


def url_de_login() -> str:
    """URL de `/auth/login` con el destino de vuelta a este front."""
    return f"{API_BASE_URL}/api/v1/auth/login?redirect={FRONTEND_URL}"


def _canjear_codigo(codigo: str) -> dict:
    """Cambia el código de un solo uso por la sesión. Devuelve el dict de usuario.

    Hace dos llamadas: `/auth/exchange` para obtener los tokens y `/auth/me` para leer la identidad
    del access token. Se pregunta a `/auth/me` en vez de decodificar el JWT aquí a propósito: el
    front no debe aprender a interpretar tokens, y así la fuente de verdad del contenido de la
    sesión sigue siendo la API.
    """
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_S) as cliente:
            canje = cliente.post("/api/v1/auth/exchange", json={"code": codigo})
            if canje.status_code == 401:
                raise ErrorDeSesion(
                    "El enlace de acceso ya se usó o expiró. Vuelve a iniciar sesión."
                )
            if canje.status_code != 200:
                raise ErrorDeSesion("No se pudo completar el inicio de sesión.")
            tokens = canje.json()

            yo = cliente.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            if yo.status_code != 200:
                raise ErrorDeSesion("No se pudo leer la sesión recién creada.")
    except httpx.HTTPError as exc:
        raise ErrorDeSesion("No se pudo contactar a la API de FARO.") from exc

    usuario = yo.json()
    # `access_token` en su propia clave porque `pages/3_Chat.py` ya lo lee de ahí (US-305).
    st.session_state["access_token"] = tokens["access_token"]
    st.session_state["refresh_token"] = tokens["refresh_token"]
    st.session_state["user"] = usuario
    return usuario


def _consumir_codigo_de_la_url() -> Optional[dict]:
    """Si venimos de vuelta del login, canjea el código y limpia la URL.

    La limpieza importa: si el `code_faro` se queda en la barra de direcciones, la persona puede
    recargar o compartir el enlace y el segundo intento falla (el código es de un solo uso), lo que
    parece un error del sistema sin serlo.
    """
    codigo = st.query_params.get(_PARAM_CODIGO)
    if not codigo:
        return None
    try:
        return _canjear_codigo(codigo)
    except ErrorDeSesion as exc:
        st.error(str(exc))
        return None
    finally:
        # Se limpia pase lo que pase: un codigo ya consumido no sirve para reintentar.
        del st.query_params[_PARAM_CODIGO]


def current_user() -> Optional[dict]:
    """Usuario en sesión, o `None` si no ha iniciado sesión.

    Dict con `sub`, `email`, `name` y `role`. Es también el punto donde se recoge la vuelta del
    login, así que las páginas no tienen que saber nada del flujo OAuth: les basta con llamar a
    esto al principio.
    """
    usuario = st.session_state.get("user")
    if usuario is not None:
        return usuario
    return _consumir_codigo_de_la_url()


def login_button() -> None:
    """Botón que arranca el flujo OAuth contra la API."""
    st.link_button("Iniciar sesión con Google", url_de_login(), type="primary")


def logout_button() -> None:
    """Cierra la sesión local.

    Borra la sesión de **este** navegador; no revoca el refresh token del lado de la API — eso es
    `SEC-005`, follow-up documentado. Para una sesión de 15 minutos y un proyecto con esta ventana
    es aceptable, pero conviene no confundir "cerré sesión" con "el token dejó de servir".
    """
    if st.sidebar.button("Cerrar sesión"):
        for clave in ("user", "access_token", "refresh_token"):
            st.session_state.pop(clave, None)
        st.rerun()


def require_role(role: str) -> bool:
    """¿La persona en sesión alcanza el rol pedido?

    `analista` es superconjunto de `ciudadano`: quien es analista pasa cualquier guarda. Sin sesión
    devuelve `False` — nunca lanza, para que una página pueda decidir si esconde la vista o muestra
    el botón de login.
    """
    assert role in ROLES, f"Rol inválido: {role}"
    usuario = current_user()
    if not usuario:
        return False
    return usuario.get("role") == role or usuario.get("role") == "analista"
