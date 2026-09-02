---
id: DOC-US521B-AMBIENTE
title: "Guía de ambiente local reproducible — Airflow y jobs ML (US-521b)"
owner: "Edgar Ulises Jiménez López"
status: in_progress
traces_up: ["vault/12_Roadmap_Sprints/Sprints/5-edgar-ulises-jimenez-lopez"]
tags: [devops, local-env, airflow, mlflow, US-521b]
---

# Guía de ambiente local reproducible

Este documento detalla la configuración local para correr Airflow y los jobs de Machine Learning
(MLflow) de manera aislada y controlada. Implementa la historia **US-521b**.

> Archivos del componente: [[VERIFICACION|guía de verificación]] y `configuracion.env` (plantilla de
> variables) en `guia-ambiente-local/`.

## 1. Mapeo de puertos

Para evitar conflictos en la máquina local, se asignan estos puertos:

- **Airflow Webserver:** puerto `8080`
- **MLflow Tracking Server:** puerto `5000`

## 2. Variables de entorno

Las variables se declaran en `guia-ambiente-local/configuracion.env`:

- `AIRFLOW_PORT`: puerto de acceso a la interfaz de Airflow.
- `MLFLOW_PORT`: puerto de acceso a la interfaz de MLflow.
- `MLFLOW_TRACKING_URI`: dirección local para el registro de experimentos de ML.

> **Nunca** subir credenciales reales ni `.env` con secretos. El archivo `configuracion.env` es solo
> una plantilla de puertos/rutas locales (ver [[vault/_Meta/Vault_Rules]] y `vault/07_Security/Secrets_Policy`).

## 3. Verificación del entorno

Una vez levantados los servicios, se valida ingresando desde el navegador a las URL locales de cada
puerto. El detalle está en [[VERIFICACION|la guía de verificación]].
