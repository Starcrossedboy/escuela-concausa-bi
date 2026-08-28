-- =============================================================================
-- MOCK LOCAL · esquema estrella de Gold (fact + dimensiones)
-- -----------------------------------------------------------------------------
-- Historia : US-212 (Marina Garcia del Buey, Celula 2 - Analytics & BI)
-- Proposito: desbloquear la construccion de DB-03 y DB-04 mientras la Celula 1
--            entrega US-112/US-113. Superset ejecuta el SQL de cada dataset
--            virtual para leer metadatos de columnas: si las tablas no existen,
--            la creacion del dataset falla con HTTP 500.
--            Regla de desbloqueo del plan de sprint C2: "si un input no llega,
--            trabaja contra mock o fixtures, avisalo en standup y registra el
--            bloqueo". US-113 vencio el 2026-08-23 sin entregarse.
--
-- ⚠️ ESTO ES UN MOCK:
--   * Solo para DESARROLLO LOCAL. Nunca en staging/prod, nunca lo carga CI.
--   * Extiende el patron que ya establecio Manuel en US-203
--     (superset/mock/gold_ml_outputs_mock.sql), que asume esta estrella creada.
--   * Los datos son SINTETICOS: CCT inventados, sin relacion con escuelas
--     reales. No hay dato personal ni descarga de fuente alguna.
--   * Sirve para validar la ESTRUCTURA de los tableros, no para presentar
--     numeros. Todo chart construido aqui queda pendiente de revalidar contra
--     los cubos reales de US-113.
--   * Cuando C1 entregue Gold, este archivo se descarta: DROP SCHEMA gold
--     CASCADE en local y `dbt run`. Nada de esto viaja fuera del repo.
--
-- Esquema conforme a Data_Model.md §4.1, §4.2 y §6.
--
-- Uso:
--   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
--       < superset/mock/gold_estrella_mock.sql
-- Idempotente: CREATE IF NOT EXISTS + ON CONFLICT DO NOTHING (sin DELETE/DROP).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS gold;

