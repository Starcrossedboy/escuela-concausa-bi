-- KPI-08 · Escuelas por nivel educativo
-- Fuente: 04_UX_Design/Screen_Specs.md §4 (canónico, Manuel Serranía, US-201)
-- Consumido en: DB-01
-- NO MODIFICAR sin ratificación de Manuel (dueño del catálogo, US-201).

SELECT e.nivel,
       COUNT(DISTINCT f.cct) AS escuelas
FROM gold.fact_escuela_ciclo f
JOIN gold.dim_escuela e ON f.cct = e.cct
GROUP BY e.nivel;
