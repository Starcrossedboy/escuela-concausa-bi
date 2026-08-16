---
id: DOC-C3-GUIA-EJECUCION
title: "Guía de ejecución local — Célula 3"
owner: "Andrés González Habib"
status: draft
version: "0.1"
traces_up: ["US-302", "US-303", "US-304a", "REQ-003", "REQ-006"]
traces_down: ["src/modelos/entrenar_ml02.py", "src/agente/guardrails.py", "src/agente/prompt.py", "tests/test_entrenar_ml02.py", "tests/test_agente_guardrails.py", "tests/test_agente_prompt.py", "tests/test_mlflow_utils.py"]
tags: [ml, agente, setup, pruebas, celula-3]
---

# Guía de ejecución local — Célula 3

> → [[15_ML_Models/_index]] · [[15_ML_Models/ML02_Clasificacion_Driver]] · [[15_ML_Models/Agente_Guardrails_US304a]]

## Objetivo

Comandos mínimos para validar el avance independiente de Célula 3: guardarraíles del agente, prompt,
scaffold de ML-02 y helper MLflow.

## Ambiente usado en esta rama

El proyecto pide Python 3.11, pero el ambiente local disponible en esta máquina es `.venv` con Python
3.12.10. Las pruebas enfocadas pasaron con ese entorno. Antes del PR final, confirmar si el equipo exige
recrear el venv con 3.11.

## Instalar dependencias mínimas

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest pandas numpy scikit-learn scipy pydantic
```

Estas dependencias alcanzan para las pruebas de esta rama. `mlflow` y `shap` siguen siendo dependencias
de Célula 3 completa y viven en `requirements/celula-3.txt`.

## Correr pruebas enfocadas

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_agente_guardrails.py tests/test_agente_prompt.py tests/test_entrenar_ml02.py tests/test_mlflow_utils.py -q --tb=short
```

Resultado observado en esta sesión:

```text
25 passed in 7.71s
```

## Ejecutar ML-02 contra fixture sintético

```powershell
.\.venv\Scripts\python.exe -m src.modelos.entrenar_ml02 --sin-mlflow
```

Resultado observado:

```text
Target usado: driver_dominante_proxy
F1 macro 0.7945 +/- 0.0241    Accuracy 0.8083
```

Interpretación: valida que el pipeline corre, no que el modelo ya tenga métrica final de negocio. El
target usado es proxy hasta que Célula 1 confirme o publique `driver_dominante` real.

## Ejecutar ML-02 con MLflow

Cuando Célula 5 confirme el `MLFLOW_TRACKING_URI`:

```powershell
.\.venv\Scripts\python.exe -m src.modelos.entrenar_ml02 --tracking-uri <URI> --registrar-modelo
```

Para solo registrar run/artefacto sin publicar en registry, omitir `--registrar-modelo`.

## Validar vault

```powershell
python _Meta/scripts/vault_lint.py .
```

Resultado observado:

```text
✅ Vault limpio.
```

## Limitaciones conocidas

- ML-02 usa `driver_dominante_proxy`; falta confirmación humana de la etiqueta real.
- SHAP queda disponible como función opcional, pero no se ejecuta en CI base porque `shap` no está en
  `requirements.txt`.
- US-303 no puede cerrarse hasta tener ML-03 y el acuerdo de MLflow/API.
- US-304a no queda integrado end-to-end hasta que existan RAG (US-304b) y endpoint real del agente.
