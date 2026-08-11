"""
FARO API - FastAPI Application
Endpoint inicial para Sprint 1: Hello World + Health Check
"""

from fastapi import FastAPI, status
from datetime import datetime
import os
import sys
import logging
import time

# Configurar logging estructurado para Cloud Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","severity":"%(levelname)s","message":"%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Tiempo de inicio para calcular uptime
START_TIME = time.time()

# Crear aplicación FastAPI
app = FastAPI(
    title="FARO API",
    description="Escuela como Sensor Social - Plataforma de BI para educación en México",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("FARO API starting up", extra={
        "event": "startup",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "local")
    })


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de apagado de la aplicación"""
    logger.info("FARO API shutting down", extra={
        "event": "shutdown"
    })


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz - Hello World from FARO

    Returns:
        dict: Mensaje de bienvenida con información del proyecto
    """
    logger.info("Root endpoint accessed")

    return {
        "message": "Hello World from FARO",
        "project": "Escuela como Sensor Social",
        "description": "Plataforma de BI end-to-end para predicción de matrícula escolar",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "local"),
        "version": "0.1.0",
        "sprint": "S1",
        "status": "operational"
    }


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health():
    """
    Health check endpoint

    Returns:
        dict: Estado de salud del servicio con métricas básicas
    """
    uptime_seconds = time.time() - START_TIME

    return {
        "status": "healthy",
        "service": "faro-api",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "environment": os.getenv("ENVIRONMENT", "local")
    }


@app.get("/info", tags=["Info"])
async def info():
    """
    Información del proyecto FARO

    Returns:
        dict: Detalles del proyecto y arquitectura
    """
    return {
        "project": "FARO - Escuela como Sensor Social",
        "university": "Universidad Anáhuac",
        "program": "Maestría MTIIA",
        "professor": "Dr. José Gustavo Fuentes",
        "team_size": 21,
        "cells": 5,
        "sprints": 6,
        "demo_date": "2026-09-09",
        "architecture": {
            "data_sources": 8,
            "drivers": 6,
            "ml_models": 3,
            "dashboards": 10,
            "layers": ["Bronze", "Silver", "Gold"]
        },
        "scope": {
            "entities": ["CDMX", "Edomex", "Nuevo León", "Jalisco"],
            "entity_codes": ["09", "15", "19", "14"]
        },
        "tech_stack": [
            "FastAPI",
            "PostgreSQL",
            "Apache Airflow",
            "dbt",
            "Apache Superset",
            "MLflow",
            "Docker",
            "GCP Cloud Run"
        ]
    }
