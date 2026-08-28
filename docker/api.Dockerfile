# FARO API - Dockerfile
# Imagen optimizada para FastAPI en Cloud Run

FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/

# Configuracion de logs (US-524a)
COPY docker/log_config.json ./log_config.json

# Puerto de Cloud Run
ENV PORT=8080
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/v1/health').read()" || exit 1

# Comando de inicio
CMD uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT} --log-config log_config.json
