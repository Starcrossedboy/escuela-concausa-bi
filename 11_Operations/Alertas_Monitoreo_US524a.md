---
title: Alertas y Monitoreo de API y Postgres
owner: Alejandro Velázquez Mendoza
traces_up: [US-524a, REQ-005]
status: in_progress
---

# Política de Monitoreo y Alertas (US-524a)

Este documento define la política operativa para la observabilidad del proyecto FARO sobre Google Cloud Platform (Cloud Run).

## 1. Monitoreo Activo (Uptime Checks)

Se configurará un Uptime Check en GCP apuntando a la ruta /api/v1/health para validar que tanto la API como la conexión a Postgres están saludables.

- **Frecuencia:** Cada 1 minuto.
- **Regiones:** Iowa, Oregon, South Carolina (Estados Unidos).
- **Criterio de falla:** Respuesta HTTP > 400 o timeout de 10 segundos.

## 2. Logs Estructurados (Log-based Metrics)

La aplicación (a través de Uvicorn) emite logs JSON con el campo severity.
Se creará una métrica basada en logs en GCP para rastrear las siguientes severidades:

- ERROR
- CRITICAL
- EMERGENCY

## 3. Canales de Notificación

Cuando la métrica de Errores exceda un umbral de **5 en 10 minutos**, o cuando el Uptime Check falle, se activarán las notificaciones en:

1. **Canal de Slack:** #faro-ops-alertas
2. **Correos electrónicos:** Célula 5 (Infraestructura) y PO (Edgar Coronel).
