-- Desempate determinista D1 > D2 > D3 > D4 > D5 > D6, con casos sintéticos armados a propósito
-- (no hay garantía de que el fixture real produzca un empate). Reproduce la MISMA regla de
-- argmax que usa la CTE `con_driver_dominante` de features_escuela.sql (unnest de dos arrays
-- paralelos, ordenado por valor desc y código asc, límite 1) -- si esa regla cambia sin
-- actualizar esta prueba (o viceversa), esto debe fallar.
with casos as (

    select
        'D2_vs_D4_empatados_en_el_maximo' as caso,
        array['D1', 'D2', 'D3', 'D4', 'D5', 'D6'] as codigos,
        array[0.2, 0.9, 0.5, 0.9, null, 0.1]::double precision[] as valores,
        'D2' as esperado

    union all

    select
        'D3_D5_D6_empatados_en_el_maximo',
        array['D1', 'D2', 'D3', 'D4', 'D5', 'D6'],
        array[null, 0.3, 0.7, 0.1, 0.7, 0.7]::double precision[],
        'D3'

    union all

    select
        'todos_empatados_gana_D1',
        array['D1', 'D2', 'D3', 'D4', 'D5', 'D6'],
        array[0.5, 0.5, 0.5, 0.5, 0.5, 0.5]::double precision[],
        'D1'

),

ganador as (

    select
        c.caso,
        c.esperado,
        (
            select t.codigo
            from unnest(c.codigos, c.valores) as t(codigo, valor)
            where t.valor is not null
            order by t.valor desc, t.codigo asc
            limit 1
        ) as obtenido
    from casos c

)

select *
from ganador
where obtenido is distinct from esperado
