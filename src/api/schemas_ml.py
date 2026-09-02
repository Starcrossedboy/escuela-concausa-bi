"""Contrato de datos entre la API y los 3 modelos ML (US-415).

Traduce entre el contrato canónico `gold.features_escuela` (Célula 1/3, `src/modelos/contrato.py`)
y las salidas crudas de ML-01/02/03, **antes** de que `src/api/v1/predicciones.py` (US-412) las
combine en el `PrediccionOut` público (`src/api/schemas.py`, §4 de `API_Specification.md`).

**Nunca redefine `FeaturesEscuela`**: se importa el canónico de `src.modelos.contrato` (dueño
Diana Alvarez / Andrés González Habib, `Data_Model.md` §5.3). Duplicarlo sería exactamente el
riesgo de divergencia que `vault/15_ML_Models/Publicacion_Gold.md` §9 ya señala para el catálogo de
recomendaciones -- no se repite aquí para el contrato de features.

La conversión de la salida de ML-01 (`variacion_predicha`, sin cota) al `indice_riesgo` ∈ [0,1]
público **no vive aquí**: es `src/modelos/riesgo.py::indice_riesgo`, capa de presentación de la
Célula 3. Este módulo solo define formas; US-412 hace el ensamblado.
"""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    StrictFloat,
    StrictInt,
    StrictStr,
    model_validator,
)

from src.modelos.contrato import (
    FeaturesEscuela,  # re-exportado: fuente única del contrato de entrada
)

__all__ = [
    "DriverId",
    "FeaturesEscuela",
    "ML01Salida",
    "ML02Salida",
    "ML03Salida",
    "PrediccionModelos",
]

#: Los 6 drivers del catálogo prescriptivo (Publicacion_Gold.md §4). Un modelo que devuelva
#: cualquier otro valor es un defecto, no un driver nuevo -- se rechaza en la puerta.
DriverId = Literal["D1", "D2", "D3", "D4", "D5", "D6"]


class ML01Salida(BaseModel):
    """Salida cruda de ML-01 (regresión de matrícula, `ML01_RegresionMatricula` en el registry).

    `variacion_predicha` es la variación con signo, sin cota -- igual que el target de
    entrenamiento (`FeaturesEscuela.target_variacion_matricula`). La conversión a `indice_riesgo`
    ∈ [0,1] vive en `src/modelos/riesgo.py`, no en este esquema.
    """

    cct: StrictStr = Field(min_length=10, max_length=10)
    id_ciclo: StrictStr
    variacion_predicha: StrictFloat
    mlflow_run_id: StrictStr


class ML02Salida(BaseModel):
    """Salida cruda de ML-02 (clasificación de driver dominante, `ML02_DriverClasificador`)."""

    cct: StrictStr = Field(min_length=10, max_length=10)
    id_ciclo: StrictStr
    driver_dominante: DriverId
    # Probabilidad por clase, si el modelo la expone (p. ej. predict_proba). Ninguna prueba de
    # contrato la exige hoy; queda opcional para no bloquear un modelo que solo dé la clase.
    probabilidades: dict[DriverId, StrictFloat] | None = None
    mlflow_run_id: StrictStr


class ML03Salida(BaseModel):
    """Salida cruda de ML-03 (clustering de escuelas, `ML03_ClusteringEscuelas`)."""

    cct: StrictStr = Field(min_length=10, max_length=10)
    id_ciclo: StrictStr
    cluster: StrictInt = Field(ge=0)
    mlflow_run_id: StrictStr


class PrediccionModelos(BaseModel):
    """Empalme formal Célula 3 → Célula 4: las 3 salidas crudas de una escuela × ciclo.

    Insumo directo de `PrediccionOut` (US-412). `recomendacion` no vive aquí: la deriva la API
    desde el catálogo prescriptivo compartido con `src/modelos/recomendaciones.py`
    (`Publicacion_Gold.md` §4), no es una salida de ningún modelo.
    """

    ml01: ML01Salida
    ml02: ML02Salida
    ml03: ML03Salida

    @model_validator(mode="after")
    def _misma_escuela_y_ciclo(self) -> PrediccionModelos:
        claves = {
            (self.ml01.cct, self.ml01.id_ciclo),
            (self.ml02.cct, self.ml02.id_ciclo),
            (self.ml03.cct, self.ml03.id_ciclo),
        }
        if len(claves) != 1:
            raise ValueError(
                f"Las 3 salidas de ML-01/02/03 deben ser de la misma escuela y ciclo, "
                f"recibido: {sorted(claves)}"
            )
        return self
