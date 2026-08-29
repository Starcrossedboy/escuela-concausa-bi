"""Pruebas de la CLI de verificación del Registry."""

from __future__ import annotations

import sys

from src.modelos import verificar_registry


def test_cli_verifica_solo_el_modelo_solicitado(monkeypatch, capsys) -> None:
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


def test_cli_verifica_los_tres_modelos_por_defecto(monkeypatch) -> None:
    recibido: dict[str, object] = {}

    def verificar(uri: str, nombres: frozenset[str]) -> dict[str, str]:
        recibido.update(uri=uri, nombres=nombres)
        return {nombre: "1" for nombre in nombres}

    monkeypatch.setattr(verificar_registry, "verificar_modelos_registrados", verificar)
    monkeypatch.setattr(sys, "argv", ["verificar_registry"])

    assert verificar_registry.main() == 0
    assert recibido["nombres"] == verificar_registry.NOMBRES_MODELOS_CANONICOS