---
project: "FARO"
date: "2026-08-24"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión única: US-212 — construcción de DB-03 y DB-04 en Superset"
touches: ["US-212", "REQ-002", "BUG-010", "DOC-CUBESPEC-DB0304", "DOC-TRACE-MATRIX", "SPRINT-MARINA-GARCIA-DEL-BUEY", "US-113"]
tags: [devlog, bi, dashboards, superset, celula-2]
---

# DevLog — 2026-08-24 — US-212: DB-03 Ficha de escuela y DB-04 Comparador de municipios

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Arranque de S4. US-212 construye los dos tableros que especificó el contrato de US-211a
([[04_UX_Design/Cube_Specs_DB03_DB04]]).

**US-113 (cubos de agregación, Célula 1) venció el 2026-08-23 sin entregarse**: `dbt/models/gold/`
sigue sin `cubo_escuela_360.sql` ni `cubo_comparador_municipio.sql`. Se aplicó la *regla de desbloqueo*
del plan de sprint: trabajar contra mock, registrar el bloqueo y avisarlo en el standup.

## Qué se hizo

### Tableros (declarativos, no a mano)

Manuel dejó en US-202/US-203 un script que renderiza tableros completos desde YAML
(`superset/sync_semantic_layer.py`). US-212 se resolvió **escribiendo dos YAML**, no haciendo clics:
así el tablero queda versionado en git y es reproducible, en vez de vivir solo dentro de Superset.

- **`superset/dashboards/db03_ficha_escuela.yaml`** — 11 charts. Cubre AC-002.4 (perfil, drivers,
  predicción y recomendación por CCT), AC-002.5 (serie de matrícula) y AC-002.6.
  Incluye el filtro por `cct`, que es lo que convierte el tablero en una *ficha*.
- **`superset/dashboards/db04_comparador_municipio.yaml`** — 13 charts. Comparativa por municipio,
  riesgo, contexto socioeconómico (KPI-14) y *small multiples* de los 6 drivers.
- Filtros globales declarados en ambos (ciclo, entidad, nivel) → base de US-214a.

### Mock del esquema estrella

`superset/mock/gold_estrella_mock.sql` (nuevo): `fact_escuela_ciclo` + las 4 dimensiones + `geo_municipio`,
con datos sintéticos y **cobertura deliberadamente parcial** para poder verificar que un hueco se
dibuja como hueco. Extiende el patrón que ya había establecido Manuel en
`superset/mock/gold_ml_outputs_mock.sql`. Vive en `superset/` (zona propia); **no se tocó `dbt/`**.

### Limpieza del contrato

`superset/semantic/metrics_db03_db04.yaml`: `kpis_propuestos` → `kpis_canonicos` (Manuel ya los
publicó) y el bloque de solicitud de cambio de grano → referencia a **DEC-008**, ya ratificado.

## Verificación

- **24/24 charts devuelven datos** vía `POST /api/v1/chart/data`.
- **La regla `SIN_DATO` se cumple end-to-end.** Naucalpan con `escuelas_con_d6 = 0` da
  `d6_promedio = null`; Coyoacán sin predicciones da `indice_riesgo_promedio = null`. En cambio
  Benito Juárez da `pct_escuelas_en_riesgo = 0.0`, que es un **cero real**. La diferencia entre
  "cero" y "sin dato" se ve en los datos, que es el punto del proyecto.
- En DB-03 las escuelas sin predicción devuelven `en_riesgo = null`, **nunca `false`**.
- `pytest tests/test_semantic_db03_db04.py` → 28 passed.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:**
  - `superset/dashboards/db03_ficha_escuela.yaml` (nuevo)
  - `superset/dashboards/db04_comparador_municipio.yaml` (nuevo)
  - `superset/mock/gold_estrella_mock.sql` (nuevo)
  - `superset/semantic/metrics_db03_db04.yaml`
  - `02_Requirements/Traceability_Matrix.md` · `12_Roadmap_Sprints/Sprints/2-marina-garcia-del-buey.md`
  - `_DevLog/2026-08-24-marina-garcia-us212-db03-db04.md` (nuevo) · `_DevLog/_index.md`
- **Fuera de alcance, no editado:** `dbt/` (US-113, C1) y `superset/sync_semantic_layer.py` (US-202,
  Manuel) — pese a los dos defectos que se le encontraron, ver abajo.
- **Manejo de secretos:** las credenciales se cargaron del `.env` al entorno sin imprimirse; la salida
  del script se filtró para enmascarar la contraseña embebida en la URI de conexión.

## Hallazgos para la Célula 2 — **resueltos por Manuel en BUG-010**

