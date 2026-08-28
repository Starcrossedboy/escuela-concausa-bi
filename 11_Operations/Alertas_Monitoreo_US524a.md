---
title: Alertas y Monitoreo de API y Postgres
owner: Alejandro VelÃ¡zquez Mendoza
traces_up: [US-524a, REQ-005]
status: in_progress
---

# PolÃ­tica de Monitoreo y Alertas (US-524a)

Este documento define la polÃ­tica operativa para la observabilidad del proyecto FARO sobre Google Cloud Platform (Cloud Run).

## 1. Monitoreo Activo (Uptime Checks)
Se configurarÃ¡ un Uptime Check en GCP apuntando a la ruta `/api/v1/health` para validar que tanto la API como la conexiÃ³n a Postgres estÃ¡n saludables.
- **Frecuencia:** Cada 1 minuto.
- **Regiones:** Iowa, Oregon, South Carolina (Estados Unidos).
- **Criterio de falla:** Respuesta HTTP > 400 o timeout de 10 segundos.

## 2. Logs Estructurados (Log-based Metrics)
La aplicaciÃ³n (a travÃ©s de Uvicorn) emite logs JSON con el campo `severity`.
Se crearÃ¡ una mÃ©trica basada en logs en GCP para rastrear las siguientes severidades:
- `ERROR`
- `CRITICAL`
- `EMERGENCY`

## 3. Canales de NotificaciÃ³n
Cuando la mÃ©trica de Errores exceda un umbral de **5 en 10 minutos**, o cuando el Uptime Check falle, se activarÃ¡n las notificaciones en:
1. **Canal de Slack:** `#faro-ops-alertas`
2. **Correos electrÃ³nicos:** CÃ©lula 5 (Infraestructura) y PO (Edgar Coronel).
