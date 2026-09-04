"""Descarga y conforma la fuente oficial DS-03 CEMABE de SEP-SIGED.

SIGED distribuye CEMABE como archivos ZIP codificados en Base64 dentro de una
respuesta JSON. Los campos requeridos por FARO están repartidos entre la tabla
de inmuebles y la de centros de trabajo, relacionadas mediante ``ID_INM``.
"""
from __future__ import annotations

import base64
import io
import logging
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    # En entornos donde certifi confía en la cadena de SIGED no hace falta.
    pass

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-03_CEMABE"
API_BASE = (
    "https://api.siged.sep.gob.mx/CoreServices/servicios/archivo/"
    "buscarArchivos/grupo=CEMABE&id="
)
SOURCE_URL = API_BASE
BRONZE_PATH = Path("data/bronze/cemabe")

ARCHIVOS = {
    "inmueble": {"id_file": 343, "nombre": "INMUEBLE_CSV.zip"},
    "centrab": {"id_file": 352, "nombre": "CENTRAB_CSV.zip"},
}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.siged.sep.gob.mx/SIGED/estadistica_educativa.html",
    "Origin": "https://www.siged.sep.gob.mx",
    "Accept": "application/json, text/plain, */*",
}

_COLUMNAS_INMUEBLE = ["ID_INM", "P17A", "P18A", "P21", "P22"]
_COLUMNAS_CENTRAB = ["ID_INM", "CLAVE_CT", "P268", "P277"]
_PATRON_CLAVE_CT_TURNO = re.compile(r"^[0-9]{2}[A-Z]{3}[0-9]{4}[A-Z][0-9]$")
_REINTENTOS = 3
_ESPERA_BASE_SEG = 3
_COLUMNAS_SALIDA = [
    "cct",
    "agua_red",
    "drenaje",
    "electricidad",
    "sanitarios",
    "internet",
    "computadoras",
    "_ingested_at",
    "_source",
    "_source_url",
]


def _descargar_zip(tipo: str, session: requests.Session | None = None) -> bytes:
    """Descarga un ZIP y valida el id, nombre y contenido devueltos por SIGED."""
    info = ARCHIVOS[tipo]
    cliente = session or requests.Session()
    cliente.headers.update(HEADERS)
    url = f"{API_BASE}{info['id_file']}"

    response = None
    for intento in range(1, _REINTENTOS + 1):
        try:
            response = cliente.get(url, timeout=180)
            response.raise_for_status()
            break
        except requests.exceptions.SSLError as exc:
            raise RuntimeError(
                f"{SOURCE_NAME}: Python no confía en la cadena TLS de SIGED. "
                "Instala truststore o usa un entorno cuyo almacén de certificados "
                "del sistema esté habilitado; no se desactiva la verificación TLS."
            ) from exc
        except requests.exceptions.ConnectionError:
            if intento == _REINTENTOS:
                raise
            espera = _ESPERA_BASE_SEG * intento
            logger.warning(
                "%s: SIGED cerró la conexión (%d/%d); reintento en %ds",
                SOURCE_NAME,
                intento,
                _REINTENTOS,
                espera,
            )
            time.sleep(espera)

    if response is None:
        raise RuntimeError(f"{SOURCE_NAME}: descarga sin respuesta")

    datos = response.json().get("datos") or []
    if len(datos) != 1:
        raise ValueError(
            f"{SOURCE_NAME}: idFile={info['id_file']} devolvió {len(datos)} archivos; "
            "se esperaba exactamente uno"
        )
    archivo = datos[0]
    if archivo.get("idFile") != info["id_file"] or archivo.get("name") != info["nombre"]:
        raise ValueError(
            f"{SOURCE_NAME}: idFile={info['id_file']} ya no corresponde a "
            f"{info['nombre']!r}; SIGED devolvió {archivo.get('name')!r}"
        )

    try:
        contenido = base64.b64decode(archivo["base64"], validate=True)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{SOURCE_NAME}: respuesta sin Base64 válido para {tipo}") from exc
    if not zipfile.is_zipfile(io.BytesIO(contenido)):
        raise ValueError(f"{SOURCE_NAME}: {info['nombre']} no contiene un ZIP válido")
    return contenido


def _leer_csv_zip(contenido: bytes, columnas: list[str], tipo: str) -> pd.DataFrame:
    """Lee únicamente las columnas físicas necesarias de un ZIP oficial."""
    with zipfile.ZipFile(io.BytesIO(contenido)) as zf:
        miembros = []
        for member in zf.infolist():
            ruta = PurePosixPath(member.filename.replace("\\", "/"))
            if ruta.is_absolute() or ".." in ruta.parts or member.is_dir():
                continue
            if ruta.suffix.lower() == ".csv":
                miembros.append(member)
        if len(miembros) != 1:
            raise ValueError(
                f"{SOURCE_NAME}: ZIP {tipo} contiene {len(miembros)} CSV; se esperaba uno"
            )
        try:
            return pd.read_csv(
                zf.open(miembros[0]),
                usecols=columnas,
                dtype=str,
                keep_default_na=False,
                encoding="latin-1",
            )
        except ValueError as exc:
            raise ValueError(
                f"{SOURCE_NAME}: el CSV {tipo} no cumple las columnas {columnas}"
            ) from exc


