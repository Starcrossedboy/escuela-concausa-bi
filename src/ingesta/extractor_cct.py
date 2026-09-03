"""Extractor de DS-02 SEP Catalogo CCT -- automatiza la descarga de los 2 ZIP reales del
portal SIGED (antes se descargaban a mano, ver cargar_bronze_cct_real.py y
DS-02_Catalogo_CCT.md SS9).

El portal (siged.sep.gob.mx/SIGED/datos_abiertos.html) no expone un link de descarga directo:
el boton dispara JavaScript (AngularJS, ver SIGED/js/tablas_siged.js `descargarArchivo`) que
arma el archivo como Blob en el navegador (URL.createObjectURL, efimera -- confirmado real via
kMDItemWhereFroms de un ZIP ya descargado, ver DevLog 2026-09-03) y lo guarda con FileSaver --
no hay URL de archivo estatica que copiar del navegador.

Verificado en vivo 2026-09-03 (inspeccion del JS + llamada real a la API, ver DevLog): el JS
llama a

    GET https://api.siged.sep.gob.mx/CoreServices/servicios/archivo/buscarArchivos/grupo=CCTS&id={idFile}

que devuelve {"datos": [{"idFile":.., "name":.., "base64":.., "tipo":.., ...}]} -- el archivo
completo en base64. Los `idFile` de las dos partes del catalogo (verificados en vivo contra el
listado sin id, `grupo=CCTS&id=`, que devuelve las 5 filas del portal con su idFile real):

    idFile=4 -> CATALOGO_CENTRO_TRABAJO_01_16_CSV.zip
    idFile=3 -> CATALOGO_CENTRO_TRABAJO_17_32_CSV.zip

OJO -- estos ids son PK de una base de datos, no una formula derivable: si SIGED alguna vez
borra y vuelve a subir estos archivos, el id puede cambiar. Por eso esta funcion SIEMPRE valida
que el `name` que regresa la API coincide con el nombre esperado antes de aceptar el archivo --
si no coincide, falla explicito en vez de cargar el archivo equivocado en silencio (mismo
principio que _detectar_columna_cct en extractor_formato911_historico.py: nunca adivinar).

Uso:
    python -m src.ingesta.extractor_cct
"""
import base64
import logging
import time
import zipfile
from pathlib import Path

import truststore

# api.siged.sep.gob.mx manda una cadena de certificados que curl/macOS valida bien (usa el
# llavero del sistema) pero que el bundle propio de Python (certifi) rechaza con
# "unable to get local issuer certificate" -- verificado real 2026-09-03 (curl -v: "SSL
# certificate verify ok", requests: SSLCertVerificationError). truststore hace que el modulo
# ssl de Python use el mismo almacen de confianza del sistema operativo que ya usa curl, en vez
# de su propio bundle -- no es bajar la verificacion, es usar la misma fuente de confianza que
# ya funciona. Debe inyectarse antes de importar requests.
truststore.inject_into_ssl()

import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-02_CATALOGO_CCT"
API_BASE = "https://api.siged.sep.gob.mx/CoreServices/servicios/archivo/buscarArchivos/grupo=CCTS&id="
BRONZE_PATH = "data/bronze/cct"

# Verificados en vivo 2026-09-03 contra el listado real (grupo=CCTS&id=, sin id -- devuelve
# las 5 filas del portal con su idFile). Ver docstring del modulo -- son PK de base de datos,
# no formula.
ARCHIVOS = {
    "01_16": {"id_file": 4, "nombre_esperado": "CATALOGO_CENTRO_TRABAJO_01_16_CSV.zip"},
    "17_32": {"id_file": 3, "nombre_esperado": "CATALOGO_CENTRO_TRABAJO_17_32_CSV.zip"},
}

# La API no es publica de proposito general: solo la llama el propio portal SIGED (via JS,
# ver docstring). Sin cabeceras que la identifiquen como una llamada de navegador normal,
# el servidor cierra la conexion sin responder (ConnectionError: Remote end closed
# connection without response -- verificado real 2026-09-03, no es un problema del cliente
# ni de SSL, ese ya se resolvio con truststore arriba). Se agregan las mismas cabeceras que
# manda el navegador real al llamar este endpoint desde datos_abiertos.html: User-Agent de
# navegador, Referer/Origin del portal, y Accept de JSON.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.siged.sep.gob.mx/SIGED/datos_abiertos.html",
    "Origin": "https://www.siged.sep.gob.mx",
    "Accept": "application/json, text/plain, */*",
}

