---
project: "FARO"
date: "2026-09-04"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión: aviso de Luis sobre agregación por ciclo, análisis del umbral y arranque de US-215a"
touches: ["US-214a", "US-215a", "US-212", "REQ-002", "AC-002.2", "BUG-031", "DEC-006"]
tags: [devlog, bi, dashboards, superset, qa, celula-2]
---

# DevLog — 2026-09-04 — Filtro de ciclo por defecto, análisis del umbral y plan de US-215a

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/04_UX_Design/Cube_Specs_DB03_DB04]] §8.quater y §8.quinquies

## Contexto

Luis Téllez avisó al grupo el 2026-09-04, al liberar la URL pública, que los dashboards
**consultan la base directo y no pasan por la API**, así que su corrección de
`/api/v1/kpis` (20.6M → 6.7M) no los cubría, y que había que verificar que los cubos
filtraran por ciclo. Esta sesión verifica ese aviso, lo arregla, y aprovecha para atender
el otro punto que dejó para C2 (el umbral) y arrancar US-215a, desbloqueada por el PR #208
de Edgar.

## 1. El aviso de Luis era correcto y nos pegaba

Verificado contra la base antes de tocar nada:

| | Matrícula que pintaban `KPI-15` (DB-03) y `KPI-01` (DB-04) |
|---|---|
| Al abrir el tablero, sin filtrar | **32 312** |
| Ciclo 2024-2025, que es lo correcto | **11 828** |

**2.7× inflado.** Los filtros globales de ciclo existían desde US-212, pero **sin valor
inicial**: al abrir el tablero nadie ha filtrado, así que toda métrica agregada recorre los
tres ciclos del cubo. Afectaba a las **8 tarjetas** de los dos tableros, no solo a las de
matrícula.

### El arreglo

Clave opcional `valor_por_defecto` en `filtros_globales`, que `_filtros_nativos()` traduce
al `defaultDataMask` de Superset — la misma estructura que ya usan los links de drill-down
en su parámetro `native_filters`, así que el formato estaba verificado contra 6.1.0 desde
US-214b.

**Aditivo y opt-in.** `sync_semantic_layer.py` es herramienta compartida de C2: un tablero
que no declara la clave se comporta exactamente igual que antes, y hay una prueba que lo
exige explícitamente. Los tableros de Manuel, Monserrat y Oscar no cambian.

### Cómo se probó

`tests/test_filtro_ciclo_por_defecto.py` (8 casos), cada guarda validada **reintroduciendo
su defecto**:

| Defecto reintroducido | ¿Lo cazó? |
|---|---|
| Quitar `valor_por_defecto` de DB-03 | ✅ 2 casos |
| Que el traductor deje de emitir `defaultDataMask` | ✅ 2 casos |

Y la prueba definitiva, contra la propia API de charts de Superset:

```
KPI-15 · Matrícula de la escuela      sin filtro 32 312 → con ciclo 11 828  (2.73x evitado)
KPI-01 · Matrícula de los municipios  sin filtro 32 312 → con ciclo 11 828  (2.73x evitado)
```

Regresión comprobada: el drill-down de US-214a sigue apuntando a los índices correctos —
el filtro nuevo no corrió ninguna posición (los IDs van por posición, era el riesgo real).

## 2. Corrección de mi propia evidencia

**El KPI-02 que reporté en el PR #211 tenía el mismo defecto.** Di **−0.192 %** como "el"
valor; ese número es la mezcla de los tres ciclos, no el de un ciclo. El correcto del ciclo
vigente es **−0.496 %**.

Peor: la mezcla **esconde el signo**. Los tres ciclos no van en la misma dirección.

| Ciclo | KPI-02 |
|---|---|
| 2022-2023 | **+0.242 %** |
| 2023-2024 | −0.483 % |
| 2024-2025 | −0.496 % |
| *(mezcla)* | *−0.192 %* |

Un tablero que dijera "la matrícula cayó 0.19 %" estaría promediando un año que **subió**
con dos que bajaron. La concordancia entre cubos que verificaba BUG-031 **se sostiene
igual** —los cinco caminos dan −0.496 % al grano correcto—, así que el arreglo de BUG-031
no se toca: lo que estaba mal era mi encuadre del número. Corregido en §8.ter.3 del
contrato y en la matriz.

## 3. `escuelas_en_riesgo = 0` — no es un defecto

Luis lo marcó como **H1** para C2. Al analizarlo resultó lo contrario de lo que parecía.

`src/modelos/riesgo.py` (C3) define el `indice_riesgo` como una sigmoide fijada por dos
anclas de negocio explícitas: variación `0.00` → riesgo `0.30`, y variación **`-0.05`
(pierde 5 %) → riesgo `0.60`**, que es exactamente el umbral de DEC-006.

