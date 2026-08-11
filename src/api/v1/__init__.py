"""Router agregado de la v1 del contrato FARO.

Reúne todos los subrouters de §3 bajo un único `api_v1_router` que la app monta en `/api/v1`.
"""
from __future__ import annotations

from fastapi import APIRouter

from src.api.v1 import admin, agente, auth, gold, health, predicciones

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(gold.router)
api_v1_router.include_router(predicciones.router)
api_v1_router.include_router(agente.router)
api_v1_router.include_router(admin.router)

__all__ = ["api_v1_router"]
