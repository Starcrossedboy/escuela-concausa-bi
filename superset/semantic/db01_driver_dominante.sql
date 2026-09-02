-- =============================================================================
-- db01_driver_dominante  ·  DB-01 Ejecutivo (KPI-07)
-- -----------------------------------------------------------------------------
-- Historia : US-205  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §4 (KPI-07)
-- Grano    : una fila por driver_dominante x cve_ent x id_ciclo
--
-- REPUNTEO A CUBOS FISICOS (US-205 / US-113): driver_dominante es salida de
--   ML-02; C1 ya la resolvio en gold.cubo_driver (grano DEC-009
--   id_driver x cve_mun x nivel x id_ciclo). Este SQL REAGREGA el cubo a
--   cve_ent x id_ciclo y preserva la categoria 'SIN_DATO' como etiqueta: las
--   escuelas sin recomendacion de ML-02 se agrupan bajo esa categoria, nunca se
--   reparten entre drivers reales (R2: etiquetar el vacio, jamas rellenar una
--   metrica con cero).
--
-- `cve_ent` entra al grano para que el filtro global de entidad (AC-002.2)
--   tambien alcance a este grafico; escuelas sigue siendo agregacion aditiva y
--   reagrega bien al quitar filtros.
--
-- Los dos bloques (base / sin_dato) se apilan con UNION ALL y respetan el
--   mismo esquema de salida (KPI-07 del YAML no cambia).
-- =============================================================================

WITH base AS (
    SELECT
        c.cve_ent,                                 -- llave del filtro global: entidad
        c.nombre_entidad,                          -- valor legible del filtro
        c.id_ciclo,                                -- filtro global: ciclo
        c.ciclo,
        c.anio_inicio,
        c.id_driver,
        c.nombre_driver,
        SUM(c.escuelas_driver)                     AS escuelas
    FROM gold.cubo_driver c
    WHERE c.cobertura_recomendacion = 'OK'
    GROUP BY
        c.cve_ent,
        c.nombre_entidad,
        c.id_ciclo,
        c.ciclo,
        c.anio_inicio,
        c.id_driver,
        c.nombre_driver
)
, sin_dato AS (
    SELECT
        c.cve_ent,
        c.nombre_entidad,
        c.id_ciclo,
        c.ciclo,
        c.anio_inicio,
        'SIN_DATO'                                 AS id_driver,
        'Sin recomendacion'                        AS nombre_driver,
        SUM(c.escuelas_sin_recomendacion)          AS escuelas
    FROM gold.cubo_driver c
    WHERE c.id_driver = 'D1'
    GROUP BY
        c.cve_ent,
        c.nombre_entidad,
        c.id_ciclo,
        c.ciclo,
        c.anio_inicio
)
SELECT * FROM base
UNION ALL
SELECT * FROM sin_dato