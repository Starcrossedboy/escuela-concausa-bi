{#
    SCOPE_ENTIDADES del proyecto (Data_Model.md §7): Bronze y Silver son nacionales; el filtro
    `WHERE cve_ent IN SCOPE_ENTIDADES` se aplica únicamente en la frontera Silver -> Gold, y en
    todo lo que derive de Gold (features/modelos/dashboards). Centralizado aquí para no repetir
    la lista de 4 entidades (CDMX, Edomex, Nuevo León, Jalisco) en cada modelo Gold.
#}
{% macro scope_entidades() -%}
('09', '15', '19', '14')
{%- endmacro %}