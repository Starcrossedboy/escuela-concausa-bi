"""Pruebas del target híbrido de dos niveles (DEC-007, TEST-009).

La agregación es donde es más fácil romper la regla de cobertura parcial sin darse cuenta: basta un
`fillna(0)` antes del promedio para que una escuela sin dato de aire arrastre a todo su municipio
hacia cero. `test_no_cuenta_la_ausencia_como_cero` fija ese comportamiento.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.modelos.contrato import DRIVERS
from src.modelos.entrenar_ml01 import COLUMNA_TARGET
from src.modelos.generar_fixture_dim import generar as generar_dim
from src.modelos.generar_fixture_dim import nivel_de_cct
from src.modelos.particion_temporal import ciclos_ordenados, dividir_por_ciclo
from src.modelos.target_hibrido import (
    LLAVE_AGREGADA,
    agregar_a_municipio_nivel,
    cargar_dimension,
    unir_target,
)


@pytest.fixture(scope="module")
def dimension(features: pd.DataFrame) -> pd.DataFrame:
    return generar_dim(features)


@pytest.fixture(scope="module")
def agregado(features: pd.DataFrame, dimension: pd.DataFrame):
    return agregar_a_municipio_nivel(features, dimension)


def _serie_simulada(agg: pd.DataFrame) -> pd.DataFrame:
    """Serie SNIEE simulada: la real es responsabilidad de la C1 (gate 30 de agosto)."""
    rng = np.random.default_rng(1)
    llaves = agg[list(LLAVE_AGREGADA)].drop_duplicates()
    return llaves.assign(**{COLUMNA_TARGET: rng.normal(-0.02, 0.04, len(llaves))})


# --------------------------------------------------------------------------- dimensión


def test_el_nivel_sale_del_cct() -> None:
    assert nivel_de_cct("09DPR0001X") == "PRIMARIA"
    assert nivel_de_cct("14DJN0007M") == "PREESCOLAR"


def test_falla_con_una_clave_de_nivel_desconocida() -> None:
    with pytest.raises(ValueError, match="Clave de nivel desconocida"):
        nivel_de_cct("09XXX0001X")


def test_municipio_y_entidad_nunca_se_contradicen(dimension: pd.DataFrame) -> None:
    """La clave INEGI de municipio empieza con la de su entidad."""
    assert (dimension["cve_mun"].str[:2] == dimension["cct"].str[:2]).all()


def test_falla_si_la_dimension_no_trae_municipio(tmp_path: Path) -> None:
    ruta = tmp_path / "dim.csv"
    pd.DataFrame({"cct": ["09DPR0001X"], "nivel": ["PRIMARIA"]}).to_csv(ruta, index=False)
    with pytest.raises(ValueError, match="cve_mun"):
        cargar_dimension(ruta)


# --------------------------------------------------------------------------- grano


def test_una_fila_por_municipio_nivel_ciclo(agregado) -> None:
    agg, _ = agregado
    assert not agg.duplicated(subset=list(LLAVE_AGREGADA)).any()


def test_conserva_todos_los_ciclos(agregado, features: pd.DataFrame) -> None:
    """Agregar no debe perder profundidad temporal: es lo único que hace validable el target."""
    agg, _ = agregado
    assert ciclos_ordenados(agg) == ciclos_ordenados(features)


def test_no_pierde_escuelas_en_silencio(agregado, features: pd.DataFrame) -> None:
    agg, resumen = agregado
    assert resumen.escuelas_sin_dimension == 0
    assert resumen.cobertura_dimension == pytest.approx(1.0)
    assert agg["escuelas"].sum() == len(features)


def test_reporta_las_escuelas_sin_dimension(features: pd.DataFrame, dimension: pd.DataFrame) -> None:
    """Si una escuela no está en `dim_escuela`, se cuenta; no desaparece sin dejar rastro."""
    parcial = dimension.iloc[:-10]
    _, resumen = agregar_a_municipio_nivel(features, parcial)
    assert resumen.escuelas_sin_dimension > 0
    assert resumen.cobertura_dimension < 1.0


def test_falla_si_ninguna_escuela_cruza(features: pd.DataFrame, dimension: pd.DataFrame) -> None:
    ajena = dimension.assign(cct="99XXX9999Z").head(1)
    with pytest.raises(ValueError, match="Ninguna escuela encontró"):
        agregar_a_municipio_nivel(features, ajena)


# --------------------------------------------------------------------------- cobertura parcial


def test_no_cuenta_la_ausencia_como_cero(dimension: pd.DataFrame) -> None:
    """Dos escuelas, una sin dato: el promedio es el valor de la que sí lo tiene, no su mitad."""
    ccts = dimension["cct"].head(2).tolist()
    grupo = dimension[dimension["cct"].isin(ccts)].assign(cve_mun="09001", nivel="PRIMARIA")
    fila = {d: 0.8 for d in DRIVERS}
    fila.update({f"d{i}_cobertura": "OK" for i in range(1, 7)})
    features = pd.DataFrame([
        {"cct": ccts[0], "id_ciclo": "2023-2024", **fila,
         "indice_completitud_drivers": 1.0, COLUMNA_TARGET: 0.0},
        {"cct": ccts[1], "id_ciclo": "2023-2024", **fila, "d6_aire": np.nan, "d6_cobertura": "SIN_DATO",
         "indice_completitud_drivers": 5 / 6, COLUMNA_TARGET: 0.0},
    ])

    agg, _ = agregar_a_municipio_nivel(features, grupo)
    assert agg["d6_aire"].iloc[0] == pytest.approx(0.8), "la ausencia arrastró el promedio"
    assert agg["d6_cobertura_frac"].iloc[0] == pytest.approx(0.5)
    assert agg["d6_cobertura"].iloc[0] == "OK"


def test_la_fraccion_de_cobertura_esta_acotada(agregado) -> None:
    agg, _ = agregado
    for driver in DRIVERS:
        col = agg[f"{driver.split('_')[0]}_cobertura_frac"]
        assert (col >= 0).all() and (col <= 1).all()


def test_sin_ninguna_escuela_con_dato_la_bandera_es_sin_dato(agregado) -> None:
    """El enum del contrato original se conserva y es coherente con la fracción."""
    agg, _ = agregado
    for driver in DRIVERS:
        prefijo = driver.split("_")[0]
        sin_dato = agg[f"{prefijo}_cobertura"] == "SIN_DATO"
        assert (agg.loc[sin_dato, f"{prefijo}_cobertura_frac"] == 0).all()
        assert agg.loc[sin_dato, driver].isna().all()


# --------------------------------------------------------------------------- objetivo


def test_une_el_objetivo_de_la_serie(agregado) -> None:
    agg, _ = agregado
    final = unir_target(agg, _serie_simulada(agg))
    assert len(final) == len(agg)
    assert COLUMNA_TARGET in final.columns


def test_un_grupo_sin_objetivo_queda_fuera_y_no_se_rellena(agregado) -> None:
    """Entrenar contra un cero inventado es peor que tener menos filas."""
    agg, _ = agregado
    serie = _serie_simulada(agg).iloc[:-5]
    final = unir_target(agg, serie)
    assert len(final) == len(agg) - 5
    assert final[COLUMNA_TARGET].notna().all()


def test_falla_si_la_serie_no_trae_el_objetivo(agregado) -> None:
    agg, _ = agregado
    with pytest.raises(ValueError, match="no trae"):
        unir_target(agg, agg[list(LLAVE_AGREGADA)])


def test_falla_si_la_serie_no_cruza(agregado) -> None:
    """Claves de otro universo: municipios inexistentes, pero únicos entre sí.

    Se numeran para no crear llaves duplicadas, que dispararían la validación `one_to_one` del
    merge antes de llegar a la comprobación de cruce.
    """
    agg, _ = agregado
    ajena = _serie_simulada(agg)
    ajena = ajena.assign(cve_mun=[f"99{i:03d}" for i in range(len(ajena))])
    with pytest.raises(ValueError, match="no cruzó"):
        unir_target(agg, ajena)


def test_falla_si_la_serie_trae_llaves_duplicadas(agregado) -> None:
    """Una serie con dos filas para el mismo municipio×nivel×ciclo es un defecto de origen."""
    agg, _ = agregado
    serie = _serie_simulada(agg)
    duplicada = pd.concat([serie, serie.head(1)], ignore_index=True)
    with pytest.raises(Exception, match="not a one-to-one merge"):
        unir_target(agg, duplicada)


# --------------------------------------------------------------------------- integración


def test_el_agregado_admite_particion_temporal(agregado) -> None:
    """El punto de DEC-007: que el objetivo sea validable con partición temporal."""
    agg, _ = agregado
    final = unir_target(agg, _serie_simulada(agg))
    entrena, prueba = dividir_por_ciclo(final, n_ciclos_prueba=1)
    assert not entrena.empty and not prueba.empty
    assert set(entrena["id_ciclo"]) & set(prueba["id_ciclo"]) == set()
