# Usamos la imagen oficial que pidió el equipo
FROM apache/superset:latest

# Cambiamos a usuario root temporalmente para poder instalar paquetes
USER root

# Instalamos el conector de Postgres.
# IMPORTANTE: apache/superset ejecuta Superset desde el venv /app/.venv,
# gestionado con `uv` (el venv no tiene pip y el Python del sistema es otro).
# Con `pip install` a secas el paquete cae en /usr/local y Postgres nunca
# conecta ("No module named 'psycopg2'" al crear cualquier dataset).
RUN uv pip install --python /app/.venv/bin/python --no-cache psycopg2-binary

# Regresamos al usuario seguro de superset
USER superset