-- =============================================================================
-- gold.cubo_riesgo_territorial (virtual)  ·  DB-02 Mapa de riesgo territorial
-- -----------------------------------------------------------------------------
-- Historia   : US-203  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato   : 04_UX_Design/Screen_Specs.md §2 (cubo de DB-02) y §4 (KPI-03/04/10)
-- Grano      : una fila por cve_mun x nivel x id_ciclo
-- Uso        : dataset virtual de Superset para el coropletico municipal (KPI-10)
--              y SQL de referencia para US-113. Mismo grano que cubo_comparador
--              (DEC-008): sin `nivel` en el grano, el filtro global de nivel
--              no tendria sobre que operar.
--
-- RIESGO POR JOIN (R1, Data_Model §4.1): indice_riesgo vive en gold.predicciones
--   y se consulta por LEFT JOIN (cct, id_ciclo) filtrando modelo = 'ML-01'.
--   LEFT y no INNER: un municipio sin predicciones sigue siendo un municipio del
--   mapa; su color sera "SIN_DATO", nunca un riesgo inventado.
--
-- Reglas aplicadas: R1 (ML por JOIN), R2 (SIN_DATO nunca cero),
--                   R3 (umbral 0.6), R5 (Gold ya viene acotado).
-- =============================================================================

SELECT
    -- ---------- identidad y llaves -------------------------------------------
    f.cve_mun,
    dm.cve_ent,                                -- filtro global: entidad
    dm.nombre_municipio,
    dm.nombre_entidad,
    e.nivel,                                   -- filtro global: nivel educativo
    f.id_ciclo,                                -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- contexto para tooltips / ranking ------------------------------
    COUNT(DISTINCT f.cct)                          AS escuelas,
    SUM(f.matricula_total)                         AS matricula_total,
    SUM(f.variacion_matricula * f.matricula_total) AS variacion_x_matricula,

    -- ---------- componentes aditivos: riesgo (ML-01) --------------------------
    SUM(p.indice_riesgo)                           AS suma_indice_riesgo,
    COUNT(p.cct)                                   AS escuelas_con_prediccion,
    COUNT(*) FILTER (WHERE p.indice_riesgo >= 0.6) AS escuelas_en_riesgo,  -- R3
    CASE
        WHEN COUNT(p.cct) = 0 THEN 'SIN_DATO'
        ELSE 'OK'
    END                                            AS cobertura_riesgo

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela   e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo    dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio dm ON f.cve_mun  = dm.cve_mun
LEFT JOIN gold.predicciones  p  ON f.cct      = p.cct
                               AND f.id_ciclo = p.id_ciclo
                               AND p.modelo   = 'ML-01'
GROUP BY
    f.cve_mun,
    dm.cve_ent,
    dm.nombre_municipio,
    dm.nombre_entidad,
    e.nivel,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio
