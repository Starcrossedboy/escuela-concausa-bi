{#
    Override estándar de dbt: cuando un modelo define `+schema:` (p.ej. `silver` o `gold`),
    usa ese nombre de esquema tal cual, en vez del comportamiento por defecto de dbt
    (`<schema_target>_<custom_schema>`, p.ej. `dbt_diana_silver`).

    Por qué: Data_Model.md §9 fija los esquemas por capa como `bronze.` / `silver.` / `gold.`
    a secas. dbt/models/gold/_gold__sources.yml ya asume `schema: silver` como nombre literal
    (dim_tiempo.sql hace `source('silver', 'matricula')`), así que sin este override los
    modelos de dbt/models/silver/ escribirían en un esquema que Gold nunca podría encontrar.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}