Es decir, `indice_riesgo ≥ 0.6` significa **"se proyecta que pierda 5 % o más"**.
Verificado contra los datos: la escuela peor del universo proyecta **−4.37 %** (riesgo
0.562). **Ninguna llega a −5 %.**

El cero es la afirmación verdadera de que ninguna escuela cruza el criterio que el propio
equipo definió. Bajar el umbral "para que se vea algo" desharía el significado de −5 % y
volvería el número incomparable entre ciclos — justo la propiedad por la que C3 eligió una
sigmoide absoluta sobre un percentil relativo.

**Recomendación de C2: no mover DEC-006.** Lo que resuelve la demo sin tocar la decisión es
dejar de contar y empezar a ordenar: un ranking de mayor riesgo con su driver dominante y
su recomendación cuenta la historia completa aunque nadie llegue a 0.60 — y ese ranking es
el diferenciador prescriptivo, que ya funciona. Alternativa, si se quiere conservar un
conteo: una banda intermedia "atención" (0.40–0.60, 15 escuelas) como KPI adicional, sin
redefinir "en riesgo". Requiere aval de Manuel (catálogo de KPIs) y de Edgar.

Análisis completo con la tabla de umbrales candidatos y sus costos de interpretación en
[[vault/04_UX_Design/Cube_Specs_DB03_DB04]] §8.quinquies. **No se cambió nada**: es insumo
de decisión, y DEC-006 no es de esta célula.

## 4. US-215a arrancada

El PR #208 de Edgar puso `vault/06_Quality_Testing/**` en `comunes`, cerrando el hallazgo
H3 que reporté el 3-sep. Con eso la historia dejó de estar bloqueada por alcance.

`vault/06_Quality_Testing/Usability_Accessibility_Test_Plan_DB03_DB04.md`
(`DOC-USABILIDAD-DB0304`), calcando el formato del plan de Monserrat para DB-05/DB-08.
**7 de 20 casos quedan verificados hoy** con evidencia de datos o de API; los que exigen
navegador quedan `⏳` explícitos. No se marcó ninguno como verificado sin correrlo — un
plan de accesibilidad firmado sin haber tabulado por los controles no vale nada.

Dos huecos del proyecto documentados sin rellenarlos por cuenta propia: no hay CI de
accesibilidad (pese a que `Accessibility.md` declara Lighthouse como bloqueante), y
`UX_Guidelines.md` está vacío con `source_of_truth: true`.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `superset/sync_semantic_layer.py`,
  `superset/dashboards/db03_ficha_escuela.yaml`,
  `superset/dashboards/db04_comparador_municipio.yaml`,
  `tests/test_filtro_ciclo_por_defecto.py` (nuevo),
  `vault/06_Quality_Testing/Usability_Accessibility_Test_Plan_DB03_DB04.md` (nuevo),
  `vault/06_Quality_Testing/_index.md`, `vault/04_UX_Design/Cube_Specs_DB03_DB04.md`,
  este DevLog, `vault/_DevLog/_index.md`, `vault/02_Requirements/Traceability_Matrix.md`
- **Herramienta compartida:** se tocó `sync_semantic_layer.py`, que usan los 10 tableros.
  El cambio es aditivo y hay prueba de compatibilidad hacia atrás, pero **conviene avisar a
  Manuel Serranía** como dueño de la convención de la capa semántica.
- **Fuera de alcance, no editado:** `src/modelos/riesgo.py` y `dbt/**` (se leyeron para el
  análisis del umbral, no se modificaron). `vault/12_Roadmap_Sprints/**` (del PM).
  `vault/10_Risk_Governance/Decision_Log.md` — DEC-006 no se toca desde C2.
- **Decisiones autónomas del agente:** hacer el arreglo opt-in en vez de cambiar el
  comportamiento por default de todos los tableros; **no** proponer bajar el umbral tras
  ver la calibración.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] 8 casos nuevos, cada guarda validada reintroduciendo su defecto
- [x] `vault_lint.py` ✅ · `ruff` ✅ · suite completa en verde
- [x] Verificado en vivo contra Superset, no solo por prueba estática

## Bloqueantes

- **Edgar Coronel (PM):** `Execution_Status.md` sigue diciendo que US-214a está `planned`
  y "sin PR ni commit" pese al PR #211 mergeado, y US-212 sigue en `in_review`. Ninguna de
  las dos rutas está en mi alcance.
- **Mesa (Manuel + Edgar):** decisión sobre la narrativa del umbral antes de la demo.
- **Manuel Serranía:** filtro `cct` en DB-06/DB-09 para las 2 rutas restantes de US-214a
  (verificado hoy: sigue sin agregarse). Y BUG-037, que sigue `open`.

## Próximos pasos

- Segunda pasada de US-215a con navegador para cerrar el §3 de accesibilidad.
- Confirmar con C1/C5 cuándo se materializan los cubos `cubo_*` en Cloud SQL: sin eso los
  tableros no pueden apuntar a producción.
