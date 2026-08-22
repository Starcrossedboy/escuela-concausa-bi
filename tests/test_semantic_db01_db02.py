"""Pruebas del contrato semántico de DB-01 y DB-02 (US-203).

Mismas reglas que `test_semantic_db03_db04.py`, ahora para el tablero ejecutivo y
el mapa de riesgo territorial:

* **`SIN_DATO` nunca es cero.** Un municipio sin predicciones ML-01 se pinta
  SIN_DATO; si alguien lo "arregla" con `COALESCE(indice_riesgo, 0)` el mapa
  mentiría pintando calma donde no hay medición.
* **Las salidas de ML se leen por `LEFT JOIN`** con la llave completa
  (`cct`, `id_ciclo`) y filtro de modelo (Data_Model §4.1).
* **El umbral de riesgo es >= 0.6** (R3, ratificado 2026-08-13).
* **Los porcentajes dividen entre el denominador real**: `% en riesgo` sobre
  escuelas *puntuadas*, no sobre el total.
* **El mock de ML es inofensivo**: determinístico, idempotente y sin DDL/DML
  destructivo (plan de sprint C2: mock mientras llega C3).

Validación estática: no necesita base de datos. La validación contra datos
corre en local vía `superset/sync_semantic_layer.py --validar-datos`.

Contratos: `04_UX_Design/Screen_Specs.md` §2/§4 y `Cube_Specs_DB03_DB04.md` §4.3.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SEMANTIC = RAIZ / "superset" / "semantic"
DASHBOARDS = RAIZ / "superset" / "dashboards"
MOCK = RAIZ / "superset" / "mock" / "gold_ml_outputs_mock.sql"

SQL_DB01_CUBO = SEMANTIC / "db01_cubo_matricula.sql"
SQL_DB01_DIST = SEMANTIC / "db01_distribucion_escuelas.sql"
SQL_DB01_DRIVER = SEMANTIC / "db01_driver_dominante.sql"
SQL_DB02_CUBO = SEMANTIC / "db02_cubo_riesgo_territorial.sql"
SQL_DB02_PUNTOS = SEMANTIC / "db02_puntos_escuela.sql"
YAML_METRICAS = SEMANTIC / "metrics_db01_db02.yaml"
YAML_DB01 = DASHBOARDS / "db01_ejecutivo.yaml"
YAML_DB02 = DASHBOARDS / "db02_mapa_riesgo.yaml"

UMBRAL_RIESGO = "0.6"

# Salidas de ML: viven en gold.predicciones / gold.recomendaciones, jamás en el hecho.
SALIDAS_ML = ("indice_riesgo", "driver_dominante", "recomendacion", "prioridad")


# --------------------------------------------------------------------------- utilidades


def leer(ruta: Path) -> str:
    """Lee un artefacto; falla con un mensaje útil si no está."""
    assert ruta.exists(), f"Falta el artefacto: {ruta}"
    texto = ruta.read_text(encoding="utf-8")
    assert texto.strip(), f"{ruta.name} está vacío"
    return texto


def sin_comentarios(sql: str) -> str:
    """Quita los comentarios `--` para que las reglas no se cumplan 'de mentiras'."""
    return "\n".join(linea.split("--")[0] for linea in sql.splitlines())


@pytest.fixture(scope="module")
def db01_cubo() -> str:
    return sin_comentarios(leer(SQL_DB01_CUBO))


@pytest.fixture(scope="module")
def db01_dist() -> str:
    return sin_comentarios(leer(SQL_DB01_DIST))


@pytest.fixture(scope="module")
def db01_driver() -> str:
    return sin_comentarios(leer(SQL_DB01_DRIVER))


@pytest.fixture(scope="module")
def db02_cubo() -> str:
    return sin_comentarios(leer(SQL_DB02_CUBO))


@pytest.fixture(scope="module")
def db02_puntos() -> str:
    return sin_comentarios(leer(SQL_DB02_PUNTOS))


# --------------------------------------------------------------------------- R2: SIN_DATO nunca es cero


@pytest.mark.parametrize("fixture_name", ["db02_cubo", "db02_puntos"])
def test_el_riesgo_no_se_rellena_con_cero(fixture_name: str, request: pytest.FixtureRequest) -> None:
    """Una escuela/municipio sin predicción no tiene riesgo 0: tiene SIN_DATO."""
    sql = request.getfixturevalue(fixture_name)
    patron = r"coalesce\s*\(\s*\w*\.?indice_riesgo\b[^)]*,\s*0"
    assert not re.search(patron, sql, re.IGNORECASE), (
        f"{fixture_name}: `indice_riesgo` se rellena con cero. Debe quedar nulo "
        "y la cobertura declararse 'SIN_DATO' (regla R2)."
    )


def test_la_etiqueta_sin_dato_es_categoria_no_metrica(db01_driver: str) -> None:
    """En driver dominante, COALESCE solo puede etiquetar la categoría vacía."""
    # Permitido: etiquetar la categoría cuando ML-02 aún no explicó la escuela.
    assert re.search(r"coalesce\s*\([^)]*,\s*'SIN_DATO'\s*\)", db01_driver, re.IGNORECASE)
    # Prohibido: rellenar conteos o métricas con cero.
    assert not re.search(r"coalesce\s*\(\s*(sum|count)\s*\(", db01_driver, re.IGNORECASE), (
        "driver_dominante: no se rellenan agregaciones con COALESCE."
    )


# --------------------------------------------------------------------------- R1: las salidas de ML van por JOIN


@pytest.mark.parametrize("fixture_name", ["db02_cubo", "db02_puntos"])
def test_las_salidas_de_ml_no_se_leen_del_hecho(fixture_name: str, request: pytest.FixtureRequest) -> None:
    """`fact_escuela_ciclo` solo tiene hechos observados (Data_Model §4.1)."""
    sql = request.getfixturevalue(fixture_name)
    for salida in SALIDAS_ML:
        assert not re.search(rf"\bf\.{salida}\b", sql), (
            f"{fixture_name}: `f.{salida}` se lee del hecho. Las salidas de ML se "
            "consultan por JOIN a gold.predicciones."
        )


@pytest.mark.parametrize("fixture_name", ["db02_cubo", "db02_puntos"])
def test_las_predicciones_se_une_con_left_join(fixture_name: str, request: pytest.FixtureRequest) -> None:
    """Con INNER JOIN, una escuela sin predicción desaparecería del mapa sin explicación."""
    sql = request.getfixturevalue(fixture_name)
    assert re.search(r"left\s+join\s+gold\.predicciones\b", sql, re.IGNORECASE), (
        f"{fixture_name}: gold.predicciones debe unirse con LEFT JOIN."
    )


@pytest.mark.parametrize("fixture_name", ["db02_cubo", "db02_puntos"])
def test_el_join_usa_llave_completa_y_filtro_de_modelo(fixture_name: str, request: pytest.FixtureRequest) -> None:
    """(cct, id_ciclo) + modelo='ML-01': sin llave completa se mezclan ciclos; sin
    filtro de modelo se mezcla el riesgo con otras salidas del catálogo."""
    sql = request.getfixturevalue(fixture_name)
    assert re.search(r"f\.cct\s*=\s*p\.cct", sql)
    assert re.search(r"f\.id_ciclo\s*=\s*p\.id_ciclo", sql)
    assert re.search(r"modelo\s*=\s*'ML-01'", sql)


def test_driver_dominante_viene_de_recomendaciones_por_left_join(db01_driver: str) -> None:
    """KPI-07 lee la salida prescriptiva de ML-02; LEFT porque el modelo va llegando."""
    assert re.search(r"left\s+join\s+gold\.recomendaciones\b", db01_driver, re.IGNORECASE)
    assert re.search(r"f\.cct\s*=\s*r\.cct", db01_driver)
    assert re.search(r"f\.id_ciclo\s*=\s*r\.id_ciclo", db01_driver)
    assert not re.search(r"\bf\.(driver_dominante|recomendacion|prioridad)\b", db01_driver)


# --------------------------------------------------------------------------- R3: umbral de negocio


def test_el_umbral_de_riesgo_es_el_ratificado(db02_cubo: str, db02_puntos: str) -> None:
    """0.6 = perder ~5% de matrícula, ratificado el 2026-08-13 (Indice_Riesgo_ML01)."""
    for nombre, sql in (("db02_cubo", db02_cubo), ("db02_puntos", db02_puntos)):
        assert re.search(rf"indice_riesgo\s*>=\s*{UMBRAL_RIESGO}", sql), (
            f"{nombre}: el umbral de 'escuela en riesgo' debe ser >= {UMBRAL_RIESGO} (R3)."
        )


def test_sin_prediccion_no_es_en_riesgo(db02_puntos: str) -> None:
    """La escuela sin predicción viaja con en_riesgo nulo, jamás FALSE ni TRUE."""
    patron = r"when\s+p\.indice_riesgo\s+is\s+null\s+then\s+null"
    assert re.search(patron, db02_puntos, re.IGNORECASE), (
        "db02_puntos: `en_riesgo` debe ser NULL cuando no hay predicción."
    )
    assert re.search(r"cobertura_prediccion", db02_puntos), (
        "db02_puntos: falta la bandera cobertura_prediccion."
    )


def test_el_cubo_declara_cobertura_por_municipio(db02_cubo: str) -> None:
    assert "cobertura_riesgo" in db02_cubo, (
        "db02_cubo: falta cobertura_riesgo para pintar SIN_DATO en el coroplético."
    )
    assert re.search(r"when\s+count\s*\(\s*\w*\.?cct\s*\)\s*=\s*0\s+then\s+'SIN_DATO'",
                     db02_cubo, re.IGNORECASE)


# --------------------------------------------------------------------------- grano y filtros globales


def test_db01_cubo_agrupa_al_grano_declarado(db01_cubo: str) -> None:
    """Grano cve_mun × nivel × ciclo (Screen_Specs §2)."""
    clausula = db01_cubo.lower().split("group by", 1)[1]
    for columna in ("cve_mun", "nivel", "id_ciclo"):
        assert columna in clausula, f"Falta `{columna}` en el GROUP BY de DB-01 cubo."


def test_distribucion_agrupa_por_nivel_sostenimiento_ciclo(db01_dist: str) -> None:
    clausula = db01_dist.lower().split("group by", 1)[1]
    for columna in ("nivel", "sostenimiento", "id_ciclo"):
        assert columna in clausula, (
            f"Falta `{columna}` en el GROUP BY de distribución de escuelas."
        )


def test_driver_dominante_agrupa_por_driver_y_ciclo(db01_driver: str) -> None:
    clausula = db01_driver.lower().split("group by", 1)[1]
    for columna in ("id_driver", "id_ciclo"):
        assert columna in clausula, f"Falta `{columna}` en el GROUP BY de driver dominante."


def test_db02_cubo_agrupa_al_mismo_grano_que_db04(db02_cubo: str) -> None:
    """Mismo grano que cubo_comparador (DEC-008): cve_mun × nivel × ciclo."""
    clausula = db02_cubo.lower().split("group by", 1)[1]
    for columna in ("cve_mun", "nivel", "id_ciclo"):
        assert columna in clausula, f"Falta `{columna}` en el GROUP BY de DB-02 cubo."


def test_puntos_esta_al_grano_del_hecho(db02_puntos: str) -> None:
    """La capa de puntos no agrega: cada CCT es un marcador (Screen_Specs §2)."""
    assert re.search(r"\bf\.cct\b", db02_puntos)
    assert not re.search(r"\bgroup\s+by\b", db02_puntos, re.IGNORECASE)


def test_los_componentes_son_aditivos_no_promedios(db01_cubo: str, db02_cubo: str) -> None:
    """Numerador y denominador por separado (patron DEC-008): la razón vive en el YAML."""
    for nombre, sql in (("db01_cubo", db01_cubo), ("db02_cubo", db02_cubo)):
        assert not re.search(r"\bavg\s*\(", sql, re.IGNORECASE), (
            f"{nombre} guarda un promedio precalculado; al quitar filtros Superset "
            "promediaría promedios (Cube_Specs §4.3)."
        )


def test_variacion_es_ponderada_por_matricula(db01_cubo: str, db02_cubo: str) -> None:
    """KPI-02 pondera por matrícula: SUM(variacion * matricula), nunca AVG(variacion)."""
    for nombre, sql in (("db01_cubo", db01_cubo), ("db02_cubo", db02_cubo)):
        assert re.search(
            r"sum\s*\(\s*f\.variacion_matricula\s*\*\s*f\.matricula_total\s*\)",
            sql, re.IGNORECASE,
        ), f"{nombre}: falta el componente ponderado variacion_x_matricula."


def test_los_filtros_globales_tienen_columna(db01_cubo: str, db02_cubo: str, db01_dist: str) -> None:
    """AC-002.2: ciclo, entidad y nivel deben existir donde el tablero los filtra."""
    for nombre, sql in (("db01_cubo", db01_cubo), ("db02_cubo", db02_cubo)):
        for columna in ("id_ciclo", "cve_ent", "nivel"):
            assert columna in sql, f"{nombre}: falta la columna del filtro global `{columna}`."
    assert "id_ciclo" in db01_dist and "nivel" in db01_dist


# --------------------------------------------------------------------------- capa semántica (YAML)


@pytest.fixture(scope="module")
def metricas() -> dict:
    yaml = pytest.importorskip("yaml", reason="pyyaml no está en requirements.txt")
    return yaml.safe_load(leer(YAML_METRICAS))


@pytest.fixture(scope="module")
def datasets_por_nombre(metricas: dict) -> dict[str, dict]:
    return {d["nombre"]: d for d in metricas["datasets"]}


def test_el_yaml_declara_los_seis_datasets(metricas: dict) -> None:
    nombres = {d["nombre"] for d in metricas["datasets"]}
    assert nombres == {
        "db01_cubo_matricula",
        "db01_distribucion_escuelas",
        "db01_driver_dominante",
        "db02_cubo_riesgo_territorial",
        "db02_coropletico",
        "db02_puntos_escuela",
    }


def test_el_coropletico_no_tiene_nivel_en_el_grano(metricas: dict) -> None:
    """Con `nivel` en el grano, el JOIN con la geometría dibujaría polígonos superpuestos."""
    coro = next(d for d in metricas["datasets"] if d["nombre"] == "db02_coropletico")
    assert coro["grano"] == ["cve_mun", "id_ciclo"]
    sql = sin_comentarios(leer(SEMANTIC / coro["sql"]))
    assert not re.search(r"\bnivel\b", sql.split("WITH riesgo")[1]), (
        "db02_coropletico: no debe exponer `nivel` (polígonos duplicados por nivel educativo)."
    )


def test_el_yaml_declara_los_tres_filtros_globales(metricas: dict) -> None:
    nombres = {f["nombre"] for f in metricas["filtros_globales"]}
    assert nombres == {"ciclo", "entidad", "nivel"}


def test_el_grano_del_yaml_coincide_con_el_sql(datasets_por_nombre: dict[str, dict]) -> None:
    assert datasets_por_nombre["db01_cubo_matricula"]["grano"] == ["cve_mun", "nivel", "id_ciclo"]
    assert datasets_por_nombre["db01_distribucion_escuelas"]["grano"] == ["nivel", "sostenimiento", "id_ciclo"]
    assert datasets_por_nombre["db02_cubo_riesgo_territorial"]["grano"] == ["cve_mun", "nivel", "id_ciclo"]
    assert datasets_por_nombre["db02_puntos_escuela"]["grano"] == ["cct", "id_ciclo"]


def test_toda_razon_protege_la_division(metricas: dict) -> None:
    """Una división sin NULLIF revienta o miente cuando el denominador es cero."""
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


def test_el_porcentaje_en_riesgo_usa_las_escuelas_puntuadas(datasets_por_nombre: dict[str, dict]) -> None:
    """Decir '10% en riesgo' cuando solo se puntuó al 30% inventaría cobertura inexistente."""
    db02 = datasets_por_nombre["db02_cubo_riesgo_territorial"]
    metrica = next(m for m in db02["metricas"] if m["nombre"] == "pct_escuelas_en_riesgo")
    assert "escuelas_con_prediccion" in metrica["expresion"]
    assert metrica.get("denominador_visible") == "escuelas_con_prediccion"


def test_los_kpis_ratificados_estan_trazados(datasets_por_nombre: dict[str, dict]) -> None:
    """Cada KPI del Screen_Specs que vive aquí declara su ID (trazabilidad REQ→US)."""
    kpis: set[str] = set()
    for dataset in datasets_por_nombre.values():
        for metrica in dataset["metricas"]:
            if metrica.get("kpi"):
                kpis.add(metrica["kpi"])
    esperados = {"KPI-01", "KPI-02", "KPI-03", "KPI-04", "KPI-05", "KPI-07", "KPI-08"}
    faltantes = esperados - kpis
    assert not faltantes, f"KPIs sin trazabilidad en el YAML: {sorted(faltantes)}"


def test_cada_dataset_declara_su_sql_real() -> None:
    """El campo `sql:` del YAML apunta a un archivo que existe en superset/semantic/."""
    yaml = pytest.importorskip("yaml", reason="pyyaml no está en requirements.txt")
    data = yaml.safe_load(leer(YAML_METRICAS))
    for dataset in data["datasets"]:
        ruta = SEMANTIC / dataset["sql"]
        assert ruta.exists(), f"{dataset['nombre']}: su SQL declarado no existe ({ruta})."


# --------------------------------------------------------------------------- tableros declarativos (YAML)


@pytest.fixture(scope="module")
def dashboards() -> dict[str, dict]:
    yaml = pytest.importorskip("yaml", reason="pyyaml no está en requirements.txt")
    resultado: dict[str, dict] = {}
    for archivo in (YAML_DB01, YAML_DB02):
        data = yaml.safe_load(leer(archivo))
        for dash in data["dashboards"]:
            resultado[dash["slug"]] = dash
    return resultado


def test_existen_los_dos_tableros(dashboards: dict[str, dict]) -> None:
    assert set(dashboards) == {"db01-ejecutivo", "db02-mapa-riesgo"}


def test_todo_chart_apunta_a_dataset_y_metrica_declarados(
    dashboards: dict[str, dict], datasets_por_nombre: dict[str, dict]
) -> None:
    """Un chart huérfano (dataset o métrica inexistente) rompe en runtime, no en CI."""
    metricas_por_dataset = {
        nombre: {m["nombre"] for m in ds.get("metricas", [])}
        for nombre, ds in datasets_por_nombre.items()
    }
    for slug, dash in dashboards.items():
        charts = dash.get("charts", [])
        assert charts, f"{slug}: sin charts"
        for chart in charts:
            ds = chart["dataset"]
            assert ds in datasets_por_nombre, f"{slug}/{chart['nombre']}: dataset '{ds}' no declarado"
            if chart.get("viz") != "deck_polygon":  # el coroplético valida aparte (geometrías locales)
                assert chart["metrica"] in metricas_por_dataset[ds], (
                    f"{slug}/{chart['nombre']}: métrica '{chart['metrica']}' no declarada en '{ds}'"
                )


def test_los_tiles_kpi_son_big_number(dashboards: dict[str, dict]) -> None:
    """Contrato visual §4: la fila superior son tiles KPI (big_number_total)."""
    for slug, dash in dashboards.items():
        primeros = dash["charts"][:4]
        for chart in primeros:
            assert chart["viz"] == "big_number_total", (
                f"{slug}: '{chart['nombre']}' debería ser un tile KPI (big_number_total)"
            )
            assert int(chart.get("ancho", 12)) <= 3, (
                f"{slug}: '{chart['nombre']}' excede el ancho de un tile KPI"
            )


def test_db02_incluye_coropletico_y_puntos(dashboards: dict[str, dict]) -> None:
    """Contrato §2: coroplético municipal + puntos de escuela georreferenciados."""
    db02 = dashboards["db02-mapa-riesgo"]
    vizzes = {c["viz"] for c in db02["charts"]}
    assert "deck_polygon" in vizzes, "DB-02 sin coroplético municipal (KPI-10)"
    assert "deck_scatter" in vizzes, "DB-02 sin capa de puntos de escuela"


def test_los_filtros_nativos_cubren_columnas_reales(
    dashboards: dict[str, dict], datasets_por_nombre: dict[str, dict]
) -> None:
    """Cada filtro nativo apunta a columnas que existen en sus datasets objetivo."""
    for slug, dash in dashboards.items():
        for filtro in dash.get("filtros_globales", []):
            assert filtro.get("columna"), f"{slug}: filtro sin columna"
            assert filtro.get("datasets"), f"{slug}: filtro '{filtro['columna']}' sin datasets"
            for ds in filtro["datasets"]:
                assert ds in datasets_por_nombre, f"{slug}: filtro apunta a dataset inexistente '{ds}'"


# --------------------------------------------------------------------------- mock local de ML (guardarrailes)


@pytest.fixture(scope="module")
def mock_sql() -> str:
    return sin_comentarios(leer(MOCK))


def test_el_mock_es_identificable(mock_sql: str) -> None:
    """Toda fila mockeada lleva la marca MOCK-US203 en mlflow_run_id."""
    assert "MOCK-US203" in mock_sql


def test_el_mock_es_idempotente(mock_sql: str) -> None:
    """Re-ejecutarlo no duplica filas ni revienta: CREATE IF NOT EXISTS + ON CONFLICT."""
    assert re.search(r"create\s+table\s+if\s+not\s+exists", mock_sql, re.IGNORECASE)
    assert mock_sql.upper().count("ON CONFLICT") >= 2
    assert "DO NOTHING" in mock_sql.upper()


def test_el_mock_no_destruye_nada(mock_sql: str) -> None:
    """Prohibido DELETE/DROP/TRUNCATE/UPDATE; el único ALTER válido es
    ADD COLUMN IF NOT EXISTS (completar DEC-005 de forma aditiva)."""
    sin_aditivos = "\n".join(
        linea for linea in mock_sql.splitlines()
        if not re.search(r"add\s+column\s+if\s+not\s+exists", linea, re.IGNORECASE)
    )
    for prohibido in ("delete", "drop table", "truncate", "update ", "alter ", "drop column"):
        assert not re.search(re.escape(prohibido), sin_aditivos, re.IGNORECASE), (
            f"El mock contiene '{prohibido.strip()}': solo CREATE/ALTER aditivo + INSERT."
        )


def test_el_mock_solo_toca_tablas_de_salida_ml(mock_sql: str) -> None:
    """INSERT únicamente a gold.predicciones, gold.recomendaciones y gold.dim_driver."""
    inserts = re.findall(r"insert\s+into\s+([\w.]+)", mock_sql, re.IGNORECASE)
    assert inserts, "El mock no inserta nada"
    assert set(inserts) == {"gold.predicciones", "gold.recomendaciones", "gold.dim_driver"}


def test_el_mock_ejercita_el_caso_sin_dato(mock_sql: str) -> None:
    """Deja un municipio completo sin predicciones para probar cobertura SIN_DATO."""
    assert re.search(r"cve_mun\s*<>\s*\(?\s*select\s+min\s*\(\s*cve_mun\s*\)", mock_sql, re.IGNORECASE)


def test_el_mock_respeta_el_umbral_r3(mock_sql: str) -> None:
    """La prioridad ALTA del mock usa el mismo umbral 0.6 que el negocio."""
    assert re.search(r">=\s*0\.6\s+then\s+'ALTA'", mock_sql, re.IGNORECASE)


# --------------------------------------------------------------------------- script de sincronización


@pytest.fixture(scope="module")
def sync():
    """Importa superset/sync_semantic_layer.py como módulo (sin red en import)."""
    ruta = RAIZ / "superset" / "sync_semantic_layer.py"
    spec = importlib.util.spec_from_file_location("sync_semantic_layer", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("sync_semantic_layer", modulo)
    spec.loader.exec_module(modulo)
    return modulo


def test_el_layout_genera_estructura_v2(sync) -> None:
    """position_json v2: ROOT_ID → filas → componentes CHART con chartId."""
    position = sync._layout_grilla([(11, "Tile A", 3, 38), (22, "Gráfico B", 6, 60)])
    assert position["DASHBOARD_VERSION_KEY"] == "v2"
    # árbol v2 correcto: ROOT → GRID → filas → charts, con parentId en cada nodo
    assert position["ROOT_ID"]["children"] == ["GRID_ID"]
    assert position["GRID_ID"]["children"] == ["ROW-0", "ROW-1"]
    assert position["ROW-0"]["parentId"] == "GRID_ID"
    assert position["CHART-0"]["parentId"] == "ROW-0"
    assert position["CHART-0"]["meta"]["chartId"] == 11
    assert position["CHART-1"]["meta"]["width"] == 6


def test_params_de_tile_kpi(sync) -> None:
    params = sync._params_chart({"nombre": "t", "viz": "big_number_total", "metrica": "escuelas"}, 7, ",d")
    assert params["datasource"] == "7__table"
    assert params["viz_type"] == "big_number_total"
    assert params["metric"] == "escuelas"
    assert params["y_axis_format"] == ",d"


def test_params_de_tabla_usan_dimensiones(sync) -> None:
    cfg = {"nombre": "r", "viz": "table", "metrica": "matricula_total",
           "dimensiones": ["nombre_entidad", "nombre_municipio"]}
    params = sync._params_chart(cfg, 9, ",d")
    assert params["groupby"] == ["nombre_entidad", "nombre_municipio"]
    assert params["metrics"] == ["matricula_total"]


def test_params_extra_sobreescrive_lo_base(sync) -> None:
    """Los ajustes finos viven en el YAML (`params_extra`), no en código."""
    cfg = {"nombre": "x", "viz": "pie", "metrica": "escuelas", "dimensiones": ["nivel"],
           "params_extra": {"sort_by_metric": False}}
    params = sync._params_chart(cfg, 5, ",d")
    assert params["sort_by_metric"] is False


def test_los_formatos_d3_cubren_los_formatos_del_yaml(sync, metricas: dict) -> None:
    """Todo `formato:` usado en metrics_db01_db02.yaml tiene formato d3 para charts."""
    formatos_yaml = {
        m.get("formato")
        for ds in metricas["datasets"]
        for m in ds["metricas"]
        if m.get("formato")
    }
    faltantes = formatos_yaml - set(sync.FORMATO_D3)
    assert not faltantes, f"Formatos sin mapeo d3 en FORMATO_D3: {sorted(faltantes)}"


def test_los_porcentajes_se_formatean_como_porcentaje(sync) -> None:
    """'porcentaje_1' debe renderizar 0.123 como '12.3%', no como '0.1'."""
    assert sync.FORMATO_D3["porcentaje_1"].endswith("%")
    assert sync.FORMATO_D3["porcentaje_0"].endswith("%")
