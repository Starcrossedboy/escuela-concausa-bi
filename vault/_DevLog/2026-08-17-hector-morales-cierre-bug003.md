---
project: "FARO"
date: "2026-08-17"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["BUG-003", "BUG-004", "US-311", "REQ-003"]
tags: [devlog, celula-3, qa, bug]
---

# DevLog — 2026-08-17 — Cierre de BUG-003 y corrección de alcance en BUG-004

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Diana Alvarez preguntó si el fix de **BUG-003** (`sklearn` no instalado, `ModuleNotFoundError` al
colectar pytest) correspondía a la Célula 3, dado que está registrado contra **US-311** y toca
`src/modelos/`, fuera de su alcance de código.

Se investigó y **el fix ya estaba en `main` desde antes de que el bug se registrara**.

### Evidencia

| Hecho | Dato |
|---|---|
| `scikit-learn>=1.5` en `requirements.txt` | commit `5f0f04a`, **2026-08-13**, PR #28 |
| BUG-003 registrado | commit `78ede8c`, **2026-08-17** — cuatro días después |
| CI verde en `main` | el job "Calidad de codigo y vault" instala **sólo** `requirements.txt` y corre `pytest`; si faltara `sklearn`, la colección fallaría ahí |
| Cubre los dos archivos del reporte | `entrenar_ml02.py` sólo requiere `sklearn` en imports de nivel superior; `shap` y `mlflow` son diferidos |

**Conclusión:** no es un defecto del repositorio, sino un ambiente virtual creado antes del 13 de
agosto que no reinstaló dependencias. Se cierra como `not_a_bug` con sección de detalle,
diagnóstico y remediación (`pip install -r requirements.txt`).

Se dejó explícito en el registro que **no había fix de código pendiente** y que la decisión de no
tocar `src/modelos/` fuera del alcance propio fue la correcta.

### Corrección adicional: BUG-004 mal asignado

BUG-004 (imagen de Superset sin `psycopg2`) estaba etiquetado como **C3** en tres lugares, uno de
ellos contradictorio consigo mismo: *"Owner: Célula 3 (DevOps/Cloud)"*. DevOps/Cloud es la
**Célula 5**, Edward Ruiz pertenece a la Célula 5 según el directorio, y US-522c cuelga de REQ-005
(Deploy GCP). Se corrigieron las tres referencias a **C5**.

Sin la corrección, el bug quedaba enrutado a la célula equivocada.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `vault/06_Quality_Testing/Bug_Register.md`
- **Decisiones autónomas del agente:**
  - Cerrar como `not_a_bug` en vez de `fixed`: el repositorio nunca tuvo el defecto en el momento
    del reporte, y la distinción importa para no atribuir un arreglo inexistente.
  - Corregir el etiquetado de BUG-004 al detectar que enrutaba trabajo de la C5 hacia la C3.
- **Correcciones manuales:** la primera pasada sólo corrigió una de las tres referencias a C3 en
  BUG-004; se revisó el archivo completo y se encontraron las otras dos, incluida la línea de
  `Owner`. Se verificó contra el directorio del equipo y el catálogo de US antes de reasignar.
- **Prompt inicial:** validar si BUG-003 estaba dentro del alcance propio y qué correspondía hacer.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] `vault_lint.py` ✅ · `validate_pm_dashboard.py` ✅ · **141 passed, 4 skipped**
- [x] Sólo se tocó documentación de QA; ningún cambio de código

## Próximos pasos

- US-312 es la única de mis tres historias sin arrancar.
- Sigue abierto el bloqueo de MLflow (servidor 2.8.0 vs cliente 3.15.1) y la duplicación del
  catálogo de recomendaciones en tres módulos.
