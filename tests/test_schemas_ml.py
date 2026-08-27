"""Pruebas del contrato de datos API ↔ modelos (US-415, TEST-XXX pendiente de numerar en TEST-Register).

Verifica que `src/api/schemas_ml.py` reutiliza el contrato canónico de `FeaturesEscuela` sin
duplicarlo, que las 3 salidas crudas validan sus formas, y que `PrediccionModelos` rechaza
salidas desalineadas (distinto cct o ciclo entre ML-01/02/03) -- el mismo tipo de invariante que
`gold.predicciones` hace cumplir con su `CHECK` (`Publicacion_Gold.md` §2).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.api.schemas_ml import (
    ML01Salida,
    ML02Salida,
    ML03Salida,
    PrediccionModelos,
)
from src.modelos.contrato import FeaturesEscuela as FeaturesEscuelaCanonico

CCT = "09DPR0001A"
CICLO = "2024-2025"


def test_features_escuela_es_el_contrato_canonico() -> None:
    """`schemas_ml` reexporta el `FeaturesEscuela` de `src.modelos.contrato`, no uno propio.

    Si algún día alguien redefine `FeaturesEscuela` dentro de `src/api`, esta prueba lo detecta
    como divergencia de identidad, no solo de forma -- el mismo espíritu que
    `tests/test_contrato_features.py` aplica contra el dbt real de la Célula 1.
    """
    from src.api.schemas_ml import FeaturesEscuela

    assert FeaturesEscuela is FeaturesEscuelaCanonico


def test_ml01_salida_valida() -> None:
    salida = ML01Salida(cct=CCT, id_ciclo=CICLO, variacion_predicha=-0.05, mlflow_run_id="abc123")
    assert salida.variacion_predicha == -0.05


def test_ml01_salida_rechaza_cct_corto() -> None:
    with pytest.raises(ValidationError):
        ML01Salida(cct="123", id_ciclo=CICLO, variacion_predicha=0.0, mlflow_run_id="abc123")


def test_ml02_salida_valida() -> None:
    salida = ML02Salida(cct=CCT, id_ciclo=CICLO, driver_dominante="D2", mlflow_run_id="abc123")
    assert salida.driver_dominante == "D2"
    assert salida.probabilidades is None


def test_ml02_salida_con_probabilidades() -> None:
    salida = ML02Salida(
        cct=CCT,
        id_ciclo=CICLO,
        driver_dominante="D1",
        probabilidades={"D1": 0.7, "D2": 0.3},
        mlflow_run_id="abc123",
    )
    assert salida.probabilidades["D1"] == 0.7


def test_ml02_salida_rechaza_driver_fuera_del_catalogo() -> None:
    """Un `D9` (o cualquier valor fuera de D1..D6) no se acepta -- mismo principio que
    `test_rechaza_drivers_fuera_del_catalogo` en `tests/test_publicar_gold.py` (Célula 3)."""
    with pytest.raises(ValidationError):
        ML02Salida(cct=CCT, id_ciclo=CICLO, driver_dominante="D9", mlflow_run_id="abc123")


def test_ml03_salida_valida() -> None:
    salida = ML03Salida(cct=CCT, id_ciclo=CICLO, cluster=2, mlflow_run_id="abc123")
    assert salida.cluster == 2


def test_ml03_salida_rechaza_cluster_negativo() -> None:
    with pytest.raises(ValidationError):
        ML03Salida(cct=CCT, id_ciclo=CICLO, cluster=-1, mlflow_run_id="abc123")


def _prediccion_modelos(**overrides) -> PrediccionModelos:
    base = {
        "ml01": ML01Salida(cct=CCT, id_ciclo=CICLO, variacion_predicha=-0.05, mlflow_run_id="r1"),
        "ml02": ML02Salida(cct=CCT, id_ciclo=CICLO, driver_dominante="D2", mlflow_run_id="r2"),
        "ml03": ML03Salida(cct=CCT, id_ciclo=CICLO, cluster=1, mlflow_run_id="r3"),
    }
    base.update(overrides)
    return PrediccionModelos(**base)


def test_prediccion_modelos_alineada_ok() -> None:
    pred = _prediccion_modelos()
    assert pred.ml01.cct == pred.ml02.cct == pred.ml03.cct == CCT


def test_prediccion_modelos_rechaza_cct_desalineado() -> None:
    with pytest.raises(ValidationError, match="misma escuela y ciclo"):
        _prediccion_modelos(
            ml03=ML03Salida(cct="19DES0007C", id_ciclo=CICLO, cluster=1, mlflow_run_id="r3")
        )


def test_prediccion_modelos_rechaza_ciclo_desalineado() -> None:
    with pytest.raises(ValidationError, match="misma escuela y ciclo"):
        _prediccion_modelos(
            ml02=ML02Salida(cct=CCT, id_ciclo="2023-2024", driver_dominante="D2", mlflow_run_id="r2")
        )
