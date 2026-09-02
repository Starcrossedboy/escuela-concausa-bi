# Contrato de la API FARO — publicación y mock (US-401)

Este directorio publica el **artefacto estable del contrato**: [`openapi.v1.json`](openapi.v1.json).
Es el OpenAPI que consumen los **mocks** de las Células 2 (BI) y 3 (ML/Agente) para trabajar
**desacopladas** de la implementación real (§6 de
[`vault/03_Architecture/API_Specification.md`](../vault/03_Architecture/API_Specification.md), que es la fuente de verdad del contrato).

> **Regla de oro:** cambiar una ruta o un modelo = editar el contrato, **regenerar** este JSON y
> avisar a C2 y C3. Nunca romper el contrato en silencio.

## Qué hay aquí

- `openapi.v1.json` — OpenAPI 3.x generado desde la app de referencia (`src/api/app.py`).

## Cómo se genera / regenera

La implementación de referencia (stub) vive en `src/api/` y sirve respuestas de ejemplo desde
`src/api/mock_data.py` (100 % sintéticas). Para regenerar el JSON tras cualquier cambio del contrato:

```bash
python scripts/export_openapi.py
```

Es **idempotente**: mismo código → mismo archivo. La prueba
`tests/test_api_contract.py::test_openapi_publicado_existe_y_sincronizado` falla si el JSON quedó
desincronizado, así que CI detecta un contrato sin regenerar.

## Cómo levantar el mock

**Opción A — servir el stub de referencia (FastAPI):**

```bash
uvicorn src.api.app:app --reload --port 8000
# Docs interactivas: http://localhost:8000/api/v1/docs
# OpenAPI vivo:      http://localhost:8000/api/v1/openapi.json
```

**Opción B — mock puro desde el OpenAPI (sin código), p. ej. Stoplight Prism:**

```bash
prism mock api/openapi.v1.json
```

Ambas devuelven payloads que **cumplen los modelos Pydantic** del contrato. Cuando exista la API real,
C2 y C3 solo cambian la URL base.

## Alcance de este stub

- **Sí** cubre: catálogo completo de endpoints (`/health`, `/auth/*`, `/escuelas`, `/municipios`,
  `/kpis`, `/predicciones/*`, `/agente/consulta`, `/admin/*`), formas de request/response, paginación,
  códigos 200/302/404/422 y el formato de error uniforme `ErrorOut` (§5).
- **No** cubre (por diseño, son otras historias): validación real de OAuth2/JWT (**US-402**),
  enforcement de RBAC por rol (**US-403**) y hardening —rate limiting, CORS— (**US-404**). El esquema
  `bearerAuth` se declara en el OpenAPI para fidelidad del contrato, pero el stub no valida tokens.

## Coexistencia con el deploy (Célula 5)

El entrypoint de despliegue es `src/api/main.py` (US-501, Cloud/DevOps): un "hola mundo" con
`/health`. Esta app del contrato (`src/api/app.py`) es **independiente** y no lo modifica. La
unificación (montar `/api/v1` dentro del servicio desplegado) se hará al implementar OAuth2/JWT en
US-402, **coordinada con la Célula 5**.
