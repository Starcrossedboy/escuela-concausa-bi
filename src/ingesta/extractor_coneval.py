"""Extractor real de CONEVAL (DS-07).

Descarga exclusivamente dos productos oficiales de CONEVAL:
- Índice de Rezago Social (IRS) municipal 2020.
- Concentrado de Medición de Pobreza Municipal 2010-2020 (edición 2020).

Ambos aterrizan como artefactos Bronze separados. Bronze conserva el contenido
oficial sin joins ni renombres de negocio; únicamente serializa el encabezado
jerárquico del XLSX a nombres de columna de texto para poder escribir Parquet.
La homologación de clave INEGI, selección del periodo 2020 y conformación IRS +
pobreza ocurren después, en Silver.

La estructura física utilizada aquí fue verificada contra los ZIP oficiales de
CONEVAL el 2026-08-30 y quedó documentada en
`_DevLog/2026-08-30-deni-garrido-ds07-probe-esquema-real.md`.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import unicodedata
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SOURCE_NAME = "DS-07_CONEVAL"
PERIODO_OBJETIVO = 2020

IRS_URL = (
    "https://www.coneval.org.mx/Medicion/Documents/"
    "IRS_2020/IRS_ent_mun_2000_2020.zip"
)
POBREZA_URL = (
    "https://www.coneval.org.mx/Medicion/Documents/"
    "Pobreza_municipal/2020/"
    "Concentrado_indicadores_de_pobreza_2020.zip"
)

# Contrato físico confirmado en vivo (probe DS-07 2026-08-30).
IRS_MEMBER_2020 = "IRS_entidades_mpios_2020.xlsx"
IRS_SHEET = "Municipios"
POBREZA_MEMBER_2020 = "Concentrado_indicadores_de_pobreza_2020.xlsx"
POBREZA_SHEET = "Concentrado municipal"
# Excel rows 5-6 => índices base cero 4-5 en pandas.
HEADER_ROWS = (4, 5)

BRONZE_ROOT = Path("data/bronze/coneval")
IRS_BRONZE_PATH = BRONZE_ROOT / "irs"
POBREZA_BRONZE_PATH = BRONZE_ROOT / "pobreza"
MANIFEST_PATH = BRONZE_ROOT / "manifests"

_HOSTS_OFICIALES = {"www.coneval.org.mx", "coneval.org.mx"}
_EXTENSIONES_TABULARES = {".xlsx", ".xls", ".csv"}


@dataclass(frozen=True)
class DescargaOficial:
    """Metadatos verificables de una descarga oficial de CONEVAL."""

    producto: str
    url_solicitada: str
    url_final: str
    sha256: str
    bytes_descargados: int


@dataclass(frozen=True)
class TablaDetectada:
    """Ubicación física y esquema de la tabla oficial seleccionada."""

    producto: str
    archivo: str
    hoja: str
    header_rows: tuple[int, int]
    filas: int
    columnas: int
    columnas_nombres: tuple[str, ...]


def _normalizar_texto(valor: object) -> str:
    """Normaliza texto solo para validaciones, nunca para persistir métricas."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-zA-Z0-9]+", " ", texto).lower()
    return " ".join(texto.split())


def _limpiar_etiqueta(valor: object) -> str:
    """Limpia solo whitespace de una etiqueta física del XLSX."""
    if valor is None:
        return ""
    texto = re.sub(r"\s+", " ", str(valor)).strip()
    if texto.lower().startswith("unnamed:"):
        return ""
    return texto


