select
    'cct_length' as regla,
    cct as valor
from {{ ref('escuela') }}
where cct is not null
  and char_length(cct) <> 10

union all

select
    'cve_ent_format' as regla,
    cve_ent as valor
from {{ ref('escuela') }}
where cve_ent is not null
  and cve_ent !~ '^[0-9]{2}$'

union all

select
    'cve_mun_format' as regla,
    cve_mun as valor
from {{ ref('escuela') }}
where cve_mun is not null
  and cve_mun !~ '^[0-9]{5}$'
