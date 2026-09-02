"""Partición temporal y backtesting para ML-01 (US-311).

Regla no negociable del proyecto (`vault/15_ML_Models/_index.md`, AC-003.3): la validación de ML-01 y
ML-02 usa partición **temporal, nunca aleatoria**. Una partición aleatoria mete filas del ciclo
2023-2024 en entrenamiento y filas del mismo ciclo en prueba: el modelo ve el futuro y la métrica
sale inflada. Es fuga de información, y con una llave CCT × ciclo es especialmente fácil de
cometer sin darse cuenta.

Este módulo no entrena nada. Sólo decide **qué ciclos** van a entrenamiento y cuáles a prueba, y
ofrece una verificación explícita de que no hay traslape. El entrenamiento vive en el script de
ML-01.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pandas as pd

COLUMNA_CICLO = "id_ciclo"


def _anio_inicial(id_ciclo: str) -> int:
    """Año con el que arranca un ciclo escolar: '2023-2024' -> 2023."""
    try:
        return int(id_ciclo.split("-")[0])
    except (ValueError, IndexError) as exc:
        raise ValueError(
            f"id_ciclo con formato inesperado: {id_ciclo!r}. Se espera 'AAAA-AAAA'."
        ) from exc


def ciclos_ordenados(df: pd.DataFrame, columna_ciclo: str = COLUMNA_CICLO) -> list[str]:
    """Ciclos únicos del DataFrame, del más antiguo al más reciente."""
    if columna_ciclo not in df.columns:
        raise KeyError(f"Falta la columna {columna_ciclo!r} en el DataFrame.")
    return sorted(df[columna_ciclo].unique(), key=_anio_inicial)


@dataclass(frozen=True)
class ParticionTemporal:
    """Un corte temporal: qué ciclos entrenan y qué ciclos evalúan.

    Inmutable a propósito: una partición ya usada para reportar una métrica no debe poder
    modificarse después.
    """

    ciclos_entrenamiento: tuple[str, ...]
    ciclos_prueba: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.ciclos_entrenamiento:
            raise ValueError("La partición no tiene ciclos de entrenamiento.")
        if not self.ciclos_prueba:
            raise ValueError("La partición no tiene ciclos de prueba.")
        ultimo_train = max(_anio_inicial(c) for c in self.ciclos_entrenamiento)
        primero_test = min(_anio_inicial(c) for c in self.ciclos_prueba)
        if ultimo_train >= primero_test:
            raise ValueError(
                "Fuga temporal: el entrenamiento llega hasta "
                f"{ultimo_train} y la prueba empieza en {primero_test}. "
                "El entrenamiento debe terminar estrictamente antes de la prueba."
            )

    def aplicar(
        self, df: pd.DataFrame, columna_ciclo: str = COLUMNA_CICLO
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Divide el DataFrame en (entrenamiento, prueba) según esta partición."""
        entrena = df[df[columna_ciclo].isin(self.ciclos_entrenamiento)].copy()
        prueba = df[df[columna_ciclo].isin(self.ciclos_prueba)].copy()
        return entrena, prueba

    def __str__(self) -> str:
        return (
            f"entrena[{self.ciclos_entrenamiento[0]}…{self.ciclos_entrenamiento[-1]}] "
            f"-> prueba[{', '.join(self.ciclos_prueba)}]"
        )


