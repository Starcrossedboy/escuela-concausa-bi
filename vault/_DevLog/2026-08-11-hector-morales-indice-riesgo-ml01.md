---
project: "FARO"
date: "2026-08-11"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "2h"
touches: ["US-311", "REQ-003", "TEST-004", "DOC-INDICE-RIESGO", "MOC-MLMODELS"]
tags: [devlog, celula-3, ml, ml-01]
---

# DevLog — 2026-08-11 — Índice de riesgo de ML-01: de variación de matrícula a [0,1] (US-311)

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Al revisar los merges recientes apareció un hueco de contrato que nadie había cubierto y que ya
tenía tres consumidores construyendo encima:

- ML-01 predice `target_variacion_matricula`: float **con signo y sin cota**.
- `src/api/schemas.py::PrediccionOut.indice_riesgo` (US-401, Christian) exige `Field(ge=0, le=1)`.
- [[vault/03_Architecture/Data_Model]] §4.5 lo declara como `valor` de `gold.predicciones`.
- [[vault/04_UX_Design/Screen_Specs]] cuenta "escuelas en riesgo" con `indice_riesgo >= 0.6`.

**La conversión entre ambas cosas no estaba definida en ningún lado.** Se define ahora en un solo
lugar para que la API, los cubos y FARO Web lean el mismo número.

Entregables:

- `src/modelos/riesgo.py` — sigmoide monótona decreciente fijada por dos anclas de negocio, con
  calibración parametrizable e inversa para interpretación.
- `tests/test_riesgo.py` — 16 casos ([[vault/15_ML_Models/Indice_Riesgo_ML01|TEST-004]]).
- [[vault/15_ML_Models/Indice_Riesgo_ML01]] — especificación, en `in_review` y con lo pendiente de
  ratificar explícito.

### La decisión

| Variación | `indice_riesgo` | Lectura |
|---|---|---|
| `0.00` | 0.30 | matrícula estable: riesgo bajo, no nulo |
| `-0.05` | 0.60 | umbral de "escuela en riesgo" de los tableros |

El ancla de `-5 %` **no se inventó**: se dedujo leyendo al revés el umbral `0.6` que
[[vault/04_UX_Design/Screen_Specs]] ya usaba. Las constantes de la sigmoide se derivan de las anclas al
importar, no están escritas a mano.

Se descartaron min-max (cambia si entra una escuela atípica; no comparable entre ciclos) y
percentil/ECDF (es relativo: si un año caen todas las escuelas, la mitad seguiría con riesgo bajo —
mala propiedad para alerta temprana).

El índice es capa de presentación: **no cambia el modelo, no cambia la métrica** (ML-01 sigue
reportando MAE/RMSE sobre la variación, AC-003.2) y no se entrena contra él.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `src/modelos/riesgo.py`, `tests/test_riesgo.py`,
  `vault/15_ML_Models/Indice_Riesgo_ML01.md`, `vault/15_ML_Models/_index.md`,
  `vault/06_Quality_Testing/Automated/_index.md`
- **Decisiones autónomas del agente:**
  - Elegir la sigmoide sobre min-max y percentil, con las razones documentadas en el §3 de la
    especificación.
  - Derivar el ancla de −5 % del umbral 0.6 ya existente en `Screen_Specs`, en vez de proponer un
    umbral nuevo.
  - Parametrizar la calibración en un `dataclass` congelado y derivar centro y escala de las anclas,
    para que recalibrar no implique tocar constantes.
  - Añadir una prueba que construye un `PrediccionOut` real de la Célula 4 con el valor calculado,
    convirtiendo el contrato entre células en algo que el CI verifica.
- **Correcciones manuales:** revisión línea por línea. Se detectaron y corrigieron dos cosas:
  1. Los ejemplos del docstring imprimían `np.float64(0.3)` en vez de `0.3`, porque `expit` devuelve
     `np.float64`. Corregidos y verificados con `pytest --doctest-modules` (el CI no corre doctests,
     pero un ejemplo incorrecto engaña a quien lo lea).
  2. Bug de formato preexistente en `vault/15_ML_Models/_index.md`: la sección `## Documentos` que
     introdujo el PR #12 quedó insertada entre los puntos 3 y 4 de "Reglas de modelado no
     negociables", partiendo la lista numerada. Se reubicó.
- **Prompt inicial:** validar el repositorio, actualizar la rama y avanzar con lo que no tuviera
  dependencias externas.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Tests agregados (TEST-004) — 16 casos; suite completa **50 passed, 4 skipped**
- [x] DevLog enlaza a los IDs afectados
- [x] `ruff check` limpio
- [x] `vault_lint.py` → ✅ Vault limpio · `validate_pm_dashboard.py` → ✅ TEST-002 válido
- [x] Sin datos reales: no se agregó ningún dataset

## Bloqueantes

- **`gold.features_escuela`** (C1, US-104, S3): la C1 sigue sin código. El entrenamiento real de
  ML-01 se hace contra el fixture hasta que llegue.
- **`docker-compose.yml`** (C5): sigue sin existir.
- **Anclas por ratificar:** las de este documento son una propuesta. Requieren visto bueno de Andrés
  (ADR-003) y de Manuel para el umbral de los tableros.

## Riesgos abiertos (no resueltos en esta sesión)

- **US-311 figura como `done`** en [[vault/12_Roadmap_Sprints/Execution_Status]] desde el cierre de
  Sprint 1, pero el PR #8 se entregó explícitamente como **avance parcial**: falta entrenar ML-01
  contra features reales, reportar MAE/RMSE y registrar en MLflow. La historia vence el 30 de agosto
  (S4). Pendiente de corregir con el PM.
- **Duplicación en `main`:** conviven `src/modelos/particion_temporal.py` (PR #8) y
  `src/modelos/utils/temporal_split.py` (PR #12), más sus respectivos generadores de fixture y
  suites. De las 5 pruebas de US-301, **4 hacen skip** porque su fixture `.parquet` cae en
  `.gitignore` y nunca se versionó; la única que corre no importa la función que dice probar.
  Pendiente de acordar la fusión con Andrés.

## Próximos pasos

- Ratificar las anclas con Andrés, Christian y Manuel.
- Corregir el estado de US-311 con el PM.
- Entrenar ML-01 contra el contrato canónico y registrarlo en MLflow (el grueso de US-311).
- Proponer la fusión de las dos implementaciones de partición temporal.
