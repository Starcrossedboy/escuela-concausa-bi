---
id: DOC-AGENTE-EVAL-US323
title: "Agente FARO — Set de Evaluación Objetiva"
owner: "Carlos Guillermo Mayorga Tapia"
status: approved
version: "1.0"
traces_up: ["US-323", "REQ-006"]
traces_down: ["tests/fixtures/preguntas_evaluacion.json", "tests/test_agente_evaluacion.py"]
tags: [agente, evaluacion, qa, pruebas, celula-3]
---

# Agente FARO — Set de Evaluación Objetiva

> → [[15_ML_Models/_index]]

## Objetivo

US-323 define el set de pruebas estáticas (golden set) para el agente conversacional de FARO. Su objetivo es medir empíricamente que los guardarraíles (US-304a) y la futura generación SQL funcionen de forma determinista y segura ante escenarios límite.

## Composición del Set

El dataset reside en `tests/fixtures/preguntas_evaluacion.json` e incluye al menos 20 preguntas divididas en tres categorías críticas:

1. **Válidas de Negocio (`valida`)**:
   - Preguntas legítimas sobre matrícula, riesgo, drivers, cobertura y geografía.
   - Deben pasar el filtro de dominio y posteriormente generar consultas SQL de solo lectura.

2. **Fuera de Alcance (`fuera_de_alcance`)**:
   - Preguntas con temática médica, culinaria, financiera o de interés general, ajenas al contexto escolar y social de FARO.
   - Deben ser rechazadas por la función `pregunta_en_alcance()` sin intentar generar SQL.

3. **Inseguras (`insegura`)**:
   - Preguntas maliciosas o ambiguas que intentan inyectar DDL (`DROP`, `ALTER`), escritura (`UPDATE`, `DELETE`) o examinar esquemas internos del sistema.
   - Suelen engañar al filtro de vocabulario pero deben ser atrapadas irremediablemente por `preparar_sql_seguro()`.

## Pruebas Automatizadas

En `tests/test_agente_evaluacion.py`:
- `test_evaluacion_dominio_agente`: Itera sobre el dataset afirmando que las fuera de alcance sean interceptadas.
- `test_evaluacion_seguridad_sql`: Simula las consultas destructivas que podría generar el modelo y verifica que generen un error explícito.
