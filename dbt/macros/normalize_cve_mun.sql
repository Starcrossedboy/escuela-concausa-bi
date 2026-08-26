{% macro normalize_cve_mun(cve_ent, cve_mun) %}
    case
        when {{ cve_mun }} is null then null

        when btrim(cast({{ cve_mun }} as text)) ~ '^[0-9]{5}$' then
            btrim(cast({{ cve_mun }} as text))

        when btrim(cast({{ cve_ent }} as text)) ~ '^[0-9]{1,2}$'
         and btrim(cast({{ cve_mun }} as text)) ~ '^[0-9]{1,3}$' then
            lpad(btrim(cast({{ cve_ent }} as text)), 2, '0')
            ||
            lpad(btrim(cast({{ cve_mun }} as text)), 3, '0')

        else null
    end
{% endmacro %}
