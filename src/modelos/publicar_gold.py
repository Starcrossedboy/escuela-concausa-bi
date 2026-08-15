"""Publicación de predicciones y recomendaciones a Gold (US-313).

Job batch que escribe `gold.predicciones` y `gold.recomendaciones`, las dos tablas que alimentan
**DB-06 (Predicciones)** y **DB-09 (Recomendaciones prescriptivas)** de Superset y los endpoints de
inferencia de la Célula 4.

## Contrato

Definido en `03_Architecture/Data_Model.md` §4.5, tras **DEC-005/006**:

- `gold.predicciones` — `cct`, `id_ciclo`, `modelo`, `valor` (variación cruda, la que conserva la
  unidad para MAE/RMSE), `indice_riesgo` (derivado, ver `src/modelos/riesgo.py`), `probabilidad`,
  `mlflow_run_id`, `generado_at`.
- `gold.recomendaciones` — `cct`, `id_ciclo`, `driver_dominante`, `recomendacion`, `prioridad`.

## Idempotencia

El job se puede correr N veces con el mismo resultado: escribe con **UPSERT** sobre la llave
natural (`cct`, `id_ciclo`, `modelo`) y (`cct`, `id_ciclo`). No borra particiones ni trunca tablas;
volver a correrlo tras reentrenar simplemente actualiza los valores y el `mlflow_run_id`.

## Alcance hoy

ML-01 ya está entrenado (US-311), así que `gold.predicciones` se puebla completa. En cambio
**`driver_dominante` es salida de ML-02 (US-302, Andrés) y todavía no existe**: por eso
`construir_recomendaciones()` lo recibe como argumento en vez de calcularlo. Cuando ML-02 aterrice,
es conectar su salida a esta función — el resto de la maquinaria ya está.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field, StrictFloat, StrictStr
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.engine import Engine

from src.modelos.contrato import DRIVERS
from src.modelos.entrenar_ml01 import cargar_features, entrenar_y_evaluar
from src.modelos.particion_temporal import COLUMNA_CICLO, ciclos_ordenados
from src.modelos.riesgo import RIESGO_ESTABLE, RIESGO_UMBRAL, indice_riesgo

ESQUEMA_GOLD = "gold"
TABLA_PREDICCIONES = "predicciones"
TABLA_RECOMENDACIONES = "recomendaciones"

#: Catálogo prescriptivo: qué intervención toca según el driver dominante.
#:
#: Coincide **literalmente** con `RECOMENDACION_POR_DRIVER` de `src/api/mock_data.py` (US-401,
#: Christian Ruiz). Vive aquí porque es dato de negocio que produce la Célula 3, no un mock de la
#: API; cuando la C4 quite sus datos simulados debería importarlo de este módulo.
#: `tests/test_publicar_gold.py::test_catalogo_coincide_con_el_de_la_api` falla si divergen.
RECOMENDACION_POR_DRIVER: dict[str, str] = {
    "D1": "Priorizar programas de becas y apoyo alimentario en la zona.",
    "D2": "Coordinar con seguridad pública rutas escolares seguras y entornos protegidos.",
    "D3": "Gestionar rehabilitación de infraestructura escolar prioritaria.",
    "D4": "Ampliar conectividad y dotación de equipo de cómputo.",
    "D5": "Asegurar suministro de agua y planes de contingencia hídrica.",
    "D6": "Activar protocolos por contingencia de calidad del aire.",
}

#: Códigos de driver válidos (`D1`…`D6`), en el orden del PRD.
CODIGOS_DRIVER: tuple[str, ...] = tuple(f"D{i}" for i in range(1, len(DRIVERS) + 1))


class Prioridad(str, Enum):
    """Urgencia de la intervención, derivada del `indice_riesgo`."""

    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class PrediccionGold(BaseModel):
    """Contrato ejecutable de una fila de `gold.predicciones` (§4.5)."""

    model_config = {"extra": "forbid"}

    cct: StrictStr = Field(min_length=10, max_length=10)
    id_ciclo: StrictStr
    modelo: StrictStr
    valor: StrictFloat
    indice_riesgo: StrictFloat = Field(ge=0, le=1)
    probabilidad: StrictFloat | None
    mlflow_run_id: StrictStr
    generado_at: datetime


class RecomendacionGold(BaseModel):
    """Contrato ejecutable de una fila de `gold.recomendaciones` (§4.5)."""

    model_config = {"extra": "forbid"}

    cct: StrictStr = Field(min_length=10, max_length=10)
    id_ciclo: StrictStr
    driver_dominante: StrictStr
    recomendacion: StrictStr
    prioridad: Prioridad


def prioridad_de_riesgo(riesgo: float) -> Prioridad:
    """Traduce el `indice_riesgo` a urgencia de intervención.

    **No inventa umbrales nuevos**: reutiliza las dos anclas ya ratificadas de
    `DOC-INDICE-RIESGO` — 0.60 es el umbral de "escuela en riesgo" que usan los tableros
    (confirmado por Manuel Serranía en el PR #27) y 0.30 corresponde a una escuela con matrícula
    estable.

    >>> prioridad_de_riesgo(0.85).value
    'alta'
    >>> prioridad_de_riesgo(0.45).value
    'media'
    >>> prioridad_de_riesgo(0.10).value
    'baja'
    """
    if riesgo >= RIESGO_UMBRAL:
        return Prioridad.ALTA
    if riesgo >= RIESGO_ESTABLE:
        return Prioridad.MEDIA
    return Prioridad.BAJA


def _metadatos(esquema: str | None = ESQUEMA_GOLD) -> tuple[MetaData, Table, Table]:
    """Define las dos tablas de Gold. `esquema=None` para motores sin esquemas (SQLite)."""
    metadata = MetaData(schema=esquema)
    predicciones = Table(
        TABLA_PREDICCIONES,
        metadata,
        Column("cct", String(10), primary_key=True),
        Column("id_ciclo", String, primary_key=True),
        Column("modelo", String, primary_key=True),
        Column("valor", Float, nullable=False),
        Column("indice_riesgo", Float, nullable=False),
        Column("probabilidad", Float, nullable=True),
        Column("mlflow_run_id", String, nullable=False),
        Column("generado_at", DateTime(timezone=True), nullable=False),
    )
    recomendaciones = Table(
        TABLA_RECOMENDACIONES,
        metadata,
        Column("cct", String(10), primary_key=True),
        Column("id_ciclo", String, primary_key=True),
        Column("driver_dominante", String, nullable=False),
        Column("recomendacion", String, nullable=False),
        Column("prioridad", String, nullable=False),
    )
    return metadata, predicciones, recomendaciones


def construir_predicciones(
    features: pd.DataFrame,
    modelo,
    mlflow_run_id: str,
    id_ciclo_objetivo: str | None = None,
    generado_at: datetime | None = None,
) -> pd.DataFrame:
    """Genera las filas de `gold.predicciones` para ML-01.

    Predice sobre el ciclo más reciente disponible (el que interesa al negocio: "¿qué escuelas van
    a perder matrícula el próximo ciclo?") y adjunta tanto la variación cruda como su traducción a
    `indice_riesgo`.

    Args:
        features: tabla conforme al contrato `FeaturesEscuela`.
        modelo: estimador ya entrenado (`ResultadoEntrenamiento.modelo`).
        mlflow_run_id: corrida que produjo el modelo; queda como trazabilidad de la predicción.
        id_ciclo_objetivo: ciclo a predecir. Por defecto, el más reciente.
        generado_at: marca de tiempo; por defecto, ahora en UTC.

    Returns:
        DataFrame con las columnas de `gold.predicciones`.

    Raises:
        ValueError: si el ciclo objetivo no existe en las features.
    """
    ciclos = ciclos_ordenados(features)
    objetivo = id_ciclo_objetivo or ciclos[-1]
    if objetivo not in ciclos:
        raise ValueError(f"El ciclo {objetivo!r} no está en las features. Disponibles: {ciclos}.")

    corte = features[features[COLUMNA_CICLO] == objetivo]
    variacion = modelo.predict(corte[list(DRIVERS)])

    filas = pd.DataFrame(
        {
            "cct": corte["cct"].to_numpy(),
            "id_ciclo": objetivo,
            "modelo": "ML-01",
            "valor": variacion.astype(float),
            "indice_riesgo": indice_riesgo(variacion).astype(float),
            # ML-01 es regresión: no produce probabilidad. NULL explícito, nunca 0.
            "probabilidad": None,
            "mlflow_run_id": mlflow_run_id,
            "generado_at": generado_at or datetime.now(tz=UTC),
        }
    )
    for fila in filas.to_dict(orient="records"):
        PrediccionGold(**fila)
    return filas


def construir_recomendaciones(
    predicciones: pd.DataFrame,
    driver_por_escuela: dict[str, str],
) -> pd.DataFrame:
    """Genera las filas de `gold.recomendaciones` a partir del driver dominante.

    El driver **se recibe, no se calcula**: es salida de ML-02 (US-302, Andrés), que aún no existe.
    Cuando aterrice, se conecta su predicción aquí y el resto no cambia.

    Args:
        predicciones: salida de `construir_predicciones` (aporta `cct`, `id_ciclo`, riesgo).
        driver_por_escuela: CCT → código de driver (`D1`…`D6`).

    Returns:
        DataFrame con las columnas de `gold.recomendaciones`, sólo para los CCT con driver conocido.

    Raises:
        ValueError: si algún driver no está en el catálogo.
    """
    desconocidos = set(driver_por_escuela.values()) - set(CODIGOS_DRIVER)
    if desconocidos:
        raise ValueError(
            f"Drivers fuera del catálogo: {sorted(desconocidos)}. Esperados: {CODIGOS_DRIVER}."
        )

    con_driver = predicciones[predicciones["cct"].isin(driver_por_escuela)].copy()
    drivers = con_driver["cct"].map(driver_por_escuela)

    filas = pd.DataFrame(
        {
            "cct": con_driver["cct"].to_numpy(),
            "id_ciclo": con_driver["id_ciclo"].to_numpy(),
            "driver_dominante": drivers.to_numpy(),
            "recomendacion": drivers.map(RECOMENDACION_POR_DRIVER).to_numpy(),
            "prioridad": [
                prioridad_de_riesgo(r).value for r in con_driver["indice_riesgo"].to_numpy()
            ],
        }
    )
    for fila in filas.to_dict(orient="records"):
        RecomendacionGold(**fila)
    return filas


def escribir(
    df: pd.DataFrame,
    tabla: Table,
    engine: Engine,
    metadata: MetaData,
) -> int:
    """Escribe con UPSERT sobre la llave primaria. Idempotente por diseño.

    Correr el job dos veces deja exactamente las mismas filas: la segunda corrida actualiza
    valores y `mlflow_run_id` en vez de duplicar. No borra ni trunca nada.

    Args:
        df: filas a publicar.
        tabla: tabla destino.
        engine: motor SQLAlchemy (PostgreSQL en producción, SQLite en pruebas).
        metadata: metadatos que contienen la tabla; se crean si no existen.

    Returns:
        Número de filas publicadas.

    Raises:
        NotImplementedError: si el motor no soporta UPSERT nativo.
    """
    if df.empty:
        return 0

    dialecto = engine.dialect.name
    if dialecto == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialecto == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:  # pragma: no cover - sólo usamos estos dos motores
        raise NotImplementedError(f"UPSERT no implementado para el dialecto {dialecto!r}.")

    llaves = [c.name for c in tabla.primary_key.columns]
    registros = df.to_dict(orient="records")

    with engine.begin() as conexion:
        if tabla.schema:
            conexion.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{tabla.schema}"')
        metadata.create_all(conexion, tables=[tabla])

        sentencia = insert(tabla).values(registros)
        actualizables = {
            c.name: sentencia.excluded[c.name] for c in tabla.columns if c.name not in llaves
        }
        conexion.execute(
            sentencia.on_conflict_do_update(index_elements=llaves, set_=actualizables)
        )
    return len(registros)


def _motor(url: str | None = None) -> Engine:
    """Crea el motor desde `--url`, `DATABASE_URL` o el `docker-compose.yml` local."""
    destino = url or os.environ.get("DATABASE_URL")
    if not destino:
        raise ValueError(
            "Falta el destino. Usa --url o define DATABASE_URL "
            "(p. ej. postgresql://postgres:...@localhost:5432/escuela_concausa_db)."
        )
    return create_engine(destino)


def main() -> int:
    """Entrena ML-01, construye las filas de Gold y las publica."""
    parser = argparse.ArgumentParser(description="Publica predicciones y recomendaciones (US-313).")
    parser.add_argument("--features", type=Path, default=Path("tests/fixtures/features_escuela_mock.csv"))
    parser.add_argument("--url", default=None, help="URL SQLAlchemy; por defecto DATABASE_URL")
    parser.add_argument("--run-id", default="local-sin-mlflow", help="mlflow_run_id a registrar")
    parser.add_argument("--esquema", default=ESQUEMA_GOLD)
    parser.add_argument("--ventanas", type=int, default=3)
    parser.add_argument(
        "--solo-predicciones",
        action="store_true",
        help="omite gold.recomendaciones (requiere ML-02, aún no disponible)",
    )
    args = parser.parse_args()

    features = cargar_features(args.features)
    resultado = entrenar_y_evaluar(features, n_ventanas=args.ventanas)
    print(f"ML-01 entrenado — MAE {resultado.mae_promedio:.4f} ± {resultado.mae_desviacion:.4f}")

    predicciones = construir_predicciones(features, resultado.modelo, args.run_id)
    print(f"Predicciones construidas: {len(predicciones)} filas (ciclo {predicciones['id_ciclo'].iloc[0]})")

    metadata, tabla_pred, _ = _metadatos(args.esquema)
    engine = _motor(args.url)
    escritas = escribir(predicciones, tabla_pred, engine, metadata)
    print(f"gold.{TABLA_PREDICCIONES}: {escritas} filas publicadas (upsert idempotente)")

    if args.solo_predicciones:
        print("gold.recomendaciones omitida: requiere ML-02 (US-302, pendiente).")
        return 0

    # Sin ML-02 no hay driver dominante real. Se publica vacío antes que inventar un driver.
    print(
        f"gold.{TABLA_RECOMENDACIONES}: sin publicar — `driver_dominante` es salida de ML-02 "
        "(US-302, pendiente). La maquinaria está lista: conecta su predicción a "
        "construir_recomendaciones()."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
