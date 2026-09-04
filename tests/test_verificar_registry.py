"""Pruebas de la CLI de verificación del Registry.

La CLI hace **dos** comprobaciones distintas y las dos se interceptan aquí: que exista la versión
y que el artefacto se pueda cargar. Dejar la segunda sin doble haría que estas pruebas salieran a
la red contra el `--tracking-uri` de mentiras y se colgaran.
"""

from __future__ import annotations

import sys

import pytest

from src.modelos import verificar_registry


@pytest.fixture
def artefactos_ok(monkeypatch):
    """Intercepta la verificación de artefactos y registra con qué se llamó."""
    llamadas: list[tuple[str, dict[str, str]]] = []
    monkeypatch.setattr(
        verificar_registry,
        "verificar_artefactos_descargables",
        lambda uri, versiones: llamadas.append((uri, dict(versiones))),
    )
    return llamadas


def test_cli_verifica_solo_el_modelo_solicitado(monkeypatch, capsys, artefactos_ok) -> None:
    recibido: dict[str, object] = {}

    def verificar(uri: str, nombres: frozenset[str]) -> dict[str, str]:
        recibido.update(uri=uri, nombres=nombres)
        return {"ML02_DriverClasificador": "3"}

    monkeypatch.setattr(verificar_registry, "verificar_modelos_registrados", verificar)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verificar_registry",
            "--tracking-uri",
            "http://mlflow:5000",
            "--modelo",
            "ML02_DriverClasificador",
        ],
    )

    assert verificar_registry.main() == 0
    assert recibido == {
        "uri": "http://mlflow:5000",
        "nombres": frozenset({"ML02_DriverClasificador"}),
    }
    assert "ML02_DriverClasificador: versión 3" in capsys.readouterr().out


def test_cli_verifica_los_tres_modelos_por_defecto(monkeypatch, artefactos_ok) -> None:
    recibido: dict[str, object] = {}

    def verificar(uri: str, nombres: frozenset[str]) -> dict[str, str]:
        recibido.update(uri=uri, nombres=nombres)
        return {nombre: "1" for nombre in nombres}

    monkeypatch.setattr(verificar_registry, "verificar_modelos_registrados", verificar)
    monkeypatch.setattr(sys, "argv", ["verificar_registry"])

    assert verificar_registry.main() == 0
    assert recibido["nombres"] == verificar_registry.NOMBRES_MODELOS_CANONICOS


def test_cli_comprueba_que_el_artefacto_carga_por_defecto(monkeypatch, artefactos_ok) -> None:
    """Sin esto la CLI vuelve a dar verde sobre un modelo inservible (BUG-043)."""
    monkeypatch.setattr(
        verificar_registry,
        "verificar_modelos_registrados",
        lambda uri, nombres: {"ML01_RegresionMatricula": "2"},
    )
    monkeypatch.setattr(
        sys, "argv", ["verificar_registry", "--tracking-uri", "http://mlflow:5000"]
    )

    assert verificar_registry.main() == 0
    assert artefactos_ok == [("http://mlflow:5000", {"ML01_RegresionMatricula": "2"})]


def test_cli_propaga_el_fallo_de_artefacto(monkeypatch) -> None:
    """Un artefacto que no carga tiene que reprobar la CLI, no sólo advertir."""

    def explota(uri: str, versiones) -> None:
        raise RuntimeError("Hay versiones en el Registry que NO se pueden cargar: ...")

    monkeypatch.setattr(
        verificar_registry,
        "verificar_modelos_registrados",
        lambda uri, nombres: {"ML01_RegresionMatricula": "1"},
    )
    monkeypatch.setattr(verificar_registry, "verificar_artefactos_descargables", explota)
    monkeypatch.setattr(sys, "argv", ["verificar_registry"])

    with pytest.raises(RuntimeError, match="NO se pueden cargar"):
        verificar_registry.main()


def test_cli_sin_artefacto_omite_la_comprobacion_y_lo_dice(
    monkeypatch, capsys, artefactos_ok
) -> None:
    """La verificación débil sigue disponible, pero el reporte no puede fingir que es la fuerte."""
    monkeypatch.setattr(
        verificar_registry,
        "verificar_modelos_registrados",
        lambda uri, nombres: {"ML01_RegresionMatricula": "2"},
    )
    monkeypatch.setattr(sys, "argv", ["verificar_registry", "--sin-artefacto"])

    assert verificar_registry.main() == 0
    assert artefactos_ok == []  # no se llamó
    assert "artefacto NO verificado" in capsys.readouterr().out
