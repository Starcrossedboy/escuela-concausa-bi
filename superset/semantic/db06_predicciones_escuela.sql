-- =============================================================================
-- db06_predicciones_escuela (virtual)  ·  DB-06 Predicciones, grano de detalle
-- -----------------------------------------------------------------------------
-- Historia : US-204  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Cube_Specs_DB06_DB09.md §4
-- Grano    : una fila por cct x id_ciclo (grano del hecho, sin agregar)
--
-- Capa de detalle de DB-06: cada escuela con su riesgo y variacion proyectada
-- por ML-01. Alimenta la distribucion de riesgo (cubetas `rango_riesgo`), el
-- semaforo en el umbral R3 y los conteos globales del tablero.
--
-- R1: indice_riesgo / variacion_proyectada / probabilidad por LEFT JOIN a
--     gold.predicciones filtrando modelo = 'ML-01' con la llave completa
--     (cct, id_ciclo) y el grano escuela (DEC-010). Una escuela sin prediccion
--     NO desaparece: viaja con cobertura_prediccion = 'SIN_DATO' y en_riesgo
--     nulo (desconocido, no falso).
-- R2: SIN_DATO nunca cero. R3: umbral 0.6.
-- =============================================================================

SELECT
    -- ---------- identidad ------------------------------------------------------
    f.cct,
    e.nombre                                    AS nombre_escuela,
    e.nivel,                                     -- filtro global: nivel educativo
    e.sostenimiento,

    -- ---------- territorio y tiempo --------------------------------------------
    f.cve_mun,
    dm.cve_ent,                                  -- filtro global: entidad
    dm.nombre_municipio,
    dm.nombre_entidad,
    f.id_ciclo,                                  -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- hechos observados ----------------------------------------------
    f.matricula_total,
    f.variacion_matricula,
    f.indice_completitud_drivers,

    -- ---------- proyeccion y riesgo (ML-01, por JOIN, grano escuela) ----------
    p.indice_riesgo,
    p.valor                                     AS variacion_proyectada,
    p.probabilidad,
    CASE
        WHEN p.indice_riesgo IS NULL THEN NULL
        WHEN p.indice_riesgo >= 0.6 THEN TRUE      -- R3
        ELSE FALSE
    END                                         AS en_riesgo,
    CASE
        WHEN p.indice_riesgo IS NULL THEN NULL
        WHEN p.indice_riesgo < 0.2 THEN '0.00 - 0.19'
        WHEN p.indice_riesgo < 0.4 THEN '0.20 - 0.39'
        WHEN p.indice_riesgo < 0.6 THEN '0.40 - 0.59'
        WHEN p.indice_riesgo < 0.8 THEN '0.60 - 0.79'
        ELSE '0.80 - 1.00'
    END                                         AS rango_riesgo,
    CASE
        WHEN p.cct IS NULL THEN 'SIN_DATO'
        ELSE 'OK'
    END                                         AS cobertura_prediccion

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela   e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo    dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio dm ON f.cve_mun  = dm.cve_mun
LEFT JOIN gold.predicciones  p  ON f.cct      = p.cct
                               AND f.id_ciclo = p.id_ciclo
                               AND p.modelo   = 'ML-01'
                               AND (p.grano IS NULL OR p.grano = 'escuela')