"""Pruebas de la publicación a Gold (US-313, TEST-006).

Usan SQLite en un archivo temporal: el CI no necesita Postgres, y el UPSERT se ejercita de verdad
(no se simula). El código es dialecto-aware, así que lo que se prueba aquí es la misma ruta que
corre contra Postgres.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest
from sqlalchemy import create_engine, select

from src.modelos.entrenar_ml01 import entrenar_y_evaluar
from src.modelos.entrenar_ml02 import entrenar_y_evaluar as entrenar_ml02
from src.modelos.entrenar_ml02 import generar_driver_dominante_proxy
from src.modelos.publicar_gold import (
    CODIGOS_DRIVER,
    RECOMENDACION_POR_DRIVER,
    PrediccionGold,
    Prioridad,
    _metadatos,
    construir_predicciones,
    construir_recomendaciones,
    construir_recomendaciones_ml02,
    escribir,
    prioridad_de_riesgo,
)
from src.modelos.riesgo import RIESGO_ESTABLE, RIESGO_UMBRAL

# --------------------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def modelo(features: pd.DataFrame):
    return entrenar_y_evaluar(features, n_ventanas=3).modelo


@pytest.fixture(scope="module")
def predicciones(features: pd.DataFrame, modelo) -> pd.DataFrame:
    return construir_predicciones(features, modelo, mlflow_run_id="run-de-prueba-000")


@pytest.fixture
def engine(tmp_path):
    """SQLite en archivo temporal; sin esquema, que SQLite no los maneja igual."""
    return create_engine(f"sqlite:///{tmp_path / 'gold.db'}")


# --------------------------------------------------------------------------- prioridad


def test_prioridad_usa_los_umbrales_ya_ratificados() -> None:
    """No inventa números: reutiliza las anclas de DOC-INDICE-RIESGO."""
    assert prioridad_de_riesgo(RIESGO_UMBRAL) is Prioridad.ALTA
    assert prioridad_de_riesgo(RIESGO_UMBRAL - 0.01) is Prioridad.MEDIA
    assert prioridad_de_riesgo(RIESGO_ESTABLE) is Prioridad.MEDIA
    assert prioridad_de_riesgo(RIESGO_ESTABLE - 0.01) is Prioridad.BAJA


def test_prioridad_cubre_los_extremos() -> None:
    assert prioridad_de_riesgo(1.0) is Prioridad.ALTA
    assert prioridad_de_riesgo(0.0) is Prioridad.BAJA


# --------------------------------------------------------------------------- predicciones


def test_predice_el_ciclo_mas_reciente(predicciones: pd.DataFrame, features: pd.DataFrame) -> None:
    """La pregunta de negocio es el próximo ciclo, no un ciclo histórico cualquiera."""
    assert predicciones["id_ciclo"].nunique() == 1
    assert predicciones["id_ciclo"].iloc[0] == max(features["id_ciclo"])


def test_una_fila_por_escuela(predicciones: pd.DataFrame, features: pd.DataFrame) -> None:
    assert len(predicciones) == features["cct"].nunique()
    assert not predicciones.duplicated(subset=["cct", "id_ciclo", "modelo"]).any()


def test_conserva_la_variacion_cruda_y_el_riesgo(predicciones: pd.DataFrame) -> None:
    """DEC-005: `valor` guarda la unidad original y `indice_riesgo` la versión acotada."""
    assert (predicciones["indice_riesgo"] >= 0).all()
    assert (predicciones["indice_riesgo"] <= 1).all()
    # La variación cruda no está acotada: es justamente lo que `valor` preserva.
    assert predicciones["valor"].min() < 0


def test_probabilidad_es_nula_en_una_regresion(predicciones: pd.DataFrame) -> None:
    """ML-01 no produce probabilidad: NULL explícito, nunca 0."""
    assert predicciones["probabilidad"].isna().all()


def test_cada_fila_valida_contra_el_contrato(predicciones: pd.DataFrame) -> None:
    for fila in predicciones.to_dict(orient="records"):
        PrediccionGold(**fila)


def test_falla_si_el_ciclo_objetivo_no_existe(features: pd.DataFrame, modelo) -> None:
    with pytest.raises(ValueError, match="no está en las features"):
        construir_predicciones(features, modelo, "run", id_ciclo_objetivo="2099-2100")


# --------------------------------------------------------------------------- recomendaciones


def test_recomendaciones_solo_para_escuelas_con_driver(predicciones: pd.DataFrame) -> None:
    """Sin ML-02 no hay driver; no se inventa uno para las escuelas restantes."""
    ccts = predicciones["cct"].head(3).tolist()
    drivers = dict(zip(ccts, ["D1", "D2", "D5"], strict=True))

    recomendaciones = construir_recomendaciones(predicciones, drivers)

    assert len(recomendaciones) == 3
    assert set(recomendaciones["cct"]) == set(ccts)


def test_el_texto_corresponde_al_driver(predicciones: pd.DataFrame) -> None:
    cct = predicciones["cct"].iloc[0]
    recomendaciones = construir_recomendaciones(predicciones, {cct: "D2"})
    assert recomendaciones["recomendacion"].iloc[0] == RECOMENDACION_POR_DRIVER["D2"]


def test_igual_riesgo_y_distinto_driver_producen_recomendaciones_distintas(
    predicciones: pd.DataFrame,
) -> None:
    mismas = predicciones.head(2).copy()
    mismas["indice_riesgo"] = 0.75
    drivers = dict(zip(mismas["cct"], ["D1", "D2"], strict=True))

    recomendaciones = construir_recomendaciones(mismas, drivers)

    assert recomendaciones["prioridad"].nunique() == 1
    assert recomendaciones["recomendacion"].nunique() == 2


def test_rechaza_drivers_fuera_del_catalogo(predicciones: pd.DataFrame) -> None:
    cct = predicciones["cct"].iloc[0]
    with pytest.raises(ValueError, match="fuera del catálogo"):
        construir_recomendaciones(predicciones, {cct: "D9"})


def test_conecta_ml02_con_recomendaciones_del_mismo_ciclo(
    predicciones: pd.DataFrame,
    features: pd.DataFrame,
) -> None:
    features_ml02 = features.copy()
    features_ml02["driver_dominante_proxy"] = generar_driver_dominante_proxy(features_ml02)
    modelo_ml02 = entrenar_ml02(features_ml02, n_ventanas=3).modelo

    recomendaciones = construir_recomendaciones_ml02(
        predicciones,
        features_ml02,
        modelo_ml02,
    )

    assert len(recomendaciones) == len(predicciones)
    assert set(recomendaciones["cct"]) == set(predicciones["cct"])
    assert set(recomendaciones["id_ciclo"]) == set(predicciones["id_ciclo"])
    assert set(recomendaciones["driver_dominante"]) <= set(CODIGOS_DRIVER)


def test_el_catalogo_cubre_los_seis_drivers() -> None:
    assert set(RECOMENDACION_POR_DRIVER) == set(CODIGOS_DRIVER)


def test_catalogo_coincide_con_el_de_la_api() -> None:
    """Anti-deriva: si la Célula 4 cambia su catálogo, esto falla y se reconcilia.

    El texto prescriptivo es dato de negocio de la Célula 3, pero hoy vive duplicado en
    `src/api/mock_data.py` (US-401). Mientras esa duplicación exista, esta prueba la vigila.
    """
    from src.api.mock_data import RECOMENDACION_POR_DRIVER as catalogo_api

    assert RECOMENDACION_POR_DRIVER == catalogo_api


# --------------------------------------------------------------------------- escritura


def test_escribe_las_filas_en_la_tabla(predicciones: pd.DataFrame, engine) -> None:
    metadata, tabla, _ = _metadatos(esquema=None)
    escritas = escribir(predicciones, tabla, engine, metadata)

    assert escritas == len(predicciones)
    with engine.connect() as conexion:
        assert len(conexion.execute(select(tabla)).fetchall()) == len(predicciones)


def test_es_idempotente(predicciones: pd.DataFrame, engine) -> None:
    """Correr el job dos veces deja las mismas filas, no el doble."""
    metadata, tabla, _ = _metadatos(esquema=None)
    escribir(predicciones, tabla, engine, metadata)
    escribir(predicciones, tabla, engine, metadata)

    with engine.connect() as conexion:
        assert len(conexion.execute(select(tabla)).fetchall()) == len(predicciones)


def test_el_upsert_actualiza_en_vez_de_duplicar(predicciones: pd.DataFrame, engine) -> None:
    """Tras reentrenar, la segunda corrida pisa el valor y el run_id de la primera."""
    metadata, tabla, _ = _metadatos(esquema=None)
    escribir(predicciones, tabla, engine, metadata)

    reentrenado = predicciones.copy()
    reentrenado["valor"] = -0.5
    reentrenado["indice_riesgo"] = 0.99
    reentrenado["mlflow_run_id"] = "run-nuevo-111"
    reentrenado["generado_at"] = datetime.now(tz=UTC)
    escribir(reentrenado, tabla, engine, metadata)

    with engine.connect() as conexion:
        filas = conexion.execute(select(tabla)).fetchall()
    assert len(filas) == len(predicciones)
    assert {f.mlflow_run_id for f in filas} == {"run-nuevo-111"}
    assert all(f.indice_riesgo == pytest.approx(0.99) for f in filas)


def test_escribir_vacio_no_falla(engine) -> None:
    metadata, tabla, _ = _metadatos(esquema=None)
    assert escribir(pd.DataFrame(), tabla, engine, metadata) == 0


def test_publica_recomendaciones(predicciones: pd.DataFrame, engine) -> None:
    metadata, _, tabla = _metadatos(esquema=None)
    cct = predicciones["cct"].iloc[0]
    recomendaciones = construir_recomendaciones(predicciones, {cct: "D3"})

    assert escribir(recomendaciones, tabla, engine, metadata) == 1
    with engine.connect() as conexion:
        fila = conexion.execute(select(tabla)).fetchone()
    assert fila.driver_dominante == "D3"
    assert fila.prioridad in {p.value for p in Prioridad}
