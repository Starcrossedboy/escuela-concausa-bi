---
id: DOC-DEV-API-LOCAL
title: "Guía de Ambiente Local: API + Postgres"
owner: "Alejandro Velázquez Mendoza"
status: draft
source_of_truth: false
last_reviewed: "2026-08-12"
tags: [devops, backend, docker, local-env]
---

# Guía de Ambiente Local: API + Postgres

> → [[vault/00_Start_Here/PROJECT_INDEX|Índice del Proyecto]]

Esta guía está diseñada para la **Célula 4 (Backend)**. Sigue estos pasos para levantar tu entorno de desarrollo local con un solo comando. No necesitas instalar PostgreSQL ni Python en tu máquina anfitriona; todo corre dentro de contenedores Docker.

## 1. Requisitos Previos

- **Docker Desktop** (o Docker Engine + Docker Compose) instalado y ejecutándose.
- Haber clonado el repositorio `escuela-concausa-bi`.

## 2. Iniciar el Ambiente Local

Abre tu terminal, navega a la raíz del repositorio (`escuela-concausa-bi`) y ejecuta:

```bash
docker-compose up -d
```

Este comando descargará las imágenes (si no las tienes) y levantará en segundo plano (`-d`) dos servicios:
1. `db`: Base de datos PostgreSQL.
2. `api`: Servidor web FastAPI.

Para ver los logs en tiempo real (útil para debugear):
```bash
docker-compose logs -f
```

## 3. Conexión a la Base de Datos (Para DBeaver/pgAdmin)

La base de datos está expuesta en tu puerto local `5432`.

- **Host**: `localhost` o `127.0.0.1`
- **Puerto**: `5432`
- **Base de datos**: `escuela_concausa_db`
- **Usuario**: `postgres`
- **Contraseña**: `postgres_password_local`

> [!WARNING]
> Estas credenciales son **exclusivamente para desarrollo local**. Nunca las uses en producción ni ambientes de nube.

## 4. Acceso a la API

Una vez que los contenedores estén corriendo, la API estará disponible en el puerto `8000`.

- **Healthcheck**: [http://localhost:8000/health](http://localhost:8000/health)
- **Documentación Interactiva (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

Desde Swagger puedes enviar peticiones de prueba a los endpoints que vayas desarrollando.

## 5. Detener el Ambiente

Cuando termines tu jornada, puedes apagar los contenedores y liberar memoria con:

```bash
docker-compose down
```

> **Nota:** Tus datos no se perderán. El volumen `postgres_data` guarda persistencia de tu base de datos local incluso si borras el contenedor. Para borrar la base de datos por completo (reset), usa `docker-compose down -v`.
