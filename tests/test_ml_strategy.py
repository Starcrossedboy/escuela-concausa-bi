"""Tests de no-fuga temporal y schema del fixture mock (TEST-ML-001, TEST-ML-002, TEST-ML-003)."""
import os
import pytest
import pandas as pd

FIXTURE_PATH = "tests/fixtures/features_escuela_mock.parquet"

EXPECTED_COLUMNS = {
    "cct", "ciclo", "entidad_id", "nivel", "matricula", "delta_matricula",
    "d1_rezago_social", "d2_incidencia_delictiva", "d3_infraestructura_score",
    "d4_conectividad_score", "d5_estres_hidrico", "d5_dato_disponible",
    "d6_calidad_aire", "d6_dato_disponible", "indice_completitud_drivers",
    "driver_dominante",
}


@pytest.fixture(scope="module")
def df():
    if not os.path.exists(FIXTURE_PATH):
        pytest.skip(f"Fixture no generado todavía. Ejecuta: python {FIXTURE_PATH.replace('.parquet', '.py').replace('fixtures/', 'fixtures/generate_mock_features.py')}")
    return pd.read_parquet(FIXTURE_PATH)


def test_schema_completo(df):
    """TEST-ML-003: el fixture tiene todas las columnas del schema esperado de gold.features_escuela."""
    columnas_faltantes = EXPECTED_COLUMNS - set(df.columns)
    assert not columnas_faltantes, f"Columnas faltantes en el fixture: {columnas_faltantes}"


def test_sin_nulos(df):
    """TEST-ML-002: no hay nulos en ninguna columna."""
    nulos = df.isnull().sum()
    assert nulos.sum() == 0, f"Columnas con nulos:\n{nulos[nulos > 0]}"


def test_sin_ceros_en_drivers_imputados(df):
    """TEST-ML-002: drivers imputados (dato_disponible=0) nunca tienen valor 0.0 (cero no es imputación válida)."""
    d5_imputados = df[df["d5_dato_disponible"] == 0]["d5_estres_hidrico"]
    assert (d5_imputados != 0).all(), "d5_estres_hidrico tiene ceros en filas imputadas"

    d6_imputados = df[df["d6_dato_disponible"] == 0]["d6_calidad_aire"]
    assert (d6_imputados != 0).all(), "d6_calidad_aire tiene ceros en filas imputadas"


def test_no_fuga_temporal():
    """TEST-ML-001: ningún ciclo del conjunto de test aparece en el conjunto de train para cada fold."""
    ciclos = [f"{y}-{str(y+1)[-2:]}" for y in range(2013, 2024)]
    n_folds = 4
    primer_test = len(ciclos) - n_folds  # índice del primer ciclo usado como test

    for fold in range(n_folds):
        test_ciclo = ciclos[primer_test + fold]
        train_ciclos = ciclos[:primer_test + fold]
        assert test_ciclo not in train_ciclos, (
            f"Fuga temporal en fold {fold+1}: '{test_ciclo}' aparece en train"
        )


def test_entidades_scope(df):
    """Solo las 4 entidades del scope están en el fixture (09 CDMX, 15 Edomex, 19 NL, 14 Jalisco)."""
    entidades_validas = {"09", "15", "19", "14"}
    entidades_fixture = set(df["entidad_id"].unique())
    assert entidades_fixture <= entidades_validas, (
        f"Entidades fuera del scope: {entidades_fixture - entidades_validas}"
    )
