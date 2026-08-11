---
project: "FARO"
date: "2026-08-09"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "claude-sonnet-4-6"
session_duration: "1h"
touches: ["US-301", "ADR-003", "DOC-ML-STRATEGY", "REQ-003"]
tags: [devlog, ml, celula-3, us301]
---

# DevLog — 2026-08-09 — US-301 Estrategia de modelado ML

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- Creado **ADR-003** (`03_Architecture/ADRs/ADR-003-ml-estrategia-modelado.md`): decisión de arquitectura de modelado ML. Cubre partición temporal walk-forward, backtesting por fold y manejo de cobertura parcial (D5/D6) con indicador binario + imputación de mediana. Registrado en `03_Architecture/ADRs/_index.md`.
- Creado **`15_ML_Models/ML_Strategy.md`**: protocolo completo de modelado con schema esperado de `gold.features_escuela`, tabla de umbrales de aceptación provisional, estructura del output de SHAP para ML-02 y convención de nombres en MLflow. Registrado en `15_ML_Models/_index.md`.
- Creado **`src/modelos/utils/temporal_split.py`**: función `walk_forward_splits()` que implementa la partición walk-forward de 1 ciclo sin fuga temporal.
- Creado **`tests/fixtures/generate_mock_features.py`**: generador de `features_escuela_mock.parquet` (550 filas, 11 ciclos, 50 escuelas × 4 entidades del scope). Permite trabajar sin `gold.features_escuela` real.
- Creado **`tests/test_ml_strategy.py`**: 5 tests (TEST-ML-001 no-fuga temporal, TEST-ML-002 sin ceros en drivers imputados, TEST-ML-003 schema completo, + entidades scope y sin nulos). **5/5 en verde**.
- Cherry-pick del fix de `vault_lint.py` (Windows) sobre esta rama para pasar el linter.

## 🤖 Sesión de IA
- **Agente / modelo:** GitHub Copilot / claude-sonnet-4-6
- **Archivos creados/modificados:** ADR-003, ML_Strategy.md, temporal_split.py, generate_mock_features.py, test_ml_strategy.py, _index.md (ADRs y 15_ML_Models)
- **Decisiones autónomas del agente:** Selección de walk-forward de 1 ciclo sobre split fijo; umbrales provisionales (MAE<15, F1≥0.60, Silhouette≥0.30); schema de features con indicadores binarios para D5/D6; estructura del JSON de SHAP.
- **Correcciones manuales:** Ninguna requerida.
- **Prompt inicial:** Avanzar en US-301 sin depender del equipo.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Fixture mock con datos sintéticos anonimizados (≤500 filas por ciclo)
- [x] 5 tests en verde (`pytest tests/test_ml_strategy.py -v`)
- [x] `vault_lint.py . → ✅ Vault limpio`
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- **`gold.features_escuela` real** (Diana, C1, US-104, S3): hasta que llegue, se trabaja contra el fixture mock. Los umbrales de aceptación se revisarán al recibirlo.
- **MLflow desplegado** (Luis, C5): necesario para US-303 (S4), no para US-301.
- PR pendiente de 2 aprobaciones (incluyendo Edgar como compuerta técnica).

## Próximos pasos
- Abrir PR en GitHub y solicitar revisión a Edgar.
- Iniciar diseño de US-304a (prompt del sistema del agente + guardarraíles) — no tiene dependencias de datos.