def _mapear_codigos(
    serie: pd.Series, codigos_si: set[str], codigos_no: set[str]
) -> pd.Series:
    """Convierte códigos oficiales a 1/0 y conserva ausencia como cadena vacía."""
    valores = serie.astype("string").str.strip()
    salida = pd.Series("", index=serie.index, dtype="string")
    salida.loc[valores.isin(codigos_si)] = "1"
    salida.loc[valores.isin(codigos_no)] = "0"
    return salida


def _mapear_computadoras(serie: pd.Series) -> pd.Series:
    """Convierte el conteo P277 en disponibilidad binaria; 9999 es no especificado."""
    numeros = pd.to_numeric(serie.astype("string").str.strip(), errors="coerce")
    salida = pd.Series("", index=serie.index, dtype="string")
    salida.loc[numeros.eq(0)] = "0"
    salida.loc[numeros.gt(0) & numeros.ne(9999)] = "1"
    return salida


def _agregar_disponibilidad(serie: pd.Series) -> str:
    """Consolida turnos: cualquier disponibilidad afirmativa prevalece."""
    valores = set(serie.dropna().astype(str))
    if "1" in valores:
        return "1"
    if "0" in valores:
        return "0"
    return ""


def conformar_cemabe(inmuebles: pd.DataFrame, centros: pd.DataFrame) -> pd.DataFrame:
    """Une los dos archivos reales y produce el contrato Bronze vigente por CCT."""
    faltantes_inmueble = set(_COLUMNAS_INMUEBLE) - set(inmuebles.columns)
    faltantes_centrab = set(_COLUMNAS_CENTRAB) - set(centros.columns)
    if faltantes_inmueble or faltantes_centrab:
        raise ValueError(
            f"{SOURCE_NAME}: columnas faltantes; inmueble={sorted(faltantes_inmueble)}, "
            f"centrab={sorted(faltantes_centrab)}"
        )

    inmuebles = inmuebles[_COLUMNAS_INMUEBLE].copy()
    centros = centros[_COLUMNAS_CENTRAB].copy()
    for frame in (inmuebles, centros):
        frame["ID_INM"] = frame["ID_INM"].astype("string").str.strip().str.zfill(6)

    duplicados = inmuebles["ID_INM"].duplicated(keep=False)
    if duplicados.any():
        muestra = inmuebles.loc[duplicados, "ID_INM"].head(5).tolist()
        raise ValueError(f"{SOURCE_NAME}: ID_INM duplicado en INMUEBLE: {muestra}")

    claves = centros["CLAVE_CT"].astype("string").str.strip().str.upper()
    invalidas = claves.ne("") & ~claves.str.match(_PATRON_CLAVE_CT_TURNO, na=False)
    if invalidas.any():
        logger.warning(
            "%s: se excluyen %d claves temporales/no canónicas; muestra=%s",
            SOURCE_NAME,
            int(invalidas.sum()),
            claves.loc[invalidas].head(5).tolist(),
        )
    validas = claves.str.match(_PATRON_CLAVE_CT_TURNO, na=False)
    centros = centros.loc[validas].copy()
    centros["cct"] = claves.loc[validas].str[:-1]

    unido = centros.merge(inmuebles, on="ID_INM", how="left", validate="many_to_one")
    unido["agua_red"] = _mapear_codigos(unido["P17A"], {"1"}, {"2", "3", "4", "5", "6"})
    unido["electricidad"] = _mapear_codigos(unido["P18A"], {"1", "2", "3", "4"}, {"5"})
    unido["sanitarios"] = _mapear_codigos(unido["P21"], {"1"}, {"2"})
    unido["drenaje"] = _mapear_codigos(unido["P22"], {"1"}, {"2"})
    unido["internet"] = _mapear_codigos(unido["P268"], {"1"}, {"2"})
    unido["computadoras"] = _mapear_computadoras(unido["P277"])

    drivers = [
        "agua_red", "drenaje", "electricidad", "sanitarios", "internet", "computadoras"
    ]
    salida = unido.groupby("cct", as_index=False)[drivers].agg(_agregar_disponibilidad)
    if salida.empty:
        raise ValueError(f"{SOURCE_NAME}: la unión oficial no produjo ningún CCT")
    return salida


def extraer_cemabe() -> str:
    """Descarga CEMABE, conforma una fila por CCT y guarda el Parquet Bronze."""
    logger.info("Iniciando extracción de %s", SOURCE_NAME)
    session = requests.Session()
    session.headers.update(HEADERS)
    inmueble_zip = _descargar_zip("inmueble", session)
    time.sleep(2)
    centrab_zip = _descargar_zip("centrab", session)

    inmuebles = _leer_csv_zip(inmueble_zip, _COLUMNAS_INMUEBLE, "inmueble")
    centros = _leer_csv_zip(centrab_zip, _COLUMNAS_CENTRAB, "centrab")
    df = conformar_cemabe(inmuebles, centros)

    ingested_at = datetime.now(timezone.utc)
    df["_ingested_at"] = ingested_at
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    timestamp = ingested_at.strftime("%Y%m%d_%H%M%S")
    output_path = BRONZE_PATH / f"cemabe_2013_{timestamp}.parquet"
    df[_COLUMNAS_SALIDA].to_parquet(output_path, index=False)
    logger.info("Guardado %s (%d CCT)", output_path, len(df))
    return str(output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print(extraer_cemabe())
