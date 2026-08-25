# ═══════════════════════════════════════════════════════════════════════
# FARO — Dockerfile de Airflow
# ═══════════════════════════════════════════════════════════════════════
# Imagen de Airflow con dependencias del proyecto (dbt, ML) pre-instaladas
#
# Creado: 2026-08-19
# Owner: Edgar Ulises Jiménez López (Célula 5)
# Historia: US-522b
# ═══════════════════════════════════════════════════════════════════════

FROM apache/airflow:2.7.3-python3.11

LABEL maintainer="Edgar Ulises Jiménez López <jimenez.lopez.e87@gmail.com>"
LABEL description="Airflow + dependencias FARO (DAGs e integración con jobs de ML)"
LABEL version="2.7.0"

USER airflow

WORKDIR /opt/airflow

COPY requirements.txt /opt/airflow/requirements.txt
RUN grep -v "^sqlalchemy" /opt/airflow/requirements.txt > /opt/airflow/requirements-airflow.txt && echo "sqlalchemy>=1.4,<2.0" >> /opt/airflow/requirements-airflow.txt && pip install --no-cache-dir --user -r /opt/airflow/requirements-airflow.txt



COPY --chown=airflow:root src/ /opt/airflow/src/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=30s \
    CMD curl -f http://localhost:8080/health || exit 1
