#!/usr/bin/env python3
"""
FARO — Sincronizar capa semántica a Superset.

Lee los archivos YAML y SQL de superset/semantic/ y configura:
  - Conexión a la base de datos gold
  - Datasets virtuales (uno por cada .sql)
  - Métricas y columnas/dimensiones (desde metrics_*.yaml)

Idempotente: crea nuevos, actualiza existentes, reporta cambios.
No modifica archivos fuente (superset/semantic/*).

Uso:
    source .venv/bin/activate
    python superset/sync_semantic_layer.py

Requiere que Superset esté corriendo (docker compose up superset) y que
las variables de entorno estén configuradas (copiar de .env.example).
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import re
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuración desde variables de entorno
# ---------------------------------------------------------------------------

SUPERSET_URL = os.environ.get("SUPERSET_URL", "http://127.0.0.1:8088")
ADMIN_USER = os.environ.get("SUPERSET_ADMIN_USERNAME", "faro_superset_admin")
ADMIN_PASS = os.environ.get("SUPERSET_ADMIN_PASSWORD", "")

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "escuela_concausa_db")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "")

# Nombre interno que Superset asigna a la conexión
CONNECTION_NAME = "faro_escuela_concausa_db"

SEMANTIC_DIR = Path(__file__).resolve().parent / "semantic"

# ---------------------------------------------------------------------------
# Utilidades HTTP (stdlib, sin dependencias externas)
# ---------------------------------------------------------------------------

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

# Cookie jar compartido para persistir sesión entre requests
_cookie_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_cookie_jar),
    urllib.request.HTTPSHandler(context=_CTX),
)


def _request(
    method: str,
    path: str,
    token: str | None = None,
    body: dict | None = None,
    csrf_token: str | None = None,
) -> dict:
    url = f"{SUPERSET_URL}{path}"
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if csrf_token:
        headers["X-CSRFToken"] = csrf_token
        headers["Referer"] = SUPERSET_URL

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with _opener.open(req) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode() if exc.fp else ""
        print(f"  ✗ HTTP {exc.code} en {method} {path}: {err_body[:300]}")
        raise


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

def login() -> tuple[str, str]:
    """Obtiene JWT + CSRF token de Superset."""
    resp = _request("POST", "/api/v1/security/login", body={
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
        "provider": "db",
        "refresh": True,
    })
    access_token = resp.get("access_token", "")
    if not access_token:
        print("✗ No se pudo obtener access_token. Verifica credenciales.")
        sys.exit(1)

    # El endpoint de CSRF token establece una cookie de sesión necesaria
    # para los POST subsiguientes. La cookie se persiste en _cookie_jar.
    csrf_resp = _request("GET", "/api/v1/security/csrf_token/", token=access_token)
    csrf_token = csrf_resp.get("result", "")
    print("✔ Autenticado en Superset")
    return access_token, csrf_token


# ---------------------------------------------------------------------------
# Conexión a base de datos
# ---------------------------------------------------------------------------

def ensure_database(token: str, csrf: str) -> int:
    """Crea o actualiza la conexión a escuela_concausa_db. Retorna el ID."""
    resp = _request("GET", "/api/v1/database/", token=token)
    for db in resp.get("result", []):
        if db.get("database_name") == CONNECTION_NAME:
            print(f"✔ Conexión '{CONNECTION_NAME}' ya existe (id={db['id']})")
            return db["id"]

    # La URI de conexión usa 'db' (nombre del servicio Docker), NO localhost.
    # Superset corre dentro de la red Docker y necesita resolver 'db'.
    superset_db_host = "db"
    body = {
        "database_name": CONNECTION_NAME,
        "engine": "postgresql",
        "sqlalchemy_uri": f"postgresql://{DB_USER}:{DB_PASS}@{superset_db_host}:{DB_PORT}/{DB_NAME}",
        "expose_in_sqllab": True,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
        "allow_run_async": False,
        "extra": json.dumps({
            "allows_virtual_table_explore": True,
            "disable_sql_lab": False,
        }),
    }
    created = _request("POST", "/api/v1/database/", token=token, csrf_token=csrf, body=body)
    db_id = created.get("id")
    print(f"✔ Conexión '{CONNECTION_NAME}' creada (id={db_id})")
    return db_id


# ---------------------------------------------------------------------------
# Datasets virtuales
# ---------------------------------------------------------------------------

def _read_sql(path: Path) -> str:
    """Lee un archivo .sql y extrae la query (sin comentarios al inicio)."""
    raw = path.read_text()
    # Quitar comentarios SQL al inicio (líneas que empiezan con --)
    lines = []
    in_comment_block = True
    for line in raw.splitlines():
        stripped = line.strip()
        if in_comment_block and (stripped.startswith("--") or stripped == ""):
            continue
        in_comment_block = False
        lines.append(line)
    return "\n".join(lines)


def ensure_datasets(
    token: str, csrf: str, db_id: int
) -> dict[str, int]:
    """Crea datasets virtuales desde cada .sql. Retorna {nombre: dataset_id}."""
    resp = _request("GET", "/api/v1/dataset/", token=token)
    existing = {
        d["table_name"]: d["id"]
        for d in resp.get("result", [])
        if d.get("database", {}).get("id") == db_id or d.get("database") == db_id
    }

    datasets: dict[str, int] = {}
    for sql_file in sorted(SEMANTIC_DIR.glob("*.sql")):
        name = sql_file.stem  # p.ej. db03_cubo_escuela_360
        sql = _read_sql(sql_file)

        if name in existing:
            ds_id = existing[name]
            print(f"  ✔ Dataset '{name}' existe (id={ds_id})")
        else:
            body = {
                "database": db_id,
                "sql": sql,
                "schema": "gold",
                "table_name": name,
            }
            created = _request(
                "POST", "/api/v1/dataset/", token=token, csrf_token=csrf, body=body
            )
            ds_id = created.get("id")
            print(f"  ✔ Dataset '{name}' creado (id={ds_id})")

        datasets[name] = ds_id

    return datasets


# ---------------------------------------------------------------------------
# Métricas y dimensiones
# ---------------------------------------------------------------------------

def _read_yaml(path: Path) -> dict:
    """
    Parser YAML mínimo para el formato de metrics_db03_db04.yaml.
    Sin dependencias externas. Maneja estructuras planas y anidadas simples.
    """
    try:
        import yaml
        return yaml.safe_load(path.read_text())
    except ImportError:
        pass

    # Fallback: parser manual para la estructura conocida
    # Parsea el YAML línea por línea, manejando indentación
    result: dict[str, Any] = {}
    stack: list[tuple[int, dict | list]] = [(0, result)]
    current_key: str | None = None
    list_accumulator: list | None = None
    in_block_scalar = False
    block_lines: list[str] = []

    for line in path.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if in_block_scalar:
            if indent > stack[-1][0]:
                block_lines.append(line.rstrip())
                continue
            else:
                if list_accumulator is not None and current_key:
                    list_accumulator.append(" ".join(block_lines))
                in_block_scalar = False
                block_lines = []

        if stripped.startswith("- "):
            # Elemento de lista
            val = stripped[2:].strip()
            if ":" in val:
                # Objeto dentro de lista: - nombre: foo
                key_val = val.split(":", 1)
                obj = {key_val[0].strip(): _coerce(key_val[1].strip())}
                if list_accumulator is None:
                    # Buscar la lista padre en el stack
                    for i in range(len(stack) - 1, -1, -1):
                        if isinstance(stack[i][1], list):
                            list_accumulator = stack[i][1]
                            break
                if list_accumulator is not None:
                    list_accumulator.append(obj)
            elif val.endswith(":"):
                # Nuevo dict dentro de lista
                obj: dict[str, Any] = {}
                if list_accumulator is not None:
                    list_accumulator.append(obj)
                stack.append((indent + 2, obj))
            else:
                if list_accumulator is not None:
                    list_accumulator.append(_coerce(val))
            continue

        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()

            if value == "":
                # Puede ser dict o lista
                next_non_empty = None
                # Miramos la siguiente línea no-vacía para decidir
                if len(stack) > 1 and indent <= stack[-2][0]:
                    # Backtrack
                    stack.pop()
                    if isinstance(stack[-1][1], dict):
                        stack[-1][1][key] = {}
                    elif isinstance(stack[-1][1], list):
                        stack[-1][1].append({key: {}})
                    current_key = key
                else:
                    parent = stack[-1][1]
                    if isinstance(parent, dict):
                        # Verificar si la siguiente línea es un `-`
                        # Por ahora asumimos que es un dict
                        parent[key] = {}
                        stack.append((indent + 2, parent[key]))
                    current_key = key
            elif value == "|":
                in_block_scalar = True
                block_lines = []
                list_accumulator = None
            else:
                parent = stack[-1][1]
                coerced = _coerce(value)
                if isinstance(parent, dict):
                    parent[key] = coerced
                elif isinstance(parent, list) and parent and isinstance(parent[-1], dict):
                    parent[-1][key] = coerced
                current_key = key

    return result


def _coerce(value: str) -> Any:
    """Convierte string a tipo nativo."""
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    if value in ("null", "None"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    # Quitar comillas
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


_FORMAT_MAP = {
    "entero": ",.0f",
    "decimal_1": ",.1f",
    "decimal_2": ",.2f",
    "porcentaje_0": ",.0f",
    "porcentaje_1": ",.1f",
}


def _apply_metrics_and_columns(
    token: str,
    csrf: str,
    ds_id: int,
    dataset_cfg: dict,
    dataset_name: str,
) -> None:
    """Aplica métricas y dimensiones al dataset."""
    # Obtener dataset actual con sus columnas y métricas
    resp = _request("GET", f"/api/v1/dataset/{ds_id}", token=token)
    ds_data = resp.get("result", {})
    current_columns = ds_data.get("columns", [])
    current_metrics = ds_data.get("metrics", [])

    # --- Métricas virtuales ---
    new_metrics: list[dict] = []
    metric_names_existing = {m.get("metric_name") for m in current_metrics}

    for m in dataset_cfg.get("metricas", []):
        mname = m["nombre"]
        if mname in metric_names_existing:
            print(f"    ✔ Métrica '{mname}' ya existe")
            continue

        # Algunas métricas son solo columnas (ej. contexto_socioeconomico), no expresiones
        if "expresion" not in m:
            print(f"    ⚠ Métrica '{mname}' sin expresión (solo columnas), se omite")
            continue

        d3_format = _FORMAT_MAP.get(m.get("formato", ""), "")
        extra = {}
        if d3_format:
            extra["d3Format"] = d3_format

        new_metrics.append({
            "metric_name": mname,
            "verbose_name": m.get("etiqueta", mname),
            "expression": m["expresion"],
            "metric_type": "sql",
            "extra": json.dumps(extra) if extra else None,
            "description": f"{m.get('kpi', '')} — {m.get('nota', '')}".strip(" —"),
        })

    # --- Dimensiones (columnas) ---
    # Las columnas existentes ya están detectadas por Superset.
    # Solo necesitamos marcar las jerarquías como dimensiones.
    # Superset usa 'groupby' y 'filterable' para dimensiones.
    # Las columnas ya existentes se actualizan con is_dttm y groupby.
    new_columns: list[dict] = []
    col_names_existing = {c.get("column_name") for c in current_columns}

    # Banderas de cobertura como dimensiones categóricas
    for bc in dataset_cfg.get("banderas_cobertura", []):
        if bc not in col_names_existing:
            continue  # columna no existe aún en el dataset, Superset la detectará

    # Las columnas de identidad son dimensiones clave
    for col in current_columns:
        col_name = col.get("column_name", "")
        is_grano = col_name in dataset_cfg.get("grano", [])

        # Agregar tipo de dato y si es filtrable
        update = {
            "column_name": col_name,
            "id": col.get("id"),
            "groupby": True,
            "filterable": True,
            "is_dttm": col.get("is_dttm", False),
        }

        # Formateo numérico para métricas que son agregaciones
        for m in dataset_cfg.get("metricas", []):
            if m["nombre"] == col_name:
                fmt = _FORMAT_MAP.get(m.get("formato", ""), "")
                if fmt:
                    update["python_date_format"] = fmt

        new_columns.append(update)

    if not new_metrics and not new_columns:
        print(f"    ✔ Métricas/dimensiones ya alineadas")
        return

    # Aplicar actualización
    body: dict[str, Any] = {}
    if new_metrics:
        body["metrics"] = [
            {
                "metric_name": m["metric_name"],
                "verbose_name": m["verbose_name"],
                "expression": m["expression"],
                "metric_type": m["metric_type"],
                "extra": m["extra"],
                "description": m["description"],
            }
            for m in new_metrics
        ]
        print(f"    ➜ {len(new_metrics)} métrica(s) nueva(s): {', '.join(m['metric_name'] for m in new_metrics)}")

    if new_columns:
        body["columns"] = [
            {
                "column_name": c["column_name"],
                "id": c["id"],
                "groupby": c["groupby"],
                "filterable": c["filterable"],
                "is_dttm": c["is_dttm"],
            }
            for c in new_columns
        ]

    try:
        _request("PUT", f"/api/v1/dataset/{ds_id}", token=token, csrf_token=csrf, body=body)
        print(f"    ✔ Dataset {ds_id} actualizado")
    except Exception as e:
        print(f"    ✗ Error actualizando dataset {ds_id}: {e}")


def sync_metrics(
    token: str, csrf: str, datasets: dict[str, int]
) -> None:
    """Lee metrics_*.yaml y aplica métricas/dimensiones a cada dataset."""
    for yaml_file in sorted(SEMANTIC_DIR.glob("metrics_*.yaml")):
        data = _read_yaml(yaml_file)
        for ds_cfg in data.get("datasets", []):
            ds_name_raw = ds_cfg.get("sql", "").replace(".sql", "")
            ds_name = ds_name_raw

            # Buscar nombre real del dataset (puede ser diferente al sql)
            sql_match = ds_cfg.get("sql", "").replace(".sql", "")
            # Intentar con el nombre del dataset primero
            if ds_cfg.get("nombre") in datasets:
                ds_id = datasets[ds_cfg["nombre"]]
                ds_label = ds_cfg["nombre"]
            elif sql_match in datasets:
                ds_id = datasets[sql_match]
                ds_label = sql_match
            else:
                print(f"  ✗ Dataset '{ds_name}' no encontrado para métricas de {yaml_file.name}")
                continue

            print(f"  Aplicando métricas a '{ds_label}'...")
            _apply_metrics_and_columns(token, csrf, ds_id, ds_cfg, ds_label)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("FARO — Sync de capa semántica a Superset")
    print("=" * 60)

    if not ADMIN_PASS:
        print("✗ SUPERSET_ADMIN_PASSWORD no está definido. Exporta las variables de .env")
        sys.exit(1)
    if not DB_PASS:
        print("✗ POSTGRES_PASSWORD no está definido. Exporta las variables de .env")
        sys.exit(1)

    print(f"\nSuperset: {SUPERSET_URL}")
    print(f"Base de datos: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Directorio semántico: {SEMANTIC_DIR}\n")

    # 1. Login
    token, csrf = login()

    # 2. Conexión a BD
    print("\n▸ Conexión a base de datos...")
    db_id = ensure_database(token, csrf)

    # 3. Datasets virtuales
    print("\n▸ Datasets virtuales...")
    datasets = ensure_datasets(token, csrf, db_id)
    print(f"  Total datasets: {len(datasets)}")

    # 4. Métricas y dimensiones
    print("\n▸ Métricas y dimensiones...")
    sync_metrics(token, csrf, datasets)

    print("\n" + "=" * 60)
    print("✔ Capa semántica sincronizada")
    print("⚠ Nota: la preview de datos requiere que gold.* exista (Célula 1)")
    print("=" * 60)


if __name__ == "__main__":
    main()
