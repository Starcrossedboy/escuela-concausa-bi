"""Pruebas del cargador real de producción de DS-01 Formato 911 -- distribución
`bronze.formato911_2024_2025` (`src/ingesta/cargar_bronze_formato911_real.py`).

Mismo espíritu que `tests/test_extractor_formato911_historico.py` (su hermano de la
distribución HISTÓRICA), pero protegiendo el comportamiento propio de este script:

- El grano de entrada es cct x turno; el grano de salida debe ser una fila por cct, con
  alumnos_total/docentes_total/grupos_total SUMADOS a través de los turnos (punto 1 del
  docstring del módulo bajo prueba) -- lo opuesto del extractor histórico, que preserva cada
  turno como fila propia.
- Un valor no numérico en insc_t/tot_doc/gpos_t debe fallar explícito, nunca convertirse
  silenciosamente en 0 (punto 4 del docstring) -- éste fue justo el bug que corrigió esta
  sesión: la primera versión del script sí hacía `.fillna(0)`.
- La detección de columna llave y la validación de columnas fijas siguen el mismo patrón
  "nunca adivinar" que el resto de los extractores de DS-01.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.ingesta.cargar_bronze_formato911_real import (
    COLUMNAS_BRONZE,
    COLUMNAS_FIJAS_REQUERIDAS,
    SOURCE_NAME,
    SOURCE_URL_POR_CICLO,
    _coercer_metrica_o_fallar,
    _detectar_columna_cct,
    _validar_columnas_fijas,
    parsear_y_agregar,
)

# --------------------------------------------------------------------------- _detectar_columna_cct


def test_detecta_columna_cct_formato_nuevo() -> None:
    """2024-2025 y 2023-2024 traen `clave_cct` (verificado real, ver docstring del módulo)."""
    assert _detectar_columna_cct(["clave_cct", "entidad", "municipio"]) == "clave_cct"


def test_detecta_columna_cct_formato_legado() -> None:
    """2021-2022 y 2022-2023 traen `clavecct` (verificado real esta sesión)."""
    assert _detectar_columna_cct(["clavecct", "entidad", "municipio"]) == "clavecct"


def test_columna_cct_desconocida_falla_explicito_en_vez_de_adivinar() -> None:
    with pytest.raises(ValueError, match=SOURCE_NAME):
        _detectar_columna_cct(["llave_escuela", "entidad", "municipio"])


# --------------------------------------------------------------------------- _validar_columnas_fijas


def test_columnas_fijas_completas_no_truena() -> None:
    _validar_columnas_fijas(list(COLUMNAS_FIJAS_REQUERIDAS) + ["clave_cct", "otra_columna"])


def test_columnas_fijas_faltantes_reporta_exactamente_cuales() -> None:
    columnas_incompletas = ["clave_cct", "entidad", "municipio"]  # faltan nivel/turno/insc_t/tot_doc/gpos_t
    with pytest.raises(ValueError) as exc_info:
        _validar_columnas_fijas(columnas_incompletas)
    for faltante in ["nivel", "turno", "insc_t", "tot_doc", "gpos_t"]:
        assert faltante in str(exc_info.value)


# --------------------------------------------------------------------------- _coercer_metrica_o_fallar


def test_coercer_metrica_convierte_texto_numerico_a_entero() -> None:
    resultado = _coercer_metrica_o_fallar(pd.Series(["120", "45", "0"]), "insc_t")
    assert list(resultado) == [120, 45, 0]


def test_coercer_metrica_falla_explicito_en_vez_de_inventar_cero() -> None:
    """Éste es el bug real corregido esta sesión: la primera versión hacía
    `pd.to_numeric(..., errors="coerce").fillna(0)`, así que un dato sucio se volvía "0
    alumnos" en vez de tronar. Una escuela con matrícula corrupta en el archivo NO debe verse
    como una deserción total silenciosa."""
    with pytest.raises(ValueError, match="insc_t"):
        _coercer_metrica_o_fallar(pd.Series(["120", "N/D", "45"]), "insc_t")


def test_coercer_metrica_celda_vacia_tambien_falla_no_se_asume_cero() -> None:
    with pytest.raises(ValueError, match="No se asumen como 0"):
        _coercer_metrica_o_fallar(pd.Series(["120", ""]), "tot_doc")


# --------------------------------------------------------------------------- parsear_y_agregar


def _escribir_csv(tmp_path, nombre_columna_cct: str, filas: list[dict]) -> str:
    columnas = [nombre_columna_cct, "entidad", "municipio", "nivel", "turno", "insc_t", "tot_doc", "gpos_t"]
    df = pd.DataFrame(filas, columns=columnas)
    ruta = tmp_path / "formato911_real_sintetico.csv"
    df.to_csv(ruta, index=False)
    return str(ruta)


def _fila(cct="01DPR0001A", entidad="9", municipio="10", nivel="PRIMARIA", turno="1",
          insc_t="300", tot_doc="12", gpos_t="10", columna_cct="clave_cct") -> dict:
    return {
        columna_cct: cct, "entidad": entidad, "municipio": municipio, "nivel": nivel,
        "turno": turno, "insc_t": insc_t, "tot_doc": tot_doc, "gpos_t": gpos_t,
    }


def test_suma_dos_turnos_del_mismo_cct(tmp_path) -> None:
    ruta = _escribir_csv(tmp_path, "clave_cct", [
        _fila(cct="01DPR0001A", turno="1", insc_t="300", tot_doc="12", gpos_t="10"),
        _fila(cct="01DPR0001A", turno="2", insc_t="180", tot_doc="8", gpos_t="6"),
    ])
    resultado = parsear_y_agregar(ruta, "2024-2025")

    assert list(resultado.columns) == COLUMNAS_BRONZE
    assert len(resultado) == 1  # una fila por cct, no por turno
    fila = resultado.iloc[0]
    assert fila["cct"] == "01DPR0001A"
    assert fila["ciclo"] == "2024-2025"
    assert fila["alumnos_total"] == 480  # 300 + 180
    assert fila["docentes_total"] == 20  # 12 + 8
    assert fila["grupos_total"] == 16    # 10 + 6
    assert fila["_source"] == SOURCE_NAME
    assert fila["_source_url"] == SOURCE_URL_POR_CICLO["2024-2025"]


def test_cct_de_un_solo_turno_no_se_altera(tmp_path) -> None:
    ruta = _escribir_csv(tmp_path, "clave_cct", [
        _fila(cct="09DJN0002B", turno="1", insc_t="85", tot_doc="4", gpos_t="3"),
    ])
    resultado = parsear_y_agregar(ruta, "2023-2024")
    assert len(resultado) == 1
    fila = resultado.iloc[0]
    assert fila["alumnos_total"] == 85
    assert fila["docentes_total"] == 4
    assert fila["grupos_total"] == 3


def test_entidad_municipio_nivel_se_toman_del_primer_turno(tmp_path) -> None:
    """Constantes por cct en el archivo real -- una escuela no cambia de municipio/nivel entre
    turnos, así que basta con el primero."""
    ruta = _escribir_csv(tmp_path, "clave_cct", [
        _fila(cct="14DES0009C", entidad="14", municipio="98", nivel="SECUNDARIA", turno="1"),
        _fila(cct="14DES0009C", entidad="14", municipio="98", nivel="SECUNDARIA", turno="2"),
    ])
    resultado = parsear_y_agregar(ruta, "2022-2023")
    fila = resultado.iloc[0]
    assert fila["entidad"] == "14"
    assert fila["municipio"] == "98"
    assert fila["nivel"] == "SECUNDARIA"


def test_variante_legada_clavecct_tambien_agrega_bien(tmp_path) -> None:
    ruta = _escribir_csv(tmp_path, "clavecct", [
        _fila(cct="19DPR0005D", turno="1", insc_t="200", tot_doc="9", gpos_t="7", columna_cct="clavecct"),
    ])
    resultado = parsear_y_agregar(ruta, "2021-2022")
    assert "clavecct" not in resultado.columns
    assert resultado.iloc[0]["cct"] == "19DPR0005D"


def test_valor_no_numerico_en_un_turno_falla_explicito_no_arruina_la_suma(tmp_path) -> None:
    """Regresión directa del bug corregido: antes, un turno con insc_t sucio se volvía 0 y se
    sumaba igual, dejando una matrícula total silenciosamente baja. Ahora todo el archivo debe
    detenerse -- no cargar una suma parcial que se ve como dato válido."""
    ruta = _escribir_csv(tmp_path, "clave_cct", [
        _fila(cct="15DPR0007E", turno="1", insc_t="300"),
        _fila(cct="15DPR0007E", turno="2", insc_t="N/D"),
    ])
    with pytest.raises(ValueError, match="insc_t"):
        parsear_y_agregar(ruta, "2024-2025")


def test_falla_si_falta_columna_fija(tmp_path) -> None:
    ruta = tmp_path / "sin_gpos_t.csv"
    pd.DataFrame([{
        "clave_cct": "09DPR0001A", "entidad": "9", "municipio": "10",
        "nivel": "PRIMARIA", "turno": "1", "insc_t": "120", "tot_doc": "5",
        # falta "gpos_t" a propósito
    }]).to_csv(ruta, index=False)

    with pytest.raises(ValueError, match="gpos_t"):
        parsear_y_agregar(str(ruta), "2024-2025")