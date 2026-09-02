---
id: DOC-C3-GUIA-EJECUCION
title: "Guía de ejecución local — Célula 3"
owner: "Andrés González Habib"
status: in_review
version: "0.2"
traces_up: ["US-302", "US-303", "US-304a", "REQ-003", "REQ-006"]
traces_down: ["src/modelos/entrenar_ml02.py", "src/agente/guardrails.py", "src/agente/prompt.py", "tests/test_entrenar_ml02.py", "tests/test_agente_guardrails.py", "tests/test_agente_prompt.py", "tests/test_mlflow_utils.py"]
tags: [ml, agente, setup, pruebas, celula-3]
---

# Guía de ejecución local — Célula 3

> → [[15_ML_Models/_index]] · [[15_ML_Models/ML02_Clasificacion_Driver]] · [[15_ML_Models/Agente_Guardrails_US304a]]

## Objetivo

Comandos mínimos para validar ML-02, su publicación a Gold, las explicaciones SHAP, el helper MLflow
y los guardarraíles del agente.

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
.\.venv\Scripts\python.exe -m pytest tests/test_agente_guardrails.py tests/test_agente_prompt.py tests/test_entrenar_ml02.py tests/test_publicar_gold.py tests/test_mlflow_utils.py -q --tb=short
```

Resultado observado en esta sesión:

```text
59 passed
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

El registro ejecuta un preflight de compatibilidad y, cuando se usa `--registrar-modelo`, exige que
MLflow confirme una versión y la guarda como tag `registered_model_version`.

Para comprobar ML-02 después del registro:

```powershell
.\.venv\Scripts\python.exe -m src.modelos.verificar_registry --modelo ML02_DriverClasificador
```

Sin `--modelo`, el comando comprueba que ML-01, ML-02 y ML-03 tengan al menos una versión y reporta
por nombre cualquier modelo faltante.

## Publicar ML-01 y ML-02 en Gold

```powershell
$env:DATABASE_URL = "<URL SQLAlchemy del entorno local>"
.\.venv\Scripts\python.exe -m src.modelos.publicar_gold --features <RUTA_FEATURES>
```

El job publica `gold.predicciones` desde ML-01 y `gold.recomendaciones` desde ML-02. La unión se
valida uno-a-uno por `cct` e `id_ciclo`; no inventa recomendaciones para escuelas sin features.

## Validar SHAP

`explicar_driver()` entrega `cct`, `driver_dominante` y seis contribuciones `D1`…`D6`, conforme a
`ExplicacionSHAPOut`. Requiere `shap` de `requirements/celula-3.txt`; se verificó localmente con una
explicación real sobre el fixture sintético.

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
- SHAP no se ejecuta en CI base porque `shap` no está en `requirements.txt`; sus transformaciones de
  contrato sí tienen prueba unitaria y el cálculo real se validó en el entorno de Célula 3.
- US-303 no puede cerrarse hasta tener ML-03 y el acuerdo de MLflow/API.
- El registry end-to-end requiere las variables locales de Compose; sin ellas `docker compose`
  rechaza la configuración antes de iniciar MLflow.
- US-304a no queda integrado end-to-end hasta que existan RAG (US-304b) y endpoint real del agente.

## Evidencia E2E incremental — 2026-08-30

Se levantó MLflow `3.15.1` como servidor HTTP local con backend SQLite y un solo worker. Usando
`registrar_sklearn()` —el helper real de US-303— se crearon corrida, artefacto y versión `1` para
los tres nombres canónicos:

```text
ML01_RegresionMatricula: versión 1
ML02_DriverClasificador: versión 1
ML03_ClusteringEscuelas: versión 1
```

La traza HTTP confirmó la creación de las tres versiones y el helper devolvió un `run_id` por
modelo. Esta evidencia valida el camino común de registro y que ML-03 ya participa en la
verificación conjunta.

US-303 permanece en revisión por dos pendientes externos a esta evidencia:

- la imagen `docker/mlflow.Dockerfile` no pudo reconstruirse en esta máquina porque la descarga de
  PyPI desde BuildKit falló con `SSLV3_ALERT_HANDSHAKE_FAILURE`;
- falta repetir `python -m src.modelos.verificar_registry` contra el contenedor compartido y validar
  la exposición de inferencia en la API de C4.
