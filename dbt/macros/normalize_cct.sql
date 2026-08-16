{% macro normalize_cct(column_name) %}
    case
        when {{ column_name }} is null then null

        when btrim(cast({{ column_name }} as text)) = '' then null

        when char_length(
            btrim(cast({{ column_name }} as text))
        ) between 1 and 10 then
            upper(
                lpad(
                    btrim(cast({{ column_name }} as text)),
                    10,
                    '0'
                )
            )

        else null
    end
{% endmacro %}
