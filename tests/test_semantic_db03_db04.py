"""Pruebas del contrato semántico de los cubos de DB-03 y DB-04 (US-211a).

Convierten en algo que el CI puede hacer cumplir las reglas que este proyecto no puede
permitirse romper en la capa de BI:

* **`SIN_DATO` nunca es cero.** Si alguien —persona o IA— "arregla" un hueco con
  `COALESCE(d1, 0)`, el tablero afirmaría "aquí no hay problema" justo donde el Estado no
  está midiendo. Estas pruebas fallan si eso aparece.
* **Las salidas de ML se leen por `JOIN`**, nunca como columna del hecho
  (`Data_Model` §4.1). En el grano de escuela el `JOIN` además debe ser `LEFT`, para que la
  ficha exista aunque el modelo todavía no haya puntuado a la escuela.
* **Las razones se guardan como numerador y denominador**, para que se puedan reagregar con
  cualquier combinación de los filtros globales (AC-002.2).

Validación **estática**: no necesita base de datos ni dependencias fuera de `requirements.txt`.
La validación contra datos reales queda pendiente de `gold.*` (US-112 / US-113, Célula 1).

Contrato: `04_UX_Design/Cube_Specs_DB03_DB04.md` (DOC-CUBESPEC-DB0304).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SEMANTIC = RAIZ / "superset" / "semantic"

SQL_DB03 = SEMANTIC / "db03_cubo_escuela_360.sql"
SQL_DB04 = SEMANTIC / "db04_cubo_comparador_municipio.sql"
YAML_METRICAS = SEMANTIC / "metrics_db03_db04.yaml"

DRIVERS = ("d1", "d2", "d3", "d4", "d5", "d6")
UMBRAL_RIESGO = "0.6"

# Salidas de ML: viven en gold.predicciones / gold.recomendaciones, jamás en el hecho.
SALIDAS_ML = ("indice_riesgo", "driver_dominante", "recomendacion", "prioridad")


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
def db03() -> str:
    return sin_comentarios(leer(SQL_DB03))


@pytest.fixture(scope="module")
def db04() -> str:
    return sin_comentarios(leer(SQL_DB04))


# --------------------------------------------------------------------------- R2: SIN_DATO nunca es cero


@pytest.mark.parametrize("cubo", ["db03", "db04"])
def test_ningun_driver_se_rellena_con_cero(cubo: str, request: pytest.FixtureRequest) -> None:
    """Prohibido `COALESCE(d#, 0)`: la ausencia de dato no es un cero (Data_Model §1)."""
    sql = request.getfixturevalue(cubo)
    for driver in DRIVERS:
        patron = rf"coalesce\s*\(\s*\w*\.?{driver}\b[^)]*,\s*0"
        assert not re.search(patron, sql, re.IGNORECASE), (
            f"{cubo}: `{driver}` se rellena con cero. SIN_DATO nunca es cero (regla R2)."
        )


@pytest.mark.parametrize("cubo", ["db03", "db04"])
def test_el_riesgo_no_se_rellena_con_cero(cubo: str, request: pytest.FixtureRequest) -> None:
    """Una escuela sin predicción no es una escuela con riesgo 0."""
    sql = request.getfixturevalue(cubo)
    patron = r"coalesce\s*\(\s*\w*\.?indice_riesgo\b[^)]*,\s*0"
    assert not re.search(patron, sql, re.IGNORECASE), (
        f"{cubo}: `indice_riesgo` se rellena con cero. Debe quedar nulo y declararse SIN_DATO."
    )


def test_db03_expone_las_banderas_de_cobertura(db03: str) -> None:
    """Cada driver viaja con su bandera, y hay bandera para predicción y recomendación."""
    for driver in DRIVERS:
        assert f"{driver}_cobertura" in db03, f"Falta la bandera {driver}_cobertura en DB-03"
    assert "cobertura_prediccion" in db03
    assert "cobertura_recomendacion" in db03


def test_db04_publica_el_denominador_real_de_cada_driver(db04: str) -> None:
    """El promedio de un driver se calcula sobre las escuelas con cobertura OK, no sobre el total."""
    for driver in DRIVERS:
        assert f"escuelas_con_{driver}" in db04, (
            f"Falta el denominador `escuelas_con_{driver}`: sin él, el promedio de {driver} "
            "se calcularía sobre escuelas que nunca se midieron."
        )
        patron = rf"sum\s*\(\s*\w*\.?{driver}\s*\)\s*filter\s*\(\s*where\s+\w*\.?{driver}_cobertura\s*=\s*'OK'"
        assert re.search(patron, db04, re.IGNORECASE), (
            f"`suma_{driver}` debe sumar solo sobre {driver}_cobertura = 'OK'."
        )


def test_db04_no_guarda_promedios_ya_calculados(db04: str) -> None:
    """Un promedio no se puede reagregar: el cubo guarda componentes, la razón vive en la capa semántica."""
    assert not re.search(r"\bavg\s*\(", db04, re.IGNORECASE), (
        "DB-04 guarda un promedio precalculado. Al quitar el filtro de nivel, Superset "
        "promediaría promedios y daría un número incorrecto (Cube_Specs §4.3)."
    )


# --------------------------------------------------------------------------- R1: las salidas de ML van por JOIN


@pytest.mark.parametrize("cubo", ["db03", "db04"])
def test_las_salidas_de_ml_no_se_leen_del_hecho(cubo: str, request: pytest.FixtureRequest) -> None:
    """`fact_escuela_ciclo` solo tiene hechos observados (Data_Model §4.1)."""
    sql = request.getfixturevalue(cubo)
    for salida in SALIDAS_ML:
        assert not re.search(rf"\bf\.{salida}\b", sql), (
            f"{cubo}: `f.{salida}` se lee del hecho. Las salidas de ML se consultan por JOIN "
            "a gold.predicciones / gold.recomendaciones."
        )


def test_db03_une_las_salidas_de_ml_con_left_join(db03: str) -> None:
    """La ficha debe existir aunque el modelo aún no haya puntuado a la escuela (Cube_Specs §2.2)."""
    for tabla in ("gold.predicciones", "gold.recomendaciones"):
        assert re.search(rf"left\s+join\s+{re.escape(tabla)}\b", db03, re.IGNORECASE), (
            f"DB-03 debe unir {tabla} con LEFT JOIN: con JOIN interno la escuela desaparecería "
            "del tablero sin explicación."
        )


def test_db04_une_las_predicciones_con_left_join(db04: str) -> None:
    """Un municipio sin predicciones sigue siendo comparable por matrícula y contexto."""
    assert re.search(r"left\s+join\s+gold\.predicciones\b", db04, re.IGNORECASE)


@pytest.mark.parametrize("cubo", ["db03", "db04"])
def test_el_join_de_predicciones_filtra_el_modelo(cubo: str, request: pytest.FixtureRequest) -> None:
    """`gold.predicciones` guarda ML-01/02/03: sin filtrar el modelo, el riesgo se mezcla."""
    sql = request.getfixturevalue(cubo)
    assert re.search(r"modelo\s*=\s*'ML-01'", sql), f"{cubo}: falta el filtro `modelo = 'ML-01'`."


@pytest.mark.parametrize("cubo", ["db03", "db04"])
def test_el_join_de_ml_usa_la_llave_completa(cubo: str, request: pytest.FixtureRequest) -> None:
    """La llave de unión es (cct, id_ciclo): unir solo por cct rompería el grano por ciclo."""
    sql = request.getfixturevalue(cubo)
    assert re.search(r"f\.cct\s*=\s*p\.cct", sql)
    assert re.search(r"f\.id_ciclo\s*=\s*p\.id_ciclo", sql)


# --------------------------------------------------------------------------- R3: umbral de negocio


@pytest.mark.parametrize("cubo", ["db03", "db04"])
def test_el_umbral_de_riesgo_es_el_ratificado(cubo: str, request: pytest.FixtureRequest) -> None:
    """0.6 = perder ~5% de matrícula, ratificado el 2026-08-13 (Indice_Riesgo_ML01)."""
    sql = request.getfixturevalue(cubo)
    assert re.search(rf"indice_riesgo\s*>=\s*{UMBRAL_RIESGO}", sql), (
        f"{cubo}: el umbral de 'escuela en riesgo' debe ser >= {UMBRAL_RIESGO}."
    )


# --------------------------------------------------------------------------- grano y filtros globales


def test_db03_tiene_grano_de_escuela_por_ciclo(db03: str) -> None:
    """Grano cct × ciclo (Data_Model §4.3)."""
    assert re.search(r"\bf\.cct\b", db03)
    assert re.search(r"\bf\.id_ciclo\b", db03)
    assert not re.search(r"\bgroup\s+by\b", db03, re.IGNORECASE), (
        "DB-03 está al grano del hecho: no debe agregar."
    )


def test_db04_agrupa_al_grano_declarado(db04: str) -> None:
    """Grano cve_mun × nivel × ciclo: sin `nivel` no se puede cumplir AC-002.2 en DB-04."""
    group_by = db04.lower().split("group by", 1)
    assert len(group_by) == 2, "DB-04 debe agregar con GROUP BY."
    clausula = group_by[1]
    for columna in ("cve_mun", "nivel", "id_ciclo"):
        assert columna in clausula, f"Falta `{columna}` en el GROUP BY de DB-04."


@pytest.mark.parametrize("cubo", ["db03", "db04"])
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
    assert nombres == {"cubo_escuela_360", "cubo_comparador_municipio"}


def test_el_yaml_declara_los_tres_filtros_globales(metricas: dict) -> None:
    """AC-002.2: ciclo, entidad y nivel aplican al conjunto de tableros."""
    nombres = {f["nombre"] for f in metricas["filtros_globales"]}
    assert nombres == {"ciclo", "entidad", "nivel"}


def test_el_grano_del_yaml_coincide_con_el_sql(metricas: dict) -> None:
    granos = {d["nombre"]: d["grano"] for d in metricas["datasets"]}
    assert granos["cubo_escuela_360"] == ["cct", "id_ciclo"]
    assert granos["cubo_comparador_municipio"] == ["cve_mun", "nivel", "id_ciclo"]


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


def test_el_porcentaje_en_riesgo_usa_las_escuelas_puntuadas(metricas: dict) -> None:
    """Decir '10% en riesgo' cuando solo se puntuó al 30% inventaría una cobertura inexistente."""
    db04 = next(d for d in metricas["datasets"] if d["nombre"] == "cubo_comparador_municipio")
    metrica = next(m for m in db04["metricas"] if m["nombre"] == "pct_escuelas_en_riesgo")
    assert "escuelas_con_prediccion" in metrica["expresion"]
    assert metrica.get("denominador_visible") == "escuelas_con_prediccion"


def test_cada_metrica_de_driver_declara_su_cobertura(metricas: dict) -> None:
    db04 = next(d for d in metricas["datasets"] if d["nombre"] == "cubo_comparador_municipio")
    por_nombre = {m["nombre"]: m for m in db04["metricas"]}
    for driver in DRIVERS:
        metrica = por_nombre[f"{driver}_promedio"]
        assert metrica["cobertura"] == f"escuelas_con_{driver}"
