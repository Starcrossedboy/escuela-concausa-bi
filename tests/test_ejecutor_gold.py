"""Pruebas del ejecutor SQL read-only del agente (US-404 / BUG-025).

Unitarias, SIN Postgres real: verifican la defensa en profundidad (rechazo de escritura antes de
tocar la BD), el fallo controlado cuando no hay configuración, el mapeo de filas con un engine falso,
y el cableado condicional del override en la app. La ejecución contra Postgres real es integración
(US-422, Eloisa).
"""
from __future__ import annotations

from contextlib import contextmanager

import pytest

import src.api.app as appmod
import src.api.ejecutor_gold as ejmod
from src.api.config import Settings


@pytest.fixture(autouse=True)
def _limpiar_cache_engine():
    """El engine está cacheado con lru_cache; se limpia entre pruebas para aislar la configuración."""
    ejmod._engine_read_only.cache_clear()
    yield
    ejmod._engine_read_only.cache_clear()


def test_sql_de_escritura_se_rechaza_sin_tocar_bd(monkeypatch) -> None:
    """Defensa en profundidad: un SQL que no es solo-lectura lanza ValueError antes de conectar."""

    def _no_debe_conectar():
        raise AssertionError("no debió intentar crear el engine")

    monkeypatch.setattr(ejmod, "_engine_read_only", _no_debe_conectar)
    with pytest.raises(ValueError):
        ejmod.ejecutar_sql_read_only("DELETE FROM gold.predicciones")


def test_sin_configuracion_lanza_runtimeerror(monkeypatch) -> None:
    monkeypatch.setattr(ejmod, "get_settings", lambda: Settings(database_url_read_only=""))
    with pytest.raises(RuntimeError):
        ejmod.ejecutar_sql_read_only("SELECT cct FROM gold.features_escuela")


def test_select_valido_mapea_filas_a_dicts(monkeypatch) -> None:
    """Happy path con engine falso: aplica SET TRANSACTION READ ONLY y devuelve list[dict]."""
    sentencias: list[str] = []

    class _FilaFake:
        def __init__(self, mapping):
            self._mapping = mapping

    class _ResultFake:
        def __init__(self, filas):
            self._filas = filas

        def __iter__(self):
            return iter(self._filas)

    class _ConnFake:
        def execute(self, clause):
            sql = str(clause)
            sentencias.append(sql)
            if "SET TRANSACTION READ ONLY" in sql:
                return _ResultFake([])
            return _ResultFake([_FilaFake({"cct": "09ABC0001X", "indice_riesgo": 0.7})])

    class _EngineFake:
        @contextmanager
        def connect(self):
            yield _ConnFake()

    monkeypatch.setattr(ejmod, "_engine_read_only", lambda: _EngineFake())

    filas = ejmod.ejecutar_sql_read_only("SELECT cct, indice_riesgo FROM gold.features_escuela LIMIT 10")
    assert filas == [{"cct": "09ABC0001X", "indice_riesgo": 0.7}]
    assert any("SET TRANSACTION READ ONLY" in s for s in sentencias)


def test_wiring_condicional_del_override(monkeypatch) -> None:
    """Con DSN configurado, la app cablea get_ejecutar_sql; sin él, no lo toca."""
    from src.api.v1.agente import get_ejecutar_sql

    monkeypatch.setattr(
        appmod,
        "get_settings",
        lambda: Settings(database_url_read_only="postgresql+psycopg2://ro@localhost/faro", cors_origins=""),
    )
    app_con = appmod.create_app()
    assert get_ejecutar_sql in app_con.dependency_overrides

    monkeypatch.setattr(
        appmod, "get_settings", lambda: Settings(database_url_read_only="", cors_origins="")
    )
    app_sin = appmod.create_app()
    assert get_ejecutar_sql not in app_sin.dependency_overrides
