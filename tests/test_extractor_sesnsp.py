"""Pruebas del extractor de DS-04 SESNSP (`src/ingesta/extractor_sesnsp.py`), con datos
sintéticos que reproducen la ESTRUCTURA real verificada a mano el 2026-08-24 (ver
DevLog y `vault/14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva.md`), no suposiciones:

- El grano nativo de la fuente incluye subtipo y modalidad de delito; el modelo Silver
  (`delitos_municipio.sql`) espera (municipio, año, mes, tipo_delito) y deduplica por
  `_ingested_at` sin sumar -- si el extractor no agregara subtipo/modalidad ANTES de
  escribir Bronze, se perdería conteo real en vez de sumarlo. El caso que más importa
  proteger aquí es justo ese: que la suma sobrevive al melt + groupby.
- `Cve. Municipio` es `Clave_Ent` (sin padding) + código local de 3 dígitos
  concatenados -- la derivación debe funcionar igual para entidades de 1 y de 2 dígitos
  (ej. Aguascalientes "1" vs. Puebla "21"), porque son formatos distintos de la MISMA
  columna, no casos raros.
- Un mismo municipio/año/mes/tipo_delito puede caer en más de un chunk (el CSV no está
  particionado por esa llave) -- `_finalizar_agregado` debe volver a sumar, no quedarse
  con el último valor visto.
- La descarga debe pedir `Accept-Encoding: identity` explícitamente (el CDN devuelve un
  gzip roto si el cliente ofrece gzip, que es lo que `requests` manda por default).
"""

from __future__ import annotations

import os

import pandas as pd

from src.ingesta.extractor_sesnsp import (
    COLUMNAS_ID,
    MESES,
    _agregar_chunk,
    _derivar_cve_mun_local,
    _descargar_a_temporal,
    _finalizar_agregado,
)

# --------------------------------------------------------------------------- _agregar_chunk


def _fila_ancha(anio, clave_ent, cve_mun, tipo_delito, **meses_con_valor) -> dict:
    fila = {
        "Año": anio, "Clave_Ent": clave_ent, "Cve. Municipio": cve_mun,
        "Tipo de delito": tipo_delito,
    }
    fila.update({mes: meses_con_valor.get(mes, 0) for mes in MESES})
    return fila


def test_agregar_chunk_suma_subtipo_y_modalidad_sin_perder_conteo() -> None:
    """Caso central: 'Homicidio' con dos subtipos/modalidades distintas en enero debe
    quedar como UNA sola fila enero con la suma -- no dos filas, no la última pisando
    a la primera (que es justo lo que haría el dedup de Silver si Bronze llegara sin
    agregar)."""
    chunk = pd.DataFrame([
        _fila_ancha(2015, "1", "1001", "Homicidio", Enero=2),
        _fila_ancha(2015, "1", "1001", "Homicidio", Enero=1),  # otra modalidad, mismo mes
        _fila_ancha(2015, "1", "1001", "Lesiones", Enero=5),
    ])

    resultado = _agregar_chunk(chunk)

    homicidio_enero = resultado[
        (resultado["Tipo de delito"] == "Homicidio") & (resultado["mes"] == 1)
    ]
    assert len(homicidio_enero) == 1
    assert homicidio_enero.iloc[0]["conteo"] == 3

    lesiones_enero = resultado[
        (resultado["Tipo de delito"] == "Lesiones") & (resultado["mes"] == 1)
    ]
    assert lesiones_enero.iloc[0]["conteo"] == 5


def test_agregar_chunk_genera_una_fila_por_mes_con_dato() -> None:
    """El unpivot debe producir 12 filas por combinación id (una por mes), no colapsar
    meses entre sí."""
    chunk = pd.DataFrame([_fila_ancha(2020, "9", "9002", "Robo", Enero=1, Marzo=4)])
    resultado = _agregar_chunk(chunk)

    assert len(resultado) == 12  # Enero..Diciembre, incluidos los ceros
    assert resultado[resultado["mes"] == 1].iloc[0]["conteo"] == 1
    assert resultado[resultado["mes"] == 3].iloc[0]["conteo"] == 4
    assert resultado[resultado["mes"] == 2].iloc[0]["conteo"] == 0


def test_agregar_chunk_no_altera_columnas_id() -> None:
    chunk = pd.DataFrame([_fila_ancha(2018, "14", "14039", "Extorsión", Julio=2)])
    resultado = _agregar_chunk(chunk)
    for columna in COLUMNAS_ID:
        assert columna in resultado.columns


# --------------------------------------------------------------------------- _derivar_cve_mun_local


def test_deriva_cve_mun_local_entidad_un_digito() -> None:
    """Aguascalientes: Clave_Ent='1', Cve. Municipio='1001' -> local '001' (caso real
    verificado a mano el 2026-08-24)."""
    assert _derivar_cve_mun_local("1", "1001") == "001"


def test_deriva_cve_mun_local_entidad_dos_digitos() -> None:
    """Puebla: Clave_Ent='21', Cve. Municipio='21002' -> local '002' (caso real
    verificado a mano el 2026-08-24, municipio Acateno)."""
    assert _derivar_cve_mun_local("21", "21002") == "002"


# --------------------------------------------------------------------------- _finalizar_agregado


def test_finalizar_agregado_re_suma_llave_repetida_entre_chunks() -> None:
    """El mismo municipio/año/mes/tipo_delito puede llegar en dos chunks distintos del
    CSV real (no está particionado por esa llave) -- _finalizar_agregado debe SUMARLOS,
    no quedarse solo con uno."""
    parcial_chunk_0 = pd.DataFrame([
        {"Año": 2019, "Clave_Ent": "21", "Cve. Municipio": "21002", "mes": 3,
         "Tipo de delito": "Robo", "conteo": 10},
    ])
    parcial_chunk_1 = pd.DataFrame([
        {"Año": 2019, "Clave_Ent": "21", "Cve. Municipio": "21002", "mes": 3,
         "Tipo de delito": "Robo", "conteo": 4},
    ])

    resultado = _finalizar_agregado(pd.concat([parcial_chunk_0, parcial_chunk_1], ignore_index=True))

    assert len(resultado) == 1
    fila = resultado.iloc[0]
    assert fila["conteo"] == 14
    assert fila["cve_ent"] == "21"
    assert fila["cve_mun"] == "002"
    assert list(resultado.columns) == [
        "cve_ent", "cve_mun", "anio", "mes", "tipo_delito", "conteo",
    ]


def test_finalizar_agregado_preserva_conteo_negativo() -> None:
    """Un ajuste retroactivo real de SESNSP puede llegar como conteo negativo (caso
    real encontrado el 2026-08-24: CDMX, sep-2017, -1). No debe filtrarse ni
    corregirse aquí -- eso es trabajo de Great Expectations (TEST-011), no del
    extractor."""
    parcial = pd.DataFrame([
        {"Año": 2017, "Clave_Ent": "9", "Cve. Municipio": "9006", "mes": 9,
         "Tipo de delito": "Otros delitos que atentan contra la libertad personal",
         "conteo": -1},
    ])
    resultado = _finalizar_agregado(parcial)
    assert resultado.iloc[0]["conteo"] == -1


# --------------------------------------------------------------------------- _descargar_a_temporal


class _RespuestaFalsa:
    def __init__(self, bloques: list[bytes]):
        self._bloques = bloques
        self.headers_recibidos: dict | None = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield from self._bloques


def _falsificar_mkstemp(monkeypatch, destino: str) -> None:
    """Redirige `tempfile.mkstemp` a una ruta fija dentro de `tmp_path` en vez del
    temp dir real del sistema."""
    fd = os.open(destino, os.O_CREAT | os.O_WRONLY)
    monkeypatch.setattr("tempfile.mkstemp", lambda **kwargs: (fd, destino))


def test_descarga_pide_accept_encoding_identity(monkeypatch, tmp_path) -> None:
    """El CDN (Akamai) devuelve un gzip roto/truncado si el cliente ofrece
    'Accept-Encoding: gzip', que es lo que `requests` manda por default -- la
    descarga debe forzar 'identity' explícitamente."""
    llamada = {}

    def _get_falso(url, timeout, stream, headers):
        llamada["headers"] = headers
        return _RespuestaFalsa([b"contenido,de,prueba\n"])

    monkeypatch.setattr("src.ingesta.extractor_sesnsp.requests.get", _get_falso)
    _falsificar_mkstemp(monkeypatch, str(tmp_path / "descarga.csv"))

    ruta = _descargar_a_temporal("https://ejemplo.test/archivo.csv")

    assert llamada["headers"] == {"Accept-Encoding": "identity"}
    with open(ruta, "rb") as f:
        assert f.read() == b"contenido,de,prueba\n"


def test_descarga_escribe_todos_los_bloques_recibidos(monkeypatch, tmp_path) -> None:
    """Varios bloques de `iter_content` deben terminar concatenados en el mismo
    archivo, en orden -- no solo el primero."""

    def _get_falso(url, timeout, stream, headers):
        return _RespuestaFalsa([b"parte1,", b"parte2,", b"parte3"])

    monkeypatch.setattr("src.ingesta.extractor_sesnsp.requests.get", _get_falso)
    _falsificar_mkstemp(monkeypatch, str(tmp_path / "descarga.csv"))

    ruta = _descargar_a_temporal("https://ejemplo.test/archivo.csv")

    with open(ruta, "rb") as f:
        assert f.read() == b"parte1,parte2,parte3"
