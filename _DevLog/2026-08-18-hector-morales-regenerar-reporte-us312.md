---
project: "FARO"
date: "2026-08-18"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["US-312", "US-301", "REQ-003", "TEST-007", "DOC-EVALUACION-MODELOS"]
tags: [devlog, celula-3, qa, metricas]
---

# DevLog — 2026-08-18 — Regeneración del reporte de US-312 y guarda anti-desincronización

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

A petición de Andrés González Habib: regenerar
[[06_Quality_Testing/Automated/Evaluacion_Modelos]] para incorporar los umbrales que alineó en
**US-301** (PR #46), donde ML-01 pasó de `MAE < 15 alumnos` a **puntos porcentuales**
(`MAE < 0.03`, `RMSE < 0.05`), en la misma unidad proporcional que `target_variacion_matricula`.

El §5 del reporte pasó de declarar los umbrales como **no comparables** a reflejar los nuevos, y
ahora explica que `0.0141` equivale a 1.41 puntos porcentuales de error medio.

### El problema de fondo, y la guarda que faltaba

El PR #46 cambia `src/modelos/evaluar.py` —el generador— pero **no regenera el documento**. El
reporte se genera desde el código precisamente para que las cifras del vault no se desincronicen
del pipeline (AC-003.2 pide métricas *reproducibles*), pero **nada obligaba a regenerarlo**: quedó
dependiendo de que alguien se acordara.

Se agrega `test_el_reporte_publicado_esta_sincronizado`, que compara el documento versionado contra
una generación fresca. Cambiar el generador y olvidar `python -m src.modelos.evaluar` ahora **rompe
el CI** en vez de dejar cifras obsoletas publicadas en el vault.

Comprobado que la guarda sirve: al alterar una línea del reporte a mano, la prueba falla; al
restaurarla, pasa.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `06_Quality_Testing/Automated/Evaluacion_Modelos.md` (regenerado),
  `tests/test_evaluar.py`
- **Decisiones autónomas del agente:**
  - Agregar la guarda en vez de sólo regenerar. Regenerar resuelve hoy; la guarda evita que
    vuelva a pasar, que es el problema real.
  - Resolver la ruta del reporte desde `__file__` y no desde el directorio de trabajo, para que la
    prueba no dependa de dónde se invoque pytest.
  - Ramificar sobre la rama del PR #46 en vez de sobre `main`, porque los umbrales nuevos viven
    ahí: regenerar desde `main` habría producido la redacción vieja.
- **Correcciones manuales:** revisión línea por línea. Se verificó la guarda alterando el reporte a
  propósito para confirmar que falla, en vez de asumir que la aserción funcionaba.
- **Prompt inicial:** validar el repositorio y atender la petición de Andrés de regenerar el
  reporte de US-312.

## Higiene local

La suite fallaba al colectar `test_api_contract.py` y `test_auth_jwt.py` con
`ModuleNotFoundError: No module named 'jose'`. **No era un defecto del repositorio**:
`python-jose[cryptography]` sí está declarado en `requirements.txt` desde US-402 (Christian Ruiz);
mi ambiente virtual estaba desactualizado. Se resolvió con `pip install -r requirements.txt`.

Es exactamente el caso de **BUG-003**, ahora del otro lado: conviene reinstalar dependencias cuando
otra célula agrega las suyas.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Suite completa **172 passed, 4 skipped** · `vault_lint` ✅ · tablero PM ✅ · `ruff` limpio
- [x] Sin datos reales: el reporte sigue advirtiendo que las métricas son sintéticas

## Dependencia de orden

Esta rama parte del PR **#46** (US-301, Andrés), que está aprobado pero **aún sin mergear**. Debe
entrar **después** de él; si se mergea antes, arrastraría sus commits.

## Próximos pasos

- **BLOCK-001 sigue abierto pese al PR #45.** La alineación de versiones (2.8.0 → 3.15.1) era
  necesaria pero no suficiente: el servidor arranca con `--default-artifact-root /mlflow/artifacts`
  y **sin `--serve-artifacts`**, así que un cliente en el host falla con
  `OSError: Read-only file system: '/mlflow'`. Verificado que agregando `--serve-artifacts` y
  `--artifacts-destination` el modelo sí llega al registry y se puede recuperar con
  `mlflow.sklearn.load_model("models:/ML01_RegresionMatricula/1")`. Falta reportarlo a Célula 5.
- Conectar ML-02 a `construir_recomendaciones()` para cerrar `gold.recomendaciones`.
