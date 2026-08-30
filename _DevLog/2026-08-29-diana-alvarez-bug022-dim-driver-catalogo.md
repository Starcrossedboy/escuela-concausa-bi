---
project: "FARO"
date: "2026-08-29"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~1h"
touches: ["BUG-022"]
tags: [devlog, gold, dbt, seeds, dim_driver, bug022, calidad]
---

# BUG-022 — `gold.dim_driver` desincronizado: catálogo divergente sin test que lo detecte

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

**Contexto.** Manuel Serranía (PR #100) y Monserrat Olivas (US-213, DB-05/DB-08) reportaron que
`gold.dim_driver` en Postgres local puede tener nombres largos ("Pobreza y rezago social"...) en
vez de los nombres cortos del catálogo canónico (`dbt/seeds/dim_driver.csv`: Pobreza, Inseguridad,
Infraestructura, Conectividad, Agua, Aire). Ya lo había confirmado en mi propio Postgres el
2026-08-28 ([[_DevLog/2026-08-28-diana-alvarez-formato911-real-validacion-us113]]): `dbt seed
--select dim_driver --full-refresh` corrige el dato, pero la causa raíz de fondo -- que el catálogo
pueda divergir sin que nada lo detecte -- seguía sin resolverse.

**Nota de numeración:** esta rama se rehizo desde cero sobre `main` actualizado (que ya incorpora
el merge de PR #115 -- mi fix de BUG-016 quedó renumerado a **BUG-021** por reconciliación de
Edgar -- y todo el trabajo de Héctor Morales del 27/28-ago, BUG-015/017/018/019 + ADR-007). El ID
`BUG-022` es el siguiente libre confirmado en `main` en el momento de abrir esta rama.

**Causa raíz.** `superset/mock/gold_estrella_mock.sql` (mock previo de Marina García del Buey/C2,
US-212, hoy superado por el seed real) crea `gold.dim_driver` con `CREATE TABLE IF NOT EXISTS` +
`INSERT ... ON CONFLICT (id_driver) DO NOTHING`, usando nombres largos distintos a los del seed
canónico. Si ese mock corre en un Postgres donde `dbt seed`/`dbt build` nunca se ha ejecutado, la
tabla se queda permanentemente con esos nombres -- y **ningún test de dbt lo detectaba**: la
columna `nombre` solo tenía `not_null`, sin `accepted_values`. El primer síntoma visible es un
HTTP 500 río abajo en Superset (US-213), no un fallo en CI ni en `dbt test`.

Nota sobre el mecanismo exacto: probé directamente si `--full-refresh` es indispensable para
corregir el dato una vez que la tabla ya existe con los nombres viejos. **No lo es** -- `dbt seed
--select dim_driver` (sin `--full-refresh`) también reemplaza correctamente los datos en Postgres
(el seed hace un `DELETE`+`INSERT` completo de la tabla, no un upsert por PK). El desface real más
probable en los entornos afectados es que `dbt seed` (o `dbt build`, que lo incluye) simplemente
nunca se corrió ahí -- `dbt run` por sí solo **no** corre seeds.

**Fix.** Se agregó un test `accepted_values` a la columna `nombre` de `dim_driver` en
`dbt/seeds/_gold__seeds.yml`, con los 6 nombres cortos canónicos como únicos valores válidos, se
documentó el catálogo canónico en `03_Architecture/Data_Model.md` §4.2, y se registró `BUG-022` en
`06_Quality_Testing/Bug_Register.md`.

## Cómo se probó

1. **Simulación del estado divergente real**: recreé a mano en Postgres la tabla `gold.dim_driver`
   exactamente como la deja `gold_estrella_mock.sql` (mismo `CREATE TABLE IF NOT EXISTS` +
   `INSERT ... ON CONFLICT DO NOTHING`, nombres largos).
2. Con ese estado divergente, corrí `dbt test --select dim_driver` **sin** sembrar primero → el
   nuevo test `accepted_values_dim_driver_nombre...` **FALLA** con `FAIL 6` (las 6 filas tienen
   nombres inválidos). Esto prueba que el fix detiene el problema en vez de dejarlo pasar en
   silencio.
3. Restauré el estado correcto con `dbt seed --select dim_driver --full-refresh` → `dbt test
   --select dim_driver` vuelve a **PASS** limpio (9 PASS en tests de `dim_driver`, mismos 3
   errores preexistentes y no relacionados de cubos que dependen de tablas ML-runtime no
   materializadas en este contexto).
4. Regresión más amplia, mismo rigor que BUG-021:
   ```
   dbt build --target dev --threads 4 --full-refresh   # PASS=174 ERROR=19 (mismos 19, todos por
                                                          # gold.recomendaciones/predicciones y
                                                          # bronze.conagua_no_ingerido no
                                                          # materializadas en este sandbox --
                                                          # no relacionados con dim_driver)
   pytest tests/ -q                                     # 497 passed, 1 failed (flake preexistente
                                                          # de test_evaluar.py, silhouette 0.5147 vs
                                                          # 0.5155 -- no toca dim_driver ni seeds),
                                                          # 5 skipped
   python _Meta/scripts/vault_lint.py .                  # Vault limpio (3 huérfanos preexistentes,
                                                          # no relacionados)
   ```

## Avance entregado

- `BUG-022`: causa raíz identificada y corregida con un test que falla en CI/local en vez de
  esperar a un HTTP 500 en Superset. Entrada agregada a `06_Quality_Testing/Bug_Register.md` sobre
  `main` ya actualizado -- sin riesgo de colisión de ID como pasó con BUG-015/016.
- `superset/mock/gold_estrella_mock.sql` (Marina García del Buey/C2, US-212): **no se editó** --
  es el archivo de otra célula. Queda como recomendación pendiente de comunicar: actualizar o
  retirar el mock ahora que el seed real lo reemplaza, para que no vuelva a sembrar el catálogo
  viejo en un Postgres limpio.
- Fila en `02_Requirements/Traceability_Matrix.md`: pendiente (fuera del alcance de este fix
  puntual).

## Uso de IA

Sesión completa asistida por Claude (Cowork): diagnóstico de la causa raíz, diseño y verificación
del test (incluida la simulación explícita del estado divergente para probar que el test lo
detecta, no solo que pasa en el caso feliz), ajuste de la hipótesis inicial sobre `--full-refresh`
tras probarla directamente y encontrarla incorrecta, y reconstrucción completa de la rama sobre
`main` actualizado tras descubrir que había avanzado significativamente (merge de PR #115,
trabajo de Héctor sobre BUG-015/017/018/019 y ADR-007) mientras se preparaba este fix. Todos los
comandos se ejecutaron y verificaron en mi propia máquina antes de este resumen; no se pegaron
datos reales ni credenciales en los prompts.
