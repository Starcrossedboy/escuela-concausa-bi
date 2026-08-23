"""Pruebas del contrato semántico de los cubos de DB-05 y DB-08 (US-211b).

Mismas reglas que `test_semantic_db03_db04.py`, ahora para el análisis por driver y el
explorador del cubo, más las reglas propias de este contrato (formato largo/unpivot y v1 sin
salidas de ML):

* **`SIN_DATO` nunca es cero.** Si alguien —persona o IA— "arregla" un hueco con
  `COALESCE(d1, 0)` o con `COALESCE(valor, 0)`, el tablero afirmaría "aquí no hay problema"
  justo donde el Estado no está midiendo (D5/agua hoy es `SIN_DATO` al 100%). Estas pruebas
  fallan si eso aparece.
* **v1 no lee salidas de ML.** `cubo_driver` y `cubo_pivot` analizan el driver observado, no la
  predicción — a diferencia de los cubos de DB-03/DB-04 (Cube_Specs §2.1).
* **Formato largo (unpivot):** una fila por driver, no columnas `d1..d6`. Toda métrica que se
  sume debe agruparse o filtrarse por `id_driver`, o se infla ×6 (Cube_Specs §2.2/§3.6).
* **Las razones se guardan como numerador y denominador**, para que se puedan reagregar con
  cualquier combinación de los filtros globales (AC-002.2).

Validación **estática**: no necesita base de datos ni dependencias fuera de `requirements.txt`.
La validación contra datos reales queda pendiente de `gold.cubo_driver`/`gold.cubo_pivot`
(US-113, Célula 1).

Contrato: `04_UX_Design/Cube_Specs_DB05_DB08.md` (DOC-CUBESPEC-DB0508).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SEMANTIC = RAIZ / "superset" / "semantic"

SQL_DB05 = SEMANTIC / "db05_cubo_driver.sql"
SQL_DB08 = SEMANTIC / "db08_cubo_pivot.sql"
YAML_METRICAS = SEMANTIC / "metrics_db05_db08.yaml"

DRIVERS = ("d1", "d2", "d3", "d4", "d5", "d6")
DRIVER_IDS = ("D1", "D2", "D3", "D4", "D5", "D6")

# Salidas de ML: viven en gold.predicciones / gold.recomendaciones. v1 de estos dos cubos no
# las lee (Cube_Specs §2.1) -- a diferencia de DB-03/DB-04.
SALIDAS_ML_TABLAS = ("gold.predicciones", "gold.recomendaciones")


# --------------------------------------------------------------------------- utilidades


def leer(ruta: Path) -> str:
    """Lee un artefacto de la capa semántica; falla con un mensaje útil si no está."""
    assert ruta.exists(), f"Falta el artefacto de la capa semántica: {ruta}"
    texto = ruta.read_text(encoding="utf-8")
    assert texto.strip(), f"{ruta.name} está vacío"
    return texto


def sin_comentarios(sql: str) -> str:
    """Quita los comentarios `--` para que las reglas no se cumplan 'de mentiras' en la prosa."""
    return "\n".join(linea.split("--")[0] for linea in sql.splitlines())


@pytest.fixture(scope="module")
def db05() -> str:
    return sin_comentarios(leer(SQL_DB05))


@pytest.fixture(scope="module")
def db08() -> str:
    return sin_comentarios(leer(SQL_DB08))


# --------------------------------------------------------------------------- R2: SIN_DATO nunca es cero


@pytest.mark.parametrize("cubo", ["db05", "db08"])
def test_ningun_driver_se_rellena_con_cero(cubo: str, request: pytest.FixtureRequest) -> None:
    """Prohibido `COALESCE(d#, 0)`: la ausencia de dato no es un cero (Data_Model §1)."""
    sql = request.getfixturevalue(cubo)
    for driver in DRIVERS:
        patron = rf"coalesce\s*\(\s*\w*\.?{driver}\b[^)]*,\s*0"
        assert not re.search(patron, sql, re.IGNORECASE), (
            f"{cubo}: `{driver}` se rellena con cero. SIN_DATO nunca es cero (regla R2)."
        )


@pytest.mark.parametrize("cubo", ["db05", "db08"])
def test_ningun_valor_agregado_se_rellena_con_cero(cubo: str, request: pytest.FixtureRequest) -> None:
    """El valor del driver (ya unpivoteado) tampoco se rellena con cero."""
    sql = request.getfixturevalue(cubo)
    for columna in ("valor", "suma_valor", "valor_driver"):
        patron = rf"coalesce\s*\(\s*\w*\.?{columna}\b[^)]*,\s*0"
        assert not re.search(patron, sql, re.IGNORECASE), (
            f"{cubo}: `{columna}` se rellena con cero. SIN_DATO nunca es cero (regla R2)."
        )


def test_db05_publica_el_denominador_real_del_driver(db05: str) -> None:
    """El promedio del driver se calcula sobre las escuelas con cobertura OK, no sobre el total."""
    assert "escuelas_con_dato" in db05, (
        "Falta el denominador `escuelas_con_dato`: sin él, el promedio del driver se "
        "calcularía sobre escuelas que nunca se midieron."
    )
    patron = r"sum\s*\(\s*\w*\.?valor\s*\)\s*filter\s*\(\s*where\s+\w*\.?cobertura\s*=\s*'OK'"
    assert re.search(patron, db05, re.IGNORECASE), (
        "`suma_valor` debe sumar solo sobre cobertura = 'OK'."
    )


def test_db05_no_guarda_promedio_ya_calculado(db05: str) -> None:
    """Un promedio no se puede reagregar: el cubo guarda componentes, la razón vive en el YAML."""
    assert not re.search(r"\bavg\s*\(", db05, re.IGNORECASE), (
        "DB-05 guarda un promedio precalculado. Al quitar el filtro de nivel, Superset "
        "promediaría promedios y daría un número incorrecto (Cube_Specs §3)."
    )


def test_db05_expone_la_bandera_de_cobertura(db05: str) -> None:
    assert "cobertura_driver" in db05, "Falta `cobertura_driver` en DB-05."


def test_db08_expone_la_bandera_de_cobertura(db08: str) -> None:
    assert "cobertura_driver" in db08, "Falta `cobertura_driver` en DB-08."


# --------------------------------------------------------------------------- v1: sin salidas de ML


@pytest.mark.parametrize("cubo", ["db05", "db08"])
def test_v1_no_depende_de_salidas_de_ml(cubo: str, request: pytest.FixtureRequest) -> None:
    """A diferencia de DB-03/DB-04, v1 de estos cubos analiza el driver observado, no la
    predicción (Cube_Specs §2.1). Si una iteración futura agrega ML, debe ser por LEFT JOIN."""
    sql = request.getfixturevalue(cubo)
    for tabla in SALIDAS_ML_TABLAS:
        assert tabla not in sql.lower(), (
            f"{cubo}: v1 no debe leer {tabla} (Cube_Specs §2.1). Si esto cambió, actualiza "
            "también esta prueba para exigir LEFT JOIN con la llave completa (cct, id_ciclo)."
        )


# --------------------------------------------------------------------------- formato largo (unpivot)


@pytest.mark.parametrize("cubo", ["db05", "db08"])
def test_unpivotea_los_seis_drivers(cubo: str, request: pytest.FixtureRequest) -> None:
    """Formato largo: cada uno de los 6 drivers debe aparecer como literal (Cube_Specs §2.2)."""
    sql = request.getfixturevalue(cubo)
    for id_driver in DRIVER_IDS:
        assert f"'{id_driver}'" in sql, f"{cubo}: falta el bloque unpivot de {id_driver}."


@pytest.mark.parametrize("cubo", ["db05", "db08"])
def test_usa_union_all_para_apilar_los_drivers(cubo: str, request: pytest.FixtureRequest) -> None:
    """6 bloques (uno por driver) requieren al menos 5 `UNION ALL`."""
    sql = request.getfixturevalue(cubo)
    ocurrencias = len(re.findall(r"union\s+all", sql, re.IGNORECASE))
    assert ocurrencias >= 5, f"{cubo}: se esperaban >= 5 `UNION ALL` (6 drivers), hay {ocurrencias}."


# --------------------------------------------------------------------------- grano y filtros globales


def test_db05_agrupa_al_grano_declarado(db05: str) -> None:
    """Grano id_driver × cve_mun × nivel × ciclo: sin `nivel` no se puede cumplir AC-002.2."""
    group_by = db05.lower().split("group by", 1)
    assert len(group_by) == 2, "DB-05 debe agregar con GROUP BY."
    clausula = group_by[1]
    for columna in ("id_driver", "cve_mun", "nivel", "id_ciclo"):
        assert columna in clausula, f"Falta `{columna}` en el GROUP BY de DB-05."


def test_db08_no_agrega_al_grano_del_hecho(db08: str) -> None:
    """DB-08 está al grano de detalle (cct × driver × ciclo): no debe agregar."""
    assert not re.search(r"\bgroup\s+by\b", db08, re.IGNORECASE), (
        "DB-08 está al grano del hecho: no debe agregar."
    )


@pytest.mark.parametrize("cubo", ["db05", "db08"])
def test_los_filtros_globales_tienen_columna(cubo: str, request: pytest.FixtureRequest) -> None:
    """Ciclo, entidad y nivel deben existir en ambos cubos (AC-002.2)."""
    sql = request.getfixturevalue(cubo)
    for columna in ("id_ciclo", "cve_ent", "nivel"):
        assert columna in sql, f"{cubo}: falta la columna del filtro global `{columna}`."


# --------------------------------------------------------------------------- capa semántica (YAML)


@pytest.fixture(scope="module")
def metricas() -> dict:
    """Carga el YAML de métricas. `pyyaml` no está en requirements.txt: si falta, se omite."""
    yaml = pytest.importorskip("yaml", reason="pyyaml no está en requirements.txt")
    return yaml.safe_load(leer(YAML_METRICAS))


def test_el_yaml_declara_los_dos_cubos(metricas: dict) -> None:
    nombres = {d["nombre"] for d in metricas["datasets"]}
    assert nombres == {"cubo_driver", "cubo_pivot"}


def test_el_yaml_declara_los_tres_filtros_globales(metricas: dict) -> None:
    """AC-002.2: ciclo, entidad y nivel aplican al conjunto de tableros."""
    nombres = {f["nombre"] for f in metricas["filtros_globales"]}
    assert nombres == {"ciclo", "entidad", "nivel"}


def test_el_grano_del_yaml_coincide_con_el_sql(metricas: dict) -> None:
    granos = {d["nombre"]: d["grano"] for d in metricas["datasets"]}
    assert granos["cubo_driver"] == ["id_driver", "cve_mun", "nivel", "id_ciclo"]
    assert granos["cubo_pivot"] == ["cct", "id_driver", "id_ciclo"]


@pytest.mark.parametrize("cubo", ["cubo_driver", "cubo_pivot"])
def test_declara_dimension_obligatoria_en_agregacion(cubo: str, metricas: dict) -> None:
    """Sin agrupar/filtrar por id_driver, las métricas del formato largo se inflan x6."""
    dataset = next(d for d in metricas["datasets"] if d["nombre"] == cubo)
    assert dataset.get("dimension_obligatoria_en_agregacion") == "id_driver"


def test_toda_razon_protege_la_division(metricas: dict) -> None:
    """Una división sin `NULLIF` revienta o miente cuando el denominador es cero."""
    for dataset in metricas["datasets"]:
        for metrica in dataset["metricas"]:
            expresion = metrica.get("expresion", "")
            if "/" in expresion:
                assert "NULLIF" in expresion.upper(), (
                    f"{dataset['nombre']}.{metrica['nombre']}: división sin NULLIF."
                )


def test_ninguna_metrica_rellena_con_cero(metricas: dict) -> None:
    for dataset in metricas["datasets"]:
        for metrica in dataset["metricas"]:
            assert "COALESCE" not in metrica.get("expresion", "").upper(), (
                f"{dataset['nombre']}.{metrica['nombre']}: no se rellenan huecos con COALESCE."
            )


def test_kpi19_y_kpi20_estan_propuestos(metricas: dict) -> None:
    """KPI-19 (DB-05) y KPI-20 (DB-08) están libres en el catálogo: se registran como propuesta,
    no como IDs ya ratificados (Cube_Specs §5.1/§8.3)."""
    propuestos = {
        kpi["id"]
        for dataset in metricas["datasets"]
        for kpi in dataset.get("kpis_propuestos", [])
    }
    assert {"KPI-19", "KPI-20"} <= propuestos


def test_pct_sin_dato_reusa_kpi06(metricas: dict) -> None:
    """El % de escuelas sin dato del driver reusa KPI-06 (dueño DB-07): no se inventa un ID nuevo."""
    cubo_driver = next(d for d in metricas["datasets"] if d["nombre"] == "cubo_driver")
    metrica = next(m for m in cubo_driver["metricas"] if m["nombre"] == "pct_escuelas_sin_dato")
    assert metrica["kpi"] == "KPI-06"


def test_cubo_driver_declara_grano_canonico_y_cambio_solicitado(metricas: dict) -> None:
    """Sólo `cubo_driver` necesita el cambio de grano estilo DEC-008 (Cube_Specs §8.1); `cubo_pivot`
    no lo necesita (Cube_Specs §8.2)."""
    cubo_driver = next(d for d in metricas["datasets"] if d["nombre"] == "cubo_driver")
    assert cubo_driver.get("grano_canonico_actual") == ["id_driver", "cve_mun", "id_ciclo"]
    assert cubo_driver.get("cambio_de_grano_solicitado_a"), (
        "cubo_driver debe documentar a quién se le solicitó el cambio de grano."
    )
    cubo_pivot = next(d for d in metricas["datasets"] if d["nombre"] == "cubo_pivot")
    assert "cambio_de_grano_solicitado_a" not in cubo_pivot


def test_cada_metrica_de_valor_declara_su_cobertura(metricas: dict) -> None:
    cubo_driver = next(d for d in metricas["datasets"] if d["nombre"] == "cubo_driver")
    metrica_driver = next(m for m in cubo_driver["metricas"] if m["nombre"] == "valor_promedio_driver")
    assert metrica_driver["cobertura"] == "cobertura_driver"

    cubo_pivot = next(d for d in metricas["datasets"] if d["nombre"] == "cubo_pivot")
    metrica_pivot = next(m for m in cubo_pivot["metricas"] if m["nombre"] == "valor_driver")
    assert metrica_pivot["cobertura"] == "cobertura_driver"
