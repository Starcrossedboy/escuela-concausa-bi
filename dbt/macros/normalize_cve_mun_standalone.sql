{% macro normalize_cve_mun_standalone(cve_mun) %}
    case
        when {{ cve_mun }} is null
          or btrim(cast({{ cve_mun }} as text)) = ''
            then null

        when btrim(cast({{ cve_mun }} as text)) ~ '^[0-9]{1,5}$'
            then lpad(
                btrim(cast({{ cve_mun }} as text)),
                5,
                '0'
            )

        else null
    end
{% endmacro %}
