---
project: "FARO"
date: "2026-08-28"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~5h"
touches: ["DS-01", "US-113"]
tags: [devlog, bronze, gold, dbt, ingesta, formato911, us113, dim_driver]
---

# DS-01 — Cargador real de Formato 911 y validación de `US-113` contra datos reales

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

**1. Cargador real de producción para `bronze.formato911_2024_2025`.** Hasta ahora esta tabla
solo se podía llenar con `cargar_bronze_fixture.py` (uso exclusivo de fixtures de desarrollo,
≤500 filas). Escribí `src/ingesta/cargar_bronze_formato911_real.py`, que reutiliza la lógica de
INSERT ya probada de `cargar_fixture()` pero parte del CSV real completo. El archivo real es
grano CCT × turno; la tabla espera una fila por (cct, ciclo), así que el script **suma**
alumnos/docentes/grupos por CCT antes de cargar (mismo principio que ya aplica
`silver.matricula_historica` para la distribución histórica).

**2. Carga de 4 ciclos reales**, descargados a mano de las URLs oficiales verificadas en
`DS-01_Formato_911.md` §9: 2021-2022, 2022-2023, 2023-2024, 2024-2025.

**3. Validación de la estrella completa contra Postgres real** — Bronze → Silver → Gold
(`fact_escuela_ciclo`, `features_escuela`) y los 8 cubos Gold materializados, vía `dbt build`
con los 4 ciclos reales ya cargados. **149/149 tests en verde.** Esto responde directamente al
gate que `US-113` tiene documentado en `PLAN_MAESTRO.md` ("in_review y no done: ningún cubo se
ha materializado contra la base real... Valida: Diana Alvarez (TL C1) corriendo
`dbt run --select gold`") — la historia es de Deni Garrido Fragoso, esto es la evidencia que
esperaba de mi parte, no un cierre unilateral de su historia.

**4. Intento de reentrenamiento real de ML-01/ML-02** vía `publicar_gold.py` (pipeline
documentado en `06_Quality_Testing/Guion_E2E_Verificacion_4.md`, de Héctor Morales). La corrida
estándar funcionó igual que documentada (80 filas en `gold.predicciones`/`gold.recomendaciones`,
grano escuela). Un intento adicional de backtesting real (`--ventanas 1`, ya con suficientes
ciclos reales para cumplir la ventana mínima) encontró un error interno de scikit-learn
(`HistGradientBoostingRegressor`: `window shape cannot be larger than input array shape`),
probablemente relacionado con `d5_agua` 100% nulo (CONAGUA/DS-06 aún no ingerida, US-121a/122a
de Emilio Galnares, sin avance). **No se resolvió esta noche** — es código de entrenamiento de
Héctor (C3), se le deja marcado para que lo revise él.

**5. Bug real encontrado y corregido en el propio cargador**, antes de subir el PR: la primera
versión convertía valores no numéricos de `insc_t`/`tot_doc`/`gpos_t` en `0` (`.fillna(0)`),
violando el principio del proyecto de "SIN_DATO explícito, nunca cero ni nulo silencioso" — un
dato sucio se habría visto como una escuela con matrícula cero. Se corrigió para fallar
explícito (`_coercer_metrica_o_fallar`) y se agregaron 14 pruebas nuevas, incluida la que
reproduce el bug corregido.

**6. Hallazgo aparte, de otra célula, solo confirmado no resuelto por mí:** el mismo día,
Manuel Serranía (PR #100) reportó que `gold.dim_driver` está desincronizado en Postgres locales
(nombres largos de un mock vs. nombres cortos del seed canónico), bloqueando el sync de DB-05/08
de Monserrat (`US-213`). Confirmé en mi propio Postgres que `dbt seed --select dim_driver
--full-refresh` corrige el problema y coincide exactamente con el seed canónico
(`dbt/seeds/dim_driver.csv`). La decisión de catálogo y la re-materialización compartida quedan
pendientes de comunicar a Manuel/Deni/Monserrat — no forman parte de este PR.

## Cómo se probó

```
python -m pytest tests/test_cargar_bronze_formato911_real.py -v   # 14/14 passed
python -m pytest tests/ -q                                          # suite completa, sin fallos nuevos
python _Meta/scripts/vault_lint.py .                                 # Vault limpio
cd dbt && dbt build --target dev                                     # 149/149 tests (estrella + 8 cubos)
```

## Avance entregado

- `DS-01`: cierra el hallazgo de Héctor (PR #51, 19-ago) de que solo existía un ciclo real
  cargado — ahora hay 4, y un cargador real reproducible por cualquiera, no solo un script de mi
  máquina.
- `US-113` (Deni Garrido Fragoso): [ ] no me corresponde cerrarla — [x] evidencia de validación
  entregada para que ella decida el cierre.
- Fila actualizada en `02_Requirements/Traceability_Matrix.md`: pendiente.
- Lo que aún falta: PR sin revisar/mergear; decisión de catálogo `dim_driver` sin comunicar;
  bug de sklearn en backtesting sin diagnosticar (Héctor).

## Uso de IA

Sesión completa asistida por Claude (Cowork): diseño del cargador, diagnóstico de los errores de
ambiente (rutas, `POSTGRES_HOST`, `--full-refresh`), y la corrección del bug de `fillna(0)` +
pruebas. Todos los comandos se ejecutaron en mi propia máquina; revisé línea por línea el código
generado antes de cada commit. No se pegaron datos reales ni credenciales en los prompts — solo
rutas de archivo, conteos y salidas de terminal.