---
id: MOC-06-AUTO
title: "Automated Testing"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
tags: [moc, qa, automation]
---

# Pruebas Automáticas

> Unit, integración y E2E. Cada caso usa [[_Templates/Test_Case_template]].
> → [[06_Quality_Testing/_index]]

## Suites
| Suite | Nivel | Ruta en repo | Comando | Corre en |
|---|---|---|---|---|
| Partición temporal y fixture ML-01 | unit | `tests/test_particion_temporal.py` | `pytest tests/ -q` | CI |
| | integración | | | CI |
| | e2e | | | nightly |

## Registro de casos (TEST-###)
| TEST | Valida (REQ/US) | Tipo | Estado |
|---|---|---|---|
| TEST-001 | REQ-001 | unit | draft |
| TEST-002 | US-004 · REQ-007 | integración | implemented |
| [[06_Quality_Testing/Automated/Particion_Temporal_ML01\|TEST-003]] | US-311 · REQ-003 · AC-003.3 | unit | implemented |

`TEST-002` ejecuta `python3 _Meta/scripts/validate_pm_dashboard.py .` y verifica 87 US únicas,
21 personas, usuarios GitHub no duplicados, cobertura exacta de US por integrante, conteos de PR
válidos, ocho fuentes, rúbrica de 10 puntos, estados válidos, evidencia para Done y las once vistas
requeridas, incluidas **Equipo** y el plan seleccionable por célula/persona. También exige la fecha
canónica y los elementos visibles de la cuenta regresiva de entrega. Es determinista y no usa red.

`TEST-003` valida el fixture simulado de `gold.features_escuela` contra su contrato y, sobre todo,
que la partición de ML-01 sea **temporal y nunca aleatoria** (AC-003.3): incluye un caso que baraja
el fixture y exige que la verificación de fuga lo rechace. Determinista y sin red.

## Convenciones
- Nombrar tests por comportamiento, no por implementación.
- Tests deterministas; sin dependencias de red reales (usar mocks/emuladores).
- Todo bug corregido añade su test de regresión.
