-- KPI-03 · Índice de riesgo promedio
-- Fuente: 04_UX_Design/Screen_Specs.md §4 (canónico, Manuel Serranía, US-201)
-- indice_riesgo es salida de ML-01 (gold.predicciones); se une por (cct, id_ciclo).
-- Cubo: gold.cubo_riesgo_territorial | Consumido en: DB-01, DB-02
-- NO MODIFICAR sin ratificación de Manuel (dueño del catálogo, US-201).

SELECT f.cve_mun,
       dt.ciclo,
       AVG(p.indice_riesgo) AS indice_riesgo_promedio
FROM gold.fact_escuela_ciclo f
JOIN gold.dim_tiempo dt ON f.id_ciclo = dt.id_ciclo
JOIN gold.predicciones p ON f.cct = p.cct AND f.id_ciclo = p.id_ciclo
WHERE p.modelo = 'ML-01'
GROUP BY f.cve_mun, dt.ciclo;
