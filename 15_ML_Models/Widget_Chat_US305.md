---
id: DOC-WIDGET-CHAT-US305
title: "FARO Web — Widget de chat del agente"
owner: "Andrés González Habib"
status: in_review
version: "0.1"
traces_up: ["US-305", "REQ-006", "03_Architecture/API_Specification"]
traces_down: ["src/frontend/agente_client.py", "src/frontend/pages/3_Chat.py", "tests/test_frontend_agente_client.py"]
tags: [frontend, agente, chat, streamlit, celula-3]
---

# FARO Web — Widget de chat del agente

> → [[15_ML_Models/_index]] · [[15_ML_Models/Agente_Guardrails_US304a]]

## Estado

El widget Streamlit de US-305 ya permite enviar preguntas al contrato canónico
`POST /api/v1/agente/consulta`, conserva el historial durante la sesión y muestra la consulta SQL
generada dentro de un panel auditable. Las respuestas fuera de alcance se presentan como advertencia.

El cliente vive separado de la vista en `src/frontend/agente_client.py`. Valida preguntas de 3 a
500 caracteres, aplica un timeout de 15 segundos, convierte fallos HTTP en un error de conexión
controlado y verifica tipos y campos mínimos de `AgenteRespuestaOut`. Su transporte es inyectable
para probarlo sin levantar la API.

## Configuración

La variable local `FARO_API_BASE_URL` define la URL de la API. Si no existe, el widget usa
`http://localhost:8000`. No contiene ni persiste credenciales.

## Validación

- `tests/test_frontend_agente_client.py`: URL, payload, timeout, respuesta, límites de entrada y
	rechazo de contratos incompletos mediante transporte falso.
- Página cargada mediante `streamlit.testing.v1.AppTest` sin excepciones.
- Ruff limpio en el cliente y la página.

## Pendientes para cerrar US-305

- Conectar la respuesta del RAG real cuando Carlos entregue US-304b.
- Propagar el JWT del flujo de autenticación de Célula 4 en la llamada HTTP.
- Ejecutar la prueba end-to-end contra la API integrada, no solo contra el contrato actual.