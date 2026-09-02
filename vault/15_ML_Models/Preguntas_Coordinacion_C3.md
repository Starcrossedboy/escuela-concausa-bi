---
id: DOC-C3-PREGUNTAS-COORDINACION
title: "Preguntas de coordinación — Célula 3"
owner: "Andrés González Habib"
status: draft
version: "0.1"
traces_up: ["US-302", "US-303", "US-304a", "REQ-003", "REQ-006"]
traces_down: ["vault/15_ML_Models/ML02_Clasificacion_Driver", "vault/15_ML_Models/Agente_Guardrails_US304a"]
tags: [ml, coordinacion, bloqueantes, celula-3]
---

# Preguntas de coordinación — Célula 3

> → [[vault/15_ML_Models/_index]]

## Para Diana Alvarez / Célula 1 — `gold.features_escuela`

1. ¿`gold.features_escuela` publicará una columna real `driver_dominante` para entrenar ML-02, o Célula
   3 debe derivarla oficialmente desde los seis drivers?
   - **Por qué importa:** hoy ML-02 usa `driver_dominante_proxy` solo para avanzar; sin etiqueta real no
     podemos reportar F1 macro de negocio.

2. Si C1 espera que C3 derive `driver_dominante`, ¿la regla aceptada será "driver observado de mayor
   puntaje" o debemos usar otra lógica validada por negocio?
   - **Por qué importa:** esta decisión define la semántica de las recomendaciones prescriptivas.

3. ¿El contrato final conservará exactamente los nombres `d1_pobreza`, `d2_inseguridad`,
   `d3_infraestructura`, `d4_conectividad`, `d5_agua`, `d6_aire` y `d*_cobertura`?
   - **Por qué importa:** el scaffold de ML-02 y ML-01 ya están alineados a esos nombres.

4. ¿En qué ciclo o fecha tendremos un extracto real de `gold.features_escuela` para probar modelos?
   - **Por qué importa:** los fixtures validan pipeline, no métricas finales.

## Para Juan Carlos / Christian / Célula 4 — API de inferencia

5. ¿El endpoint `/predicciones/{cct}/explicacion` recibirá solo `cct` o también `id_ciclo` como query
   param?
   - **Por qué importa:** las predicciones son por `cct × id_ciclo`; solo `cct` puede ser ambiguo.

6. Para `ExplicacionSHAPOut.contribuciones`, ¿prefieren llaves `D1`…`D6` o nombres de feature
   (`d1_pobreza`, `d2_inseguridad`, etc.)?
   - **Por qué importa:** SHAP sale naturalmente por feature, pero la API mock actual habla en drivers.

7. ¿Célula 4 cargará modelos directamente desde MLflow o Célula 3 debe entregar wrappers/artefactos
   serializados listos para importar?
   - **Por qué importa:** define el contrato real de US-303 y US-412/415.

8. En `/agente/consulta`, cuando el guardarraíl rechace una pregunta, ¿la API debe devolver la razón
   interna de rechazo o solo `fuera_de_alcance=true` con mensaje genérico?
   - **Por qué importa:** balance entre auditabilidad y no filtrar reglas internas.

## Para Luis / Edgar Ulises / Célula 5 — MLflow y jobs ML

9. ¿Cuál será el `MLFLOW_TRACKING_URI` local estándar: `sqlite:///mlflow.db`, servicio Docker en
   `http://localhost:5000` u otro valor?
   - **Por qué importa:** los scripts tienen import diferido, pero el registro final necesita URI común.

10. ¿El Model Registry estará habilitado en local/CI o solo registraremos runs y artefactos?
    - **Por qué importa:** `--registrar-modelo` depende de registry funcional.

11. ¿Los jobs batch de ML correrán desde Airflow, script CLI o endpoint administrativo?
    - **Por qué importa:** define cómo persistir `mlflow_run_id` y predicciones a Gold.

## Para Estefany / ML-03

12. ¿ML-03 devolverá `cluster` como entero estable (`0`, `1`, `2`...) o como etiqueta de negocio
    (`urbana_alta_cobertura`, etc.)?
    - **Por qué importa:** `PrediccionOut.cluster` hoy es `StrictInt`; si quieren etiquetas hay que avisar
      a Célula 4 antes.

13. ¿Qué features compartirá ML-03 con ML-02 y cuáles necesita excluir por cobertura parcial?
    - **Por qué importa:** conviene reutilizar la misma matriz de drivers cuando sea posible.

## Para Carlos / US-304b y US-323

14. ¿El RAG recuperará solo esquema/tablas de Gold o también documentación de métricas y reglas de
    negocio?
    - **Por qué importa:** el prompt ya acepta `contexto_recuperado`; hay que acordar su contenido.

15. ¿El set de evaluación del agente incluirá casos negativos de SQL peligroso y preguntas fuera de
    alcance?
    - **Por qué importa:** los guardarraíles ya tienen tests unitarios, pero US-323 debe cubrir evaluación
      funcional end-to-end.

16. ¿Qué formato usará el contexto recuperado: texto plano, JSON con tablas/columnas o documentos con
    metadata?
    - **Por qué importa:** define cómo `construir_prompt_sistema()` debe insertar contexto sin romper el
      prompt.

## Para Edgar / PM

17. ¿Podemos registrar `driver_dominante_proxy` como avance técnico de US-302 sin marcar la historia
    como `done` hasta tener etiqueta real?
    - **Por qué importa:** evita sobredeclarar avance y mantiene trazabilidad honesta.

18. ¿La actualización de `Traceability_Matrix` para este PR la hago yo en la rama o la consolida PM?
    - **Por qué importa:** es archivo compartido y el Agent Context lo marca como coordinación con PM.
