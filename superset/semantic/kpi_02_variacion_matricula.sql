-- KPI-02 · Variación de matrícula (%Δ ponderado)
-- Fuente: 04_UX_Design/Screen_Specs.md §4 (canónico, Manuel Serranía, US-201)
-- Cubo: gold.cubo_matricula | Consumido en: DB-01, DB-06
-- NO MODIFICAR sin ratificación de Manuel (dueño del catálogo, US-201).
--
-- Razón de sumas con la columna directa `matricula_ciclo_anterior` (BUG-031/P-09):
-- `variacion_matricula` son alumnos absolutos (matricula_total - matricula_ciclo_anterior), no
-- una fracción; promediarla ponderada pintaba -54.5% donde el real es -0.19%. El `* 1.0` evita
-- la división entera de dos columnas integer (en Postgres y en SQLite).
SELECT dt.ciclo,
       SUM(f.matricula_total) AS matricula_total,
       SUM(f.matricula_total) * 1.0
         / NULLIF(SUM(f.matricula_ciclo_anterior), 0) - 1 AS variacion_ponderada_pct
FROM gold.fact_escuela_ciclo f
JOIN gold.dim_tiempo dt ON f.id_ciclo = dt.id_ciclo
GROUP BY dt.ciclo;