-- ---------------------------------------------------------------------------
-- Dimensiones
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_tiempo (
    id_ciclo    TEXT PRIMARY KEY,
    ciclo       TEXT NOT NULL,
    anio_inicio INTEGER NOT NULL,
    anio_fin    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.dim_municipio (
    cve_mun              TEXT PRIMARY KEY,
    cve_ent              TEXT NOT NULL,
    nombre_municipio     TEXT NOT NULL,
    nombre_entidad       TEXT NOT NULL,
    poblacion            INTEGER,
    indice_rezago_social DOUBLE PRECISION,
    grado_rezago         TEXT,
    pobreza_pct          DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS gold.dim_escuela (
    cct           TEXT PRIMARY KEY,
    nombre        TEXT NOT NULL,
    nivel         TEXT NOT NULL,
    sostenimiento TEXT,
    latitud       DOUBLE PRECISION,
    longitud      DOUBLE PRECISION,
    cve_ent       TEXT NOT NULL,
    cve_mun       TEXT NOT NULL,
    -- Infraestructura CEMABE (D3/D4). NULL = SIN_DATO, nunca FALSE por ausencia.
    agua          BOOLEAN,
    drenaje       BOOLEAN,
    electricidad  BOOLEAN,
    sanitarios    BOOLEAN,
    internet      BOOLEAN,
    computadoras  INTEGER
);

CREATE TABLE IF NOT EXISTS gold.dim_driver (
    id_driver        TEXT PRIMARY KEY,
    nombre           TEXT NOT NULL,
    descripcion      TEXT,
    fuente           TEXT,
    cobertura        TEXT,
    nivel_geografico TEXT
);

-- ---------------------------------------------------------------------------
-- Hecho central. Solo hechos observados: las salidas de ML viven en
-- gold.predicciones / gold.recomendaciones (Data_Model §4.1, regla R1).
-- d1..d6 son NULL cuando su bandera dice SIN_DATO: la bandera es la fuente
-- de verdad, nunca el nulo (regla R2).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_escuela_ciclo (
    cct                        TEXT NOT NULL,
    id_ciclo                   TEXT NOT NULL,
    cve_mun                    TEXT NOT NULL,
    matricula_total            INTEGER NOT NULL,
    variacion_matricula        DOUBLE PRECISION NOT NULL,
    indice_completitud_drivers DOUBLE PRECISION NOT NULL,
    d1 DOUBLE PRECISION, d1_cobertura TEXT NOT NULL DEFAULT 'OK',
    d2 DOUBLE PRECISION, d2_cobertura TEXT NOT NULL DEFAULT 'OK',
    d3 DOUBLE PRECISION, d3_cobertura TEXT NOT NULL DEFAULT 'OK',
    d4 DOUBLE PRECISION, d4_cobertura TEXT NOT NULL DEFAULT 'OK',
    d5 DOUBLE PRECISION, d5_cobertura TEXT NOT NULL DEFAULT 'OK',
    d6 DOUBLE PRECISION, d6_cobertura TEXT NOT NULL DEFAULT 'OK',
    PRIMARY KEY (cct, id_ciclo)
);

-- ---------------------------------------------------------------------------
-- Datos sinteticos
--
-- Cobertura DELIBERADAMENTE parcial, para poder verificar en el tablero que un
-- hueco se dibuja como hueco y no como cero (AC-002.6, regla R2):
--   * D5 (agua, CONAGUA) sin dato en el municipio 09003 — cobertura regional.
--   * D6 (aire, SINAICA) sin dato en 09003 y en 15057 — solo ~80 zonas urbanas.
--   * 09DES0004D sin dato de D3 — CEMABE incompleto para ese plantel.
--   * Infraestructura CEMABE con NULL en varios planteles: el chip debe leer
--     "sin dato", nunca "no".
-- Ademas 09003 es el menor cve_mun, asi que gold_ml_outputs_mock.sql lo excluye
-- COMPLETO de predicciones: ejercita cobertura_prediccion = 'SIN_DATO'.
-- ---------------------------------------------------------------------------

INSERT INTO gold.dim_tiempo (id_ciclo, ciclo, anio_inicio, anio_fin) VALUES
    ('2023-2024', '2023-2024', 2023, 2024),
    ('2024-2025', '2024-2025', 2024, 2025)
ON CONFLICT (id_ciclo) DO NOTHING;

INSERT INTO gold.dim_municipio
    (cve_mun, cve_ent, nombre_municipio, nombre_entidad, poblacion,
     indice_rezago_social, grado_rezago, pobreza_pct) VALUES
    ('09003', '09', 'Coyoacan',      'Ciudad de Mexico', 614447, -1.21, 'Muy bajo', 22.4),
    ('09014', '09', 'Benito Juarez', 'Ciudad de Mexico', 434153, -1.65, 'Muy bajo',  8.4),
    ('15057', '15', 'Naucalpan',     'Mexico',           834434, -0.78, 'Bajo',     33.1)
ON CONFLICT (cve_mun) DO NOTHING;

INSERT INTO gold.dim_escuela
    (cct, nombre, nivel, sostenimiento, latitud, longitud, cve_ent, cve_mun,
     agua, drenaje, electricidad, sanitarios, internet, computadoras) VALUES
    ('09DPR0001A', 'Primaria Sor Juana Ines de la Cruz', 'PRIMARIA',    'PUBLICO', 19.3467, -99.1617, '09', '09003', TRUE,  TRUE,  TRUE, TRUE,  TRUE,   24),
    ('09DES0002B', 'Secundaria Tecnica 12',              'SECUNDARIA',  'PUBLICO', 19.3402, -99.1523, '09', '09003', TRUE,  TRUE,  TRUE, FALSE, FALSE,   0),
    ('09DPR0003C', 'Colegio Vista Hermosa',              'PRIMARIA',    'PRIVADO', 19.3729, -99.1585, '09', '09014', TRUE,  TRUE,  TRUE, TRUE,  TRUE,   40),
    ('09DES0004D', 'Secundaria Diurna 108',              'SECUNDARIA',  'PUBLICO', 19.3812, -99.1701, '09', '09014', NULL,  NULL,  TRUE, TRUE,  NULL, NULL),
    ('15DPR0005E', 'Primaria Benito Juarez',             'PRIMARIA',    'PUBLICO', 19.4785, -99.2396, '15', '15057', TRUE,  FALSE, TRUE, TRUE,  FALSE,   6),
    ('15DES0006F', 'Instituto Naucalli',                 'SECUNDARIA',  'PRIVADO', 19.4901, -99.2312, '15', '15057', TRUE,  TRUE,  TRUE, TRUE,  TRUE,   35)
ON CONFLICT (cct) DO NOTHING;

INSERT INTO gold.dim_driver (id_driver, nombre, fuente, cobertura, nivel_geografico) VALUES
    ('D1', 'Pobreza y rezago social',          'CONEVAL + CONAPO', 'Nacional', 'municipio'),
    ('D2', 'Inseguridad del entorno',          'SESNSP',           'Nacional', 'municipio'),
    ('D3', 'Infraestructura escolar',          'CEMABE',           'Nacional', 'escuela'),
    ('D4', 'Conectividad digital',             'CEMABE',           'Nacional', 'escuela'),
    ('D5', 'Estres hidrico',                   'CONAGUA SINA',     'Regional', 'region'),
    ('D6', 'Calidad del aire',                 'SINAICA',          'Parcial',  'zona urbana')
ON CONFLICT (id_driver) DO NOTHING;

INSERT INTO gold.fact_escuela_ciclo
    (cct, id_ciclo, cve_mun, matricula_total, variacion_matricula, indice_completitud_drivers,
     d1, d1_cobertura, d2, d2_cobertura, d3, d3_cobertura,
     d4, d4_cobertura, d5, d5_cobertura, d6, d6_cobertura) VALUES
    -- 09003 Coyoacan · D5 sin dato
    ('09DPR0001A', '2023-2024', '09003', 412, -0.021, 0.833, 0.31,'OK', 0.44,'OK', 0.22,'OK', 0.18,'OK', NULL,'SIN_DATO', 0.61,'OK'),
    ('09DPR0001A', '2024-2025', '09003', 388, -0.058, 0.833, 0.33,'OK', 0.47,'OK', 0.24,'OK', 0.19,'OK', NULL,'SIN_DATO', 0.64,'OK'),
    -- 09003 · D5 y D6 sin dato -> completitud 4/6
    ('09DES0002B', '2023-2024', '09003', 640, -0.012, 0.667, 0.29,'OK', 0.52,'OK', 0.58,'OK', 0.71,'OK', NULL,'SIN_DATO', NULL,'SIN_DATO'),
    ('09DES0002B', '2024-2025', '09003', 598, -0.066, 0.667, 0.30,'OK', 0.55,'OK', 0.60,'OK', 0.74,'OK', NULL,'SIN_DATO', NULL,'SIN_DATO'),
    -- 09014 Benito Juarez · cobertura completa
    ('09DPR0003C', '2023-2024', '09014', 305,  0.014, 1.000, 0.08,'OK', 0.19,'OK', 0.06,'OK', 0.04,'OK', 0.12,'OK', 0.55,'OK'),
    ('09DPR0003C', '2024-2025', '09014', 311,  0.020, 1.000, 0.07,'OK', 0.21,'OK', 0.05,'OK', 0.04,'OK', 0.14,'OK', 0.57,'OK'),
    -- 09014 · D3 sin dato (CEMABE incompleto)
    ('09DES0004D', '2023-2024', '09014', 521, -0.004, 0.833, 0.11,'OK', 0.24,'OK', NULL,'SIN_DATO', 0.33,'OK', 0.15,'OK', 0.56,'OK'),
    ('09DES0004D', '2024-2025', '09014', 517, -0.008, 0.833, 0.12,'OK', 0.26,'OK', NULL,'SIN_DATO', 0.35,'OK', 0.16,'OK', 0.58,'OK'),
    -- 15057 Naucalpan · D6 sin dato
    ('15DPR0005E', '2023-2024', '15057', 733, -0.035, 0.833, 0.58,'OK', 0.67,'OK', 0.74,'OK', 0.81,'OK', 0.49,'OK', NULL,'SIN_DATO'),
    ('15DPR0005E', '2024-2025', '15057', 671, -0.085, 0.833, 0.61,'OK', 0.71,'OK', 0.77,'OK', 0.83,'OK', 0.52,'OK', NULL,'SIN_DATO'),
    ('15DES0006F', '2023-2024', '15057', 284,  0.007, 0.833, 0.22,'OK', 0.63,'OK', 0.14,'OK', 0.11,'OK', 0.47,'OK', NULL,'SIN_DATO'),
    ('15DES0006F', '2024-2025', '15057', 279, -0.018, 0.833, 0.23,'OK', 0.66,'OK', 0.15,'OK', 0.12,'OK', 0.50,'OK', NULL,'SIN_DATO')
ON CONFLICT (cct, id_ciclo) DO NOTHING;

-- ---------------------------------------------------------------------------
-- gold.geo_municipio · NO la consumen DB-03 ni DB-04.
--
-- Se incluye porque sync_semantic_layer.py procesa TODOS los .sql de
-- superset/semantic/ en un solo lote y aborta en el primero que falla:
-- sin esta tabla, db02_coropletico.sql (US-203, Manuel) revienta con HTTP 500
-- y el script nunca llega a los datasets de DB-03/DB-04.
--
-- Geometrias sinteticas: un cuadrado alrededor del centroide de cada municipio.
-- El GeoJSON real vive en superset/assets/geojson/municipios_scope.geojson y lo
-- carga superset/cargar_geojson_municipios.py (Manuel).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.geo_municipio (
    cve_mun          TEXT PRIMARY KEY,
    nombre_municipio TEXT NOT NULL,
    geometria        TEXT
);

INSERT INTO gold.geo_municipio (cve_mun, nombre_municipio, geometria) VALUES
    ('09003', 'Coyoacan',      '[[[-99.19,19.31],[-99.13,19.31],[-99.13,19.37],[-99.19,19.37],[-99.19,19.31]]]'),
    ('09014', 'Benito Juarez', '[[[-99.19,19.35],[-99.14,19.35],[-99.14,19.40],[-99.19,19.40],[-99.19,19.35]]]'),
    ('15057', 'Naucalpan',     '[[[-99.28,19.44],[-99.20,19.44],[-99.20,19.52],[-99.28,19.52],[-99.28,19.44]]]')
ON CONFLICT (cve_mun) DO NOTHING;
