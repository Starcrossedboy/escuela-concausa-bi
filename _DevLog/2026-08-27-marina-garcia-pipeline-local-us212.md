---
project: "FARO"
date: "2026-08-27"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión única: pipeline local real para US-212, sin datos mock"
touches: ["US-212", "REQ-002", "BUG-012", "BUG-013", "BUG-011", "US-113", "US-313"]
tags: [devlog, bi, dbt, pipeline-local, celula-2]
---

# DevLog — 2026-08-27 — US-212 corriendo sobre el pipeline real (sin mock)

→ [[_DevLog/_index|Volver al índice]]

## Contexto

US-113 entregó los 9 cubos y `cubo_escuela_360` / `cubo_comparador_municipio` resultaron **idénticos
al contrato de US-211a**. Con eso, DB-03 y DB-04 ya no necesitan el mock del 24-ago. Esta sesión
levanta el pipeline real en local y valida los dos tableros contra él.

## Resultado

**Los 24 charts devuelven datos del pipeline real. Cero mock, cero fallos.**

El mock (`superset/mock/gold_estrella_mock.sql`) queda obsoleto para DB-03/DB-04; se conserva en el
repo porque `gold_ml_outputs_mock.sql` de Manuel aún lo referencia para DB-01/DB-02.

## Cómo se levanta el pipeline local (los pasos que faltan documentar — BUG-012)

Ninguno de estos pasos está escrito en el repo. Se dejan aquí para que C1 los convierta en runbook.

1. `pip install dbt-core dbt-postgres` — no están en la base ni en `requirements/celula-2.txt`.
2. **`profiles.yml` en `~/.dbt/`, NO en el repo.** `.gitignore` no cubre `profiles.yml`, así que un
   archivo dentro del repo se puede subir con la contraseña adentro. La contraseña se lee con
   `env_var('POSTGRES_PASSWORD')`, y `host: localhost` (no `db`: dbt corre en el host).
3. **`POSTGRES_HOST=localhost`** al invocar los scripts de `src/`, porque el `.env` trae `db`.
4. **Cargar DOS fixtures de Formato 911 en la MISMA tabla**, no uno:
   `bronze_formato911_sample.csv` **y** `bronze_formato911_ciclo_anterior_sample.csv`.
   Con solo el primero, `gold.fact_escuela_ciclo` sale con **0 filas** y todo Gold queda vacío —
   el hecho filtra `where matricula_ciclo_anterior is not null` y ningún CCT tiene dos ciclos.
   Los 25 CCT del segundo fixture son justamente los que el primero trae en 2023-2024.
5. `dbt run --full-refresh` sobre el hecho: sin `--full-refresh` la tabla vacía se queda vacía.
6. **`PYTHONUTF8=1`** o dbt truena leyendo `dbt_project.yml` (tiene acentos) en consolas Windows.
7. `DATABASE_URL` para `publicar_gold.py`; no lo deriva del `.env`.

Errores esperados y correctos: `silver.agua_region` falla porque DS-06 (CONAGUA) no está ingerida —
por eso **D5 sale `SIN_DATO` en las 25 escuelas, no en cero**. `cubo_pipeline` falla (DB-10, C1).

## Verificación

| Qué | Resultado |
|---|---|
| Pipeline | bronze 9 tablas → silver 8 → gold 15 modelos, cubos incluidos |
| `gold.fact_escuela_ciclo` | 25 filas · `cubo_escuela_360` 25 · `cubo_comparador_municipio` 25 |
| Charts de DB-03/DB-04 | **24/24 con datos reales**, ninguno vacío |
| Regla `SIN_DATO` | ✅ D5 `SIN_DATO` en 25/25 (CONAGUA no ingerida), D6 en 24/25 (SINAICA ~80 zonas) |

Que D5 salga `SIN_DATO` y no `0` **con datos reales** es la mejor evidencia de que la regla del
proyecto funciona de punta a punta: la fuente no existe y el tablero lo dice, no lo inventa.

## Hallazgos reportados

- **BUG-012 (high)** — no hay runbook del pipeline local; los 7 pasos de arriba no están en ningún
  lado, y el más caro (cargar dos fixtures) deja Gold en cero sin ningún mensaje de error.
- **BUG-013 (high)** — `publicar_gold.py` usa por defecto el fixture sintético de ML y publica para
  **ciclo 2023-2024**, mientras el hecho real tiene **2024-2025**. El JOIN da cero y DB-03 muestra
  `cobertura_prediccion = SIN_DATO` en el 100% de las escuelas: los bloques de predicción y
  recomendación de **AC-002.4 quedan vacíos**. Apuntarlo al Gold real tampoco basta: `features_escuela`
  tiene un solo ciclo y ML exige partición temporal.
- **Residuo de BUG-011** — el fix de Manuel arregló la **lectura** (`read_text(encoding="utf-8")`), pero
  al script le falta el `sys.stdout.reconfigure()` que Edgar sí le puso a `vault_lint.py`: sigue
  tronando al **imprimir** en consola Windows. Verificado aislando las dos variables:
  con `PYTHONIOENCODING=utf-8` y sin `PYTHONUTF8` el sync corre completo.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `06_Quality_Testing/Bug_Register.md`,
  `_DevLog/2026-08-27-marina-garcia-pipeline-local-us212.md` (nuevo), `_DevLog/_index.md`,
  `02_Requirements/Traceability_Matrix.md`, `12_Roadmap_Sprints/Sprints/2-marina-garcia-del-buey.md`
- **Fuera de alcance, no editado:** `dbt/**` (C1) y `src/modelos/**` (C3) — se ejecutaron, no se
  modificaron. `superset/sync_semantic_layer.py` (Manuel) tampoco.
- **Manejo de secretos:** `profiles.yml` vive fuera del repo y lee la contraseña de variable de
  entorno; la salida de los scripts se filtró para enmascarar la URI de conexión.

## Seguridad / calidad

- [x] Sin secretos hardcodeados; `profiles.yml` fuera del repo por el hueco de `.gitignore`
- [x] 29 pruebas de contrato en verde · 24/24 charts validados contra datos reales
- [x] `vault_lint.py` → ✅ Vault limpio
- [x] Datos: fixtures anonimizados de ≤500 filas del propio repo; ninguna descarga de fuente real

## Bloqueantes

- **BUG-013 bloquea cerrar US-212 al 100%**: sin alineación de ciclo entre `gold.predicciones` y el
  hecho, los bloques de predicción y recomendación de DB-03 no se pueden validar con datos.
- Las URLs reales de las fuentes siguen bloqueadas: todo corre sobre muestras de ≤500 filas.

## Próximos pasos

- Acordar con Manuel el **repunte de los datasets a los cubos materializados** (`SELECT ... FROM
  gold.cubo_escuela_360`) en vez de reconstruir desde `fact` + dims. Cambia la convención de
  `superset/semantic/` para los 10 tableros, por eso no se hizo aquí.
- US-214a (S5) sobre los filtros ya declarados.
