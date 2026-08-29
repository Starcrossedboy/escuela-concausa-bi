-- KPI-02 · Variación de matrícula (%Δ ponderado)
-- Fuente: 04_UX_Design/Screen_Specs.md §4 (canónico, Manuel Serranía, US-201)
-- Cubo: gold.cubo_matricula | Consumido en: DB-01, DB-06
-- NO MODIFICAR sin ratificación de Manuel (dueño del catálogo, US-201).

SELECT dt.ciclo,
       SUM(f.matricula_total) AS matricula_total,
       SUM(f.variacion_matricula * f.matricula_total)
         / NULLIF(SUM(f.matricula_total), 0) AS variacion_ponderada_pct
FROM gold.fact_escuela_ciclo f
JOIN gold.dim_tiempo dt ON f.id_ciclo = dt.id_ciclo
GROUP BY dt.ciclo;
