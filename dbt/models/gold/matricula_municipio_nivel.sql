-- gold.matricula_municipio_nivel -- agregado municipio x nivel x ciclo de silver.matricula_historica
-- (DS-01 distribucion HISTORICA), construido para alimentar unir_target() en
-- src/modelos/target_hibrido.py (PR #56, Hector Morales) -- mitigacion de RISK-007/DEC-007.
--
-- Grano: cve_mun x nivel x id_ciclo, un registro por combinacion -- UNIQUE, requerido por
-- unir_target(agregado, serie_target, validate="one_to_one") en target_hibrido.py (ver
-- LLAVE_AGREGADA = ("cve_mun", "nivel", "id_ciclo") en particion_temporal.py). matricula_total
-- se SUMA de todos los cct de silver.matricula_historica que caen en el mismo municipio x
-- nivel x ciclo.
--
-- Alias ciclo -> id_ciclo: mismo patron que dim_tiempo.sql y fact_escuela_ciclo.sql --
-- silver.matricula_historica expone `ciclo`, el rename al nombre que exige target_hibrido.py
-- se hace aqui, en el limite Silver->Gold.
--
-- nivel: silver.matricula_historica ya normaliza a MAYUSCULAS (ver matricula_historica.sql)
-- para hacer match exacto con gold.dim_escuela.nivel (DS-02), que target_hibrido.py exige
-- via LLAVE_AGREGADA.
--
-- SCOPE_ENTIDADES (Data_Model.md §7): aplicado aqui, en el limite Silver->Gold -- ver
-- scope_entidades.sql. silver.matricula_historica es nacional/sin filtrar, como todo Silver.
--
-- FIX (2026-09-03, Diana/DS-01): bronze.formato911_historico es append-only (medallion, no se
-- borra), y trae 182 filas fixture antiguas junto a los ~1.37M reales cargados hoy
-- (cargar_bronze_formato911_historico_real.py). De esas 182, varias traen un cct que no existe
-- en el catalogo real de DS-02 -- sumarian matricula fantasma al agregado real que consume
-- target_hibrido.py. Se exige que el cct exista en silver.escuela (catalogo real) antes de
-- sumar, igual que el filtro de scope_entidades() de arriba. Verificado 2026-09-03: de 182
-- filas fixture, solo 6 coinciden con un cct real -- y esas 6 ya compiten en el dedup de
-- matricula_historica.sql (partition by cct, ciclo, turno) contra la carga real, mucho mas
-- reciente en _ingested_at.

with real_data as (

    select
        cct,
        cve_mun,
        nivel,
        ciclo,
        matricula_total

    from {{ ref('matricula_historica') }}

    where cve_ent in {{ scope_entidades() }}

)

select
    real_data.cve_mun,
    real_data.nivel,
    real_data.ciclo as id_ciclo,
    sum(real_data.matricula_total) as matricula_total

from real_data

inner join {{ ref('escuela') }} as catalogo_real
    on {{ normalize_cct('real_data.cct') }} = catalogo_real.cct

group by
    real_data.cve_mun,
    real_data.nivel,
    real_data.ciclo
