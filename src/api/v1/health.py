"""Salud y versión (endpoints públicos, §3.1 del contrato)."""
from __future__ import annotations

import os

from fastapi import APIRouter

from src.api.schemas import HealthOut, VersionOut

router = APIRouter(tags=["Salud"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Liveness del contrato v1 (público, sin token)."""
    return HealthOut(status="ok")


@router.get("/version", response_model=VersionOut)
def version() -> VersionOut:
    """Versión de la API y commit desplegado (público, sin token)."""
    return VersionOut(api="v1", commit=os.getenv("GIT_COMMIT", "dev"))
