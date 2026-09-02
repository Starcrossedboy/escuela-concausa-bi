---
project: "FARO"
date: "2026-08-19"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["US-104", "US-311", "REQ-001", "REQ-003", "TEST-008", "MOC-06-AUTO"]
tags: [devlog, celula-3, contrato, qa]
---

# DevLog — 2026-08-19 — Guarda del contrato `gold.features_escuela` (C1 ↔ C3)

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Diana Alvarez entregó **US-103 y US-104** (PR #48): el esquema estrella Gold y
`gold.features_escuela` con drivers reales D1–D4.

**Lo primero fue verificar el contrato, no asumirlo.** El resultado es bueno: las 10 columnas que
declara en `dbt/models/gold/_gold__models.yml` existen en el espejo Pydantic
`src/modelos/contrato.py`, y el SQL produce los 6 drivers, las 6 banderas de cobertura,
`indice_completitud_drivers` y `target_variacion_matricula` con los mismos nombres del §5.3.
**El pipeline de ML-01 puede consumirlo sin cambios.**

Su modelo marca D5 (agua) y D6 (aire) como `SIN_DATO` explícito hasta que US-105 entregue el join
espacial de CONAGUA/SINAICA — coherente con la regla de cobertura parcial.

### La guarda

El `Data_Model` §5.3 dice que cambiar una columna es cambiar el contrato y exige avisar a la C3; el
propio `_gold__models.yml` lo repite. Era un acuerdo escrito que **nada hacía cumplir**.

`tests/test_contrato_features.py` (TEST-008) lo convierte en verificación automática:

1. Toda columna declarada por la C1 existe en `FeaturesEscuela`.
2. Cada campo del espejo aparece en el SQL que construye la tabla (detecta renombres).
3. Cada driver conserva su bandera de cobertura.
4. El modelo usa el centinela `SIN_DATO`.

Comprobado que sirve: renombrando `d1_pobreza` a `d1_rezago_social` en el SQL —justo el nombre que
divergía en el `ML_Strategy` antes de alinearse— la prueba falla; al restaurar, pasa.

Se leen los archivos de dbt **como texto, sin `yaml` ni `dbt`**: el CI instala sólo
`requirements.txt`, y una prueba que dependa de paquetes ausentes no correría — que es exactamente
el defecto de BUG-003 y el que yo mismo cometí en el PR #41.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `tests/test_contrato_features.py`,
  `vault/06_Quality_Testing/Automated/_index.md`
- **Decisiones autónomas del agente:**
  - Verificar la correspondencia antes de celebrar la entrega de US-104.
  - Parsear con expresiones regulares en vez de `yaml`, para que la prueba corra en el CI.
  - Recortar el bloque del modelo en el `schema.yml` para no arrastrar columnas de otros modelos.
  - Marcar las pruebas con `skipif` sobre la existencia de los archivos de dbt: si la C1
    reorganiza su carpeta, la prueba se salta con un motivo claro en vez de romper por ruta.
- **Correcciones manuales:** revisión línea por línea. Se comprobó la guarda provocando un renombre
  real en el SQL, en vez de asumir que la aserción funcionaba.
- **Prompt inicial:** validar el repositorio tras un día de mucha actividad y ver qué se podía
  atender de inmediato.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Pruebas agregadas (TEST-008) — 4 casos
- [x] `ruff` limpio · `vault_lint` ✅
- [x] Sin dependencias nuevas: sólo `re` y `pathlib`

## Bloqueantes

- **BLOCK-001 sigue abierto pese al PR #45.** Alinear versiones era necesario pero no suficiente: el
  servidor corre sin `--serve-artifacts` y con `--default-artifact-root` apuntando a una ruta del
  contenedor, así que un cliente en el host falla con `Read-only file system: '/mlflow'`. Verificado
  que con `--serve-artifacts` + `--artifacts-destination` el modelo sí llega al registry y se
  recupera con `load_model("models:/ML01_RegresionMatricula/1")`. Reportado a la C5 en el PR #50.
- **Datos reales del Formato 911:** sigue disponible sólo el ciclo 2024-2025. Sin dos ciclos no hay
  `target_variacion_matricula` que predecir, por más que la tabla ya exista.

## Próximos pasos

- Correr el pipeline de ML-01 contra `gold.features_escuela` real en cuanto haya datos cargados.
- Conectar ML-02 a `construir_recomendaciones()` para cerrar `gold.recomendaciones`.
