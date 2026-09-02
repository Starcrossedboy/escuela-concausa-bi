---
id: DOC-WIDGET-CHAT-US305
title: "FARO Web — Widget de chat del agente"
owner: "Andrés González Habib"
status: in_review
version: "0.4"
traces_up: ["US-305", "REQ-006", "vault/03_Architecture/API_Specification"]
traces_down: ["src/frontend/agente_client.py", "src/frontend/pages/3_Chat.py", "tests/test_frontend_agente_client.py", "tests/test_frontend_chat_streamlit.py"]
tags: [frontend, agente, chat, streamlit, celula-3]
---

# FARO Web — Widget de chat del agente

> → [[vault/15_ML_Models/_index]] · [[vault/15_ML_Models/Agente_Guardrails_US304a]]

## Estado

El widget Streamlit de US-305 ya permite enviar preguntas al contrato canónico
`POST /api/v1/agente/consulta`, conserva el historial durante la sesión y muestra la consulta SQL
generada dentro de un panel auditable. Las respuestas fuera de alcance se presentan como advertencia.

El cliente vive separado de la vista en `src/frontend/agente_client.py`. Valida preguntas de 3 a
500 caracteres, aplica un timeout de 15 segundos, convierte fallos HTTP en un error de conexión
controlado y verifica tipos y campos mínimos de `AgenteRespuestaOut`. Su transporte es inyectable
para probarlo sin levantar la API. También acepta el `access_token` de la sesión y, cuando está
disponible, lo propaga como `Authorization: Bearer <token>`; las llamadas sin token conservan el
comportamiento actual mientras se completa el flujo de autenticación del frontend.
También distingue una sesión ausente o expirada (`401`), un rol insuficiente (`403`) y una caída de
conectividad, para que el E2E protegido no oculte errores de autorización como fallos de red.

## Configuración

La variable local `FARO_API_BASE_URL` define la URL de la API. Si no existe, el widget usa
`http://localhost:8000`. No contiene ni persiste credenciales.

## Validación

- `tests/test_frontend_agente_client.py`: URL, payload, timeout, respuesta, límites de entrada,
	rechazo de contratos incompletos y presencia/ausencia del encabezado Bearer mediante transporte
	falso, además de respuestas diferenciadas para `401` y `403`.
- `tests/test_frontend_chat_streamlit.py`: dos turnos completos contra un servidor HTTP efímero;
	verifica historial, SQL auditable y advertencia para preguntas fuera de alcance. Si Streamlit no
	está instalado, pytest omite únicamente este caso.
- Ruff limpio en el cliente y la página.

## Pendientes para cerrar US-305

- Conectar la respuesta del RAG real cuando Carlos entregue US-304b.
- Conectar el `access_token` real al estado de sesión cuando Célula 4/US-405 complete el login; el
	cliente y la vista ya están preparados para propagarlo.
- Ejecutar la prueba end-to-end contra la API integrada, no solo contra el contrato actual.
