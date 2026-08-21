"""Target híbrido de dos niveles para ML-01 (DEC-007, mitigación de RISK-007).

## Por qué existe

El Formato 911 sólo se pudo descargar con el ciclo **2024-2025**. `target_variacion_matricula` es
la variación contra el ciclo anterior, así que **con un solo ciclo no hay etiqueta que predecir**
(RISK-007).

**DEC-007** resuelve el problema separando los dos niveles:

| | Grano | Fuente |
|---|---|---|
| **Objetivo supervisado** | `municipio × nivel × ciclo` | serie agregada SNIEE de la SEP, multi-año |
| **Features y driver dominante** | `cct` (escuela) | 911 2024-2025 + los 6 drivers |

Así hay un target real y validable con partición temporal, sin perder el carácter prescriptivo: la
recomendación se sigue emitiendo por escuela, porque el **driver dominante no se agrega**.

## Lo que este módulo aporta

`gold.features_escuela` **no expone `cve_mun` ni `nivel`** — el contrato §5.3 sólo trae `cct`, los
seis drivers, sus banderas, la completitud y el target. Ambas columnas viven en `gold.dim_escuela`,
así que la agregación es un **join a la dimensión**: no hace falta cambiar el contrato de la
Célula 1 ni pedirle columnas nuevas.

## Cómo se agregan los drivers

Un driver agregado es el **promedio de las escuelas que sí tienen dato**, nunca de las que no. Una
escuela sin dato de aire no arrastra el promedio hacia cero: queda fuera del cálculo y su ausencia
se refleja en la cobertura.

La cobertura pasa de enum a **fracción** (`d6_cobertura_frac` = escuelas con dato / total del
grupo), porque a nivel agregado «OK / SIN_DATO» pierde información: no es lo mismo un municipio
donde mide una estación de cada diez escuelas que uno donde miden todas. Se conserva además el enum
para que el consumidor que sólo entiende el contrato original siga funcionando.

## Estado

El target real todavía no llega: la serie SNIEE es responsabilidad de la Célula 1 y el gate de
DEC-007 es el **30 de agosto**. `unir_target()` lo recibe como argumento en vez de calcularlo, igual
que hicimos con el driver de ML-02 en US-313 — cuando la serie aterrice, es conectarla.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.modelos.contrato import DRIVERS, columna_cobertura
from src.modelos.entrenar_ml01 import COLUMNA_TARGET
from src.modelos.particion_temporal import COLUMNA_CICLO

DIM_POR_DEFECTO = Path("tests/fixtures/dim_escuela_mock.csv")

#: Llave del grano agregado que fija DEC-007.
LLAVE_AGREGADA: tuple[str, ...] = ("cve_mun", "nivel", COLUMNA_CICLO)

#: Columnas que la agregación necesita de `gold.dim_escuela`.
COLUMNAS_DIM: tuple[str, ...] = ("cct", "cve_mun", "nivel")


@dataclass(frozen=True)
class ResumenAgregacion:
    """Qué pasó al agregar. Sirve para no publicar un dataset sin saber qué se perdió."""

    escuelas_entrada: int
    escuelas_sin_dimension: int
    grupos: int
    ciclos: int

    @property
    def cobertura_dimension(self) -> float:
        """Fracción de escuelas que sí encontraron su municipio y nivel."""
        if self.escuelas_entrada == 0:
            return 0.0
        return 1.0 - self.escuelas_sin_dimension / self.escuelas_entrada


def cargar_dimension(ruta: Path = DIM_POR_DEFECTO) -> pd.DataFrame:
    """Lee `gold.dim_escuela` (o su fixture) con las columnas que la agregación necesita.

    Raises:
        FileNotFoundError: si la ruta no existe.
        ValueError: si falta alguna columna requerida.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe {ruta}. Genera el fixture con: python -m src.modelos.generar_fixture_dim"
        )
    dim = pd.read_parquet(ruta) if ruta.suffix == ".parquet" else pd.read_csv(ruta, dtype=str)

    faltantes = set(COLUMNAS_DIM) - set(dim.columns)
    if faltantes:
        raise ValueError(
            f"`dim_escuela` no trae {sorted(faltantes)}. DEC-007 necesita municipio y nivel para "
            "agregar el objetivo; el contrato de features_escuela no los expone."
        )
    return dim[list(COLUMNAS_DIM)]


