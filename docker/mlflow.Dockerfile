# ═══════════════════════════════════════════════════════════════════════
# FARO — Dockerfile de MLflow
# ═══════════════════════════════════════════════════════════════════════
# Imagen con MLflow 3.15.1 pre-instalado para arranque rápido
#
# Creado: 2026-08-15
# Owner: Luis Téllez Domínguez (Célula 5)
# Historia: US-502
# ═══════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# Metadatos
LABEL maintainer="Luis Téllez <luis.tellez@faro.local>"
LABEL description="MLflow Tracking Server para proyecto FARO"
LABEL version="3.15.1"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gcc \
        g++ \
        python3-dev \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Instalar MLflow y dependencias de Python
RUN pip install --no-cache-dir \
    mlflow==3.15.1 \
    psycopg2-binary

# Crear directorio de trabajo
WORKDIR /mlflow

# Puerto de MLflow
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=30s \
    CMD curl -f http://localhost:5000/health || exit 1

# Script de inicio con warnings
COPY docker/mlflow-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/mlflow-entrypoint.sh

# Comando por defecto
ENTRYPOINT ["/usr/local/bin/mlflow-entrypoint.sh"]
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
