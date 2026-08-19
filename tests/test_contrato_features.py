"""Guarda del contrato `gold.features_escuela` entre Célula 1 y Célula 3 (TEST-008).

`src/modelos/contrato.py` es un **espejo** del contrato que produce la Célula 1 (US-104, Diana
Alvarez). El `Data_Model` §5.3 dice que cambiar una columna es cambiar el contrato y exige avisar a
la C3; el propio `_gold__models.yml` lo repite: *"Compartido con Andrés González Habib (C3): avisar
antes de cambiar columnas"*.

Estas pruebas convierten ese acuerdo en algo que el CI hace cumplir. Si la C1 renombra o quita una
columna, **falla aquí** en vez de descubrirse al entrenar ML-01 con datos reales.

Se leen los archivos de dbt como texto, sin `yaml` ni `dbt`: el CI instala sólo `requirements.txt`
y una prueba que dependa de paquetes ausentes no correría —que es justo el defecto de BUG-003.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.modelos.contrato import DRIVERS, FeaturesEscuela, columna_cobertura

RAIZ = Path(__file__).resolve().parents[1]
MODELO_SQL = RAIZ / "dbt" / "models" / "gold" / "features_escuela.sql"
ESQUEMA_YML = RAIZ / "dbt" / "models" / "gold" / "_gold__models.yml"


def _columnas_declaradas() -> set[str]:
    """Columnas que la Célula 1 declara para `features_escuela` en su `schema.yml`.

    Se recorta al bloque del modelo para no arrastrar columnas de otros modelos del mismo archivo.
    """
    texto = ESQUEMA_YML.read_text(encoding="utf-8")
    inicio = texto.index("- name: features_escuela")
    siguiente = re.search(r"\n  - name: (?!features_escuela)", texto[inicio:])
    bloque = texto[inicio : inicio + siguiente.start()] if siguiente else texto[inicio:]
    return set(re.findall(r"^\s+- name: (\w+)$", bloque, re.MULTILINE)) - {"features_escuela"}


@pytest.mark.skipif(not ESQUEMA_YML.exists(), reason="la Célula 1 aún no publica el esquema dbt")
def test_lo_que_declara_la_celula_1_existe_en_el_espejo() -> None:
    """Toda columna declarada por la C1 debe existir en `FeaturesEscuela`."""
    declaradas = _columnas_declaradas()
    assert declaradas, "no se pudo leer ninguna columna del schema.yml"

    faltantes = declaradas - set(FeaturesEscuela.model_fields)
    assert not faltantes, (
        f"La Célula 1 declara columnas que el espejo de la C3 no tiene: {sorted(faltantes)}. "
        "Actualiza src/modelos/contrato.py o coordina con Diana Alvarez (Data_Model §5.3)."
    )


@pytest.mark.skipif(not MODELO_SQL.exists(), reason="la Célula 1 aún no publica el modelo dbt")
def test_el_sql_produce_todas_las_columnas_del_contrato() -> None:
    """Cada campo del espejo debe aparecer en el SQL que construye la tabla.

    Detecta renombres: si `d1_pobreza` pasara a llamarse de otro modo, el nombre desaparece del SQL
    y esta prueba falla antes de que ML-01 truene al leer la tabla.
    """
    sql = MODELO_SQL.read_text(encoding="utf-8")
    ausentes = [campo for campo in FeaturesEscuela.model_fields if not re.search(rf"\b{campo}\b", sql)]
    assert not ausentes, (
        f"El modelo dbt de la C1 ya no produce: {ausentes}. "
        "El contrato cambió sin actualizar el espejo de la C3."
    )


@pytest.mark.skipif(not MODELO_SQL.exists(), reason="la Célula 1 aún no publica el modelo dbt")
def test_cada_driver_conserva_su_bandera_de_cobertura() -> None:
    """La regla de cobertura parcial exige valor + bandera para los seis drivers."""
    sql = MODELO_SQL.read_text(encoding="utf-8")
    for driver in DRIVERS:
        bandera = columna_cobertura(driver)
        assert re.search(rf"\b{bandera}\b", sql), f"falta la bandera {bandera} de {driver}"


@pytest.mark.skipif(not MODELO_SQL.exists(), reason="la Célula 1 aún no publica el modelo dbt")
def test_la_ausencia_se_marca_sin_dato_y_no_con_cero() -> None:
    """Regla 4 de `15_ML_Models/_index`: nunca cero, nunca nulo silencioso."""
    sql = MODELO_SQL.read_text(encoding="utf-8")
    assert "SIN_DATO" in sql, "el modelo de la C1 no usa el centinela SIN_DATO"
