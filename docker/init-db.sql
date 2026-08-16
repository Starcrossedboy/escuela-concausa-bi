-- ═══════════════════════════════════════════════════════════════
-- FARO — Script de Inicialización de Bases de Datos
-- ═══════════════════════════════════════════════════════════════
-- Este script se ejecuta AUTOMÁTICAMENTE cuando Postgres arranca
-- por primera vez (solo si el volumen postgres-data está vacío).
--
-- Crea 4 bases de datos:
-- 1. escuela_concausa_db → Datos del proyecto (Bronze, Silver, Gold)
-- 2. airflow             → Metadata de Airflow (DAGs, logs, usuarios)
-- 3. mlflow              → Tracking de experimentos ML
-- 4. superset            → Metadata de dashboards
--
-- Creado: 2026-08-15
-- Owner: Luis Téllez Domínguez (Célula 5)
-- Historia: US-502
-- ═══════════════════════════════════════════════════════════════

-- La base escuela_concausa_db ya existe (creada por POSTGRES_DB en docker-compose)
-- Solo necesitamos crear las 3 adicionales

\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo '🔧 FARO - Inicializando bases de datos'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- ═══════════════════════════════════════════════════════════════
-- BASE DE DATOS 2: airflow
-- ═══════════════════════════════════════════════════════════════
\echo '📦 Creando base de datos: airflow'

-- Crear base si no existe
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

-- Otorgar privilegios al usuario postgres
GRANT ALL PRIVILEGES ON DATABASE airflow TO postgres;

\echo '   ✅ Base de datos "airflow" creada'

-- ═══════════════════════════════════════════════════════════════
-- BASE DE DATOS 3: mlflow
-- ═══════════════════════════════════════════════════════════════
\echo '📦 Creando base de datos: mlflow'

-- Crear base si no existe
SELECT 'CREATE DATABASE mlflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mlflow')\gexec

-- Otorgar privilegios al usuario postgres
GRANT ALL PRIVILEGES ON DATABASE mlflow TO postgres;

\echo '   ✅ Base de datos "mlflow" creada'

-- ═══════════════════════════════════════════════════════════════
-- BASE DE DATOS 4: superset
-- ═══════════════════════════════════════════════════════════════
\echo '📦 Creando base de datos: superset'

-- Crear base si no existe
SELECT 'CREATE DATABASE superset'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset')\gexec

-- Otorgar privilegios al usuario postgres
GRANT ALL PRIVILEGES ON DATABASE superset TO postgres;

\echo '   ✅ Base de datos "superset" creada'

-- ═══════════════════════════════════════════════════════════════
-- EXTENSIONES ÚTILES (en cada base de datos)
-- ═══════════════════════════════════════════════════════════════

-- Extensión pg_trgm: búsquedas de texto rápidas (útil para logs, búsqueda de DAGs)
-- Extensión postgis: operaciones geográficas (útil para datos de municipios)

\echo '🔌 Instalando extensiones en base "escuela_concausa_db"'
\c escuela_concausa_db;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS postgis;
\echo '   ✅ Extensiones instaladas en escuela_concausa_db'

\echo '🔌 Instalando extensiones en base "airflow"'
\c airflow;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\echo '   ✅ Extensiones instaladas en airflow'

\echo '🔌 Instalando extensiones en base "mlflow"'
\c mlflow;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\echo '   ✅ Extensiones instaladas en mlflow'

\echo '🔌 Instalando extensiones en base "superset"'
\c superset;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\echo '   ✅ Extensiones instaladas en superset'

-- ═══════════════════════════════════════════════════════════════
-- RESUMEN FINAL
-- ═══════════════════════════════════════════════════════════════
\c postgres;  -- Volver a la base por defecto

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo '✅ Inicialización completada'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo ''
\echo '📊 Bases de datos creadas:'
\echo '   1. escuela_concausa_db → Datos del proyecto'
\echo '   2. airflow             → Metadata de Airflow'
\echo '   3. mlflow              → Tracking de modelos ML'
\echo '   4. superset            → Metadata de dashboards'
\echo ''
\echo '🔌 Extensiones instaladas en todas las bases:'
\echo '   - pg_trgm  → Búsquedas de texto rápidas'
\echo '   - postgis  → Operaciones geográficas (solo en escuela_concausa_db)'
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
