---
id: DOC-C3-PR-DRAFT-TRABAJO-INDEPENDIENTE
title: "Borrador de PR — trabajo independiente Célula 3"
owner: "Andrés González Habib"
status: draft
version: "0.1"
traces_up: ["US-302", "US-303", "US-304a", "REQ-003", "REQ-006"]
traces_down: ["vault/_DevLog/2026-08-15-andres-gonzalez-trabajo-independiente-ml-agente", "vault/15_ML_Models/Guia_Ejecucion_C3", "vault/15_ML_Models/Preguntas_Coordinacion_C3"]
tags: [pr, borrador, ml, agente, celula-3]
---

# Borrador de PR — trabajo independiente Célula 3

> → [[vault/15_ML_Models/_index]] · [[vault/_DevLog/2026-08-15-andres-gonzalez-trabajo-independiente-ml-agente]]

## Título sugerido

```text
feat(c3): avance independiente ML-02, MLflow y guardarraíles del agente (US-302, US-303, US-304a)
```

## ¿Qué cambia y por qué?

Este PR adelanta el trabajo de Célula 3 que no depende de Gold real, endpoints de Célula 4, MLflow
desplegado ni RAG de Carlos:

- agrega guardarraíles del agente (`src/agente/guardrails.py`) para validar alcance FARO, bloquear SQL
  de escritura/DDL, rechazar sentencias múltiples y forzar `LIMIT 1000`;
- agrega prompt de sistema importable (`src/agente/prompt.py`) con reglas de alcance, seguridad y
  auditoría;
- agrega scaffold ejecutable de ML-02 (`src/modelos/entrenar_ml02.py`) con backtesting temporal,
  `driver_dominante_proxy`, métricas F1/accuracy, recomendaciones por driver y SHAP opcional;
- agrega helper común de MLflow (`src/modelos/mlflow_utils.py`) con nombres canónicos de modelos;
- sincroniza `ML_Strategy` con el contrato vigente de `gold.features_escuela`;
- documenta el estado de ML-02, guardarraíles, ejecución local y preguntas de coordinación.

## IDs relacionados

- Historia: `US-302`, `US-303`, `US-304a`
- Requisito: `REQ-003`, `REQ-006`
- Otros: `DOC-ML02-CLASIFICACION-DRIVER`, `DOC-AGENTE-GUARDRAILS-US304A`, `DOC-C3-GUIA-EJECUCION`, `DOC-C3-PREGUNTAS-COORDINACION`

## ¿Cómo lo probaste?

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_agente_guardrails.py tests/test_agente_prompt.py tests/test_entrenar_ml02.py tests/test_mlflow_utils.py -q --tb=short
```

```text
25 passed in 7.71s
```

```powershell
.\.venv\Scripts\python.exe -m src.modelos.entrenar_ml02 --sin-mlflow
```

```text
Target usado: driver_dominante_proxy
F1 macro 0.7945 +/- 0.0241    Accuracy 0.8083
```

```powershell
python vault/_Meta/scripts/vault_lint.py .
```

```text
✅ Vault limpio.
```

## Avance entregado

- Historia `US-302`: [ ] cerrada por completo · [x] avance parcial
- Historia `US-303`: [ ] cerrada por completo · [x] avance parcial
- Historia `US-304a`: [ ] cerrada por completo · [x] avance parcial
- Fila actualizada en `vault/02_Requirements/Traceability_Matrix.md`: [ ] sí · [x] pendiente de coordinar con PM
- Lo que aún falta:
  - Confirmar etiqueta real `driver_dominante` o derivación canónica con Célula 1 / PM.
  - Confirmar contrato SHAP/API con Célula 4.
  - Confirmar `MLFLOW_TRACKING_URI` y Model Registry con Célula 5.
  - Integrar guardarraíles con RAG (US-304b) y endpoint real del agente.
  - Completar US-303 cuando existan ML-01/ML-02/ML-03 registrados.

## Definition of Filed

- [x] Tiene **ID** según `vault/_Meta/Naming_Conventions.md`
- [x] Vive en su **carpeta correcta**
- [x] Tiene **frontmatter** con `owner` y `status`
- [x] Enlaza `traces_up` y `traces_down`
- [x] Listado en el **`_index.md`** de su carpeta
- [ ] Fila actualizada en la matriz de trazabilidad

## Calidad

- [x] `python vault/_Meta/scripts/vault_lint.py .` da Vault limpio
- [x] Pruebas enfocadas en verde: 25 passed
- [ ] `pytest tests/ -q` completo pendiente de correr tras confirmar ambiente/deps globales del proyecto
- [ ] Commits en Conventional Commits con el ID

## Uso de IA

- [x] Usé IA — enlace al DevLog: `vault/_DevLog/2026-08-15-andres-gonzalez-trabajo-independiente-ml-agente.md`
- [ ] **Revisé línea por línea** el código generado
- [x] No pegué datos reales ni credenciales en prompts
- [ ] (Alternativa) No usé IA en este cambio

## Seguridad

- [x] No subo `.env`, credenciales ni llaves
- [x] No subo datos reales pesados (>5 MB)
- [x] No toqué esquema, seguridad ni CI/CD; solo módulos de C3, docs y tests

---

## Aprobación — compuerta única (PM · DEC-003)

**Aprobación obligatoria · Proceso + trazabilidad** — @edgarcoroneln (PM)
- [ ] CI verde · plantilla completa · IDs · DevLog · Definition of Filed · matriz actualizada

**Revisión técnica de apoyo (no bloqueante)** — Tech Lead del área
- [ ] Solicité revisión de C1/C4/C5 cuando respondan las preguntas de coordinación