> Los tres se reportaron en el PR y Manuel los corrigió en `fix/manuel-serrania-bug010-sync-charts-utf8`:
> el script ya compara `datasource_id` antes de reusar un chart homónimo (crea uno nuevo avisando con ⚠
> en vez de repuntar el ajeno), las tres lecturas usan `read_text(encoding="utf-8")` —así que deja de
> hacer falta `PYTHONUTF8=1`— y la guía ya apunta al mock real. Se dejan documentados por trazabilidad.


1. **Colisión de nombres de chart entre tableros.** `sync_semantic_layer.py` identifica los charts por
   `slice_name` global, no por tablero. Tres charts de DB-03/DB-04 se llamaban igual que los de DB-01
   (`KPI-01 · Matrícula total`, `KPI-02 · Variación de matrícula`, `KPI-05 · Completitud de drivers`) y
   el script **repuntó silenciosamente los de Manuel** a mis datasets — se detectó porque el log decía
   "actualizado (id=1)" en vez de "creado". Se resolvió renombrando los míos, pero **la trampa sigue ahí
   para el siguiente tablero**: conviene que el script prefije el nombre con el slug del tablero.
2. **`_read_yaml()` lee sin encoding** (`path.read_text()`), así que en Windows usa cp1252 y truena con
   los acentos de cualquier `metrics_*.yaml`. `PYTHONIOENCODING` no lo arregla porque solo afecta la
   salida; hay que correr todo con `PYTHONUTF8=1`. El fix es una palabra:
   `path.read_text(encoding="utf-8")`. Misma familia que BUG-005.
3. **Referencia rota en la guía:** `04_UX_Design/Superset_Setup_US202.md` §2 manda correr
   `docker/gold_mock.sql`, que no existe en el repo.

## Correcciones tras la revisión

**Edgar detectó un error de formato que yo no vi** (`pct_escuelas_en_riesgo`): la expresión traía
`* 100.0` **y** `formato: porcentaje_1`, que el sync mapea al d3 `,.1%` — y ese formato ya multiplica
por 100 al renderizar. DB-04 habría pintado `10,000.0%` donde debía decir `100.0%`.

No lo detecté porque **el municipio que revisé daba `0.0`, y con cero el error es invisible**: sólo se
nota en una fila con valor distinto de cero. La corrección es quitar el `* 100.0` y guardar la razón
como fracción.

Es la **tercera vez** que este error aparece en el proyecto (US-203, US-211b y ahora US-212), así que
además de corregirlo se cerró la puerta:

- `superset/semantic/metrics_db03_db04.yaml`: expresión corregida + nota explicando por qué no lleva `* 100`.
- `04_UX_Design/Cube_Specs_DB03_DB04.md` §4.4: se corrigieron **dos** fórmulas —`pct_escuelas_en_riesgo`
  y `pct_escuelas_con_d1…d6`, esta última **aún sin implementar**, que era la vía por la que el error
  se iba a propagar una cuarta vez— y se agregó la regla explícita.
- `tests/test_semantic_db03_db04.py`: **prueba de regresión** (`test_los_porcentajes_no_se_multiplican_dos_veces`)
  que falla si una métrica con formato de porcentaje contiene `100` en su expresión. Verificada
  reintroduciendo el error a propósito: la prueba lo atrapa.

Verificado en Superset tras el fix: Naucalpan SECUNDARIA con 1 de 1 escuela en riesgo devuelve `1.0`
(se pinta `100.0%`), Benito Juárez `0.0` (cero real) y Coyoacán `null` (sin dato).

## Seguridad / calidad

- [x] Sin secretos hardcodeados; el `.env` no se leyó ni se imprimió
- [x] 29 pruebas de contrato en verde · 24/24 charts validados contra la API
- [x] `python _Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [x] Datos 100% sintéticos: ningún CCT real, ninguna descarga de fuente

## Bloqueantes

- **US-113 (Deni Garrido, C1) sigue sin entregarse y venció el 2026-08-23.** Los tableros quedan
  **estructuralmente completos pero validados solo contra mock**. No se pueden dar por buenos con
  datos reales hasta que existan los cubos.
- **Local:** `pandas` dejó de cargar por una directiva de Control de aplicaciones de Windows
  (`DLL load failed`). No afecta a este entregable —las 28 pruebas de US-212 no usan pandas y el CI
  corre en Linux— pero impide correr la suite completa en local.

## Próximos pasos

- Revalidar ambos tableros contra los cubos reales en cuanto C1 entregue.
- US-214a (S5): refinar el drill-down cruzado sobre los filtros ya declarados.
