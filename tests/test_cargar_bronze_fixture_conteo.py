"""Regresión de BUG-034: `cargar_fixture()` (src/ingesta/cargar_bronze_fixture.py) contaba las
filas insertadas leyendo `cur.rowcount` justo después de `execute_values()` -- pero
`execute_values()` pagina el INSERT en lotes (page_size=100 por default) y `cur.rowcount`
después de la llamada solo refleja el ÚLTIMO lote, no el total. Real: una carga de 385,175 filas
nuevas (DS-02) reportó "75 insertadas" (= 385175 % 100), confirmado como falso con un COUNT(*)
directo en Postgres.

Esta prueba no toca Postgres real (`cargar_fixture()` lo requiere y no hay suite para ella hoy):
mockea `psycopg2.connect` y `execute_values`, dejando `cur.rowcount` deliberadamente en un valor
menor y distinto -- imitando el bug real -- para que la prueba falle si `cargar_fixture()` vuelve
a leer `cur.rowcount` en vez del resultado de `execute_values(..., fetch=True)`.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from src.ingesta.cargar_bronze_fixture import COLUMNAS_CCT, cargar_fixture


def _escribir_fixture_cct(tmp_path, n_filas: int) -> str:
    df = pd.DataFrame({
        "cct": [f"09DPR{i:04d}A" for i in range(n_filas)],
        "nombre": ["ESCUELA X"] * n_filas,
        "nivel": ["PRIMARIA"] * n_filas,
        "sostenimiento": ["PÚBLICO"] * n_filas,
        "entidad": ["09"] * n_filas,
        "municipio": ["010"] * n_filas,
        "latitud": ["19.4"] * n_filas,
        "longitud": ["-99.1"] * n_filas,
        "_ingested_at": ["2026-08-30T00:00:00+00:00"] * n_filas,
        "_source": ["DS-02_CATALOGO_CCT"] * n_filas,
        "_source_url": ["https://siged.example"] * n_filas,
    }, columns=COLUMNAS_CCT)
    ruta = tmp_path / "fixture.csv"
    df.to_csv(ruta, index=False)
    return str(ruta)


def test_cuenta_todas_las_filas_no_solo_el_ultimo_lote(tmp_path) -> None:
    """385,175 filas, page_size=100 -> el bug real reportaba 75 (el resto del último lote).
    Con el fix, cargar_fixture() debe reportar el total real (simulado aquí con 250 filas)."""
    ruta = _escribir_fixture_cct(tmp_path, 250)

    fake_cur = MagicMock()
    fake_cur.rowcount = 50  # valor distinto y MENOR a propósito -- imita el bug real
    fake_conn = MagicMock()
    fake_conn.__enter__.return_value = fake_conn
    fake_conn.cursor.return_value.__enter__.return_value = fake_cur

    with patch("src.ingesta.cargar_bronze_fixture.psycopg2.connect", return_value=fake_conn), \
         patch(
             "src.ingesta.cargar_bronze_fixture.execute_values",
             return_value=[(1,)] * 250,
         ) as mock_execute_values:
        insertadas = cargar_fixture(ruta, "tabla_test", esquema="cct")

    assert insertadas == 250  # el total real, no fake_cur.rowcount (50)
    assert insertadas != fake_cur.rowcount

    _, kwargs = mock_execute_values.call_args
    assert kwargs.get("fetch") is True
    sql_usado = mock_execute_values.call_args.args[1]
    assert "RETURNING" in sql_usado.upper()


def test_todo_conflicto_reporta_cero_insertadas(tmp_path) -> None:
    """Si ON CONFLICT DO NOTHING descarta TODAS las filas (ya existían), RETURNING no emite
    ninguna -- execute_values(fetch=True) debe devolver una lista vacía y cargar_fixture()
    reportar 0, no el rowcount del último lote de un INSERT que en realidad no insertó nada."""
    ruta = _escribir_fixture_cct(tmp_path, 10)

    fake_cur = MagicMock()
    fake_conn = MagicMock()
    fake_conn.__enter__.return_value = fake_conn
    fake_conn.cursor.return_value.__enter__.return_value = fake_cur

    with patch("src.ingesta.cargar_bronze_fixture.psycopg2.connect", return_value=fake_conn), \
         patch("src.ingesta.cargar_bronze_fixture.execute_values", return_value=[]):
        insertadas = cargar_fixture(ruta, "tabla_test", esquema="cct")

    assert insertadas == 0
