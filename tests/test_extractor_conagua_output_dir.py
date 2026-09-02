from pathlib import Path

import src.ingesta.extractor_conagua as modulo


class _Response:
    content = b"[1]"

    def raise_for_status(self):
        pass

    def json(self):
        return [{
            "id_presa": "1",
            "nombre_oficial": "Presa A",
            "estado": "Estado A",
            "cap_namo": 10.0,
        }]


def test_extractor_crea_directorio_bronze_si_no_existe(tmp_path, monkeypatch):
    destino = tmp_path / "bronze" / "conagua"
    monkeypatch.setattr(modulo, "BRONZE_PATH", str(destino))
    monkeypatch.setattr(modulo.requests, "post", lambda *args, **kwargs: _Response())

    salida = Path(modulo.extraer_conagua())

    assert destino.is_dir()
    assert salida.is_file()
    assert salida.parent == destino
