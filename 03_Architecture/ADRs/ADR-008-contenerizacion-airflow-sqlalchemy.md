---
id: ADR-008
title: "ADR-008 — Contenerización propia de Airflow con SQLAlchemy fijado en 1.4.x"
owner: "Edgar Ulises Jiménez López"
status: accepted
traces_up: ["US-522b"]
supersedes: []
tags: [architecture, adr, devops, airflow]
date: "2026-08-25"
---

# ADR-008 — Contenerización propia de Airflow con SQLAlchemy fijado en 1.4.x

## Contexto
El contenedor `airflow-webserver` entraba en crash loop al iniciar. El diagnóstico mostró una incompatibilidad entre Airflow 2.7.3 y SQLAlchemy 2.0: Airflow en esta versión depende de comportamientos de SQLAlchemy 1.4.x que fueron removidos o cambiados en la 2.0. El `requirements.txt` del proyecto fija SQLAlchemy en 2.0.x porque otros servicios (API, otras células) sí lo requieren, por lo que no era viable bajar la versión globalmente sin romper otras partes del sistema.

## Decisión
Se construye una imagen Docker propia para Airflow (`docker/airflow.Dockerfile`), separada de la imagen base oficial `apache/airflow:2.7.0`, que instala/fija SQLAlchemy en un rango 1.4.x compatible únicamente dentro del entorno de Airflow, sin modificar el `requirements.txt` compartido del resto del proyecto. Además, se configura `AIRFLOW__DATABASE__SQL_ALCHEMY_ENGINE_ARGS` en `docker-compose.yml` para habilitar batching de `executemany` y mejorar el rendimiento de escritura a la base de datos de metadatos.

## Alternativas consideradas
| Opción | Pros | Contras |
|---|---|---|
| Bajar SQLAlchemy a 1.4.x en el `requirements.txt` global | Cambio simple, un solo archivo | Rompe compatibilidad con otros servicios (API) que requieren 2.0.x |
| Actualizar Airflow a una versión más reciente compatible con SQLAlchemy 2.0 | Resuelve el conflicto de raíz | Mayor esfuerzo de migración, riesgo de romper DAGs existentes, fuera de alcance de esta historia |
| Imagen Docker propia para Airflow con dependencias aisladas (elegida) | Aísla el conflicto de versiones sin afectar otros servicios; cambio contenido y reversible | Mantenimiento de un Dockerfile adicional |

## Consecuencias
- **Positivas:** Airflow queda estable (`healthy`) sin afectar las dependencias de SQLAlchemy 2.0 que usan otros servicios del proyecto. El cambio es aislado, fácil de revertir y no requiere coordinación con otras células.
- **Negativas:** Se introduce un Dockerfile adicional que debe mantenerse sincronizado si Airflow se actualiza en el futuro. Existe deuda técnica: la migración real a SQLAlchemy 2.0 (o a una versión de Airflow compatible) queda pendiente para una historia futura.

## Trazabilidad
- Requisito(s): US-522b
- Impacta: [[03_Architecture/System_Design]]
