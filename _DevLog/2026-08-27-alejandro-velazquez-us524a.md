---
title: "InstrumentaciÃ³n de Logs y Monitoreo (US-524a)"
author: Alejandro VelÃ¡zquez Mendoza
date: 2026-08-27
traces_up: [US-524a, REQ-005]
---

# 1. Objetivo
Implementar la captura de logs estructurados (JSON) y las mÃ©tricas para GCP sobre la API de FARO, manteniÃ©ndolo completamente aislado de la capa de desarrollo (CÃ©lula 4).

# 2. AnÃ¡lisis del Problema
FastAPI no formatea logs estructurados por defecto, y tocar su cÃ³digo (`app.py`) invadirÃ­a las responsabilidades de CÃ©lula 4. 

# 3. Decisiones TÃ©cnicas
- ConfiguraciÃ³n de Uvicorn inyectada desde el Dockerfile: Se creÃ³ el archivo `docker/log_config.json` para definir la salida estÃ¡ndar en formato JSON (compatible con GCP).
- Esto nos permite capturar latencia y estado de los endpoints sin programar middlewares de Python.
- El Dockerfile copia el archivo localmente y cambia el `CMD` respetando el puerto dinÃ¡mico.

# 4. Evidencia
Se actualizaron los siguientes artefactos:
- `docker/api.Dockerfile` modificado.
- `docker/log_config.json` creado.
- `11_Operations/Alertas_Monitoreo_US524a.md` con las polÃ­ticas definidas.
