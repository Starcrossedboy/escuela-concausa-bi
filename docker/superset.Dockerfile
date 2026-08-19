# Usamos la imagen oficial que pidió el equipo
FROM apache/superset:latest

# Cambiamos a usuario root temporalmente para poder instalar paquetes
USER root

# Instalamos el conector de Postgres
RUN pip install psycopg2-binary

# Regresamos al usuario seguro de superset
USER superset