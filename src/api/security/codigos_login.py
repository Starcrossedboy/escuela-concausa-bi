"""Códigos de un solo uso para entregar la sesión al frontend (US-405, ADR-010).

**El problema.** `/auth/callback` termina el flujo OAuth y tiene el par de JWT en la mano, pero
quien está ahí es el **navegador**, no el frontend: el callback responde JSON y Streamlit nunca se
entera de que hubo login. Hay que pasarle la sesión al front, y la forma obvia —redirigir con los
tokens en la query string— es justo la mala: la URL queda en el historial del navegador, en los
logs de cualquier proxy y en la cabecera `Referer` de la siguiente petición.

**La solución.** El callback guarda la *identidad* recién verificada y redirige al front con un
**código corto de un solo uso**. El front lo canjea desde el servidor en `POST /auth/exchange` y
recibe ahí los tokens, por el cuerpo de la respuesta. Por la URL solo viaja el código, que muere
en el primer canje y expira en 60 s.

**Tres decisiones que sostienen esto:**

1. **No se guardan tokens, se guarda la identidad.** Los JWT se emiten al canjear. Así no hay
   credenciales en reposo en la base: lo que queda es el mismo `sub`/`email`/`name`/`role` que
   cualquiera obtendría iniciando sesión.
2. **Se guarda el SHA-256 del código, nunca el código.** Quien lea la tabla no puede canjear nada,
   igual que con una contraseña. El código en claro solo existe en el redirect del navegador.
3. **El canje es atómico** (`DELETE ... RETURNING`): dos peticiones simultáneas con el mismo código
   no pueden ganar las dos. "Un solo uso" lo garantiza Postgres, no el código de Python.

**Sobre el almacén.** El de producción es Postgres. Existe un `AlmacenMemoria` para pruebas y para
degradar si la base no está disponible al arrancar — pero **solo es correcto con una instancia**:
con varias, el canje puede caer en un proceso distinto al que emitió el código y el login falla de
forma intermitente. Por eso la degradación grita en el log y queda registrada como riesgo.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable

from sqlalchemy import text

from src.api.config import get_settings
from src.api.schemas import Rol

_logger = logging.getLogger("faro.api.codigos")

ESQUEMA = "auth"
TABLA = "codigos_login"


@dataclass(frozen=True)
class IdentidadSesion:
    """Lo que se guarda entre el callback y el canje. Sin tokens: se emiten al canjear."""

    sub: str
    email: str
    name: str
    role: Rol


def _hash(codigo: str) -> str:
    """SHA-256 hexadecimal del código. Es lo único que toca la base."""
    return hashlib.sha256(codigo.encode("utf-8")).hexdigest()


def _nuevo_codigo() -> str:
    """Código opaco de 256 bits. No es adivinable ni enumerable."""
    return secrets.token_urlsafe(32)


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


@runtime_checkable
class AlmacenCodigos(Protocol):
    def guardar(self, identidad: IdentidadSesion) -> str:  # pragma: no cover - interfaz
        """Genera un código, guarda la identidad y devuelve el código en claro."""
        ...

    def canjear(self, codigo: str) -> IdentidadSesion | None:  # pragma: no cover - interfaz
        """Consume el código y devuelve la identidad, o `None` si no existe o expiró."""
        ...


class AlmacenMemoria:
    """Almacén en memoria del proceso. Para pruebas y como degradación de emergencia.

    **No es válido con varias instancias**: el canje puede llegar a un proceso que no emitió el
    código. Ver la nota del módulo.
    """

    def __init__(self) -> None:
        self._filas: dict[str, tuple[IdentidadSesion, datetime]] = {}
        self._lock = threading.Lock()

    def guardar(self, identidad: IdentidadSesion) -> str:
        codigo = _nuevo_codigo()
        expira = _ahora() + timedelta(seconds=get_settings().login_code_expire_segundos)
        with self._lock:
            self._purgar()
            self._filas[_hash(codigo)] = (identidad, expira)
        return codigo

    def canjear(self, codigo: str) -> IdentidadSesion | None:
        with self._lock:
            self._purgar()
            fila = self._filas.pop(_hash(codigo), None)  # pop => un solo uso
        if fila is None:
            return None
        identidad, expira = fila
        return identidad if expira > _ahora() else None

    def _purgar(self) -> None:
        ahora = _ahora()
        for clave in [k for k, (_, exp) in self._filas.items() if exp <= ahora]:
            del self._filas[clave]


class AlmacenPostgres:
    """Almacén en Postgres: sobrevive al reinicio y sirve para varias instancias.

    La tabla vive en su propio esquema `auth`, **fuera de `gold`**: no es un artefacto analítico y
    no le corresponde a la Célula 1. Se crea de forma idempotente al construir el almacén, así que
    no hace falta una migración manual — pero el rol de la aplicación necesita permiso de `CREATE`
    sobre la base (ver el aviso a C5 en el DevLog).
    """

    def __init__(self, engine) -> None:
        self._engine = engine
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = (
            f"CREATE SCHEMA IF NOT EXISTS {ESQUEMA};",
            # `codigo_hash` es la PK: el codigo en claro nunca se almacena.
            f"""CREATE TABLE IF NOT EXISTS {ESQUEMA}.{TABLA} (
                    codigo_hash TEXT PRIMARY KEY,
                    sub         TEXT        NOT NULL,
                    email       TEXT        NOT NULL,
                    nombre      TEXT        NOT NULL DEFAULT '',
                    rol         TEXT        NOT NULL,
                    expira_en   TIMESTAMPTZ NOT NULL
                );""",
            f"CREATE INDEX IF NOT EXISTS ix_{TABLA}_expira ON {ESQUEMA}.{TABLA} (expira_en);",
        )
        with self._engine.begin() as conexion:
            for sentencia in ddl:
                conexion.execute(text(sentencia))

    def guardar(self, identidad: IdentidadSesion) -> str:
        codigo = _nuevo_codigo()
        expira = _ahora() + timedelta(seconds=get_settings().login_code_expire_segundos)
        with self._engine.begin() as conexion:
            # Se aprovecha cada escritura para barrer lo vencido: la tabla nunca crece sola.
            conexion.execute(text(f"DELETE FROM {ESQUEMA}.{TABLA} WHERE expira_en <= now();"))
            conexion.execute(
                text(
                    f"""INSERT INTO {ESQUEMA}.{TABLA}
                            (codigo_hash, sub, email, nombre, rol, expira_en)
                        VALUES (:h, :sub, :email, :nombre, :rol, :expira);"""
                ),
                {
                    "h": _hash(codigo),
                    "sub": identidad.sub,
                    "email": identidad.email,
                    "nombre": identidad.name,
                    "rol": identidad.role.value,
                    "expira": expira,
                },
            )
        return codigo

    def canjear(self, codigo: str) -> IdentidadSesion | None:
        # DELETE ... RETURNING: borrar y leer son la MISMA operacion, asi que dos peticiones
        # simultaneas con el mismo codigo no pueden ganar las dos. El "un solo uso" lo garantiza
        # Postgres, no una comprobacion en Python.
        with self._engine.begin() as conexion:
            fila = conexion.execute(
                text(
                    f"""DELETE FROM {ESQUEMA}.{TABLA}
                        WHERE codigo_hash = :h
                        RETURNING sub, email, nombre, rol, expira_en;"""
                ),
                {"h": _hash(codigo)},
            ).first()
        if fila is None:
            return None
        expira = fila.expira_en
        if expira.tzinfo is None:  # por si el driver devuelve naive
            expira = expira.replace(tzinfo=timezone.utc)
        if expira <= _ahora():
            return None
        return IdentidadSesion(
            sub=fila.sub, email=fila.email, name=fila.nombre, role=Rol(fila.rol)
        )


_almacen: AlmacenCodigos | None = None
_almacen_lock = threading.Lock()


def get_almacen_codigos() -> AlmacenCodigos:
    """Dependencia FastAPI del almacén. Postgres si se puede; memoria si no, con aviso.

    La degradación es deliberada: preferimos un login que funcione con una instancia a un login
    que no funcione en absoluto. Pero se registra como `error` en el log, no como detalle, porque
    con varias instancias produce fallos intermitentes difíciles de diagnosticar.

    Se captura **cualquier** excepción a propósito: aquí caben la base inalcanzable, el driver
    ausente (`ModuleNotFoundError` al importar psycopg2), una URL mal formada o un permiso de
    `CREATE` que falta. Ninguna de esas cosas justifica dejar sin login a todo el mundo.
    """
    global _almacen
    with _almacen_lock:
        if _almacen is not None:
            return _almacen
        try:
            from src.api.db import get_engine

            _almacen = AlmacenPostgres(get_engine())
        except Exception as exc:  # noqa: BLE001 - degradar SIEMPRE, ver docstring
            _logger.error(
                "No se pudo preparar el almacen de codigos en Postgres (%s). Se degrada a memoria: "
                "el login SOLO funcionara con una instancia. Ver ADR-010 y SEC-007.",
                type(exc).__name__,
            )
            _almacen = AlmacenMemoria()
        return _almacen


def reset_almacen_codigos() -> None:
    """Olvida el almacén cacheado. Para pruebas, que no deben compartir estado."""
    global _almacen
    with _almacen_lock:
        _almacen = None
