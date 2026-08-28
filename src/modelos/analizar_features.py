"""Diagnóstico reproducible de features y cobertura para US-322 y US-325.

No transforma ni imputa datos para entrenamiento. Su objetivo es convertir en
validaciones y tablas auditables las decisiones que preceden al clustering de
ML-03: exclusión de llaves y targets, coherencia de ``SIN_DATO`` y cobertura
por driver y entidad.
"""

from __future__ import annotations

import pandas as pd

from src.modelos.contrato import DRIVERS, columna_cobertura, entidad_de_cct

COLUMNA_COMPLETITUD = "indice_completitud_drivers"
COLUMNA_TARGET = "target_variacion_matricula"
COLUMNAS_NO_ENTRENABLES = frozenset({"cct", "id_ciclo", COLUMNA_TARGET})


def validar_features_para_analisis(df: pd.DataFrame) -> None:
    """Verifica el mínimo contrato antes de generar un diagnóstico.

    Cada valor ausente debe declararse con ``SIN_DATO`` y cada ``SIN_DATO``
    debe conservar el valor ausente. Así se evita ocultar cobertura parcial
    antes de seleccionar variables o entrenar un modelo.
    """
    requeridas = {
        "cct",
        "id_ciclo",
        COLUMNA_COMPLETITUD,
        COLUMNA_TARGET,
        *DRIVERS,
        *(columna_cobertura(driver) for driver in DRIVERS),
    }
    faltantes = requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {sorted(faltantes)}")

    duplicadas = df.duplicated(["cct", "id_ciclo"])
    if bool(duplicadas.any()):
        raise ValueError("Hay filas duplicadas para la llave cct × id_ciclo.")

    for driver in DRIVERS:
        cobertura = columna_cobertura(driver)
        valores_cobertura = set(df[cobertura].dropna().unique())
        invalidos = valores_cobertura - {"OK", "SIN_DATO"}
        if invalidos:
            raise ValueError(f"{cobertura} tiene valores inválidos: {sorted(invalidos)}")

        sin_dato = df[cobertura].eq("SIN_DATO")
        valor_ausente = df[driver].isna()
        if not sin_dato.equals(valor_ausente):
            raise ValueError(
                f"Cobertura inconsistente en {driver}: SIN_DATO y valor ausente deben coincidir."
            )


def columnas_excluidas_por_fuga() -> frozenset[str]:
    """Devuelve llaves y target que no pueden entrar a una matriz de clustering."""
    return COLUMNAS_NO_ENTRENABLES


def variables_candidatas_ml03() -> tuple[str, ...]:
    """Declara las variables candidatas para ML-03, sin construir aún la matriz.

    D5 y D6 incluyen indicadores de disponibilidad conforme a ADR-003. La
    imputación solo se incorporará al entrenar, ajustada exclusivamente sobre
    cada partición de entrenamiento.
    """
    return (*DRIVERS, COLUMNA_COMPLETITUD, "d5_dato_disponible", "d6_dato_disponible")


def resumen_eda(df: pd.DataFrame) -> pd.DataFrame:
    """Resume nulos, cardinalidad y correlación lineal de variables numéricas."""
    validar_features_para_analisis(df)
    columnas = [*DRIVERS, COLUMNA_COMPLETITUD, COLUMNA_TARGET]
    filas: list[dict[str, object]] = []
    for columna in columnas:
        serie = pd.to_numeric(df[columna], errors="raise")
        filas.append(
            {
                "feature": columna,
                "observaciones": len(serie),
                "nulos": int(serie.isna().sum()),
                "pct_nulos": float(serie.isna().mean()),
                "valores_unicos": int(serie.nunique(dropna=True)),
                "correlacion_target": (
                    None
                    if columna == COLUMNA_TARGET
                    else float(serie.corr(df[COLUMNA_TARGET]))
                ),
            }
        )
    return pd.DataFrame(filas)


def correlaciones_drivers(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula correlaciones entre drivers y completitud, sin incluir el target."""
    validar_features_para_analisis(df)
    columnas = [*DRIVERS, COLUMNA_COMPLETITUD]
    return df[columnas].astype(float).corr()


def cobertura_por_driver(df: pd.DataFrame) -> pd.DataFrame:
    """Mide la cobertura por driver a grano CCT × ciclo y escuelas afectadas."""
    validar_features_para_analisis(df)
    filas: list[dict[str, object]] = []
    for driver in DRIVERS:
        sin_dato = df[columna_cobertura(driver)].eq("SIN_DATO")
        filas.append(
            {
                "driver": driver,
                "observaciones": len(df),
                "con_dato": int((~sin_dato).sum()),
                "sin_dato": int(sin_dato.sum()),
                "pct_sin_dato": float(sin_dato.mean()),
                "escuelas_afectadas": int(df.loc[sin_dato, "cct"].nunique()),
            }
        )
    return pd.DataFrame(filas)


def cobertura_por_entidad(df: pd.DataFrame) -> pd.DataFrame:
    """Desglosa la cobertura por entidad derivada del CCT, sin inventar municipio."""
    validar_features_para_analisis(df)
    filas: list[dict[str, object]] = []
    entidades = df["cct"].map(entidad_de_cct)
    for driver in DRIVERS:
        sin_dato = df[columna_cobertura(driver)].eq("SIN_DATO")
        detalle = pd.DataFrame({"entidad": entidades, "sin_dato": sin_dato, "cct": df["cct"]})
        for entidad, grupo in detalle.groupby("entidad", sort=True):
            filas.append(
                {
                    "entidad": entidad,
                    "driver": driver,
                    "observaciones": len(grupo),
                    "sin_dato": int(grupo["sin_dato"].sum()),
                    "pct_sin_dato": float(grupo["sin_dato"].mean()),
                    "escuelas_afectadas": int(
                        grupo.loc[grupo["sin_dato"], "cct"].nunique()
                    ),
                }
            )
    return pd.DataFrame(filas)


def completitud_por_entidad(df: pd.DataFrame) -> pd.DataFrame:
    """Resume el índice de completitud por entidad para detectar sesgo territorial."""
    validar_features_para_analisis(df)
    detalle = df.assign(entidad=df["cct"].map(entidad_de_cct))
    return (
        detalle.groupby("entidad", sort=True)
        .agg(
            observaciones=("cct", "size"),
            escuelas=("cct", "nunique"),
            completitud_promedio=(COLUMNA_COMPLETITUD, "mean"),
            completitud_minima=(COLUMNA_COMPLETITUD, "min"),
            completitud_maxima=(COLUMNA_COMPLETITUD, "max"),
        )
        .reset_index()
    )


def requerir_clave_municipio(df: pd.DataFrame) -> None:
    """Falla explícitamente si se solicita un análisis municipal sin ``cve_mun``.

    El contrato vigente no publica esta llave. No se debe inferir un municipio
    desde un CCT ni sustituir este análisis por un agregado estatal.
    """
    if "cve_mun" not in df.columns:
        raise ValueError(
            "El análisis municipal requiere cve_mun de gold.features_escuela; "
            "coordina este campo con Célula 1 antes de concluir US-325."
        )
