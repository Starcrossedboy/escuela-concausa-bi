"""Fábrica de la app del **contrato v1** de FARO (US-401).

Esta app es la **implementación de referencia / stub** del contrato descrito en
`03_Architecture/API_Specification.md`. Su propósito es doble:

1. Generar el `openapi.json` estable que se publica en `api/openapi.v1.json` (§6) y del que las
   Células 2 y 3 levantan sus mocks.
2. Servir respuestas de ejemplo (desde `src/api/mock_data.py`) para desarrollo desacoplado.

**No sustituye** al entrypoint de despliegue `src/api/main.py` (Célula 5, US-501). Ambas conviven:
`main.py` es el "hola mundo" del deploy temprano; esta app es el contrato. La unificación (montar
`/api/v1` dentro de `main.py`) se hará al implementar OAuth2/JWT en US-402 y se coordinará con
Cloud/DevOps.

Errores: todos los `4xx`/`5xx` se devuelven con la forma uniforme `ErrorOut` del §5, sin fugar
trazas, SQL ni rutas internas.
"""
from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.schemas import ErrorOut
from src.api.v1 import api_v1_router

API_PREFIX = "/api/v1"

# Código estable de error por status HTTP (§5). Lo no mapeado cae en internal_error.
_ERROR_POR_STATUS: dict[int, str] = {
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    422: "validation_error",  # literal para portabilidad entre versiones de Starlette
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}

# Mensajes seguros para el cliente (sin detalle interno) por código de error.
_MENSAJE_SEGURO: dict[str, str] = {
    "unauthorized": "No hay credenciales válidas para esta operación.",
    "forbidden": "Tu rol no permite esta operación.",
    "not_found": "El recurso solicitado no existe o está fuera de alcance.",
    "validation_error": "La entrada no cumple el formato esperado.",
    "rate_limited": "Demasiadas peticiones. Intenta más tarde.",
    "internal_error": "Ocurrió un error interno. El equipo fue notificado.",
}


def _nuevo_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:8]}"


def _respuesta_error(status_code: int, error: str, request_id: str) -> JSONResponse:
    cuerpo = ErrorOut(
        error=error,
        message=_MENSAJE_SEGURO.get(error, _MENSAJE_SEGURO["internal_error"]),
        request_id=request_id,
    )
    return JSONResponse(status_code=status_code, content=cuerpo.model_dump())


def create_app() -> FastAPI:
    """Construye la app del contrato v1 con sus routers y manejadores de error uniformes."""
    app = FastAPI(
        title="FARO API — Contrato v1",
        description=(
            "Contrato REST de FARO (Escuela como Sensor Social). Fuente de verdad: "
            "03_Architecture/API_Specification.md. Este servicio publica el OpenAPI que "
            "consumen los mocks de las Células 2 y 3 (US-401)."
        ),
        version="1.0.0",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )

    app.include_router(api_v1_router, prefix=API_PREFIX)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        error = _ERROR_POR_STATUS.get(exc.status_code, "internal_error")
        return _respuesta_error(exc.status_code, error, _nuevo_request_id())

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _respuesta_error(422, "validation_error", _nuevo_request_id())

    @app.exception_handler(Exception)
    async def _unhandled_exc(request: Request, exc: Exception) -> JSONResponse:
        # No se filtra el detalle real: vive solo en los logs internos.
        return _respuesta_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", _nuevo_request_id()
        )

    return app


app = create_app()
