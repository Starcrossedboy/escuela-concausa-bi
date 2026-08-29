---
project: "FARO"
date: "2026-08-29"
author_human: "Estefany Lucero Hernández Loredo"
agent: "Codex"
model: "GPT-5.6"
session_duration: "~2h"
touches: ["US-322", "US-325", "REQ-003"]
tags: [devlog, celula-3, eda, cobertura, municipio]
---

# DevLog — 2026-08-29 — Diagnóstico territorial de features

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se amplió `src/modelos/analizar_features.py` con validación de `cve_mun`, cobertura y
  completitud por municipio, y una medición de la brecha de `SIN_DATO` entre municipios.
- `cve_mun` se agregó a las columnas no entrenables de ML-03: sirve para auditoría territorial,
  no como distancia numérica en KMeans.
- Se agregaron ocho casos de prueba, incluidos cero inicial, formato inválido, entidad
  inconsistente, reconciliación contra totales y dispersión municipal.
- Se registraron los dos documentos nuevos en el MOC de modelos y se actualizó el avance del plan.

## Decisión de entrega

US-322/US-325 se entrega en un PR separado de US-321. El diagnóstico es revisable sin fijar una
política de imputación todavía pendiente; el entrenamiento de KMeans tendrá su propia rama, pruebas
y aprobación. Esta separación evita que una dependencia de modelado bloquee evidencia ya completa
de calidad y cobertura.

El cambio de esquema que publica `cve_mun` permanece en la rama de Diana Alvarez Varela. Este PR no
copia ni mezcla archivos de Célula 1: acepta la columna cuando está disponible y falla claramente
cuando falta.

## Seguridad / calidad

- [x] Datos municipales de pruebas 100% sintéticos y asignados explícitamente.
- [x] No se infiere municipio desde el CCT ni se convierte `SIN_DATO` en cero.
- [x] `pytest tests/test_analizar_features.py -q`: 17 passed.
- [x] Ruff limpio en módulo y pruebas.
- [x] `vault_lint.py`: Vault limpio.
- [ ] Suite completa: no recolectó en el runtime aislado por dependencias no instaladas de otras
  células (`fastapi`, `sqlalchemy`, `sklearn`, `requests`, entre otras); CI debe ejecutar el gate.

## Pendientes

- Integrar el PR de Célula 1 que expone `cve_mun` y reconstruir Gold.
- Ejecutar el diagnóstico sobre `gold.features_escuela` real antes de declarar US-325 `done`.
- D5 conserva cobertura parcial hasta que exista el crosswalk `region_hidrologica → cve_mun`.
- US-321 se desarrolla en un PR separado; la imputación definitiva espera ratificación del
  fallback para municipios sin observaciones suficientes.

## Uso de IA

Codex ayudó a implementar y probar el diagnóstico municipal, actualizar documentación y preparar
la separación de PR. Estefany debe revisar línea por línea el código antes del merge.
