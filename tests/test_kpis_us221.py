"""
TEST-US221 · Guarda antiduplicación de KPIs globales.

Tras la ratificación de Manuel Serranía (dueño del catálogo, US-201), US-221 ya no
crea datasets ni SQL por KPI: las tarjetas globales (AC-002.5) consumen las
métricas canónicas de los datasets existentes. Este test lo garantiza:

* **No debe existir ningún `kpi_*.sql`** en `superset/semantic/`: todo KPI del
  catálogo (Screen_Specs.md §4) se implementa en el SQL del tablero que lo
  expone, nunca en un archivo suelto (regla 1 del vault; el `*100` duplicado
  reapareció 3 veces en DB-01, DB-03/04 y US-211b).

* **El mapeo `metrics_kpis_base_us221.yaml` solo referencia datasets, métricas
  y archivos de métricas que existen**: si alguien renombra la métrica canónica
  o borra el dataset, el mapeo de tarjetas falla aquí, no en el demo.

Validación estática: no necesita base de datos.

Contrato: `04_UX_Design/Screen_Specs.md` §2/§4 · `metrics_kpis_base_us221.yaml`.
"""

from __future__ import annotations

from pathlib import Path

SEMANTIC = Path(__file__).resolve().parents[1] / "superset" / "semantic"
MAPPING = SEMANTIC / "metrics_kpis_base_us221.yaml"

KPI_GLOBALES = {"KPI-01", "KPI-02", "KPI-03", "KPI-04", "KPI-08"}


def _load_yaml(path: Path) -> dict:
    import yaml

    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _dataset_metricas(nombre_dataset: str, yaml_metricas: str) -> list[dict]:
    """Devuelve las métricas declaradas para un dataset en un metrics_*.yaml."""
    ruta = SEMANTIC / yaml_metricas
    assert ruta.exists(), (
        f"El mapeo de tarjetas referencia {yaml_metricas}, que no existe."
    )
    data = _load_yaml(ruta)
    datasets = data.get("datasets", [])
    coincidencias = [ds for ds in datasets if ds.get("nombre") == nombre_dataset]
    assert coincidencias, (
        f"El dataset '{nombre_dataset}' no está declarado en {yaml_metricas}."
    )
    assert len(coincidencias) == 1, (
        f"Dataset '{nombre_dataset}' duplicado en {yaml_metricas}."
    )
    return coincidencias[0].get("metricas", [])


def test_no_hay_sql_kpi_duplicado():
    """Los KPIs del catálogo se implementan en el dataset de su tablero, nunca en
    un `kpi_*.sql` suelto. Si este test falla, alguien reintrodujo duplicación."""
    duplicados = sorted(p.name for p in SEMANTIC.glob("kpi_*.sql"))
    assert duplicados == [], (
        f"Existen SQL por KPI duplicando la capa de datasets: {duplicados}. "
        "Bórralos y referencia la métrica canónica del dataset del tablero "
        "(ver metrics_kpis_base_us221.yaml)."
    )


def test_mapeo_cubre_las_kpis_globales():
    mapping = _load_yaml(MAPPING)
    kpis = {tarjeta["kpi"] for tarjeta in mapping["tarjetas"]}
    assert kpis == KPI_GLOBALES, (
        f"El mapeo de tarjetas debe cubrir exactamente {sorted(KPI_GLOBALES)}"
    )


def test_cada_tarjeta_apunta_a_metrica_canonica_existente():
    """Cada tarjeta referencia un dataset+metrica real, declarado en el
    metrics_*.yaml correspondiente, y esa métrica lleva el tag `kpi` correcto."""
    mapping = _load_yaml(MAPPING)

    for tarjeta in mapping["tarjetas"]:
        kpi = tarjeta["kpi"]
        fuente = tarjeta.get("fuente")
        assert fuente, f"KPI {kpi}: falta el bloque 'fuente' con dataset/métrica."

        dataset = fuente.get("dataset")
        metrica = fuente.get("metrica")
        yaml_metricas = fuente.get("yaml_metricas")
        assert dataset and metrica and yaml_metricas, (
            f"KPI {kpi}: 'fuente' incompleto (dataset, metrica, yaml_metricas)."
        )

        metricas = _dataset_metricas(dataset, yaml_metricas)
        coincidencia = [m for m in metricas if m.get("nombre") == metrica]
        assert coincidencia, (
            f"KPI {kpi}: la métrica '{metrica}' no está declarada para "
            f"'{dataset}' en {yaml_metricas}."
        )
        etiqueta_kpi = coincidencia[0].get("kpi")
        assert etiqueta_kpi == kpi, (
            f"KPI {kpi}: la métrica '{metrica}' está declarada con `kpi: "
            f"{etiqueta_kpi}` en {yaml_metricas}. El mapeo debe apuntar a la "
            "métrica canónica del KPI correspondiente."
        )


def test_no_se_redefine_filtros_globales_fuera_del_scope():
    """Los filtros globales del mapeo respetan AC-002.2 y el alcance geográfico."""
    mapping = _load_yaml(MAPPING)
    columnas = {f["columna"] for f in mapping["filtros_globales"]}
    assert {"id_ciclo", "cve_ent", "nivel"} <= columnas

    for f in mapping["filtros_globales"]:
        dominio = f.get("dominio")
        if f["columna"] == "cve_ent" and dominio is not None:
            assert set(dominio) == {"09", "15", "19", "14"}, (
                "El dominio geográfico debe ser exactamente SCOPE_ENTIDADES."
            )
