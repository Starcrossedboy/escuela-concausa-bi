---
project: "FARO"
date: "2026-08-29"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión única: BUG-031, corrección de KPI-02 y prueba de regresión por clase de error"
touches: ["US-211a", "US-212", "REQ-002", "AC-002.4", "BUG-031", "BUG-019", "ADR-007", "DEC-008", "US-113"]
tags: [devlog, bi, qa, celula-2]
---

# DevLog — 2026-08-29 — BUG-031: KPI-02 pintaba −54.5 % donde el valor real es −0.19 %

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Preparando la mesa de ADR-007 audité mis propias métricas de porcentaje contra la base, en vez de
leerlas. La cuarta salió mal, y el defecto es mío: nace en §4.4 del contrato que yo escribí.

## El defecto

`variacion_ponderada_pct` era `SUM(variacion_matricula * matricula_total) / SUM(matricula_total)` con
formato de porcentaje. Eso es un promedio de `variacion_matricula` ponderado por matrícula, y solo
tiene sentido si esa columna es una razón. **No lo es:** `fact_escuela_ciclo.sql:49` la produce como
`matricula_total - matricula_ciclo_anterior`, alumnos absolutos, rango observado −24 a 24.

| | |
|---|---|
| Matrícula del ciclo | 32 312 |
| Matrícula del ciclo anterior | 32 374 |
| Valor real | **−0.19 %** |
| Lo que pintaban DB-03 y DB-04 | **−54.5 %** |

Factor 287. El tablero afirmaba que las escuelas perdieron más de la mitad de su matrícula en un
ciclo, y lleva así desde US-212.

## Dónde nace, que es lo incómodo

En la especificación, no en el código. §4.4 declaró `variacion_x_matricula = SUM(variacion_matricula *
matricula_total)` como componente aditivo del cubo de DB-04, y **Deni Garrido lo implementó
exactamente como se lo pedí**. La implementación es fiel; la especificación estaba mal.

Ese componente carga dos errores a la vez. Asume una unidad que el contrato nunca declaró —el mismo
hueco que ADR-007 vino a cerrar en el ML, aquí en el frontend— y congela la agregación equivocada: una
razón es razón de sumas, no promedio ponderado de razones. Y una vez materializado en el cubo ya no se
puede corregir desde la capa semántica, porque el numerador y el denominador reales dejaron de existir
como columnas.

## El alcance es seis tableros, no dos

Encontrado al buscar referencias colgantes después de corregir lo mío. **El componente defectuoso se
reutilizó en toda la célula**, con expresión y formato idénticos:

| Archivo | Tableros |
|---|---|
| `metrics_db01_db02.yaml` (líneas 74 y 177) | DB-01 · DB-02 |
| `metrics_db03_db04.yaml` | DB-03 · DB-04 |
| `metrics_db06_db09.yaml` (línea 73) | DB-06 · DB-09 |

`gold.cubo_matricula`, que alimenta DB-01 y DB-02, también da **−54.5 %**, verificado contra Postgres.

Y **dos pruebas exigen el defecto como requisito**: `test_semantic_db01_db02.py:251` y
`test_semantic_db06_db09.py:268` afirman que `variacion_x_matricula` tiene que estar presente.
Mientras existan, quitar el componente reprueba CI. Son archivos de Manuel Serranía; no se tocan desde
aquí, se le escalan.

Por eso BUG-031 sube a **critical**: no es una tarjeta en dos tableros, es KPI-02 del catálogo
canónico mal en seis de los diez, sostenida por pruebas.

Esto salió únicamente de buscar referencias colgantes, no de la corrección en sí. Es el argumento
más claro a favor de la regla nueva: si me hubiera detenido al ver mis dos tableros en verde, el error
seguiría vivo en cuatro más.

## Por qué mis propias defensas no lo vieron

Las dos fallaron por la misma razón, y vale escribirlo:

- **`test_los_porcentajes_no_se_multiplican_dos_veces`** busca la cadena `100` en la expresión. Esta
  métrica nunca tuvo `* 100`, así que pasó en verde. Cubría la **forma** del error que Edgar Coronel
  encontró en `pct_escuelas_en_riesgo`, no su **clase**. Una prueba que da confianza falsa es peor que
  no tener prueba.
- **La verificación de US-212** fue "24/24 charts devuelven datos reales". **"Devuelve datos" no es
  "devuelve el dato correcto".**

## Lo que se hizo

1. **BUG-031** en el registro, con la evidencia numérica y la autoría del defecto donde corresponde.
2. **§4.4 del contrato**: `suma_matricula_anterior` reemplaza a `variacion_x_matricula`, con la regla
   nueva escrita — toda razón se guarda como numerador y denominador por separado, y ambos son sumas
   de una sola columna. Si hace falta multiplicar dos medidas para construir un componente, la métrica
   está mal planteada.
3. **DB-03 corregido hoy**: `SUM(matricula_total) / NULLIF(SUM(matricula_total - variacion_matricula),
   0) - 1`, verificado contra Postgres. Da −0.19 %.
4. **DB-04: la tarjeta se retira.** No se puede corregir sin tocar el cubo, que es de C1. Un tablero
   con una tarjeta menos es defendible; con una tarjeta falsa, no. Queda el comentario con la
   expresión exacta para restituirla.
5. **`test_una_metrica_de_porcentaje_no_multiplica_dos_medidas`**: una métrica con formato de
   porcentaje no puede multiplicar dos columnas de medida dentro de un agregado. Ese producto es la
   firma del defecto y es verificable sin base de datos.

## La corrección es inmune a ADR-007

Se expresa solo con matrículas, que son alumnos y lo seguirán siendo se ratifique lo que se ratifique.
Esto responde una objeción concreta que se planteó al decidirlo: no hay escenario en que haya que
revertirla. La versión que sí quedaba acoplada —derivar restando— se conserva únicamente como forma
transitoria en DB-03 mientras C1 no exponga `matricula_ciclo_anterior`, y así está anotado en el YAML.

## Lo que hace falta de C1

Cuatro líneas, que conviene meter en el **mismo PR de la normalización de ADR-007** porque ya van a
tocar esos archivos: exponer `matricula_ciclo_anterior` en `fact_escuela_ciclo.sql` (el dato ya existe
en el CTE `con_anterior`, solo se está tirando), pasarla a `cubo_escuela_360.sql`, y sustituir
`variacion_x_matricula` por `sum(f.matricula_ciclo_anterior) as suma_matricula_anterior` en
`cubo_comparador_municipio.sql`.

## Verificación

| Qué | Resultado |
|---|---|
| Expresión nueva contra Postgres | **−0.19 %** (la vieja, −54.5 %) |
| Test nuevo con el defecto reintroducido a propósito | **falla**, como debe |
| Test nuevo sobre la versión corregida | pasa |
| `pytest tests/test_semantic_db03_db04.py -q` | 28 passed |
| `pytest tests/ -q` (suite completa) | **631 passed, 5 skipped** |
| `vault_lint.py` | Vault limpio |
| Ninguna prueba existente se perdió | comparado `--collect-only` contra `main` |

## Uso de IA

Claude Code (Opus 5). Regla de trabajo adoptada en esta sesión a petición de la autora: **antes de
cualquier push, ejecutar y comprobar que los números son correctos, no solo que corre**. Aplicada
aquí de punta a punta — el hallazgo mismo salió de aplicarla a trabajo ya mergeado.
