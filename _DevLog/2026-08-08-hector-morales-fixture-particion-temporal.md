---
project: "FARO"
date: "2026-08-08"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "3h"
touches: ["US-311", "REQ-003", "TEST-003", "DOC-ONBOARD"]
tags: [devlog, celula-3, ml]
---

# DevLog — 2026-08-08 — Ambiente local, fixture de features y partición temporal (US-311)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

**1. Ambiente local de la Célula 3.** Python 3.11.15 en `.venv`, dependencias base, stack de ML
(scikit-learn 1.9.0, xgboost 3.2.0, mlflow 3.15.1, shap 0.51.0, chromadb 1.5.9,
sentence-transformers 5.7.0), `libomp` para xgboost en macOS, `.env` local y freeze en
`requirements/celula-3.txt`.

**2. Revisión del onboarding.** Al montar el ambiente aparecieron 6 defectos de documentación, 5 de
ellos con impacto en las 21 personas. Se reportaron al PM en un issue y **ya están corregidos** en
`main` (ver [[_DevLog/2026-08-07-edgar-remediacion-sprint1]]).

**3. Andamiaje de US-311.** Fixture simulado de `gold.features_escuela`, módulo de partición
temporal con backtesting, espejo del contrato Pydantic y 15 pruebas — las primeras del repositorio
([[06_Quality_Testing/Automated/Particion_Temporal_ML01|TEST-003]]).

Ensayo de punta a punta con backtesting sobre el fixture:

| Ventana | MAE | RMSE | MAE baseline |
|---|---|---|---|
| entrena 2019-2022 → prueba 2022-2023 | 0.0145 | 0.0184 | 0.0283 |
| entrena 2019-2023 → prueba 2023-2024 | 0.0157 | 0.0184 | 0.0295 |

> Métricas sobre **datos simulados**: sirven para confirmar que las piezas encajan, no como
> resultado de ML-01.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:**
  - `src/modelos/contrato.py`, `src/modelos/particion_temporal.py`, `src/modelos/generar_fixture.py`
  - `tests/conftest.py`, `tests/test_particion_temporal.py`, `tests/fixtures/features_escuela_mock.csv`
  - `06_Quality_Testing/Automated/Particion_Temporal_ML01.md` (+ su `_index`)
  - `requirements/celula-3.txt`
- **Decisiones autónomas del agente:**
  - Derivar la entidad de los 2 primeros caracteres del CCT en vez de pedir `cve_ent` a la Célula 1,
    porque el contrato no la incluye y US-312 exige error por entidad.
  - Expresar las restricciones `ge`/`le` con `Annotated` para que apliquen a la rama no nula de los
    drivers opcionales. Misma semántica que el contrato.
  - No imputar `SIN_DATO`: se deja `None` real y se usa un estimador que maneja nulos de forma
    nativa, conforme a la regla 4 de modelado.
  - Probabilidades de cobertura por driver distintas entre sí (D5 regional, D6 urbano) para que el
    fixture se parezca a la cobertura documentada.
- **Correcciones manuales:** revisión línea por línea de los tres módulos y las pruebas. Se detectó
  y corrigió un defecto del generador propuesto por la IA: redondeaba
  `indice_completitud_drivers` a 4 decimales y rompía la invariante `completitud == observados / 6`.
  La prueba lo atrapó; se corrigió el generador, no la prueba. También se descartó su primera
  versión de un wrapper de `vault_lint`, que pasaba varias rutas a un `main()` que sólo lee
  `sys.argv[1]` y habría linteado una sola carpeta en silencio.
- **Prompt inicial:** validar el onboarding del proyecto y preparar el ambiente local de la Célula 3.

## Seguridad / calidad

- [x] Sin secretos hardcodeados — `.env` local, confirmado ignorado por git
- [x] Tests agregados/actualizados (TEST-003) — 15 passed
- [x] DevLog enlaza a los IDs afectados
- [x] `ruff check` limpio en los archivos nuevos
- [x] `python _Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [x] Sin datos reales: el fixture es 100 % sintético, 400 filas, 44 KB

## Bloqueantes

- **`gold.features_escuela`** (Célula 1, Diana Alvarez): sin el contrato versionado,
  `src/modelos/contrato.py` es un espejo temporal. No bloquea: se avanza con el fixture conforme a
  la regla de desbloqueo del plan.
- **MLflow desplegado** (Célula 5): pendiente. Además, **MLflow 3.15 deprecó el file store** —
  `mlruns/` ya no funciona y exige backend de base de datos (`sqlite:///mlflow.db` en local,
  Postgres en prod). `mlflow.db` **no está en `.gitignore`**, que sí cubre `airflow.db` y
  `superset.db`. Reportado al PM como adenda; afecta a US-303 y al despliegue de la Célula 5.
- **`docker-compose.yml`** (Célula 5): sin él, el paso 4.4 del onboarding sigue inejecutable.

## Próximos pasos

- PR de este andamiaje a revisión de Andrés González Habib (Tech Lead C3).
- Compartir `particion_temporal.py` con Andrés **antes de US-301** (S3, 17–23 ago), para que el
  protocolo de validación se escriba sobre lo que ya existe.
- Acordar con Christian Ruiz (C4) el contrato de request/response de inferencia: con FARO Web
  (US-207) hay ahora dos consumidores de la salida de ML-01, no uno.
- Entrenar ML-01 en serio hasta tener el contrato real o el diseño de US-301: afinar contra
  distribuciones simuladas es tiempo perdido.
