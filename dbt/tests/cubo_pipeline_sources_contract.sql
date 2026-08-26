-- Catálogo SOURCE_NAME exacto: ocho fuentes, sin alias abreviados ni extras.
with esperadas(id_fuente, fuente) as (
    values
        ('DS-01', 'DS-01_FORMATO911'),
        ('DS-02', 'DS-02_CATALOGO_CCT'),
        ('DS-03', 'DS-03_CEMABE'),
        ('DS-04', 'DS-04_SESNSP'),
        ('DS-05', 'DS-05_SINAICA'),
        ('DS-06', 'DS-06_CONAGUA_SINA'),
        ('DS-07', 'DS-07_CONEVAL'),
        ('DS-08', 'DS-08_CONAPO')
),
faltantes_o_extras as (
    (select id_fuente, fuente from esperadas
     except
     select id_fuente, fuente from {{ ref('cubo_pipeline') }})
    union all
    (select id_fuente, fuente from {{ ref('cubo_pipeline') }}
     except
     select id_fuente, fuente from esperadas)
)
select * from faltantes_o_extras
