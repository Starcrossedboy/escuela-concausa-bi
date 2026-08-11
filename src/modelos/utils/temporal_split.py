"""Utilidad de partición temporal walk-forward para modelos de series de tiempo escolares."""
from __future__ import annotations

import pandas as pd


def walk_forward_splits(
    df: pd.DataFrame,
    ciclo_col: str = "ciclo",
    n_folds: int = 4,
) -> list[tuple[pd.Index, pd.Index]]:
    """Genera índices de train/test con walk-forward de 1 ciclo.

    Garantiza que no haya fuga temporal: el test siempre es 1 ciclo posterior al train.

    Args:
        df: DataFrame con columna de ciclo escolar (e.g. "2022-23").
        ciclo_col: nombre de la columna de ciclo.
        n_folds: número de folds. El último fold usa el ciclo más reciente como test.

    Returns:
        Lista de tuplas (train_index, test_index) como índices de pandas.

    Example:
        >>> for train_idx, test_idx in walk_forward_splits(df, n_folds=4):
        ...     X_train = df.loc[train_idx]
        ...     X_test  = df.loc[test_idx]
    """
    ciclos_ordenados = sorted(df[ciclo_col].unique())

    if len(ciclos_ordenados) < n_folds + 1:
        raise ValueError(
            f"Se necesitan al menos {n_folds + 1} ciclos para {n_folds} folds. "
            f"Encontrados: {len(ciclos_ordenados)}"
        )

    primer_test_idx = len(ciclos_ordenados) - n_folds
    splits = []

    for fold in range(n_folds):
        test_ciclo = ciclos_ordenados[primer_test_idx + fold]
        train_ciclos = ciclos_ordenados[: primer_test_idx + fold]

        train_mask = df[ciclo_col].isin(train_ciclos)
        test_mask = df[ciclo_col] == test_ciclo

        splits.append((df.index[train_mask], df.index[test_mask]))

    return splits
