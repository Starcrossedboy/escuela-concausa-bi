-- KPI-04 · Escuelas en riesgo
-- Fuente: 04_UX_Design/Screen_Specs.md §4 (canónico, Manuel Serranía, US-201)
-- Umbral ratificado por negocio (DEC-006): indice_riesgo >= 0.6 = perder ~5% de matrícula.
-- Consumido en: DB-01, DB-02
-- NO MODIFICAR sin ratificación de Manuel (dueño del catálogo, US-201).

SELECT dt.ciclo,
       COUNT(*) FILTER (WHERE p.indice_riesgo >= 0.6) AS escuelas_en_riesgo,
       COUNT(*)                                       AS total_escuelas
FROM gold.fact_escuela_ciclo f
JOIN gold.dim_tiempo dt ON f.id_ciclo = dt.id_ciclo
JOIN gold.predicciones p ON f.cct = p.cct AND f.id_ciclo = p.id_ciclo
WHERE p.modelo = 'ML-01'
GROUP BY dt.ciclo;
