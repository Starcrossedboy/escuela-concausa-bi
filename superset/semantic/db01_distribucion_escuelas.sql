-- =============================================================================
-- db01_distribucion_escuelas  ·  DB-01 Ejecutivo (KPI-08 / KPI-09)
-- -----------------------------------------------------------------------------
-- Historia : US-205  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §4
-- Grano    : una fila por nivel x sostenimiento x cve_ent x id_ciclo
--
-- REPUNTEO A CUBOS FISICOS (US-205 / US-113): dataset chico para los donuts de
--   composicion del tablero ejecutivo; se REAGREGA desde gold.cubo_escuela_360
--   (grano cct x id_ciclo, decision C2 aprobada). Los agregados son aditivos:
--   COUNT(DISTINCT cct) y SUM(matricula_total) sobre el universo ya acotado.
--
-- `cve_ent` entra al grano para que el filtro global de entidad (AC-002.2)
--   tambien alcance a estos donuts; las metricas siguen siendo SUM aditivas.
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero), R5 (Gold ya viene acotado).
-- =============================================================================

SELECT
    -- ---------- dimensiones ----------------------------------------------------
    c.cve_ent,                                 -- llave del filtro global: entidad
    c.nombre_entidad,                          -- valor legible del filtro
    c.nivel,                                   -- filtro global + KPI-08
    c.sostenimiento,                           -- KPI-09
    c.id_ciclo,                                -- filtro global: ciclo
    c.ciclo,
    c.anio_inicio,

    -- ---------- componentes aditivos (reagregados desde el cubo) --------------
    COUNT(DISTINCT c.cct)  AS escuelas,
    SUM(c.matricula_total) AS matricula_total

FROM gold.cubo_escuela_360 c
GROUP BY
    c.cve_ent,
    c.nombre_entidad,
    c.nivel,
    c.sostenimiento,
    c.id_ciclo,
    c.ciclo,
    c.anio_inicio