"""Pruebas del extractor de DS-05 SINAICA (`src/ingesta/extractor_sinaica.py`), con
datos sintéticos que reproducen la ESTRUCTURA real verificada en vivo el 2026-08-14/21
(ver `vault/14_Data_Sources/DS-05_SINAICA_Calidad_Aire.md` sección 9), no suposiciones:

- `datGrafs.php` no devuelve JSON puro: los datos vienen embebidos en una línea
  `var dat = [...]` dentro de HTML+JS. El caso que más importa proteger aquí es que el
  extractor sabe encontrar y parsear exactamente esa línea, sin asumir que toda la
  respuesta es JSON.
- Una estación sin datos para un parámetro (`var dat = [];`) es un caso ESPERADO, no un
  error -- no debe lanzar excepción, debe devolver un DataFrame vacío con las columnas
  correctas para que `pd.concat` más arriba no truene.
- Una respuesta sin el patrón `var dat = [...]` en absoluto (endpoint caído, HTML de
  error) SÍ debe fallar explícito, no devolver silenciosamente datos vacíos.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.ingesta.extractor_sinaica import (
    SOURCE_NAME,
    _parsear_estaciones_activas,
    _parsear_respuesta_datos,
)

# --------------------------------------------------------------------------- _parsear_respuesta_datos

_RESPUESTA_REAL_TIPICA = """
<script src="/lib/j/js/graficas.js"></script>
<script type="text/javascript">
    var dat = [{"id":"33PM2.526080100","fecha":"2026-08-01","hora":0,"valor":16,"bandO":"129","val":1},{"id":"33PM2.526080101","fecha":"2026-08-01","hora":1,"valor":16,"bandO":"129","val":1}];
</script>
"""


def test_parsea_respuesta_real_tipica() -> None:
    df = _parsear_respuesta_datos(_RESPUESTA_REAL_TIPICA, estacion_id=33, parametro="PM2.5")

    assert list(df.columns) == ["fecha", "hora", "valor", "val", "id_estacion", "parametro"]
    assert len(df) == 2
    assert df.iloc[0]["fecha"] == "2026-08-01"
    assert df.iloc[0]["hora"] == 0
    assert df.iloc[0]["valor"] == 16
    assert df.iloc[0]["val"] == 1
    assert df.iloc[0]["id_estacion"] == 33
    assert df.iloc[0]["parametro"] == "PM2.5"
    # bandO no está documentado por INECC -- no debe filtrarse a la salida.
    assert "bandO" not in df.columns


def test_estacion_sin_datos_para_el_parametro_no_es_error() -> None:
    """`var dat = [];` es la respuesta real cuando una estación no reporta ese
    parámetro -- caso esperado (ver docstring del módulo), no una falla."""
    respuesta_vacia = '<script>var dat = [];</script>'
    df = _parsear_respuesta_datos(respuesta_vacia, estacion_id=99, parametro="SO2")

    assert df.empty
    assert list(df.columns) == ["id_estacion", "parametro", "fecha", "hora", "valor", "val"]


def test_respuesta_sin_var_dat_falla_explicito() -> None:
    """Si el endpoint cambia o cae (HTML de error, sin 'var dat' en absoluto), debe
    fallar de forma explícita y mencionar la fuente -- no devolver datos vacíos en
    silencio, que se vería igual que 'la estación no tiene ese parámetro'."""
    html_de_error = "<html><body>Service Unavailable</body></html>"
    with pytest.raises(ValueError, match=SOURCE_NAME):
        _parsear_respuesta_datos(html_de_error, estacion_id=33, parametro="O3")


def test_multiples_estaciones_y_parametros_no_se_mezclan() -> None:
    """id_estacion/parametro los pone el extractor, no vienen en el 'var dat' -- deben
    quedar exactamente como se pidieron, no inferidos del contenido."""
    df = _parsear_respuesta_datos(_RESPUESTA_REAL_TIPICA, estacion_id=271, parametro="O3")
    assert (df["id_estacion"] == 271).all()
    assert (df["parametro"] == "O3").all()


# --------------------------------------------------------------------------- _parsear_estaciones_activas


def test_parsea_estaciones_activas_deduplica_y_ordena() -> None:
    data = [
        {"idEstacion": 53, "ultimoEnvio": "2026-08-14 13:13:46", "numDatos": 11160},
        {"idEstacion": 32, "ultimoEnvio": "2026-08-14 13:03:10", "numDatos": 14},
        {"idEstacion": 53, "ultimoEnvio": "2026-08-14 12:00:00", "numDatos": 5},  # repetida
    ]
    assert _parsear_estaciones_activas(data) == [32, 53]


def test_parsea_estaciones_activas_lista_vacia() -> None:
    assert _parsear_estaciones_activas([]) == []


def test_dataframe_vacio_es_concatenable_con_uno_con_datos() -> None:
    """Reproduce el flujo real de `extraer_sinaica_observaciones`: varias estaciones,
    algunas sin ese parámetro (DataFrame vacío) y otras con datos -- `pd.concat` no
    debe tronar ni perder las filas reales."""
    con_datos = _parsear_respuesta_datos(_RESPUESTA_REAL_TIPICA, estacion_id=33, parametro="PM2.5")
    sin_datos = _parsear_respuesta_datos('<script>var dat = [];</script>', estacion_id=99, parametro="SO2")

    combinado = pd.concat([sin_datos, con_datos], ignore_index=True)
    assert len(combinado) == 2