def agregar_a_municipio_nivel(
    features: pd.DataFrame,
    dimension: pd.DataFrame,
) -> tuple[pd.DataFrame, ResumenAgregacion]:
    """Agrega las features de escuela al grano `municipio × nivel × ciclo` de DEC-007.

    **No calcula el objetivo.** El target agregado viene de la serie SNIEE y se adjunta después con
    `unir_target()`; agregarlo desde el 911 de un solo ciclo reproduciría el problema que DEC-007
    resuelve.

    Args:
        features: tabla conforme al contrato `FeaturesEscuela`.
        dimension: `gold.dim_escuela` con `cct`, `cve_mun` y `nivel`.

    Returns:
        El DataFrame agregado y un `ResumenAgregacion` con lo que se perdió en el camino.

    Raises:
        ValueError: si ninguna escuela encuentra su fila en la dimensión.
    """
    unido = features.merge(dimension, on="cct", how="left", validate="many_to_one")
    sin_dim = int(unido["cve_mun"].isna().sum())
    if sin_dim == len(unido):
        raise ValueError("Ninguna escuela encontró municipio y nivel en `dim_escuela`.")

    completas = unido[unido["cve_mun"].notna()].copy()
    llave = list(LLAVE_AGREGADA)

    # Promedio sólo sobre las escuelas con dato: `mean()` de pandas ignora NaN por diseño, así que
    # una ausencia nunca se cuenta como cero.
    agregado = completas.groupby(llave, dropna=False).agg(
        **{d: (d, "mean") for d in DRIVERS},
        **{f"{d}_n_con_dato": (d, "count") for d in DRIVERS},
        escuelas=("cct", "size"),
        indice_completitud_drivers=("indice_completitud_drivers", "mean"),
    ).reset_index()

    for driver in DRIVERS:
        prefijo = driver.split("_")[0]
        frac = agregado[f"{driver}_n_con_dato"] / agregado["escuelas"]
        agregado[f"{prefijo}_cobertura_frac"] = frac
        # Se conserva el enum del contrato original para consumidores que sólo entienden OK/SIN_DATO.
        agregado[columna_cobertura(driver)] = np.where(frac > 0, "OK", "SIN_DATO")
        agregado = agregado.drop(columns=[f"{driver}_n_con_dato"])

    resumen = ResumenAgregacion(
        escuelas_entrada=len(unido),
        escuelas_sin_dimension=sin_dim,
        grupos=agregado.groupby(["cve_mun", "nivel"]).ngroups,
        ciclos=agregado[COLUMNA_CICLO].nunique(),
    )
    return agregado, resumen


def unir_target(agregado: pd.DataFrame, serie_target: pd.DataFrame) -> pd.DataFrame:
    """Adjunta el objetivo multi-año de la serie SNIEE al grano agregado.

    El target **se recibe, no se calcula**: es responsabilidad de la Célula 1 publicarlo, y el gate
    de DEC-007 es el 30 de agosto. Mientras tanto esta función permite probar el pipeline completo
    con una serie simulada.

    Args:
        agregado: salida de `agregar_a_municipio_nivel`.
        serie_target: `cve_mun`, `nivel`, `id_ciclo` y `target_variacion_matricula`.

    Returns:
        El agregado con su objetivo, **sólo para los grupos que tienen etiqueta**. Un grupo sin
        target no se rellena con cero: se queda fuera, porque entrenar contra un cero inventado es
        peor que tener menos filas.

    Raises:
        ValueError: si la serie no trae las columnas esperadas o si no cruza con ningún grupo.
    """
    requeridas = set(LLAVE_AGREGADA) | {COLUMNA_TARGET}
    faltantes = requeridas - set(serie_target.columns)
    if faltantes:
        raise ValueError(f"La serie de objetivo no trae {sorted(faltantes)}.")

    unido = agregado.merge(
        serie_target[list(requeridas)], on=list(LLAVE_AGREGADA), how="inner", validate="one_to_one"
    )
    if unido.empty:
        raise ValueError(
            "La serie de objetivo no cruzó con ningún grupo `municipio × nivel × ciclo`. "
            "Revisa que use las mismas claves INEGI y el mismo formato de ciclo."
        )
    return unido
