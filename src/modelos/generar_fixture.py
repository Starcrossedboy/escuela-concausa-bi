"""Generador del fixture simulado de `gold.features_escuela` (US-311).

**Los datos son 100% sintéticos.** No provienen de ninguna fuente real, ningún CCT corresponde a
una escuela existente y no hay dato personal alguno. Sirven para desbloquear el desarrollo de
ML-01 mientras la Célula 1 publica el contrato real, conforme a la regla de desbloqueo del plan
de sprint (trabajar contra fixtures antes que esperar).

El generador es **determinista** (semilla fija): dos corridas producen el mismo archivo, así el
fixture no genera diff espurio en cada PR.

Uso:
    python -m src.modelos.generar_fixture
    python -m src.modelos.generar_fixture --escuelas 80 --salida tests/fixtures/otro.csv

Lo que el fixture SÍ reproduce del contrato: el grano CCT × ciclo, las 18 columnas, el rango
[0,1] de los drivers, la ausencia explícita `SIN_DATO` y su coherencia con el valor nulo, una
cobertura desigual entre drivers parecida a la real (D5 es regional, D6 cubre ~80 zonas urbanas),
y `driver_dominante` (US-302) calculado con la misma regla de argmax que
`gold.features_escuela` publica de verdad (ver dbt/models/gold/features_escuela.sql): el driver
con cobertura OK y mayor valor, desempate D1>D2>D3>D4>D5>D6, NULL si ninguno es elegible.

Lo que NO reproduce: las distribuciones reales de cada driver. Sirve para validar la mecánica de
la partición y el pipeline, **no para sacar conclusiones sustantivas ni métricas comparables**.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.modelos.contrato import DRIVERS, Cobertura, FeaturesEscuela

SEMILLA = 20260808

#: Alcance del proyecto: CDMX, Edomex, Nuevo León, Jalisco (claves INEGI de entidad).
SCOPE_ENTIDADES: tuple[str, ...] = ("09", "15", "19", "14")

#: Ciclos simulados, del más antiguo al más reciente.
CICLOS: tuple[str, ...] = (
    "2019-2020",
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
)

#: Probabilidad de que un driver TENGA dato, según su cobertura documentada en CLAUDE.md §4.
#: D1/D2 son nacionales; D3/D4 vienen de CEMABE a nivel escuela; D5 es regional; D6 urbano.
PROB_COBERTURA: dict[str, float] = {
    "d1_pobreza": 0.99,
    "d2_inseguridad": 0.97,
    "d3_infraestructura": 0.93,
    "d4_conectividad": 0.93,
    "d5_agua": 0.70,
    "d6_aire": 0.45,
}

#: Peso de cada driver en la caída de matrícula simulada. Da señal aprendible sin ser trivial.
PESOS_TARGET: dict[str, float] = {
    "d1_pobreza": -0.09,
    "d2_inseguridad": -0.07,
    "d3_infraestructura": -0.05,
    "d4_conectividad": -0.04,
    "d5_agua": -0.03,
    "d6_aire": -0.02,
}


def _generar_ccts(rng: np.random.Generator, n_escuelas: int) -> list[str]:
    """CCTs sintéticos con formato válido: 2 dígitos de entidad + 3 letras + 4 dígitos + 1 letra."""
    letras = np.array(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    niveles = ("DPR", "DJN", "DES", "DCT")  # primaria, preescolar, secundaria, telesecundaria
    ccts: list[str] = []
    for i in range(n_escuelas):
        entidad = SCOPE_ENTIDADES[i % len(SCOPE_ENTIDADES)]
        nivel = niveles[int(rng.integers(len(niveles)))]
        consecutivo = f"{i:04d}"
        verificador = str(rng.choice(letras))
        ccts.append(f"{entidad}{nivel}{consecutivo}{verificador}")
    return ccts

def _generar_municipios(rng: np.random.Generator, n_escuelas: int) -> list[str]:
    """Claves INEGI de municipio sintéticas (US-325): 2 dígitos de entidad + 3 de municipio.

    Varios municipios por entidad y varias escuelas por municipio (módulo 7), para que el
    análisis de concentración geográfica de US-325 tenga con qué trabajar -- no una escuela
    por municipio.
    """
    municipios: list[str] = []
    for i in range(n_escuelas):
        entidad = SCOPE_ENTIDADES[i % len(SCOPE_ENTIDADES)]
        consecutivo = f"{(i % 7) + 1:03d}"
        municipios.append(f"{entidad}{consecutivo}")
    return municipios

def generar(n_escuelas: int = 80, semilla: int = SEMILLA) -> pd.DataFrame:
    """Construye el DataFrame simulado de features.

    Args:
        n_escuelas: escuelas distintas a simular. El total de filas es `n_escuelas * len(CICLOS)`.
        semilla: semilla del generador, para reproducibilidad.

    Returns:
        DataFrame con las 18 columnas del contrato, ordenado por CCT y ciclo.

    Raises:
        ValueError: si el total de filas excede el tope de 500 del plan de sprint §8.
    """
    total_filas = n_escuelas * len(CICLOS)
    if total_filas > 500:
        raise ValueError(
            f"{n_escuelas} escuelas × {len(CICLOS)} ciclos = {total_filas} filas. "
            "El plan de sprint §8 topa los fixtures en 500 filas."
        )

    rng = np.random.default_rng(semilla)
    ccts = _generar_ccts(rng, n_escuelas)

    # Nivel base por escuela: una escuela pobre tiende a seguir siéndolo entre ciclos.
    base = {d: rng.beta(2, 3, size=n_escuelas) for d in DRIVERS}
    # Cada escuela tiene un driver dominante; prepara el terreno de ML-02 (US-302).
    dominante = rng.integers(len(DRIVERS), size=n_escuelas)

    filas: list[dict[str, object]] = []
    for i, cct in enumerate(ccts):
        for t, ciclo in enumerate(CICLOS):
            fila: dict[str, object] = {"cct": cct, "id_ciclo": ciclo, "cve_mun": _generar_municipios(rng, n_escuelas)[i]}
            observados = 0
            presion = 0.0

            for j, driver in enumerate(DRIVERS):
                hay_dato = rng.random() < PROB_COBERTURA[driver]
                if hay_dato:
                    # Deriva lenta en el tiempo + ruido; el driver dominante pesa más.
                    valor = base[driver][i] + 0.02 * t + rng.normal(0, 0.05)
                    if j == dominante[i]:
                        valor += 0.25
                    valor = float(np.clip(valor, 0.0, 1.0))
                    fila[driver] = round(valor, 4)
                    fila[f"d{j + 1}_cobertura"] = Cobertura.OK.value
                    observados += 1
                    presion += PESOS_TARGET[driver] * valor
                else:
                    # Ausencia explícita: nunca 0, nunca nulo silencioso.
                    fila[driver] = None
                    fila[f"d{j + 1}_cobertura"] = Cobertura.SIN_DATO.value

            # driver_dominante (US-302): misma regla que gold.features_escuela -- argmax entre
            # los drivers con cobertura OK, desempate por orden de DRIVERS (D1..D6) al conservar
            # el primero en un empate (`>` estricto, no `>=`).
            mejor_driver: str | None = None
            mejor_valor: float | None = None
            for j, driver in enumerate(DRIVERS):
                valor_driver = fila[driver]
                if valor_driver is not None and (mejor_valor is None or valor_driver > mejor_valor):
                    mejor_valor = valor_driver
                    mejor_driver = f"D{j + 1}"
            fila["driver_dominante"] = mejor_driver

            # Sin redondear: debe cumplirse exactamente que completitud == observados / 6.
            fila["indice_completitud_drivers"] = observados / len(DRIVERS)
            fila["target_variacion_matricula"] = round(
                float(presion + rng.normal(0, 0.015)), 4
            )
            filas.append(fila)

    columnas = (
        ["cct", "id_ciclo", "cve_mun"]
        + list(DRIVERS)
        + [f"d{k}_cobertura" for k in range(1, len(DRIVERS) + 1)]
        + ["driver_dominante", "indice_completitud_drivers", "target_variacion_matricula"]
    )
    return pd.DataFrame(filas, columns=columnas).sort_values(["cct", "id_ciclo"], ignore_index=True)


def validar_contra_contrato(df: pd.DataFrame) -> int:
    """Valida cada fila contra `FeaturesEscuela`. Devuelve las filas validadas.

    Es la garantía de que el fixture no se desvía del contrato §5.3: si la Célula 1 cambia una
    columna y actualizamos el espejo, esta función truena de inmediato.

    Raises:
        pydantic.ValidationError: en la primera fila que no cumpla el contrato.
    """
    registros = df.astype(object).where(pd.notna(df), None).to_dict(orient="records")
    for registro in registros:
        FeaturesEscuela(**registro)
    return len(registros)


def main() -> int:
    """Punto de entrada: genera, valida y escribe el fixture."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--escuelas", type=int, default=80, help="escuelas a simular")
    parser.add_argument("--semilla", type=int, default=SEMILLA, help="semilla determinista")
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("tests/fixtures/features_escuela_mock.csv"),
        help="ruta del CSV de salida",
    )
    args = parser.parse_args()

    df = generar(n_escuelas=args.escuelas, semilla=args.semilla)
    validadas = validar_contra_contrato(df)

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.salida, index=False)

    sin_dato = int((df[list(DRIVERS)].isna()).sum().sum())
    print(f"Fixture escrito en {args.salida}")
    print(f"  filas: {len(df)} ({args.escuelas} escuelas × {len(CICLOS)} ciclos)")
    print(f"  validadas contra el contrato: {validadas}")
    print(f"  celdas SIN_DATO: {sin_dato} de {len(df) * len(DRIVERS)}")
    print(f"  completitud media: {df['indice_completitud_drivers'].mean():.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
