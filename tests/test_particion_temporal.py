"""Pruebas de la partición temporal y del fixture de features (US-311).

La prueba que más importa aquí es `test_particion_aleatoria_es_rechazada`: convierte la regla
"partición temporal, nunca aleatoria" en algo que el CI puede hacer cumplir. Si alguien
—persona o IA— sustituye la partición por un `train_test_split` aleatorio, esta prueba falla.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.modelos.contrato import DRIVERS, Cobertura, columna_cobertura, entidad_de_cct
from src.modelos.generar_fixture import CICLOS, SCOPE_ENTIDADES, validar_contra_contrato
from src.modelos.particion_temporal import (
    ParticionTemporal,
    ciclos_ordenados,
    dividir_por_ciclo,
    generar_backtesting,
    verificar_sin_fuga,
)

# --------------------------------------------------------------------------- fixture de datos


def test_fixture_cumple_el_contrato(features: pd.DataFrame) -> None:
    """Cada fila del fixture valida contra `FeaturesEscuela`."""
    assert validar_contra_contrato(features) == len(features)


def test_fixture_respeta_el_tope_de_filas(features: pd.DataFrame) -> None:
    """El plan de sprint §8 topa los fixtures en 500 filas."""
    assert len(features) <= 500


def test_grano_es_cct_por_ciclo(features: pd.DataFrame) -> None:
    """Una sola fila por CCT × ciclo, según el contrato §4.4."""
    assert not features.duplicated(subset=["cct", "id_ciclo"]).any()


def test_sin_dato_es_coherente_con_el_valor_nulo(features: pd.DataFrame) -> None:
    """`SIN_DATO` ⇔ valor nulo. Nunca cero, nunca nulo silencioso."""
    for driver in DRIVERS:
        cobertura = features[columna_cobertura(driver)]
        nulos = features[driver].isna()
        assert (nulos == (cobertura == Cobertura.SIN_DATO.value)).all(), (
            f"{driver}: la bandera de cobertura no concuerda con los nulos"
        )


def test_completitud_coincide_con_los_drivers_observados(features: pd.DataFrame) -> None:
    """`indice_completitud_drivers` = drivers con dato / 6."""
    observados = features[list(DRIVERS)].notna().sum(axis=1) / len(DRIVERS)
    assert (observados - features["indice_completitud_drivers"]).abs().max() < 1e-9


def test_ccts_pertenecen_al_alcance(features: pd.DataFrame) -> None:
    """Todas las escuelas caen en las 4 entidades del alcance."""
    entidades = {entidad_de_cct(cct) for cct in features["cct"].unique()}
    assert entidades <= set(SCOPE_ENTIDADES)


# --------------------------------------------------------------- partición y fuga temporal


def test_ciclos_se_ordenan_cronologicamente(features: pd.DataFrame) -> None:
    assert ciclos_ordenados(features) == list(CICLOS)


def test_division_simple_no_traslapa_ciclos(features: pd.DataFrame) -> None:
    """El ciclo de prueba no aparece en entrenamiento."""
    entrena, prueba = dividir_por_ciclo(features, n_ciclos_prueba=1)
    assert set(entrena["id_ciclo"]) & set(prueba["id_ciclo"]) == set()
    assert set(prueba["id_ciclo"]) == {CICLOS[-1]}
    assert len(entrena) + len(prueba) == len(features)
    verificar_sin_fuga(entrena, prueba)


def test_entrenamiento_precede_estrictamente_a_la_prueba(features: pd.DataFrame) -> None:
    """Todo ciclo de entrenamiento es anterior a todo ciclo de prueba."""
    entrena, prueba = dividir_por_ciclo(features, n_ciclos_prueba=2)
    assert max(entrena["id_ciclo"]) < min(prueba["id_ciclo"])


def test_particion_aleatoria_es_rechazada(features: pd.DataFrame) -> None:
    """Una partición aleatoria mezcla ciclos y debe detectarse como fuga.

    Ésta es la regla AC-003.3 convertida en prueba ejecutable.
    """
    barajado = features.sample(frac=1.0, random_state=0)
    corte = len(barajado) // 2
    entrena, prueba = barajado.iloc[:corte], barajado.iloc[corte:]

    with pytest.raises(ValueError, match="Fuga temporal"):
        verificar_sin_fuga(entrena, prueba)


def test_particion_con_orden_invertido_es_rechazada() -> None:
    """Entrenar con el futuro y evaluar con el pasado es fuga."""
    with pytest.raises(ValueError, match="Fuga temporal"):
        ParticionTemporal(
            ciclos_entrenamiento=("2023-2024",),
            ciclos_prueba=("2019-2020",),
        )


def test_particion_vacia_es_rechazada() -> None:
    with pytest.raises(ValueError, match="ciclos de prueba"):
        ParticionTemporal(ciclos_entrenamiento=("2019-2020",), ciclos_prueba=())


# ------------------------------------------------------------------------------ backtesting


def test_backtesting_genera_ventanas_crecientes(features: pd.DataFrame) -> None:
    """Cada ventana entrena con más pasado que la anterior y evalúa un ciclo posterior."""
    ventanas = list(generar_backtesting(features, n_ventanas=2))

    assert len(ventanas) == 2
    assert [v.ciclos_prueba for v in ventanas] == [(CICLOS[-2],), (CICLOS[-1],)]
    assert len(ventanas[0].ciclos_entrenamiento) < len(ventanas[1].ciclos_entrenamiento)

    for ventana in ventanas:
        entrena, prueba = ventana.aplicar(features)
        assert not entrena.empty and not prueba.empty
        verificar_sin_fuga(entrena, prueba)


def test_backtesting_falla_sin_ciclos_suficientes(features: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Se necesitan al menos"):
        list(generar_backtesting(features, n_ventanas=99))


def test_division_falla_sin_ciclos_suficientes(features: pd.DataFrame) -> None:
    un_ciclo = features[features["id_ciclo"] == CICLOS[0]]
    with pytest.raises(ValueError, match="Se necesitan al menos"):
        dividir_por_ciclo(un_ciclo, n_ciclos_prueba=1)
