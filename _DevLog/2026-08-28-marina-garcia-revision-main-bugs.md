---
project: "FARO"
date: "2026-08-28"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión única: revisión de main tras 123 commits, diagnóstico de BUG-013 y alta de BUG-026/BUG-027"
touches: ["US-212", "US-214a", "US-215a", "REQ-002", "BUG-013", "BUG-014", "BUG-017", "BUG-019", "BUG-020", "BUG-015", "BUG-026", "BUG-027", "ADR-007", "US-104", "US-113", "US-313", "US-221"]
tags: [devlog, bi, qa, revision, celula-2]
---

# DevLog — 2026-08-28 — Revisión de `main`, causa raíz de BUG-013 y dos bugs nuevos

→ [[_DevLog/_index|Volver al índice]]

## Contexto

`main` recibió **123 commits en 30 horas**, y mañana (sáb 29) corre el **hito crítico S4 — Ensayo E2E
en vivo** de [[12_Roadmap_Sprints/PLAN_MAESTRO]], cuya casilla 6 nombra a **DB-03** explícitamente.
Esta sesión revisa qué de todo eso toca a Célula 2 y si US-212 puede cerrarse.

No se modificó código de nadie más. La única ejecución con efecto fue `publicar_gold.py --desde-gold`
contra la base local, que **falló antes de escribir** — el diagnóstico salió de ese fallo.

## Lo que se resolvió solo

- **BUG-014 `fixed`** (Edgar, `fix/edgar-navarrete-mojibake-higiene-vault`). Además de acotar el
  patrón, hizo dos cosas que yo no había propuesto: recortar la sección `## Aprobación` antes de
  evaluar, y agregar el evento **`edited`** — sin el cual un cuerpo corregido tras el push se quedaba
  en rojo para siempre, que es exactamente lo que me pasó.
- **Mitad C3 de BUG-013 `fixed`** (Héctor, `a76c748`). El hueco real no era de configuración:
  `publicar_gold.py` **no sabía leer de una tabla**, solo de CSV/Parquet.

## Dónde está realmente parada la mitad C1 de BUG-013

Corriendo `--desde-gold` en un local al día:

```
ValueError: Con 1 ciclos no se puede hacer backtesting: se necesitan al menos 3.
Ciclos disponibles: ['2024-2025'].
```

Mi primera lectura fue que `features_escuela.sql` debía leer `ref('matricula_historica')` en vez de
`ref('matricula')`. **La corrijo:** el DevLog de Diana muestra que el diseño previsto sí funciona —
cargó **4 ciclos reales** en `bronze.formato911_2024_2025` el 27-ago y materializó la estrella
completa con **149/149 tests en verde**. La mitad C1 de BUG-013 está resuelta *con datos reales*.

Lo que queda no es de wiring, es de **fixtures**, y por eso lo levanté aparte.

## BUG-026 — la verificación existe pero nadie salvo Diana puede reproducirla

Hay dos fixtures de Formato 911 y cada uno resuelve la mitad:

| Fixture | Ciclos | CCT ∩ `dim_escuela` |
|---|---|---|
| `…_sample.csv` + `…_ciclo_anterior_sample.csv` | 2 | **59 de 60** ✅ |
| `…_historico_sample.csv` | **6** ✅ | 3 de 30 |

```
historico            ∩ dim_escuela          →  3 de 30
formato911_2024_2025 ∩ dim_escuela          → 59 de 60
historico            ∩ formato911_2024_2025 →  3 de 30
```

Antes de proponer el arreglo obvio lo verifiqué, y no funciona: repuntar el `ref()` al histórico daría
un modelo **en verde con 3 escuelas en vez de 30**, sin error y con los tests de dbt pasando — el modo
de falla silenciosa de BUG-012.

Consecuencia real: **CI nunca ejercita el entrenamiento de ML-01 a grano escuela**, y yo no puedo
verificar AC-002.4 de DB-03 sin pedirle a Diana que corra su ambiente con 460 MB de CSV. Alta como
[[06_Quality_Testing/Bug_Register|BUG-026]], `high`, para **C1**. El arreglo no toca ningún modelo dbt:
un fixture con ≥4 ciclos sembrado desde `bronze.cct`.

## De paso: el error de sklearn de Diana ya está arreglado

Su DevLog deja sin resolver un `HistGradientBoostingRegressor: window shape cannot be larger than
input array shape` al intentar backtesting real, y se lo pasa a Héctor. **Ese es BUG-015, y Héctor lo
arregló el mismo día.**

