---
project: "FARO"
date: "2026-08-29"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "45m"
touches: ["US-303", "REQ-003", "AC-003.4", "ML-01", "ML-02", "ML-03"]
tags: [devlog, celula-3, mlflow, registry, e2e]
---

# DevLog — 2026-08-29 — E2E local del Registry con tres modelos

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se entrenaron ML-01, ML-02 y ML-03 sobre `tests/fixtures/features_escuela_mock.csv`.
- Los tres modelos se registraron en un backend temporal SQLite con MLflow 3.15.1.
- `verificar_modelos_registrados()` confirmó una versión para cada nombre canónico.
- No se persistieron bases, artefactos ni datos fuera del directorio temporal.

## Resultado

| Modelo | Versión verificada |
|---|---:|
| `ML01_RegresionMatricula` | 1 |
| `ML02_DriverClasificador` | 1 |
| `ML03_ClusteringEscuelas` | 1 |

ML-03 conservó el resultado ya reportado: Silhouette 0.1086 y 107 de 400 filas entrenadas bajo
la política provisional `casos_completos`. La versión registrada no se promueve a producción.

## Alcance del criterio

La prueba cubre localmente el registro versionado exigido por AC-003.4. Aún falta repetirla contra
el servidor MLflow compartido, cuya configuración de artefactos depende de Célula 5, y completar
la exposición vía API con Célula 4 antes de cerrar US-303.

## Seguridad y calidad

- [x] MLflow 3.15.1.
- [x] Backend y artefactos temporales fuera del repositorio.
- [x] Sin `.env`, credenciales ni datos reales.
- [x] Verificación conjunta de los tres nombres canónicos.
