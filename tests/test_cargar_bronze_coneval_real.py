import pandas as pd
import pytest

from src.ingesta.cargar_bronze_coneval_real import (
    TABLAS_PERMITIDAS,
    _pg_column_name,
    _renombrar_para_postgres,
    _tipo_postgres,
    _ultimo_parquet,
)


def test_tablas_reales_separadas():
    assert TABLAS_PERMITIDAS == {
        "irs": "coneval_irs_2020",
        "pobreza": "coneval_pobreza_2020",
    }


@pytest.mark.parametrize(
    ("serie", "esperado"),
    [
        (pd.Series([1, 2], dtype="int64"), "BIGINT"),
        (pd.Series([1.2, 2.3], dtype="float64"), "DOUBLE PRECISION"),
        (pd.Series(["1", "n.d."], dtype="string"), "TEXT"),
        (pd.Series(pd.to_datetime(["2026-08-30"], utc=True)), "TIMESTAMPTZ"),
    ],
)
def test_tipo_postgres_tecnico(serie, esperado):
    assert _tipo_postgres(serie) == esperado


def test_ultimo_parquet_falla_si_no_hay_archivo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="No hay Parquet real DS-07"):
        _ultimo_parquet("irs")


def test_pg_column_name_evade_truncamiento_postgres():
    a = "Indicadores de rezago social (porcentaje) | Población de 15 años o más analfabeta"
    b = "Indicadores de rezago social (porcentaje) | Población de 15 años o más con educación básica incompleta"
    assert _pg_column_name(a) != _pg_column_name(b)
    assert len(_pg_column_name(a).encode("utf-8")) <= 63


def test_renombrar_para_postgres_preserva_metadatos():
    df = pd.DataFrame({
        "Clave entidad": ["01"],
        "_source": ["DS-07_CONEVAL"],
    })
    out, mapping = _renombrar_para_postgres(df)
    assert mapping["_source"] == "_source"
    assert mapping["Clave entidad"].startswith("c_")
    assert mapping["Clave entidad"] in out.columns
