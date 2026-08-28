---
title: "Instrumentación de Logs y Monitoreo (US-524a)"
author: Alejandro Velázquez Mendoza
date: 2026-08-27
traces_up: [US-524a, REQ-005]
---

# 1. Objetivo
Implementar la captura de logs estructurados (JSON) y las métricas para GCP sobre la API de FARO, manteniéndolo completamente aislado de la capa de desarrollo (Célula 4).

# 2. Análisis del Problema
FastAPI no formatea logs estructurados por defecto, y tocar su código (`app.py`) invadiría las responsabilidades de Célula 4. 

# 3. Decisiones Técnicas
- Configuración de Uvicorn inyectada desde el Dockerfile: Se creó el archivo `docker/log_config.json` para definir la salida estándar en formato JSON (compatible con GCP).
- Esto nos permite capturar latencia y estado de los endpoints sin programar middlewares de Python.
- El Dockerfile copia el archivo localmente y cambia el `CMD` respetando el puerto dinámico.

# 4. Evidencia
Se actualizaron los siguientes artefactos:
- `docker/api.Dockerfile` modificado.
- `docker/log_config.json` creado.
- `11_Operations/Alertas_Monitoreo_US524a.md` con las políticas definidas.

# 5. Nota sobre BUG-008
Se identificó el problema del CMD en el Dockerfile. El bug fue asignado y resuelto oficialmente por Luis Téllez en el PR #99.
