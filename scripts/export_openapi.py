"""Exporta el OpenAPI del contrato v1 a `api/openapi.v1.json` (US-401).

Este JSON es el **artefacto estable** que consumen los mocks de las Células 2 y 3 (§6 del
contrato). Regenéralo cada vez que cambie una ruta o un modelo:

    python scripts/export_openapi.py

Es idempotente: mismo código → mismo archivo. Corre en CI para detectar contrato desincronizado.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.api.app import app  # noqa: E402

SALIDA = RAIZ / "api" / "openapi.v1.json"


def exportar() -> Path:
    """Genera el OpenAPI y lo escribe con formato estable (claves ordenadas, UTF-8)."""
    esquema = app.openapi()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps(esquema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return SALIDA


if __name__ == "__main__":
    ruta = exportar()
    print(f"OpenAPI escrito en: {ruta.relative_to(RAIZ)}")
