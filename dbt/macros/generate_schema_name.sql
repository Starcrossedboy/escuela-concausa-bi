{#
    Override estándar de dbt: cuando un modelo define `+schema:` (p.ej. `silver` o `gold`),
    usa ese nombre de esquema tal cual, en vez del comportamiento por defecto de dbt
    (`<schema_target>_<custom_schema>`, p.ej. `dbt_diana_silver`).

    Por qué: Data_Model.md §9 fija los esquemas por capa como `bronze.` / `silver.` / `gold.`
    a secas. Sin este override los modelos de dbt/models/silver/ y dbt/models/gold/ escribirían
    en un esquema con prefijo (p.ej. `dbt_diana_silver`) en vez del literal que el resto del
    proyecto espera.

    Nota (BUG-021, 2026-08-28): los modelos Gold usan `ref()` hacia los modelos de
    dbt/models/silver/, no `source()` -- `silver.*` son modelos de este mismo proyecto, no datos
    externos. `dbt/models/gold/_gold__sources.yml` sigue existiendo solo para documentar las
    columnas de esas tablas; no se usa para resolver dependencias.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}