> **Corrección (29-ago), señalada por Héctor Morales y ratificada por el PM.** Mi primera redacción
> citaba `4f22bd8` (22:45) como el fix. **No lo es**: ese fue el primer intento y evaluaba la
> cobertura de drivers de forma **global**, así que no sirvió — Diana volvió a correr después de ese
> commit y obtuvo el mismo error. El que funcionó es **`f906a7d` (23:04)**, que la evalúa **por
> ventana**: `d6_aire` tenía datos globalmente pero estaba vacío en el tramo de entrenamiento.
>
> La corrección importa por una razón concreta que Héctor explicó mejor que yo: tal como lo redacté,
> Diana concluiría que su segundo fallo **no debió ocurrir** y acabaría dudando de su ambiente en vez
> de confiar en él. Un reporte que hace desconfiar de un ambiente sano cuesta más que el bug.
>
> Y donde escribí *"probablemente pasa"* ya hay certeza, no conjetura: Héctor verificó la cadena
> completa sobre `main` con el target real — **F1 0.633, 78 de 80 predicciones con recomendación**.

## BUG-027 — referencia rota que CI no puede ver

`superset/semantic/metrics_kpis_base_us221.yaml` apunta sus 5 `sql_ref` a `sql/…`, directorio que ya
no existe. `tests/test_kpis_us221.py` codifica la ruta a mano y nunca lee el `sql_ref`, así que la
prueba pasa mientras el catálogo apunta al vacío. Severidad `low`, para **C2** (Oscar Quiroz).

De paso, lo bueno: US-221 **no colisiona** con DB-03/DB-04 (sus KPI viven sobre `cubo_matricula`,
de DB-01), y Oscar aplicó bien la regla del porcentaje — dejó escrito *"Ya viene como razón (no \*100)"*.

## Lo que cambia el significado de mis tableros: BUG-017 y ADR-007

`indice_riesgo` se publicó **saturado en ≈1.00 para las 45 249 filas**: la sigmoide está calibrada
sobre fracción (`-0.05` = pierde 5 % de matrícula) y `features_escuela.sql` produce **alumnos
absolutos**. Con esa escala, `en_riesgo` (DEC-006, umbral 0.6) marcaría **el 100 % de las escuelas** y
`pct_escuelas_en_riesgo` de DB-04 diría 100 %. Se vería perfectamente normal.

[[03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula|ADR-007]] propone fijar la unidad en
fracción. Está en `proposed` y **no me lista como ratificadora**, aunque su rechazo de la alternativa B
se apoya en *"un tablero que lea Gold directo — que es justo lo que hace Superset"*. Pedir entrar a esa
mesa: si se ratifica fracción, el umbral 0.6 sigue válido tal cual; si no, §5.1 del contrato de
[[04_UX_Design/Cube_Specs_DB03_DB04]] hay que rehacerlo.

## Hallazgos de proceso

- **Criterio nuevo del 28-ago** en [[12_Roadmap_Sprints/Execution_Status]]: *"las historias cuyo
  entregable es una ruta HTTP no cierran mientras esa ruta no responda en el despliegue que se va a
  demostrar"*. Un tablero de Superset es superficie desplegada. Falta que Edgar confirme si US-212 se
  juzga con esa vara — si sí, el 10 % restante ya no depende solo de BUG-013.
- **BUG-020 (`critical`)**: en la URL pública toda ruta que toca base de datos responde 500. Es lo que
  de verdad amenaza la casilla 6 del ensayo, y no es de C2.
- **BUG-012 sigue abierto sin avance**: `dbt/README.md` continúa siendo el scaffold por defecto de dbt.

## Verificación

| Qué | Resultado |
|---|---|
| `pytest tests/test_semantic_db03_db04.py` | ✅ 29 passed sobre `main` de hoy |
| Archivos canónicos de DB-03/DB-04 | ✅ nadie los tocó en los 123 commits |
| Colisiones de nombre con US-221 | ✅ ninguna |
| `publicar_gold.py --desde-gold` | ❌ falla por 1 solo ciclo (evidencia de BUG-026) |
| Solape de CCT entre los tres caminos | ❌ 3/30 en el histórico, 59/60 en el actual |

## Pendientes

1. **US-214a** — es lo único que puedo adelantar sin esperar a nadie; los `filtros_globales` ya quedaron
   declarados en US-212. No se arrancó en esta sesión por decisión de la autora.
2. **US-215a** — deliberadamente **no** se adelanta: probar usabilidad sobre bloques vacíos y sobre un
   `indice_riesgo` en disputa obliga a repetir la prueba. Espera a ADR-007.
3. Decisión pendiente con Manuel: repuntar `superset/semantic/*.sql` a los cubos materializados.
4. `requirements/celula-2.txt` sigue sin existir; se necesita antes de US-207.

## Uso de IA

Claude Code (Opus 5) para la revisión de los 123 commits, el diagnóstico de BUG-013 y la redacción de
BUG-026/BUG-027. Las tres consultas SQL de solape de CCT y la corrida de `--desde-gold` se ejecutaron
y verificaron en la base local antes de escribir nada. Ninguna afirmación de este DevLog viene de
lectura de código sin ejecutar, salvo las señaladas como propuestas.
