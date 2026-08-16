{% macro normalize_binary_driver(column_name) %}
    case
        when {{ column_name }} is null
          or btrim(cast({{ column_name }} as text)) = ''
            then 'SIN_DATO'

        when lower(btrim(cast({{ column_name }} as text)))
             in ('1', 'true', 't', 'si', 'sí')
            then '1'

        when lower(btrim(cast({{ column_name }} as text)))
             in ('0', 'false', 'f', 'no')
            then '0'

        when upper(btrim(cast({{ column_name }} as text))) = 'SIN_DATO'
            then 'SIN_DATO'

        else upper(btrim(cast({{ column_name }} as text)))
    end
{% endmacro %}
