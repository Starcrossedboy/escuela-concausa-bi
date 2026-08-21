"""Fixture simulado de `gold.dim_escuela` para probar la agregación de DEC-007 (US-311).

**Datos 100 % sintéticos**, derivados de forma determinista de
`tests/fixtures/features_escuela_mock.csv` para que ambos fixtures sean consistentes: mismos CCT,
misma entidad.

Existe porque **`gold.features_escuela` no expone `cve_mun` ni `nivel`** —el contrato §5.3 sólo
trae `cct`, los 6 drivers, sus banderas, la completitud y el target—, pero DEC-007 pide el objetivo
a nivel `municipio × nivel`. Esas dos columnas viven en `gold.dim_escuela`, así que la agregación
es un **join a la dimensión** y no requiere cambiar el contrato de la Célula 1.

Uso:
    python -m src.modelos.generar_fixture_dim
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.modelos.contrato import entidad_de_cct
from src.modelos.entrenar_ml01 import FEATURES_POR_DEFECTO, cargar_features

SEMILLA = 20260819
SALIDA_POR_DEFECTO = Path("tests/fixtures/dim_escuela_mock.csv")

#: Los tres caracteres centrales del CCT codifican el nivel educativo.
NIVEL_POR_CLAVE: dict[str, str] = {
    "DJN": "PREESCOLAR",
    "DPR": "PRIMARIA",
    "DES": "SECUNDARIA",
    "DCT": "TELESECUNDARIA",
}

#: Municipios simulados por entidad. Suficientes para que la agregación tenga varios grupos.
MUNICIPIOS_POR_ENTIDAD = 4


def nivel_de_cct(cct: str) -> str:
    """Deriva el nivel educativo de los caracteres 3–5 del CCT.

    >>> nivel_de_cct("09DPR0001X")
    'PRIMARIA'
    """
    clave = cct[2:5]
    if clave not in NIVEL_POR_CLAVE:
        raise ValueError(f"Clave de nivel desconocida en {cct!r}: {clave!r}.")
    return NIVEL_POR_CLAVE[clave]


def generar(features: pd.DataFrame, semilla: int = SEMILLA) -> pd.DataFrame:
    """Construye la dimensión simulada: una fila por CCT.

    El municipio se asigna de forma determinista dentro de la entidad que ya codifica el CCT, así
    que entidad y municipio nunca se contradicen.
    """
    rng = np.random.default_rng(semilla)
    ccts = sorted(features["cct"].unique())

    filas = []
    for cct in ccts:
        entidad = entidad_de_cct(cct)
        consecutivo = int(rng.integers(1, MUNICIPIOS_POR_ENTIDAD + 1))
        filas.append(
            {
                "cct": cct,
                "cve_ent": entidad,
                "cve_mun": f"{entidad}{consecutivo:03d}",
                "nivel": nivel_de_cct(cct),
            }
        )
    return pd.DataFrame(filas).sort_values("cct", ignore_index=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--features", type=Path, default=FEATURES_POR_DEFECTO)
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    args = parser.parse_args()

    dim = generar(cargar_features(args.features))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    dim.to_csv(args.salida, index=False)

    print(f"Fixture escrito en {args.salida}")
    print(f"  escuelas: {len(dim)}")
    print(f"  municipios: {dim['cve_mun'].nunique()} · niveles: {dim['nivel'].nunique()}")
    print(f"  grupos municipio × nivel: {dim.groupby(['cve_mun', 'nivel']).ngroups}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
