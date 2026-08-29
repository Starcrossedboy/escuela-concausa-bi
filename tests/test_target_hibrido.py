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
from src.modelos.particion_temporal import (
    _anio_inicial,
    ciclos_ordenados,
    dividir_por_ciclo,
)
from src.modelos.target_hibrido import (
    LLAVE_AGREGADA,
    agregar_a_municipio_nivel,
    cargar_dimension,
    unir_target,
    variacion_desde_serie,
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


# ------------------------------------------------- variación desde la serie histórica (DEC-007)


def _serie(filas: list[tuple[str, str, str, int]]) -> pd.DataFrame:
    """Serie con el contrato de `gold.matricula_municipio_nivel`."""
    return pd.DataFrame(filas, columns=["cve_mun", "nivel", "id_ciclo", "matricula_total"])


def test_calcula_la_variacion_proporcional_contra_el_ciclo_anterior() -> None:
    serie = _serie([
        ("09001", "PRIMARIA", "2022-2023", 1000),
        ("09001", "PRIMARIA", "2023-2024", 900),
    ])
    salida = variacion_desde_serie(serie)

    assert len(salida) == 1
    assert salida[COLUMNA_TARGET].iloc[0] == pytest.approx(-0.10)
    assert salida["id_ciclo"].iloc[0] == "2023-2024"


def test_el_primer_ciclo_de_un_grupo_no_genera_variacion() -> None:
    """Sin ciclo previo no hay contra qué comparar: la fila no se emite."""
    serie = _serie([("09001", "PRIMARIA", "2022-2023", 1000)])
    assert variacion_desde_serie(serie).empty


def test_no_compara_a_traves_de_un_hueco_de_ciclos() -> None:
    """Si falta 2022-2023, comparar 2023-2024 contra 2021-2022 mediría dos años como si fuera uno."""
    serie = _serie([
        ("09001", "PRIMARIA", "2021-2022", 1000),
        ("09001", "PRIMARIA", "2023-2024", 500),
    ])
    assert variacion_desde_serie(serie).empty


def test_un_grupo_que_desaparece_no_produce_una_caida_total() -> None:
    """Dejar de reportarse no es perder el 100% de la matrícula."""
    serie = _serie([
        ("09001", "PRIMARIA", "2022-2023", 1000),
        ("09001", "PRIMARIA", "2023-2024", 950),
        ("09002", "PRIMARIA", "2022-2023", 800),   # no aparece en 2023-2024
    ])
    salida = variacion_desde_serie(serie)

    assert set(salida["cve_mun"]) == {"09001"}
    assert (salida[COLUMNA_TARGET] > -1.0).all()


def test_cada_grupo_se_compara_solo_consigo_mismo() -> None:
    serie = _serie([
        ("09001", "PRIMARIA", "2022-2023", 1000),
        ("09001", "PRIMARIA", "2023-2024", 1100),
        ("09001", "SECUNDARIA", "2022-2023", 500),
        ("09001", "SECUNDARIA", "2023-2024", 400),
    ])
    salida = variacion_desde_serie(serie).set_index("nivel")[COLUMNA_TARGET]

    assert salida["PRIMARIA"] == pytest.approx(0.10)
    assert salida["SECUNDARIA"] == pytest.approx(-0.20)


def test_rechaza_una_serie_sin_las_columnas_del_contrato() -> None:
    with pytest.raises(ValueError, match="matricula_municipio_nivel"):
        variacion_desde_serie(pd.DataFrame({"cve_mun": ["09001"]}))


def test_rechaza_duplicados_por_grupo_y_ciclo() -> None:
    serie = _serie([
        ("09001", "PRIMARIA", "2023-2024", 1000),
        ("09001", "PRIMARIA", "2023-2024", 900),
    ])
    with pytest.raises(ValueError, match="más de una fila"):
        variacion_desde_serie(serie)


def test_rechaza_matricula_previa_cero() -> None:
    """Dividir entre cero daría un infinito que envenenaría el entrenamiento."""
    serie = _serie([
        ("09001", "PRIMARIA", "2022-2023", 0),
        ("09001", "PRIMARIA", "2023-2024", 100),
    ])
    with pytest.raises(ValueError, match="matrícula previa 0"):
        variacion_desde_serie(serie)


def test_la_salida_encaja_con_unir_target(agregado) -> None:
    """El circuito completo de DEC-007: serie histórica → variación → objetivo del agregado."""
    agg, _ = agregado
    llaves = agg[["cve_mun", "nivel", "id_ciclo"]].drop_duplicates()

    filas = []
    for (mun, niv), grupo in llaves.groupby(["cve_mun", "nivel"]):
        for i, ciclo in enumerate(sorted(grupo["id_ciclo"], key=_anio_inicial)):
            filas.append((mun, niv, ciclo, 1000 + i * 50))
    serie = _serie(filas)

    objetivo = variacion_desde_serie(serie)
    final = unir_target(agg, objetivo)

    assert not final.empty
    assert COLUMNA_TARGET in final.columns
    assert final[COLUMNA_TARGET].notna().all()


# ------------------------------------------------- cve_mun en el contrato (US-325)


@pytest.fixture
def features_con_cve_mun(features: pd.DataFrame, dimension: pd.DataFrame) -> pd.DataFrame:
    """Las features como quedan cuando el contrato publica `cve_mun` (cambio de C1 para US-325)."""
    return features.merge(dimension[["cct", "cve_mun"]], on="cct", how="left")


def test_agrega_igual_traiga_o_no_cve_mun_el_contrato(
    features: pd.DataFrame, features_con_cve_mun: pd.DataFrame, dimension: pd.DataFrame
) -> None:
    """El reporte de Diana: con `cve_mun` en ambos lados, pandas lo renombra y el `groupby` truena.

    La agregación no debe depender de qué lado aporta la clave; el resultado tiene que ser el mismo.
    """
    sin_columna, _ = agregar_a_municipio_nivel(features, dimension)
    con_columna, _ = agregar_a_municipio_nivel(features_con_cve_mun, dimension)

    assert "cve_mun" in con_columna.columns
    assert not any(c.endswith(("_x", "_y")) for c in con_columna.columns)
    pd.testing.assert_frame_equal(
        sin_columna.sort_values(list(LLAVE_AGREGADA)).reset_index(drop=True),
        con_columna.sort_values(list(LLAVE_AGREGADA)).reset_index(drop=True),
    )


def test_detecta_la_escuela_ausente_de_la_dimension_aunque_traiga_cve_mun(
    features_con_cve_mun: pd.DataFrame, dimension: pd.DataFrame
) -> None:
    """La trampa de tomar `cve_mun` de las features sin cambiar el detector de faltantes.

    Antes el hueco se detectaba con `cve_mun.isna()`. Si la clave llega desde las features, una
    escuela que no está en la dimensión la sigue trayendo: el `isna()` no la ve, y su `nivel` en
    NaN se cuela al `groupby`. Por eso el faltante se detecta con el indicador del merge.
    """
    huerfana = dimension["cct"].iloc[0]
    dimension_corta = dimension[dimension["cct"] != huerfana]

    agregado, resumen = agregar_a_municipio_nivel(features_con_cve_mun, dimension_corta)

    assert resumen.escuelas_sin_dimension > 0, "la escuela ausente tiene que contarse"
    assert not agregado["nivel"].isna().any(), "ningún nivel nulo puede llegar al agregado"


def test_el_espejo_acepta_el_contrato_antes_y_despues_del_cambio() -> None:
    """`extra='forbid'`: sin el campo, el espejo rechazaría las filas nuevas de la C1."""
    from src.modelos.contrato import FeaturesEscuela

    base = {
        "cct": "09DPR0001A",
        "id_ciclo": "2023-2024",
        **{d: 0.5 for d in DRIVERS},
        **{f"{d.split('_')[0]}_cobertura": "OK" for d in DRIVERS},
        "driver_dominante": "D1",
        "indice_completitud_drivers": 1.0,
        "target_variacion_matricula": -0.03,
    }

    assert FeaturesEscuela(**base).cve_mun is None
    assert FeaturesEscuela(**base, cve_mun="09002").cve_mun == "09002"
