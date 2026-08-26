---
id: DOC-AGENTE-GUARDRAILS-US304A
title: "Agente FARO — Guardarraíles de seguridad"
owner: "Andrés González Habib"
status: in_review
version: "0.2"
traces_up: ["US-304a", "REQ-006", "03_Architecture/API_Specification"]
traces_down: ["src/agente/guardrails.py", "src/agente/prompt.py", "tests/test_agente_guardrails.py", "tests/test_agente_prompt.py"]
tags: [agente, rag, seguridad, guardrails, celula-3]
---

# Agente FARO — Guardarraíles de seguridad

> → [[15_ML_Models/_index]] · Contrato API: [[03_Architecture/API_Specification]]

## Objetivo

US-304a define el comportamiento seguro del agente conversacional antes de conectarlo a la capa RAG de
Carlos (US-304b) o al endpoint `/agente/consulta` de Célula 4.

Los módulos ejecutables viven en `src/agente/guardrails.py` y `src/agente/prompt.py`. No ejecutan SQL:
solo definen instrucciones, validan y normalizan la pregunta o consulta generada para que una capa
posterior pueda decidir si continúa.

## Reglas implementadas

1. **Alcance FARO.** La pregunta debe contener vocabulario del dominio: escuelas, matrícula, riesgo,
   drivers, municipios, CCT, agua, aire, pobreza, inseguridad, infraestructura o conectividad.
2. **Solo lectura.** El SQL generado debe iniciar con `SELECT` o `WITH`.
3. **Sin escritura ni DDL.** Se rechazan `DELETE`, `UPDATE`, `DROP`, `INSERT`, `ALTER`, `TRUNCATE`,
   `CREATE`, `MERGE`, `REPLACE`, `UPSERT` y `VACUUM`.
4. **Una sentencia.** Se rechazan sentencias múltiples y comentarios SQL.
5. **Solo esquema Gold.** Cada tabla de `FROM` o `JOIN` debe pertenecer a `gold.*`; se permiten CTE
    definidos en la misma consulta, pero no `public`, `information_schema`, `pg_catalog` ni tablas
    sin esquema.
6. **Límite auditable.** Toda consulta queda con `LIMIT 1000`; si el modelo propone un límite mayor,
   se reduce a 1000.

## Prompt de sistema

`src/agente/prompt.py` publica `SYSTEM_PROMPT` y `construir_prompt_sistema(contexto_recuperado)`. El
prompt fija el alcance FARO, prohíbe SQL de escritura/DDL, exige `SELECT`/`WITH`, limita las consultas
a `LIMIT 1000`, evita inventar tablas o resultados y reserva un bloque explícito para el contexto que
recuperará US-304b.

## Contrato esperado

La salida se alinea con `AgenteRespuestaOut`:

- `respuesta`: explicación en lenguaje natural;
- `sql_generado`: consulta auditada, o `None` si no aplica;
- `fuera_de_alcance`: `true` cuando el guardarraíl rechaza la pregunta.

## Validación

`tests/test_agente_guardrails.py` cubre:

- pregunta dentro y fuera del dominio;
- rechazo de escritura SQL y sentencias múltiples;
- aceptación de `SELECT` y CTE que solo consultan Gold;
- rechazo de tablas fuera de Gold, sin esquema y `JOIN` mixtos;
- inyección o reducción de `LIMIT 1000`;
- error explícito cuando `preparar_sql_seguro()` recibe un verbo prohibido.
- presencia de reglas obligatorias en el prompt de sistema y composición con contexto recuperado.

## Pendientes para cerrar US-304a

- Acordar con Célula 4 si el endpoint devuelve la razón de rechazo o solo `fuera_de_alcance=true`.
- Integrar estos guardarraíles en el servicio del agente cuando exista la capa de recuperación US-304b.
- Registrar ejemplos aceptados/rechazados en el set de evaluación del agente (US-323).
