{% macro normalize_cve_ent(cve_ent) %}
    case
        when {{ cve_ent }} is null then null

        when btrim(cast({{ cve_ent }} as text)) ~ '^[0-9]{1,2}$' then
            lpad(
                btrim(cast({{ cve_ent }} as text)),
                2,
                '0'
            )

        else null
    end
{% endmacro %}
