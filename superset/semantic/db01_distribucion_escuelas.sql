-- =============================================================================
-- Distribucion de escuelas (KPI-08 / KPI-09)  ·  DB-01 Ejecutivo
-- -----------------------------------------------------------------------------
-- Historia : US-203  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §4
-- Grano    : una fila por nivel x sostenimiento x cve_ent x id_ciclo
--
-- Dataset chico para los donuts de composicion del tablero ejecutivo: escuelas
-- por nivel educativo (KPI-08) y por sostenimiento (KPI-09). Vive separado del
-- cubo municipal porque meter `sostenimiento` al grano cve_mun x nivel lo
-- fragmentaria sin aportar nada a las KPIs territoriales.
-- `cve_ent` entra al grano para que el filtro global de entidad (AC-002.2)
-- tambien alcance a estos donuts; las metricas siguen siendo SUM aditivas.
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero), R5 (Gold ya acotado).
-- =============================================================================

SELECT
    -- ---------- dimensiones ----------------------------------------------------
    e.cve_ent,                                 -- llave del filtro global: entidad
    dm.nombre_entidad,                         -- valor legible del filtro
    e.nivel,                                   -- filtro global + KPI-08
    e.sostenimiento,                           -- KPI-09
    f.id_ciclo,                                -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- componentes aditivos ------------------------------------------
    COUNT(DISTINCT f.cct)     AS escuelas,
    SUM(f.matricula_total)    AS matricula_total

FROM gold.fact_escuela_ciclo f
JOIN gold.dim_escuela   e  ON f.cct      = e.cct
JOIN gold.dim_municipio dm ON f.cve_mun  = dm.cve_mun
JOIN gold.dim_tiempo    dt ON f.id_ciclo = dt.id_ciclo
GROUP BY
    e.cve_ent,
    dm.nombre_entidad,
    e.nivel,
    e.sostenimiento,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio
