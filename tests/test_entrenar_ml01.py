"""Pruebas del entrenamiento y backtesting de ML-01 (US-311, TEST-005).

Sólo ejercitan `entrenar_y_evaluar`, que es puro respecto a MLflow: el CI no necesita levantar
tracking ni escribir artefactos. El registro se valida a mano y queda evidenciado en el DevLog.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.modelos.contrato import DRIVERS
from src.modelos.entrenar_ml01 import (
    COLUMNA_TARGET,
    MetricasVentana,
    _matriz,
    cargar_features,
    cargar_features_desde_gold,
    entrenar_y_evaluar,
)
from src.modelos.generar_fixture import SCOPE_ENTIDADES
from src.modelos.particion_temporal import ParticionTemporal, _anio_inicial

# --------------------------------------------------------------------------- carga


def test_carga_el_fixture_por_defecto(features: pd.DataFrame) -> None:
    assert len(features) == 400
    assert COLUMNA_TARGET in features.columns


def test_falla_si_no_existe_la_ruta() -> None:
    with pytest.raises(FileNotFoundError, match="generar_fixture"):
        cargar_features(Path("no/existe/features.csv"))


def test_falla_si_la_tabla_no_cumple_el_contrato(tmp_path: Path) -> None:
    """Si la Célula 1 publica una tabla sin las columnas acordadas, se detecta al cargar."""
    ruta = tmp_path / "incompleta.csv"
    pd.DataFrame({"cct": ["09DPR0001X"], "id_ciclo": ["2023-2024"]}).to_csv(ruta, index=False)
    with pytest.raises(ValueError, match="no cumple el contrato"):
        cargar_features(ruta)


# --------------------------------------------------------------------------- backtesting


@pytest.fixture(scope="module")
def resultado(features: pd.DataFrame):
    return entrenar_y_evaluar(features, n_ventanas=3)


def test_genera_las_ventanas_pedidas(resultado) -> None:
    assert len(resultado.ventanas) == 3


def test_ninguna_ventana_tiene_fuga_temporal(resultado) -> None:
    """Todo ciclo de entrenamiento es anterior a todo ciclo de prueba, en cada ventana."""
    for ventana in resultado.ventanas:
        ultimo_train = max(_anio_inicial(c) for c in ventana.particion.ciclos_entrenamiento)
        primero_test = min(_anio_inicial(c) for c in ventana.particion.ciclos_prueba)
        assert ultimo_train < primero_test


def test_el_entrenamiento_crece_con_cada_ventana(resultado) -> None:
    tamanos = [v.n_entrena for v in resultado.ventanas]
    assert tamanos == sorted(tamanos)
    assert tamanos[0] < tamanos[-1]


def test_le_gana_al_baseline_en_todas_las_ventanas(resultado) -> None:
    """Si el modelo no supera a predecir la media, no hay modelo."""
    for ventana in resultado.ventanas:
        assert ventana.mae < ventana.mae_baseline
        assert ventana.mejora_sobre_baseline > 0


def test_las_metricas_son_finitas_y_positivas(resultado) -> None:
    for ventana in resultado.ventanas:
        assert np.isfinite([ventana.mae, ventana.rmse, ventana.mae_baseline]).all()
        assert ventana.mae > 0
        assert ventana.rmse >= ventana.mae  # RMSE nunca es menor que MAE


def test_la_ventana_de_produccion_evalua_el_ciclo_mas_reciente(
    resultado, features: pd.DataFrame
) -> None:
    ciclo_mas_reciente = max(features["id_ciclo"], key=_anio_inicial)
    assert resultado.ventana_produccion.particion.ciclos_prueba == (ciclo_mas_reciente,)


def test_agrega_metricas_como_promedio_y_desviacion(resultado) -> None:
    """ADR-003 exige reportar promedio ± desviación de las ventanas."""
    maes = [v.mae for v in resultado.ventanas]
    assert resultado.mae_promedio == pytest.approx(float(np.mean(maes)))
    assert resultado.mae_desviacion == pytest.approx(float(np.std(maes)))


# --------------------------------------------------------------------------- SIN_DATO


def test_no_imputa_los_sin_dato(features: pd.DataFrame) -> None:
    """Regla 4: los `SIN_DATO` llegan al modelo como `NaN`, nunca como cero.

    Compara la matriz que el pipeline entrega al estimador contra la fuente: si alguien mete un
    `fillna(0)` (o cualquier imputación) dentro de `_matriz`, el conteo de nulos cae y esto falla.
    """
    nulos_origen = int(features[list(DRIVERS)].isna().to_numpy().sum())
    assert nulos_origen > 0, "el fixture debería traer SIN_DATO"

    matriz = _matriz(features)
    assert int(matriz.isna().to_numpy().sum()) == nulos_origen, (
        "el pipeline imputó valores ausentes; los SIN_DATO deben llegar como NaN"
    )


def test_el_modelo_predice_con_drivers_ausentes(resultado, features: pd.DataFrame) -> None:
    """Una escuela sin dato de agua ni de aire sigue recibiendo predicción."""
    fila = features[list(DRIVERS)].head(1).copy()
    fila.loc[:, ["d5_agua", "d6_aire"]] = np.nan
    prediccion = resultado.modelo.predict(fila)
    assert np.isfinite(prediccion).all()


# --------------------------------------------------------------------------- error por entidad


def test_desglosa_el_error_por_entidad(resultado) -> None:
    """Insumo de US-312: el análisis de error por entidad."""
    tabla = resultado.error_por_entidad
    assert set(tabla.columns) == {"entidad", "escuelas", "mae"}
    assert set(tabla["entidad"]) <= set(SCOPE_ENTIDADES)
    assert (tabla["mae"] >= 0).all()
    assert tabla["mae"].is_monotonic_decreasing  # ordenado de peor a mejor


# --------------------------------------------------------------------------- métricas


def test_mejora_sobre_baseline_es_una_fraccion() -> None:
    ventana = MetricasVentana(
        particion=ParticionTemporal(("2019-2020",), ("2020-2021",)),
        mae=0.5,
        rmse=0.6,
        mae_baseline=1.0,
        n_entrena=10,
        n_prueba=5,
    )
    assert ventana.mejora_sobre_baseline == pytest.approx(0.5)


def test_mejora_sobre_baseline_es_negativa_si_el_modelo_es_peor() -> None:
    ventana = MetricasVentana(
        particion=ParticionTemporal(("2019-2020",), ("2020-2021",)),
        mae=2.0,
        rmse=2.5,
        mae_baseline=1.0,
        n_entrena=10,
        n_prueba=5,
    )
    assert ventana.mejora_sobre_baseline < 0


# ------------------------------------------------- lectura desde Gold (BUG-013)


def _engine_tmp(tmp_path):
    from sqlalchemy import create_engine

    return create_engine(f"sqlite:///{tmp_path / 'gold.db'}")


def test_lee_las_features_desde_la_tabla_de_gold(features: pd.DataFrame, tmp_path) -> None:
    """El camino que cierra BUG-013: publicar desde `gold.features_escuela`, no del fixture."""
    engine = _engine_tmp(tmp_path)
    features.to_sql("features_escuela", engine, index=False)

    leidas = cargar_features_desde_gold(engine, esquema=None)

    assert len(leidas) == len(features)
    assert set(leidas["id_ciclo"]) == set(features["id_ciclo"])


def test_falla_con_mensaje_accionable_si_gold_no_esta_materializada(tmp_path) -> None:
    """El error debe decir qué hacer, no sólo que algo no existe."""
    with pytest.raises(ValueError, match="dbt run"):
        cargar_features_desde_gold(_engine_tmp(tmp_path), esquema=None)


def test_falla_si_la_tabla_de_gold_esta_vacia(features: pd.DataFrame, tmp_path) -> None:
    """Una tabla vacía es distinto de una ausente, y se avisa distinto."""
    engine = _engine_tmp(tmp_path)
    features.head(0).to_sql("features_escuela", engine, index=False)

    with pytest.raises(ValueError, match="está vacía"):
        cargar_features_desde_gold(engine, esquema=None)


def test_falla_si_gold_no_cumple_el_contrato(features: pd.DataFrame, tmp_path) -> None:
    """Si la C1 publica la tabla sin una columna acordada, se detecta al leer."""
    engine = _engine_tmp(tmp_path)
    features.drop(columns=["d1_pobreza"]).to_sql("features_escuela", engine, index=False)

    with pytest.raises(ValueError, match="d1_pobreza"):
        cargar_features_desde_gold(engine, esquema=None)


# ------------------------------- driver sin ningún dato (caso real de gold.features_escuela)


def test_un_driver_sin_ningun_dato_no_rompe_el_entrenamiento(features: pd.DataFrame) -> None:
    """Reproduce el fallo del Gold real: D5 (agua) está 100% en SIN_DATO porque DS-06 no llega.

    Sin este manejo, `HistGradientBoostingRegressor` falla dentro del binning con
    `window shape cannot be larger than input array shape`, un error que no dice nada de la causa.
    """
    sin_agua = features.copy()
    sin_agua["d5_agua"] = np.nan
    sin_agua["d5_cobertura"] = "SIN_DATO"

    resultado = entrenar_y_evaluar(sin_agua, n_ventanas=2)

    assert "d5_agua" in resultado.drivers_excluidos
    assert "d5_agua" not in resultado.drivers_usados
    assert len(resultado.drivers_usados) == 5
    assert all(np.isfinite(v.mae) for v in resultado.ventanas)


def test_la_exclusion_de_drivers_queda_registrada(features: pd.DataFrame) -> None:
    """Excluir un driver nunca es silencioso: es un hallazgo del proyecto, no un detalle."""
    resultado = entrenar_y_evaluar(features, n_ventanas=2)
    assert resultado.drivers_excluidos == ()
    assert len(resultado.drivers_usados) == 6


def test_una_columna_constante_si_es_utilizable(features: pd.DataFrame) -> None:
    """Sin varianza no es lo mismo que sin datos: el modelo puede ignorarla por su cuenta."""
    constante = features.copy()
    constante["d6_aire"] = 0.5

    resultado = entrenar_y_evaluar(constante, n_ventanas=2)

    assert "d6_aire" in resultado.drivers_usados


def test_falla_con_mensaje_claro_si_ningun_driver_tiene_datos(features: pd.DataFrame) -> None:
    vacio = features.copy()
    for driver in DRIVERS:
        vacio[driver] = np.nan

    with pytest.raises(ValueError, match="Ningún driver tiene datos"):
        entrenar_y_evaluar(vacio, n_ventanas=2)


def test_se_puede_publicar_aunque_falte_un_driver(features: pd.DataFrame) -> None:
    """El circuito completo con un driver ausente: entrenar y construir las filas de Gold."""
    from src.modelos.publicar_gold import construir_predicciones

    sin_agua = features.copy()
    sin_agua["d5_agua"] = np.nan

    resultado = entrenar_y_evaluar(sin_agua, n_ventanas=2)
    filas = construir_predicciones(sin_agua, resultado.modelo, "run-sin-d5")

    assert len(filas) == sin_agua["cct"].nunique()
    assert filas["indice_riesgo"].between(0, 1).all()


def test_un_driver_vacio_solo_dentro_de_la_ventana_no_rompe(features: pd.DataFrame) -> None:
    """El caso que sobrevivió al primer arreglo: cobertura global sí, cobertura por ventana no.

    D6 (aire) llega por la interpolación IDW de US-105 y sólo cubre el ciclo más reciente. Mirado
    sobre el conjunto completo el driver "tiene datos", pero el tramo con el que se entrena está
    entero en `NaN` — y sklearn falla al binear con el mismo error que no dice por qué.
    """
    tres = features[features["id_ciclo"].isin(["2021-2022", "2022-2023", "2023-2024"])].copy()
    tres.loc[tres["id_ciclo"] != "2023-2024", "d6_aire"] = np.nan

    assert tres["d6_aire"].notna().any(), "globalmente el driver sí tiene datos"

    resultado = entrenar_y_evaluar(tres, n_ventanas=1)

    assert "d6_aire" in resultado.drivers_excluidos
    assert all(np.isfinite(v.mae) for v in resultado.ventanas)


def test_falla_si_la_ventana_de_entrenamiento_queda_sin_drivers(features: pd.DataFrame) -> None:
    """El mensaje debe nombrar la ventana, no sólo decir que faltan datos."""
    tres = features[features["id_ciclo"].isin(["2021-2022", "2022-2023", "2023-2024"])].copy()
    for driver in DRIVERS:
        tres.loc[tres["id_ciclo"] != "2023-2024", driver] = np.nan

    with pytest.raises(ValueError, match="ventana de entrenamiento"):
        entrenar_y_evaluar(tres, n_ventanas=1)
