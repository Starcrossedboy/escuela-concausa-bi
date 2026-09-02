---
project: "FARO"
date: "2026-08-16"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "2h"
touches: ["US-311", "US-313", "REQ-003", "DOC-ML01-ENTRENAMIENTO", "US-502"]
tags: [devlog, celula-3, ml, mlflow, infraestructura]
---

# DevLog — 2026-08-16 — ML-01 contra el MLflow desplegado: incompatibilidad de versiones

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Tras el PR #34 (Luis Téllez, US-502) el `docker-compose.yml` ya trae MLflow, Airflow, Superset y
ChromaDB. Se intentó mover el registro de ML-01 del SQLite local al servidor desplegado.

**No funciona, y el modo de falla es silencioso.**

### El hallazgo

| | |
|---|---|
| Servidor | **MLflow 2.8.0** (`docker/mlflow.Dockerfile`) |
| Cliente C3 | **MLflow 3.15.1** (`requirements/celula-3.txt`) |

Con versiones mayores distintas, `mlflow.sklearn.log_model()` llama
`/api/2.0/mlflow/logged-models` —endpoint que no existe en 2.x— y recibe **404**.

Lo peligroso es el síntoma: **las métricas y los parámetros sí se registran**. La corrida aparece
en la UI y todo se ve bien, pero `list_artifacts()` devuelve `[]` y `search_registered_models()`
devuelve `[]`. **AC-003.4 ("los 3 modelos registrados en MLflow con versión") no se cumple, y nada
lo delata** salvo ir a buscar el artefacto.

Reproducido contra el servicio real: 4 corridas creadas, métricas correctas, cero artefactos, cero
modelos en el registry.

### Mitigación entregada

`src/modelos/mlflow_utils.py` (módulo compartido de la C3, de US-303) gana dos funciones:

- `version_del_servidor()` — consulta `GET /version`, que el servidor expone en texto plano.
- `verificar_compatibilidad()` — falla **antes de entrenar** con un mensaje que explica el modo de
  falla y **nombra los dos archivos a alinear**.

`entrenar_ml01.py` la invoca al inicio de `registrar_en_mlflow()`. El 404 tardío y confuso se
convierte en:

```
RuntimeError: MLflow incompatible: servidor 2.8.0 vs cliente 3.15.1 en http://localhost:5001.
Con versiones mayores distintas las métricas sí se registran, pero los MODELOS no: `log_model()`
falla con 404 y el registry queda vacío (AC-003.4 sin cumplir).
Alinea las versiones: el servidor lo define `docker/mlflow.Dockerfile` (Célula 5) y el cliente
`requirements/celula-3.txt`.
```

**Esto no arregla el problema, sólo lo hace evidente.** La corrección de fondo es de la Célula 5.
Le va a pasar igual a Andrés (US-302/US-303) y a Estefany (US-321).

### Otro detalle de configuración

`.env.example` documenta `MLFLOW_TRACKING_URI=http://mlflow:5000`, que es el nombre **interno de la
red de Docker** y sirve para los contenedores. Desde la máquina del desarrollador el servicio está
publicado en **`http://localhost:5001`** (mapeo `127.0.0.1:5001:5000`). Quien corra el
entrenamiento desde su host —que es como trabaja la C3— necesita el segundo, y no está documentado.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `src/modelos/mlflow_utils.py`, `src/modelos/entrenar_ml01.py`,
  `tests/test_mlflow_utils.py`, `vault/15_ML_Models/ML01_Entrenamiento.md`
- **Decisiones autónomas del agente:**
  - Poner la verificación en `mlflow_utils.py` —el módulo compartido de la C3— en vez de crear uno
    propio, para no repetir la duplicación que ya arrastra la célula.
  - Que un servidor inalcanzable **no** bloquee: si `/version` no responde, se deja pasar y manda el
    error real del entrenamiento, en vez de inventar una incompatibilidad.
  - Comparar sólo la versión mayor, no la exacta.
- **Correcciones manuales:** revisión línea por línea. Ruff detectó un `import pytest` duplicado en
  el bloque de pruebas agregado; corregido. Se verificó a mano contra el servidor real que el
  artefacto y el registry quedaban vacíos, en vez de asumirlo por el 404.
- **Prompt inicial:** actualizar la rama tras los merges recientes y apuntar el entrenamiento al
  MLflow desplegado.

## Higiene local

Se regeneró el `.env` local desde el `.env.example` nuevo (que cambió bastante con US-502).
Los secretos se generaron escribiéndolos **directo al archivo**, sin imprimirlos en la sesión de IA,
conforme a `vault/07_Security/Secrets_Policy.md`. El respaldo temporal se eliminó.

## Seguridad / calidad

- [x] Sin secretos hardcodeados ni impresos en la sesión
- [x] Pruebas agregadas — 5 casos nuevos; suite completa **141 passed, 4 skipped**
- [x] `ruff` limpio en los archivos propios
- [x] `vault_lint.py` ✅ · `validate_pm_dashboard.py` ✅
- [x] Contenedores levantados sólo para verificar y bajados al terminar

## Bloqueantes

1. **MLflow 2.8.0 vs 3.15.1** (Célula 5) — bloquea AC-003.4 para toda la Célula 3.
2. **`gold.features_escuela`** (US-104, Diana, vence **23 ago**).
3. **Datos reales del Formato 911**: en el repositorio de datos.gob.mx sólo está el ciclo
   2024-2025; los ciclos anteriores responden 503. Sin al menos dos ciclos **no hay
   `target_variacion_matricula` que predecir**. Es el riesgo mayor y sigue sin dueño asignado.

## Próximos pasos

- Escalar a Luis Téllez la alineación de versiones de MLflow.
- Consolidar el catálogo de recomendaciones, hoy en tres módulos y con acentos distintos en uno.
- Conectar `predecir_driver()` de ML-02 a `construir_recomendaciones()` para cerrar US-313.
- US-312 sigue siendo la única de mis historias sin arrancar.
