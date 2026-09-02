from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from src.ingesta import extractor_coneval as mod


def _zip_bytes(filename: str, content: bytes = b"fake-xlsx") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(filename, content)
    return buffer.getvalue()


class _FakeResponse:
    def __init__(self, content: bytes, url: str, status_code: int = 200):
        self.content = content
        self.url = url
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeExcel:
    def __init__(self, sheets: list[str]):
        self.sheet_names = sheets


def test_rechaza_url_no_oficial() -> None:
    with pytest.raises(ValueError, match="Solo se acepta HTTPS"):
        mod._validar_url_oficial("https://ejemplo.com/coneval.zip")
    with pytest.raises(ValueError, match="Solo se acepta HTTPS"):
        mod._validar_url_oficial("http://www.coneval.org.mx/coneval.zip")


def test_zip_rechaza_path_traversal() -> None:
    data = _zip_bytes("../escape.xlsx")
    with pytest.raises(ValueError, match="ZIP inseguro"):
        mod._validar_zip_seguro(data)


def test_descarga_verifica_redirect_y_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _zip_bytes("oficial.xlsx")

    def fake_get(url: str, timeout: int, allow_redirects: bool, headers: dict[str, str]):
        assert timeout == 120
        assert allow_redirects is True
        return _FakeResponse(data, mod.IRS_URL)

    monkeypatch.setattr(mod.requests, "get", fake_get)
    meta, returned = mod._descargar_zip_oficial("irs", mod.IRS_URL)
    assert returned == data
    assert meta.sha256 == hashlib.sha256(data).hexdigest()


def test_aplana_header_multinivel_sin_aliases_de_negocio() -> None:
    cols = pd.MultiIndex.from_tuples(
        [
            ("Clave entidad", "Unnamed: 0_level_1"),
            ("Pobreza", "Porcentaje 2020"),
            ("Indicadores de rezago social (porcentaje)", "Población analfabeta"),
        ]
    )
    assert mod._aplanar_columnas(cols) == [
        "Clave entidad",
        "Pobreza | Porcentaje 2020",
        "Indicadores de rezago social (porcentaje) | Población analfabeta",
    ]


def test_lee_irs_workbook_y_hoja_exactos(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _zip_bytes(mod.IRS_MEMBER_2020)
    raw = pd.DataFrame(
        [[1, "Aguascalientes", 1, "Aguascalientes", -1.2, "Muy bajo"]],
        columns=pd.MultiIndex.from_tuples(
            [
                ("Clave entidad", "Unnamed: 0_level_1"),
                ("Entidad federativa", "Unnamed: 1_level_1"),
                ("Clave municipio", "Unnamed: 2_level_1"),
                ("Municipio", "Unnamed: 3_level_1"),
                ("Índice de rezago social", "Unnamed: 4_level_1"),
                ("Grado de rezago social", "Unnamed: 5_level_1"),
            ]
        ),
    )

    monkeypatch.setattr(mod.pd, "ExcelFile", lambda *a, **k: _FakeExcel([mod.IRS_SHEET]))

    def fake_read_excel(excel, sheet_name, header, dtype):
        assert sheet_name == mod.IRS_SHEET
        assert header == list(mod.HEADER_ROWS)
        return raw.copy()

    monkeypatch.setattr(mod.pd, "read_excel", fake_read_excel)
    df = mod._leer_xlsx_oficial(
        data,
        producto="irs",
        member=mod.IRS_MEMBER_2020,
        sheet=mod.IRS_SHEET,
    )
    contrato = mod._validar_contrato_irs(df)
    assert contrato["cve_ent"] == "Clave entidad"
    assert contrato["cve_mun"] == "Clave municipio"
    assert contrato["indice"] == "Índice de rezago social"


def test_pobreza_localiza_porcentaje_2020_exactamente() -> None:
    df = pd.DataFrame(
        columns=[
            "Clave de entidad",
            "Entidad federativa",
            "Clave de municipio",
            "Municipio",
            "Pobreza | Porcentaje 2010",
            "Pobreza | Porcentaje 2015",
            "Pobreza | Porcentaje 2020",
            "Pobreza extrema | Porcentaje 2020",
        ]
    )
    contrato = mod._validar_contrato_pobreza(df)
    assert contrato["pobreza_pct_2020"] == "Pobreza | Porcentaje 2020"


def test_falla_si_cambia_nombre_fisico_del_workbook() -> None:
    data = _zip_bytes("otro.xlsx")
    with pytest.raises(ValueError, match="cambió su estructura"):
        mod._leer_xlsx_oficial(
            data,
            producto="irs",
            member=mod.IRS_MEMBER_2020,
            sheet=mod.IRS_SHEET,
        )


def test_guardar_bronze_solo_agrega_metadatos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "IRS_BRONZE_PATH", tmp_path / "irs")
    original = pd.DataFrame({"Clave entidad": [1], "Municipio": ["A"]})
    when = datetime(2026, 8, 30, 5, 0, tzinfo=timezone.utc)
    captured = {}

    def fake_to_parquet(self, path, index=False):
        captured["df"] = self.copy()
        captured["path"] = Path(path)

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)
    path, tabla = mod._guardar_bronze(
        "irs", original, mod.IRS_URL, mod.IRS_MEMBER_2020, mod.IRS_SHEET, when
    )
    assert list(captured["df"].columns[:2]) == list(original.columns)
    assert captured["df"]["_source"].eq(mod.SOURCE_NAME).all()
    assert str(captured["path"]) == path
    assert tabla.header_rows == mod.HEADER_ROWS


def test_manifest_registra_contrato(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path)
    when = datetime(2026, 8, 30, 5, 0, tzinfo=timezone.utc)
    descarga = mod.DescargaOficial("irs", mod.IRS_URL, mod.IRS_URL, "abc", 10)
    tabla = mod.TablaDetectada(
        "irs", mod.IRS_MEMBER_2020, mod.IRS_SHEET, mod.HEADER_ROWS, 2478, 19, ("Municipio",)
    )
    path = mod._guardar_manifest(
        when,
        [descarga],
        [tabla],
        {"irs": {"cve_mun": "Clave municipio"}},
    )
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["contratos_detectados"]["irs"]["cve_mun"] == "Clave municipio"


def test_guardar_bronze_preserva_nd_en_columna_mixta(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "POBREZA_BRONZE_PATH", tmp_path / "pobreza")
    original = pd.DataFrame(
        {
            "Población 2010* (leer nota al final del cuadro)": [1234, "n.d."],
            "Municipio": ["A", "B"],
        }
    )
    when = datetime(2026, 8, 30, 5, 0, tzinfo=timezone.utc)
    captured = {}

    def fake_to_parquet(self, path, index=False):
        captured["df"] = self.copy()

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)
    mod._guardar_bronze(
        "pobreza",
        original,
        mod.POBREZA_URL,
        mod.POBREZA_MEMBER_2020,
        mod.POBREZA_SHEET,
        when,
    )

    serie = captured["df"]["Población 2010* (leer nota al final del cuadro)"]
    assert str(serie.dtype) == "string"
    assert serie.tolist() == ["1234", "n.d."]
