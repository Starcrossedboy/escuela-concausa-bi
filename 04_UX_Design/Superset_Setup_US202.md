---
id: DOC-SUPERSET-SETUP
title: "Setup de Superset — conexión, datasets y capa semántica"
owner: "Manuel Alejandro Serranía Reinada"
status: done
source_of_truth: true
traces_up: ["04_UX_Design/Screen_Specs", "04_UX_Design/Cube_Specs_DB03_DB04"]
traces_down: ["US-202", "REQ-002"]
last_reviewed: "2026-08-16"
tags: [superset, setup, semantic-layer, bi]
---

# Setup de Superset — conexión, datasets y capa semántica

> Historia: US-202 · Configurar Superset: conexión, datasets y capa semántica reutilizable.
> Convención canónica: [[superset/README]]

## 1. Requisitos previos

- Docker Desktop corriendo
- Python 3.11 con venv activado (`source .venv/bin/activate`)
- `.env` configurado desde `.env.example` (con secretos generados vía `scripts/generate-keys.py`)

## 2. Levantar servicios

```bash
# Solo Postgres + Superset (no necesita Airflow/MLflow para US-202)
docker compose up -d db superset

# Verificar
docker compose ps                      # ambos healthy
curl http://127.0.0.1:8088/health      # debe responder 200
```

### Dependencia: psycopg2-binary en Superset

La imagen `apache/superset:latest` **no trae** `psycopg2`. Sin él, Superset no puede conectarse a PostgreSQL y la creación de datasets virtuales falla con 422.

```bash
# Instalar psycopg2 en el venv de Superset (se pierde al reiniciar el contenedor)
docker exec -u root faro-superset pip install --target /app/.venv/lib/python3.10/site-packages psycopg2-binary
```

> **Fix permanente (pendiente):** agregar la instalación al `docker/superset-init.sh` o crear un Dockerfile custom.

### Gold mock (tablas mínimas para validación)

Superset ejecuta el SQL de los datasets virtuales para obtener metadatos de columnas. Si las tablas Gold no existen, la creación falla con 500. Los mocks viven en `superset/mock/`; cárgalos vía `psql`:

```bash
docker exec -i faro-postgres psql -U postgres -d escuela_concausa_db < superset/mock/gold_ml_outputs_mock.sql
```

> **Las tablas mock contienen 1 fila dummy cada una.** Serán reemplazadas cuando la Célula 1 entregue `gold.*` (US-112/113). Para los datasets de DB-02 (mapa) y DB-03/DB-04 revisa también el resto de archivos en `superset/mock/`.

Login: `SUPERSET_ADMIN_USERNAME` / `SUPERSET_ADMIN_PASSWORD` (definidos en `.env`).

## 3. Variables de entorno para el script

El script `superset/sync_semantic_layer.py` necesita estas variables exportadas (las lee de `.env`):

```bash
# Superset
SUPERSET_URL=http://127.0.0.1:8088
SUPERSET_ADMIN_USERNAME=faro_superset_admin
SUPERSET_ADMIN_PASSWORD=<tu-password>

# Postgres (para crear la conexión desde Superset)
POSTGRES_HOST=localhost      # desde el host; dentro de compose es 'db'
POSTGRES_PORT=5432
POSTGRES_DB=escuela_concausa_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<tu-password>
```

## 4. Ejecutar sync de capa semántica

```bash
source .venv/bin/activate
python superset/sync_semantic_layer.py
```

### Qué hace el script
1. **Login** a Superset (REST API) y obtiene JWT + CSRF token.
2. **Crea conexión** `faro_escuela_concausa_db` (si no existe) apuntando a Postgres.
3. **Crea datasets virtuales** desde cada `superset/semantic/*.sql`:
   - `db03_cubo_escuela_360` (DB-03 Ficha de escuela)
   - `db04_cubo_comparador_municipio` (DB-04 Comparador de municipios)
4. **Aplica métricas y dimensiones** desde `metrics_db03_db04.yaml`:
   - Métricas virtuales con nombre `snake_case` = KPI canónico (ej. `matricula_total`, `variacion_ponderada_pct`).
   - Formato D3 (entero, porcentaje, decimal) según el tipo declarado en el YAML.
5. **Reporta** qué se creó, qué ya existía, qué falló.

### Idempotente
- Si la conexión ya existe, la reutiliza (no duplica).
- Si el dataset ya existe, lo omite.
- Si la métrica ya existe, la omite.

## 5. Verificación

```bash
# En Superset UI (http://127.0.0.1:8088):
# → Datasets → debe aparecer db03_cubo_escuela_360 y db04_cubo_comparador_municipio
# → SQL Lab → seleccionar 'faro_escuela_concausa_db' → la conexión funciona
# → Métricas → al abrir un dataset, las métricas aparecen configuradas
```

## 6. Limitaciones conocidas

| Limitación | Causa | Mitigación |
|---|---|---|
| Preview de datos falla | `gold.*` no existe (Célula 1 US-112/113 pendiente) | La capa semántica queda lista; la preview funcionará cuando existan las tablas Gold. Registrar en standup como bloqueo. |
| DB-05/DB-08 no configurados | US-211b pendiente | Se agregan cuando el contrato de DB-05/DB-08 esté listo |
| Métricas predicción/recomendación | US-311 en progreso | Se agregan cuando ML-01/ML-02/ML-03 entrenados |

## 7. Mapeo a convención US-202

| Elemento | Convención | Ejemplo |
|---|---|---|
| Dataset SQL | `<tablero>_<cubo>.sql` | `db03_cubo_escuela_360.sql` |
| Métricas YAML | `metrics_<cubos>.yaml` | `metrics_db03_db04.yaml` |
| Nombre métrica | `snake_case` = KPI canónico | `variacion_ponderada_pct` = KPI-02 |
| Conexión BD | `faro_escuela_concausa_db` | Nombre descriptivo del proyecto |
| Directorio | `superset/semantic/` | Compartido para DB-03/04 (US-211a) |

## 8. Referencias

- Convención canónica: [[superset/README]]
- Contrato de cubos: [[04_UX_Design/Cube_Specs_DB03_DB04]]
- Catálogo de KPIs: [[04_UX_Design/Screen_Specs]]
- Script: `superset/sync_semantic_layer.py`
- Datos YAML/SQL: `superset/semantic/` (Marina García, US-211a)