def dividir_por_ciclo(
    df: pd.DataFrame,
    n_ciclos_prueba: int = 1,
    columna_ciclo: str = COLUMNA_CICLO,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Corte temporal simple: los últimos `n_ciclos_prueba` ciclos son la prueba.

    Es la partición por defecto para reportar el MAE/RMSE de ML-01: entrena con todo el pasado
    disponible y evalúa contra el ciclo más reciente, que es exactamente la pregunta de negocio
    ("¿qué escuelas van a perder matrícula el próximo ciclo?").

    Args:
        df: features con una columna de ciclo.
        n_ciclos_prueba: cuántos ciclos finales se reservan para prueba.
        columna_ciclo: nombre de la columna de ciclo.

    Returns:
        Tupla (entrenamiento, prueba).

    Raises:
        ValueError: si no quedan ciclos suficientes para entrenar y evaluar.
    """
    ciclos = ciclos_ordenados(df, columna_ciclo)
    if len(ciclos) < n_ciclos_prueba + 1:
        raise ValueError(
            f"Se necesitan al menos {n_ciclos_prueba + 1} ciclos para partir con "
            f"n_ciclos_prueba={n_ciclos_prueba}; el DataFrame tiene {len(ciclos)}: {ciclos}."
        )
    particion = ParticionTemporal(
        ciclos_entrenamiento=tuple(ciclos[:-n_ciclos_prueba]),
        ciclos_prueba=tuple(ciclos[-n_ciclos_prueba:]),
    )
    return particion.aplicar(df, columna_ciclo)


def ventanas_posibles(
    df: pd.DataFrame,
    min_ciclos_entrenamiento: int = 2,
    columna_ciclo: str = COLUMNA_CICLO,
) -> int:
    """Cuántas ventanas de backtesting admiten los ciclos disponibles.

    Un default fijo no sirve: el fixture tiene 5 ciclos y admite 3 ventanas, pero
    `gold.features_escuela` real tiene 3 —uno se consume como referencia del target— y admite 1.
    Pedir más de las posibles falla con un error correcto pero evitable.

    Returns:
        El máximo de ventanas, siempre al menos 1.

    Raises:
        ValueError: si no hay ciclos suficientes ni para una ventana.
    """
    ciclos = ciclos_ordenados(df, columna_ciclo)
    posibles = len(ciclos) - min_ciclos_entrenamiento
    if posibles < 1:
        raise ValueError(
            f"Con {len(ciclos)} ciclos no se puede hacer backtesting: se necesitan al menos "
            f"{min_ciclos_entrenamiento + 1} (entrenar con {min_ciclos_entrenamiento} y evaluar "
            f"con 1). Ciclos disponibles: {ciclos}."
        )
    return posibles


def generar_backtesting(
    df: pd.DataFrame,
    n_ventanas: int = 2,
    min_ciclos_entrenamiento: int = 2,
    columna_ciclo: str = COLUMNA_CICLO,
) -> Iterator[ParticionTemporal]:
    """Genera ventanas de backtesting *walk-forward* (ventana de entrenamiento creciente).

    Con ciclos [c1, c2, c3, c4, c5], `n_ventanas=2` produce:

        [c1, c2, c3]       -> [c4]
        [c1, c2, c3, c4]   -> [c5]

    El entrenamiento sólo crece hacia el pasado inmediato: nunca se reentrena con datos
    posteriores al ciclo evaluado. AC-003.3 exige backtesting, no un solo corte.

    Args:
        df: features con una columna de ciclo.
        n_ventanas: cuántas ventanas generar, terminando en el ciclo más reciente.
        min_ciclos_entrenamiento: mínimo de ciclos en la primera ventana de entrenamiento.
        columna_ciclo: nombre de la columna de ciclo.

    Yields:
        Cada `ParticionTemporal`, de la ventana más antigua a la más reciente.

    Raises:
        ValueError: si no hay ciclos suficientes para las ventanas pedidas.
    """
    ciclos = ciclos_ordenados(df, columna_ciclo)
    necesarios = min_ciclos_entrenamiento + n_ventanas
    if len(ciclos) < necesarios:
        raise ValueError(
            f"Se necesitan al menos {necesarios} ciclos para {n_ventanas} ventana(s) con "
            f"min_ciclos_entrenamiento={min_ciclos_entrenamiento}; hay {len(ciclos)}: {ciclos}."
        )
    for corte in range(len(ciclos) - n_ventanas, len(ciclos)):
        yield ParticionTemporal(
            ciclos_entrenamiento=tuple(ciclos[:corte]),
            ciclos_prueba=(ciclos[corte],),
        )


def verificar_sin_fuga(
    entrena: pd.DataFrame,
    prueba: pd.DataFrame,
    columna_ciclo: str = COLUMNA_CICLO,
) -> None:
    """Falla si la partición tiene fuga temporal o solapamiento de ciclos.

    Pensado para llamarse **dentro del script de entrenamiento**, justo antes de `fit()`. Es la
    red de seguridad que convierte la regla escrita en una garantía ejecutable.

    Raises:
        ValueError: si algún ciclo aparece en ambos lados o si el orden temporal se rompe.
    """
    ciclos_entrena = set(entrena[columna_ciclo].unique())
    ciclos_prueba = set(prueba[columna_ciclo].unique())

    traslape = ciclos_entrena & ciclos_prueba
    if traslape:
        raise ValueError(
            f"Fuga temporal: los ciclos {sorted(traslape)} están en entrenamiento y en prueba. "
            "¿Se usó una partición aleatoria?"
        )
    if not ciclos_entrena or not ciclos_prueba:
        raise ValueError("Entrenamiento o prueba quedaron vacíos tras la partición.")

    ultimo_train = max(_anio_inicial(c) for c in ciclos_entrena)
    primero_test = min(_anio_inicial(c) for c in ciclos_prueba)
    if ultimo_train >= primero_test:
        raise ValueError(
            f"Fuga temporal: entrenamiento hasta {ultimo_train}, prueba desde {primero_test}."
        )
