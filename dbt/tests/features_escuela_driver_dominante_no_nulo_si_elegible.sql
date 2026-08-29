-- driver_dominante solo puede ser NULL cuando NINGÚN driver tiene cobertura 'OK' en esa fila.
-- Si existe al menos un elegible, debe haberse elegido uno -- nunca dejar la fila sin
-- etiqueta cuando sí hay de dónde escoger.
select cct, id_ciclo
from {{ ref('features_escuela') }}
where driver_dominante is null
  and (
      d1_cobertura = 'OK'
      or d2_cobertura = 'OK'
      or d3_cobertura = 'OK'
      or d4_cobertura = 'OK'
      or d5_cobertura = 'OK'
      or d6_cobertura = 'OK'
  )
