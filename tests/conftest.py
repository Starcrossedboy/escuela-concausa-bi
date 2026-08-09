"""Configuración compartida de pytest.

Pone la raíz del repositorio en `sys.path` para poder importar `src.*` sin instalar el proyecto
como paquete (aún no hay `pyproject.toml`).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

FIXTURE_FEATURES = RAIZ / "tests" / "fixtures" / "features_escuela_mock.csv"


@pytest.fixture(scope="session")
def features() -> pd.DataFrame:
    """Fixture simulado de `gold.features_escuela` (datos 100% sintéticos)."""
    if not FIXTURE_FEATURES.exists():
        pytest.skip(
            f"Falta {FIXTURE_FEATURES}. Genéralo con: "
            "python -m src.modelos.generar_fixture"
        )
    return pd.read_csv(FIXTURE_FEATURES)
