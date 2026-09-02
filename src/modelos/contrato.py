"""Espejo local del contrato `gold.features_escuela` (US-311).

El contrato canónico vive en `vault/03_Architecture/Data_Model.md` §5.3 y lo **produce la Célula 1**
(Diana Alvarez). Este módulo es un espejo ejecutable para poder validar fixtures y avanzar con
datos simulados mientras el módulo canónico existe.

**Cuando la Célula 1 publique su modelo Pydantic, este archivo se borra y se importa el suyo.**
Cualquier divergencia entre ambos es un defecto: el contrato manda, no este espejo.

Única diferencia de forma con el documento: las restricciones `ge`/`le` se expresan con
`Annotated` para que apliquen a la rama no nula de los drivers opcionales. La semántica es
idéntica.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, StrictFloat, StrictStr

#: Drivers del proyecto, en el orden del PRD (D1…D6).
DRIVERS: tuple[str, ...] = (
    "d1_pobreza",
    "d2_inseguridad",
    "d3_infraestructura",
    "d4_conectividad",
    "d5_agua",
    "d6_aire",
)

#: Puntaje normalizado de un driver. `None` sólo si su bandera es SIN_DATO.
Puntaje = Annotated[StrictFloat, Field(ge=0, le=1)]


class Cobertura(str, Enum):
    """Ausencia explícita de dato: nunca 0, nunca nulo silencioso."""

    OK = "OK"
    SIN_DATO = "SIN_DATO"


class DriverDominante(str, Enum):
    """Códigos aceptados de `driver_dominante` (US-302). Mismos valores que `CODIGOS_DRIVER`
    en `src/modelos/recomendaciones.py` y que `DRIVER_A_CLASE` en `entrenar_ml02.py`."""

    D1 = "D1"
    D2 = "D2"
    D3 = "D3"
    D4 = "D4"
    D5 = "D5"
    D6 = "D6"


class FeaturesEscuela(BaseModel):
    """Una fila por CCT × ciclo. Grano y columnas fijados por el contrato §5.3."""

    model_config = {"extra": "forbid"}  # ninguna columna fuera de contrato

    cct: StrictStr = Field(min_length=10, max_length=10)
    id_ciclo: StrictStr

    #: Clave INEGI municipal (5 dígitos). La agrega la C1 para el análisis de sesgo geográfico de
    #: US-325. Lleva default porque el fixture sintético es anterior al cambio: sin él, y con
    #: `extra="forbid"`, el espejo rechazaría tanto las filas viejas como —al revés— las nuevas.
    cve_mun: StrictStr | None = None

    d1_pobreza: Puntaje | None
    d2_inseguridad: Puntaje | None
    d3_infraestructura: Puntaje | None
    d4_conectividad: Puntaje | None
    d5_agua: Puntaje | None
    d6_aire: Puntaje | None

    d1_cobertura: Cobertura
    d2_cobertura: Cobertura
    d3_cobertura: Cobertura
    d4_cobertura: Cobertura
    d5_cobertura: Cobertura
    d6_cobertura: Cobertura

    #: Etiqueta OPERATIVA (US-302, acordada con Andrés González Habib/C3 el 2026-08-28): argmax
    #: entre los drivers con cobertura OK, desempate determinista D1>D2>D3>D4>D5>D6. NO es una
    #: observación independiente ni evidencia causal. NULL cuando ninguna fila tiene un driver
    #: elegible. Ver dbt/models/gold/features_escuela.sql (CTE `con_driver_dominante`).
    driver_dominante: DriverDominante | None

    indice_completitud_drivers: Annotated[StrictFloat, Field(ge=0, le=1)]

    #: Etiqueta (partición temporal), unidad declarada por ADR-007 (ratificado 2026-08-29,
    #: BUG-017/BUG-019): FRACCIÓN de matrícula vs el ciclo anterior del mismo cct
    #: (matricula_total/matricula_ciclo_anterior - 1.0), NO alumnos absolutos. Ej.: -0.05 = pierde
    #: 5 % de su matrícula. Mismo patrón/unidad que target_hibrido.py::variacion_desde_serie (C3).
    target_variacion_matricula: StrictFloat

def columna_cobertura(driver: str) -> str:
    """Devuelve el nombre de la bandera de cobertura de un driver.

    >>> columna_cobertura("d1_pobreza")
    'd1_cobertura'
    """
    if driver not in DRIVERS:
        raise ValueError(f"Driver desconocido: {driver!r}. Esperado uno de {DRIVERS}.")
    return f"{driver.split('_')[0]}_cobertura"


def entidad_de_cct(cct: str) -> str:
    """Extrae la clave INEGI de entidad (2 dígitos) que prefija al CCT.

    `features_escuela` no trae `cve_ent` —el contrato la omite—, pero US-312 pide el análisis
    de error **por entidad**. Los dos primeros caracteres del CCT la codifican, así que se
    deriva de ahí en vez de pedir una columna nueva a la Célula 1.

    >>> entidad_de_cct("09DPR0001X")
    '09'
    """
    if len(cct) != 10:
        raise ValueError(f"CCT debe tener 10 caracteres, recibido {len(cct)}: {cct!r}")
    return cct[:2]
