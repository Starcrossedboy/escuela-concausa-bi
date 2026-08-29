-- KPI-01 · Matrícula total
-- Fuente: 04_UX_Design/Screen_Specs.md §4 (canónico, Manuel Serranía, US-201)
-- Cubo: gold.cubo_matricula | Consumido en: DB-01, DB-06
-- NO MODIFICAR sin ratificación de Manuel (dueño del catálogo, US-201).

SELECT f.cve_mun,
       dt.ciclo,
       SUM(f.matricula_total) AS matricula_total
FROM gold.fact_escuela_ciclo f
JOIN gold.dim_tiempo dt ON f.id_ciclo = dt.id_ciclo
JOIN gold.dim_escuela e ON f.cct = e.cct
WHERE e.nivel = :nivel            -- filtro global (opcional)
GROUP BY f.cve_mun, dt.ciclo;
