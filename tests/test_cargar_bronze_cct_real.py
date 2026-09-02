"""Pruebas del cargador real de producción de DS-02 SEP Catálogo CCT --
`src/ingesta/cargar_bronze_cct_real.py`.

Mismo espíritu que `tests/test_cargar_bronze_formato911_real.py`: protege las decisiones reales
documentadas en el docstring del módulo bajo prueba, no solo el camino feliz.

- `C_TIPO == "ESCUELA"` por sí solo NO implica educación básica (también incluye media
  superior, superior, inicial, CAM, formación para el trabajo) -- se necesitan los dos filtros
  combinados (punto 2 y 3 del docstring).
- CCT duplicado entre las dos partes del catálogo debe fallar explícito, nunca resolverse en
  silencio quedándose con uno de los dos (punto 6).
- Coordenadas en 0,0 se cargan tal cual, sin convertirlas a NULL (punto 7) -- ese hueco se
  resuelve en Silver, no aquí.
- Columna faltante en el archivo real debe fallar explícito, nunca asumirse vacía.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.ingesta.cargar_bronze_cct_real import (
    COLUMNAS_BRONZE,
    COLUMNAS_CRUDAS_REQUERIDAS,
    NIVELES_BASICA,
    SOURCE_NAME,
    SOURCE_URL,
    _validar_columnas_crudas,
    parsear_y_combinar,
)

# --------------------------------------------------------------------------- helpers


def _fila(cct, nombre="ESCUELA X", c_tipo="ESCUELA", sostenimiento="PÚBLICO",
          entidad="09", municipio="010", latitud="19.4", longitud="-99.1",
          nivel="PRIMARIA") -> dict:
    return {
        "CV_CCT": cct,
        "C_NOMBRE": nombre,
        "C_TIPO": c_tipo,
        "SOSTENIMIENTO_C_CONTROL": sostenimiento,
        "INMUEBLE_CV_ENT": entidad,
        "INMUEBLE_CV_MUN": municipio,
        "INMUEBLE_LATITUD": latitud,
        "INMUEBLE_LONGITUD": longitud,
        "TIPONIVELSUB_C_SERVICION2": nivel,
    }


def _escribir_csv(tmp_path, nombre_archivo: str, filas: list[dict]) -> str:
    df = pd.DataFrame(filas, columns=COLUMNAS_CRUDAS_REQUERIDAS)
    ruta = tmp_path / nombre_archivo
    df.to_csv(ruta, index=False, encoding="latin-1")
    return str(ruta)


# --------------------------------------------------------------------------- _validar_columnas_crudas


def test_columnas_completas_no_truena() -> None:
    _validar_columnas_crudas(list(COLUMNAS_CRUDAS_REQUERIDAS) + ["OTRA_COLUMNA"], "ruta_ficticia.csv")


def test_columna_faltante_reporta_exactamente_cual() -> None:
    incompletas = [c for c in COLUMNAS_CRUDAS_REQUERIDAS if c != "TIPONIVELSUB_C_SERVICION2"]
    with pytest.raises(ValueError, match="TIPONIVELSUB_C_SERVICION2"):
        _validar_columnas_crudas(incompletas, "ruta_ficticia.csv")


# --------------------------------------------------------------------------- parsear_y_combinar — filtros


def test_filtra_por_tipo_escuela(tmp_path) -> None:
    ruta_a = _escribir_csv(tmp_path, "parte_a.csv", [
        _fila("09DPR0001A", c_tipo="ESCUELA"),
        _fila("09SUP0002A", c_tipo="SUPERVISION DE ZONA DE EDUCACION"),
    ])
    ruta_b = _escribir_csv(tmp_path, "parte_b.csv", [])
    resultado = parsear_y_combinar(ruta_a, ruta_b)
    assert list(resultado["cct"]) == ["09DPR0001A"]


def test_escuela_no_implica_basica_media_superior_se_filtra(tmp_path) -> None:
    """Éste es justo el hallazgo real de esta sesión: C_TIPO=="ESCUELA" incluye media
    superior/superior/inicial/CAM, no solo básica. El filtro de nivel es el que de verdad
    acota — sin él, este test fallaría con 2 filas en vez de 1."""
    ruta_a = _escribir_csv(tmp_path, "parte_a.csv", [
        _fila("09DPR0001A", c_tipo="ESCUELA", nivel="PRIMARIA"),
        _fila("09EMS0002A", c_tipo="ESCUELA", nivel="MEDIA SUPERIOR"),
    ])
    ruta_b = _escribir_csv(tmp_path, "parte_b.csv", [])
    resultado = parsear_y_combinar(ruta_a, ruta_b)
    assert list(resultado["cct"]) == ["09DPR0001A"]


def test_todos_los_niveles_de_basica_pasan(tmp_path) -> None:
    ruta_a = _escribir_csv(tmp_path, "parte_a.csv", [
        _fila("09DJN0001A", nivel="PREESCOLAR"),
        _fila("09DPR0002A", nivel="PRIMARIA"),
        _fila("09DES0003A", nivel="SECUNDARIA"),
    ])
    ruta_b = _escribir_csv(tmp_path, "parte_b.csv", [])
    resultado = parsear_y_combinar(ruta_a, ruta_b)
    assert set(resultado["nivel"]) == set(NIVELES_BASICA)
    assert len(resultado) == 3


# --------------------------------------------------------------------------- parsear_y_combinar — esquema de salida


def test_columnas_y_valores_de_salida(tmp_path) -> None:
    ruta_a = _escribir_csv(tmp_path, "parte_a.csv", [
        _fila("09DPR0001A", nombre="ESCUELA A", sostenimiento="PÚBLICO",
              entidad="09", municipio="010", latitud="19.4", longitud="-99.1"),
    ])
    ruta_b = _escribir_csv(tmp_path, "parte_b.csv", [])
    resultado = parsear_y_combinar(ruta_a, ruta_b)

    assert list(resultado.columns) == COLUMNAS_BRONZE
    fila = resultado.iloc[0]
    assert fila["cct"] == "09DPR0001A"
    assert fila["nombre"] == "ESCUELA A"
    assert fila["sostenimiento"] == "PÚBLICO"
    assert fila["entidad"] == "09"
    assert fila["municipio"] == "010"  # sin concatenar con entidad -- lo hace Silver
    assert fila["latitud"] == "19.4"
    assert fila["longitud"] == "-99.1"
    assert fila["_source"] == SOURCE_NAME
    assert fila["_source_url"] == SOURCE_URL


def test_coordenadas_en_0_0_se_cargan_tal_cual(tmp_path) -> None:
    """No se convierten a NULL aquí -- ver punto 7 del docstring del módulo."""
    ruta_a = _escribir_csv(tmp_path, "parte_a.csv", [
        _fila("09DPR0001A", latitud="0.0", longitud="0.0"),
    ])
    ruta_b = _escribir_csv(tmp_path, "parte_b.csv", [])
    resultado = parsear_y_combinar(ruta_a, ruta_b)
    assert resultado.iloc[0]["latitud"] == "0.0"
    assert resultado.iloc[0]["longitud"] == "0.0"


# --------------------------------------------------------------------------- parsear_y_combinar — duplicados


def test_cct_duplicado_entre_las_dos_partes_falla_explicito(tmp_path) -> None:
    ruta_a = _escribir_csv(tmp_path, "parte_a.csv", [_fila("09DPR0001A")])
    ruta_b = _escribir_csv(tmp_path, "parte_b.csv", [_fila("09DPR0001A")])
    with pytest.raises(ValueError, match="duplicado"):
        parsear_y_combinar(ruta_a, ruta_b)


def test_sin_duplicados_no_truena(tmp_path) -> None:
    ruta_a = _escribir_csv(tmp_path, "parte_a.csv", [_fila("09DPR0001A")])
    ruta_b = _escribir_csv(tmp_path, "parte_b.csv", [_fila("19DPR0002A", entidad="19")])
    resultado = parsear_y_combinar(ruta_a, ruta_b)
    assert len(resultado) == 2
