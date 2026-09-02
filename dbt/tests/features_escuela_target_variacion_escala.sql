-- Regresión de BUG-017/BUG-019 (ADR-007): target_variacion_matricula debe venir en FRACCIÓN, no en
-- alumnos absolutos. Mismo criterio que verificar_escala_variacion() (src/modelos/riesgo.py,
-- MEDIANA_MAXIMA_FRACCION=1.0): con datos reales la mediana de |variación| es del orden de
-- centésimas; si vuelve a colarse una diferencia absoluta de alumnos (el defecto real de BUG-017,
-- del orden de decenas por escuela), la mediana rebasa por mucho ese umbral. Se usa la mediana, no
-- el máximo, para no confundir la unidad equivocada con unos cuantos valores extremos legítimos --
-- misma razón que documenta el guard de Python.

select mediana_abs
from (
    select
        percentile_cont(0.5) within group (order by abs(target_variacion_matricula))
            as mediana_abs
    from {{ ref('features_escuela') }}
) x
where mediana_abs > 1.0