# Sesion compartida (no un requests.get() suelto por llamada): conserva las cookies que la
# API pudiera fijar en la primera respuesta para la segunda, igual que hace un navegador real
# entre dos clics en la misma pagina.
_SESSION = requests.Session()
_SESSION.headers.update(HEADERS)

# La API cerro la conexion sin responder (RemoteDisconnected) en la 2a llamada consecutiva
# de la misma corrida -- verificado real 2026-09-03, probable limite de tasa/proteccion
# anti-bot ante 2 requests seguidas sin pausa. Reintento con backoff + una pausa entre partes
# en vez de golpear la API de vuelta inmediatamente (mismo principio de las demas fuentes:
# nunca inventar, aqui tampoco se inventa nada -- es tolerar una falla transitoria conocida).
_REINTENTOS = 3
_ESPERA_BASE_SEG = 3


def _descargar_y_extraer(parte: str) -> str:
    """Descarga un ZIP real (via la API real de SIGED, ver docstring), valida que el nombre
    coincide con el esperado, lo extrae, y devuelve la ruta al CSV que contiene."""
    info = ARCHIVOS[parte]
    logger.info("%s: descargando parte %s (idFile=%d)", SOURCE_NAME, parte, info["id_file"])

    respuesta = None
    for intento in range(1, _REINTENTOS + 1):
        try:
            respuesta = _SESSION.get(f"{API_BASE}{info['id_file']}", timeout=180)
            respuesta.raise_for_status()
            break
        except requests.exceptions.ConnectionError as exc:
            if intento == _REINTENTOS:
                raise
            espera = _ESPERA_BASE_SEG * intento
            logger.warning(
                "%s: intento %d/%d fallo (%s), reintentando en %ds",
                SOURCE_NAME, intento, _REINTENTOS, exc, espera,
            )
            time.sleep(espera)
    datos = respuesta.json().get("datos") or []
    if not datos:
        raise ValueError(
            f"{SOURCE_NAME}: la API no devolvio ningun archivo para idFile={info['id_file']} "
            f"(parte {parte}). El id pudo haber cambiado -- revisar a mano en "
            "https://www.siged.sep.gob.mx/SIGED/datos_abiertos.html"
        )
    archivo = datos[0]

    if archivo.get("name") != info["nombre_esperado"]:
        raise ValueError(
            f"{SOURCE_NAME}: idFile={info['id_file']} (parte {parte}) ya no apunta a "
            f"{info['nombre_esperado']!r} -- ahora es {archivo.get('name')!r}. El id cambio en "
            "SIGED, no se adivina cual es el correcto ahora: revisar a mano el portal."
        )

    Path(BRONZE_PATH).mkdir(parents=True, exist_ok=True)
    ruta_zip = f"{BRONZE_PATH}/{archivo['name']}"
    with open(ruta_zip, "wb") as f:
        f.write(base64.b64decode(archivo["base64"]))
    logger.info("%s: guardado %s", SOURCE_NAME, ruta_zip)

    with zipfile.ZipFile(ruta_zip) as zf:
        csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(csvs) != 1:
            raise ValueError(
                f"{SOURCE_NAME}: {ruta_zip} no trae exactamente 1 CSV adentro (trae {csvs}) -- "
                "no se adivina cual usar, revisar a mano."
            )
        zf.extract(csvs[0], BRONZE_PATH)
        ruta_csv = f"{BRONZE_PATH}/{csvs[0]}"

    logger.info("%s: extraido %s", SOURCE_NAME, ruta_csv)
    return ruta_csv


def extraer_cct() -> tuple:
    """Descarga y extrae las 2 partes reales del catalogo CCT. Devuelve (ruta_01_16, ruta_17_32)."""
    ruta_01_16 = _descargar_y_extraer("01_16")
    time.sleep(2)  # pausa entre partes, ver _REINTENTOS arriba
    ruta_17_32 = _descargar_y_extraer("17_32")
    return ruta_01_16, ruta_17_32


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    r1, r2 = extraer_cct()
    print("OK:")
    print(f"  {r1}")
    print(f"  {r2}")
