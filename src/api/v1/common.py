"""Utilidades compartidas por los routers de la v1 del contrato.

Incluye la paginación por *offset* del §1 y el esquema de seguridad declarado en el OpenAPI.

**Alcance (US-401):** este stub declara el esquema `bearerAuth` para que el `openapi.json`
sea fiel al contrato, pero **no valida tokens ni roles**. La validación real es US-402 (OAuth2/JWT)
y US-403 (RBAC). Los endpoints marcados con rol mínimo lo documentan vía `descripcion_rol`.
"""
from __future__ import annotations

from typing import TypeVar

from fastapi.security import HTTPBearer

from src.api.schemas import Page

T = TypeVar("T")

# Esquema declarativo para el OpenAPI (no fuerza autenticación en el stub).
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


def paginate(items: list[T], page: int, size: int) -> Page:
    """Aplica paginación por *offset* y devuelve el sobre `Page[T]` del contrato."""
    total = len(items)
    inicio = (page - 1) * size
    fin = inicio + size
    return Page(items=items[inicio:fin], total=total, page=page, size=size)
