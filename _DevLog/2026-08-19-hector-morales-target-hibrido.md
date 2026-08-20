---
project: "FARO"
date: "2026-08-19"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "3h"
touches: ["US-311", "US-313", "DEC-005", "RISK-007", "TEST-009", "DOC-TARGET-HIBRIDO", "BLOCK-001"]
tags: [devlog, celula-3, ml, ml-01, dec-005]
---

# DevLog — 2026-08-19 — Target híbrido de dos niveles (DEC-005) y corrección del estado de MLflow

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Edgar registró **RISK-007** (el Formato 911 sólo tiene el ciclo 2024-2025) y su mitigación,
**DEC-005**, que dice explícitamente *"Toca US-104, US-311, US-313"*. Esta sesión implementa la
parte que corresponde a la Célula 3.

## 1. Corrección del estado de MLflow en [[15_ML_Models/ML01_Entrenamiento]]

El documento seguía diciendo que el servidor corre **2.8.0**, pero Luis Téllez lo alineó a
**3.15.1** en el PR #45. Se reescribió el bloque con el estado real: la primera causa está resuelta;
**BLOCK-001 sigue abierto por una segunda causa** —el servicio arranca sin `--serve-artifacts` y con
`--default-artifact-root` apuntando a una ruta del contenedor—, con el fix ya probado y pendiente de
que lo aplique la Célula 5.

## 2. Implementación de DEC-005

### El hueco que había que resolver

DEC-005 pide el objetivo a nivel `municipio × nivel`, pero **`gold.features_escuela` no expone
`cve_mun` ni `nivel`**: el contrato §5.3 sólo trae `cct`, los seis drivers, sus banderas, la
completitud y el target.

Ambas columnas viven en **`gold.dim_escuela`** (US-103, ya en `main`), así que la agregación se
resuelve con un **join a la dimensión**. No hace falta cambiar el contrato de la Célula 1 ni pedirle
columnas nuevas.

### Lo entregado

- `src/modelos/target_hibrido.py` — agregación a `municipio × nivel × ciclo` y unión del objetivo.
- `src/modelos/generar_fixture_dim.py` — fixture determinista de `dim_escuela`, consistente con el
  de features (mismos CCT, misma entidad).
- `tests/test_target_hibrido.py` — 18 casos ([[15_ML_Models/Target_Hibrido_DEC005|TEST-009]]).
- [[15_ML_Models/Target_Hibrido_DEC005]] — documento de la implementación.

### Decisiones

**Un driver agregado es el promedio de las escuelas que sí tienen dato.** Una escuela sin medición
de aire no arrastra el promedio de su municipio hacia cero: queda fuera del cálculo. Es la regla de
cobertura parcial aplicada a la agregación, y es donde más fácil se rompe sin darse cuenta.

**La cobertura pasa de enum a fracción.** A nivel agregado, «OK / SIN_DATO» pierde información: no
es lo mismo un municipio donde mide una estación de cada diez escuelas que uno donde miden todas. Se
conserva **además** el enum original para no romper a quien sólo entienda el contrato §5.3.

**El objetivo se recibe, no se calcula.** La serie SNIEE es de la Célula 1 y el gate es el 30 de
agosto; `unir_target()` la toma como argumento, igual que hicimos con el driver de ML-02 en US-313.

**Un grupo sin objetivo queda fuera, no se rellena.** Entrenar contra un cero inventado es peor que
tener menos filas.

### Ensayo sobre el fixture

```
entrada: 400 filas escuela×ciclo · 80 escuelas
salida : 230 filas municipio×nivel×ciclo · 46 grupos · 5 ciclos
cobertura de dimensión: 100.0%
```

Los cinco ciclos se conservan, que es lo único que hace validable el objetivo con partición
temporal — el propósito entero de DEC-005.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `src/modelos/target_hibrido.py`,
  `src/modelos/generar_fixture_dim.py`, `tests/test_target_hibrido.py`,
  `tests/fixtures/dim_escuela_mock.csv`, `15_ML_Models/Target_Hibrido_DEC005.md`,
  `15_ML_Models/ML01_Entrenamiento.md`, `15_ML_Models/_index.md`,
  `06_Quality_Testing/Automated/_index.md`
- **Decisiones autónomas del agente:**
  - Resolver el grano faltante con un join a `dim_escuela` en lugar de pedir columnas nuevas al
    contrato de la Célula 1.
  - Emitir la cobertura como fracción y conservar el enum, en vez de sustituirlo.
  - Devolver un `ResumenAgregacion` que reporta las escuelas sin dimensión: agregar es donde se
    pierden filas en silencio.
  - Validar el merge del objetivo como `one_to_one`, para que una serie con llaves duplicadas falle
    en vez de multiplicar filas.
- **Correcciones manuales:** revisión línea por línea. Una prueba propia estaba mal construida:
  forzaba el mismo `cve_mun` en toda la serie para simular «no cruza», lo que creaba llaves
  duplicadas y disparaba la validación `one_to_one` antes que la comprobación de cruce. Se
  reescribió con municipios inexistentes pero únicos, y se **añadió** un caso aparte para las llaves
  duplicadas, que resultó ser un escenario que valía la pena fijar.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Pruebas agregadas (TEST-009) — 18 casos; suite completa **194 passed, 4 skipped**
- [x] `ruff` limpio en los archivos propios · `vault_lint` ✅
- [x] Fixture de `dim_escuela` sintético, determinista y versionable (80 filas)

## Defectos de gobernanza detectados (no son míos de arreglar)

1. **Colisión de ID en DEC-005.** El `Decision_Log` tiene un único DEC-005, el del target híbrido
   (2026-08-19). Pero **DEC-005 ya se venía usando** para la decisión de `indice_riesgo` como
   columna de `gold.predicciones` (2026-08-14), y así está referenciado en
   `src/modelos/publicar_gold.py`, [[15_ML_Models/Publicacion_Gold]], el registro de TEST-006 y tres
   DevLogs. La regla del vault dice que **los IDs nunca se reciclan**: hoy esas referencias apuntan
   a la decisión equivocada.
2. **Filas duplicadas en la matriz de trazabilidad.** REQ-002 y REQ-003 aparecen **dos veces cada
   uno**, con contenido distinto: la copia vieja de REQ-003 no incluye TEST-006 ni TEST-007, y la de
   REQ-002 dice `📋 Planeado` mientras la otra dice `🟡 En progreso`. Es efecto secundario del
   `merge=union` de `.gitattributes`: resuelve conflictos concatenando, y en una tabla eso duplica
   filas en vez de fusionarlas. Va a empeorar con cada merge.

## Pendiente

- **La serie SNIEE** (Célula 1, gate 30 de agosto). Sin ella el objetivo sigue simulado.
- **Grano de `gold.predicciones`:** la tabla es `cct × ciclo × modelo`. Si ML-01 predice por
  `municipio × nivel`, hay que decidir si la predicción se reparte a las escuelas del grupo o si la
  tabla admite ambos granos. **Toca coordinar con Diana y Christian.**
- **BLOCK-001** sigue abierto por el artifact root.