def _aplanar_columnas(columnas: pd.Index) -> list[str]:
    """Serializa un header multinivel sin crear aliases de negocio.

    Los XLSX oficiales usan dos filas de encabezado con celdas combinadas. Parquet
    necesita nombres de columna de texto, así que unimos los niveles originales con
    ` | `. Si el segundo nivel es `Unnamed`, se conserva únicamente el primero.
    """
    salida: list[str] = []
    usados: dict[str, int] = {}

    for col in columnas:
        niveles = col if isinstance(col, tuple) else (col,)
        partes: list[str] = []
        for nivel in niveles:
            limpio = _limpiar_etiqueta(nivel)
            if limpio and (not partes or limpio != partes[-1]):
                partes.append(limpio)
        nombre = " | ".join(partes) or "columna_sin_nombre"

        # Evita nombres duplicados sin alterar el significado de la etiqueta.
        cuenta = usados.get(nombre, 0) + 1
        usados[nombre] = cuenta
        if cuenta > 1:
            nombre = f"{nombre} | duplicado_{cuenta}"
        salida.append(nombre)

    return salida


def _validar_url_oficial(url: str) -> None:
    """Exige HTTPS y dominio institucional exacto de CONEVAL."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https" or host not in _HOSTS_OFICIALES:
        raise ValueError(
            f"{SOURCE_NAME}: URL no oficial o insegura: {url!r}. "
            "Solo se acepta HTTPS en coneval.org.mx."
        )


def _validar_zip_seguro(data: bytes) -> list[str]:
    """Valida ZIP no vacío y evita path traversal al inspeccionar miembros."""
    if not data or not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError(f"{SOURCE_NAME}: la respuesta no es un ZIP válido")

    tabulares: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.infolist():
            ruta = PurePosixPath(member.filename.replace("\\", "/"))
            tiene_drive = bool(ruta.parts and ":" in ruta.parts[0])
            if ruta.is_absolute() or ".." in ruta.parts or tiene_drive:
                raise ValueError(
                    f"{SOURCE_NAME}: ZIP inseguro; ruta no permitida: {member.filename!r}"
                )
            if member.is_dir():
                continue
            suffix = Path(member.filename).suffix.lower()
            es_temporal = Path(member.filename).name.startswith("~$")
            if suffix in _EXTENSIONES_TABULARES and not es_temporal:
                tabulares.append(member.filename)

    if not tabulares:
        raise ValueError(f"{SOURCE_NAME}: ZIP válido pero sin archivo tabular")
    return tabulares


def _descargar_zip_oficial(producto: str, url: str) -> tuple[DescargaOficial, bytes]:
    """Descarga y valida un ZIP institucional de CONEVAL."""
    _validar_url_oficial(url)
    response = requests.get(
        url,
        timeout=120,
        allow_redirects=True,
        headers={"User-Agent": "FARO-DS07/1.0 (proyecto académico)"},
    )
    response.raise_for_status()
    _validar_url_oficial(response.url)

    data = response.content
    _validar_zip_seguro(data)
    meta = DescargaOficial(
        producto=producto,
        url_solicitada=url,
        url_final=response.url,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes_descargados=len(data),
    )
    return meta, data


def _leer_xlsx_oficial(
    zip_bytes: bytes,
    *,
    producto: str,
    member: str,
    sheet: str,
) -> pd.DataFrame:
    """Lee el workbook/hoja exactos confirmados por el probe real DS-07."""
    miembros = _validar_zip_seguro(zip_bytes)
    if member not in miembros:
        raise ValueError(
            f"{SOURCE_NAME}: {producto} cambió su estructura: no existe {member!r}. "
            f"Miembros tabulares encontrados: {miembros}"
        )

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        xlsx = zf.read(member)

    try:
        excel = pd.ExcelFile(io.BytesIO(xlsx), engine="openpyxl")
    except ImportError as exc:
        raise RuntimeError(
            "DS-07 requiere openpyxl para leer los XLSX oficiales de CONEVAL."
        ) from exc

    if sheet not in excel.sheet_names:
        raise ValueError(
            f"{SOURCE_NAME}: {producto} cambió su estructura: falta hoja {sheet!r}; "
            f"hojas encontradas={excel.sheet_names}"
        )

    df = pd.read_excel(
        excel,
        sheet_name=sheet,
        header=list(HEADER_ROWS),
        dtype=object,
    )
    df.columns = _aplanar_columnas(df.columns)
    df = df.dropna(how="all")
    if df.empty:
        raise ValueError(f"{SOURCE_NAME}: {producto} quedó vacío después de leer XLSX")
    return df


def _buscar_columna_unica(df: pd.DataFrame, *tokens: str) -> str:
    """Encuentra una única columna cuyo nombre normalizado contiene todos los tokens."""
    candidatos = []
    for col in df.columns:
        n = _normalizar_texto(col)
        if all(_normalizar_texto(t) in n for t in tokens):
            candidatos.append(str(col))
    if len(candidatos) != 1:
        raise ValueError(
            f"{SOURCE_NAME}: columna ambigua/no encontrada para tokens={tokens}: {candidatos}"
        )
    return candidatos[0]


def _validar_contrato_irs(df: pd.DataFrame) -> dict[str, str]:
    """Valida que el workbook IRS leído conserva el contrato municipal 2020."""
    cols = {
        "cve_ent": _buscar_columna_unica(df, "clave", "entidad"),
        "entidad": _buscar_columna_unica(df, "entidad", "federativa"),
        "cve_mun": _buscar_columna_unica(df, "clave", "municipio"),
        "indice": _buscar_columna_unica(df, "indice", "rezago", "social"),
        "grado": _buscar_columna_unica(df, "grado", "rezago", "social"),
    }

    # La búsqueda simple de `municipio` también capturaría `Clave municipio`.
    mun_candidates = [
        str(c)
        for c in df.columns
        if _normalizar_texto(c) == "municipio"
    ]
    if len(mun_candidates) != 1:
        raise ValueError(
            f"{SOURCE_NAME}: IRS requiere una columna física exacta 'Municipio': {mun_candidates}"
        )
    cols["municipio"] = mun_candidates[0]
    return cols


def _validar_contrato_pobreza(df: pd.DataFrame) -> dict[str, str]:
    """Valida el concentrado municipal y localiza Pobreza | Porcentaje 2020."""
    cols = {
        "cve_ent": _buscar_columna_unica(df, "clave", "entidad"),
        "entidad": _buscar_columna_unica(df, "entidad", "federativa"),
        "cve_mun": _buscar_columna_unica(df, "clave", "municipio"),
    }

    mun_candidates = [str(c) for c in df.columns if _normalizar_texto(c) == "municipio"]
    if len(mun_candidates) != 1:
        raise ValueError(
            f"{SOURCE_NAME}: pobreza requiere una columna física exacta 'Municipio': {mun_candidates}"
        )
    cols["municipio"] = mun_candidates[0]

    pobreza_2020 = [
        str(c)
        for c in df.columns
        if _normalizar_texto(c) == "pobreza porcentaje 2020"
    ]
    if len(pobreza_2020) != 1:
        raise ValueError(
            f"{SOURCE_NAME}: se esperaba exactamente 'Pobreza | Porcentaje 2020'; "
            f"candidatos={pobreza_2020}"
        )
    cols["pobreza_pct_2020"] = pobreza_2020[0]
    return cols


def _guardar_bronze(
    producto: str,
    df: pd.DataFrame,
    source_url: str,
    archivo: str,
    hoja: str,
    ingested_at: datetime,
) -> tuple[str, TablaDetectada]:
    """Añade solo metadatos técnicos y escribe el producto como Parquet Bronze."""
    base = IRS_BRONZE_PATH if producto == "irs" else POBREZA_BRONZE_PATH
    base.mkdir(parents=True, exist_ok=True)

    out = df.copy()

    # Bronze preserva el valor crudo. Los XLSX oficiales mezclan números con
    # etiquetas textuales como `n.d.` en una misma columna; PyArrow no puede
    # serializar de forma segura ese dtype `object` mixto. Solo para persistencia
    # Parquet convertimos esas columnas mixtas a texto, sin interpretar ni
    # reemplazar valores. El tipado de negocio ocurre después en Silver.
    for columna in out.columns:
        if out[columna].dtype == "object":
            out[columna] = out[columna].astype("string")

    # Metadato técnico de procedencia temporal del artefacto oficial seleccionado.
    out["_periodo_medicion"] = PERIODO_OBJETIVO
    out["_ingested_at"] = ingested_at
    out["_source"] = SOURCE_NAME
    out["_source_url"] = source_url

    stamp = ingested_at.strftime("%Y%m%d_%H%M%S")
    output_path = base / f"coneval_{producto}_{PERIODO_OBJETIVO}_{stamp}.parquet"
    out.to_parquet(output_path, index=False)

    tabla = TablaDetectada(
        producto=producto,
        archivo=archivo,
        hoja=hoja,
        header_rows=HEADER_ROWS,
        filas=len(df),
        columnas=len(df.columns),
        columnas_nombres=tuple(str(c) for c in df.columns),
    )
    return str(output_path), tabla


def _guardar_manifest(
    ingested_at: datetime,
    descargas: list[DescargaOficial],
    tablas: list[TablaDetectada],
    contratos: dict[str, dict[str, str]],
) -> str:
    """Guarda evidencia reproducible de descarga y esquema, sin datos municipales."""
    MANIFEST_PATH.mkdir(parents=True, exist_ok=True)
    stamp = ingested_at.strftime("%Y%m%d_%H%M%S")
    path = MANIFEST_PATH / f"ds07_coneval_{stamp}.json"
    payload = {
        "source": SOURCE_NAME,
        "periodo_objetivo": PERIODO_OBJETIVO,
        "ingested_at": ingested_at.isoformat(),
        "descargas": [asdict(item) for item in descargas],
        "tablas": [asdict(item) for item in tablas],
        "contratos_detectados": contratos,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(path)


def extraer_coneval() -> dict[str, str]:
    """Descarga IRS y pobreza municipal oficiales y genera dos Bronze + manifiesto."""
    logger.info("Iniciando extracción real de %s", SOURCE_NAME)
    ingested_at = datetime.now(timezone.utc)

    irs_meta, irs_zip = _descargar_zip_oficial("irs", IRS_URL)
    pobreza_meta, pobreza_zip = _descargar_zip_oficial("pobreza", POBREZA_URL)

    irs_df = _leer_xlsx_oficial(
        irs_zip,
        producto="irs",
        member=IRS_MEMBER_2020,
        sheet=IRS_SHEET,
    )
    pobreza_df = _leer_xlsx_oficial(
        pobreza_zip,
        producto="pobreza",
        member=POBREZA_MEMBER_2020,
        sheet=POBREZA_SHEET,
    )

    contratos = {
        "irs": _validar_contrato_irs(irs_df),
        "pobreza": _validar_contrato_pobreza(pobreza_df),
    }

    irs_path, irs_tabla = _guardar_bronze(
        "irs",
        irs_df,
        irs_meta.url_final,
        IRS_MEMBER_2020,
        IRS_SHEET,
        ingested_at,
    )
    pobreza_path, pobreza_tabla = _guardar_bronze(
        "pobreza",
        pobreza_df,
        pobreza_meta.url_final,
        POBREZA_MEMBER_2020,
        POBREZA_SHEET,
        ingested_at,
    )
    manifest_path = _guardar_manifest(
        ingested_at,
        [irs_meta, pobreza_meta],
        [irs_tabla, pobreza_tabla],
        contratos,
    )

    logger.info(
        "DS-07 real guardado: IRS=%s (%d filas), pobreza=%s (%d filas)",
        irs_path,
        irs_tabla.filas,
        pobreza_path,
        pobreza_tabla.filas,
    )
    return {
        "irs": irs_path,
        "pobreza": pobreza_path,
        "manifest": manifest_path,
    }
