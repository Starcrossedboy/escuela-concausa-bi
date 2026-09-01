-- Regresión de BUG-034: ninguna escuela del alcance está realmente en (0,0) -- ese valor en el
-- catálogo real de DS-02 es georreferencia ausente disfrazada de válida (6 filas verificadas en
-- la descarga real de SIGED, ver DS-02_Catalogo_CCT.md §10). silver/escuela.sql debe nulificar
-- el 0 numérico igual que la cadena vacía; este test falla si algún 0 se cuela.

select
    'latitud_cero' as regla,
    cct as valor
from {{ ref('escuela') }}
where latitud = 0

union all

select
    'longitud_cero' as regla,
    cct as valor
from {{ ref('escuela') }}
where longitud = 0
