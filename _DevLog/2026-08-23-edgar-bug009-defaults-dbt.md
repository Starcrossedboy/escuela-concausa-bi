---
project: "FARO"
date: "2026-08-23"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "media — cierre de BUG-009: 11 defaults de dbt, DEC-011 y test de regresión en CI"
touches: ["BUG-009", "DEC-011", "RISK-008", "US-111", "US-106", "REQ-001", "DOC-BUGREG", "DOC-DECLOG"]
tags: [devlog, dbt, gobernanza, ci]
---

# DevLog — 2026-08-23 — BUG-009: defaults de dbt, DEC-011 y `dbt parse` en CI

→ [[_DevLog/_index|Volver al índice]] · [[06_Quality_Testing/Bug_Register]] · [[10_Risk_Governance/Decision_Log]]

## Contexto

Diana me asignó BUG-009 con una decisión pendiente concreta: **decidir el reparto** para que los
`identifier` de las fuentes Bronze quedaran con default permanente. Ella ya había hecho el trabajo
duro — encontró empíricamente 6 de los 7 valores reales materializando Gold contra el compose local
para el ensayo E2E de Héctor (PR #70) — y dejó la evidencia lista en el registro.

## Qué encontré al validarlo

Tres cosas que cambiaron la forma del arreglo:

1. **Son 11 vars, no 7.** Faltaba `bronze_conagua_id_column`, en
   `dbt/models/silver/agua_region.sql:4`. Nadie la había topado porque `conagua` no tiene datos
   ingeridos, así que `agua_region` nunca llegó a correr. Se lo pasé a Diana y lo ratificó.
2. **`dbt_project.yml` no tenía bloque `vars:` en absoluto.** Ese hueco explica por qué las 4 vars
   que no son identifiers no tenían dónde vivir.
3. **Ningún workflow del CI corre dbt.** Verificado sobre los 5 workflows. O sea: el bug se podía
   reintroducir sin que nadie se enterara, y no existía el test de regresión que el propio
   `Bug_Register` exige para pasar algo a `closed`.

Efecto colateral que nadie había señalado: los comandos que `CLAUDE.md` documenta como estándar
(`dbt run --select silver`, `dbt test`) estaban **rotos de fábrica** para cualquiera que clonara el
repo. No es un problema de un modelo aislado; era el proyecto entero.

## Decisiones

**Reparto (mía, como PM):** no dividirlo entre los 4 dueños de DS. Cuatro PRs paralelos sobre el
mismo YAML garantizaban conflicto entre ellos — exactamente lo que estuvimos resolviendo todo el día
en los PRs #73–#79 — y 4 ciclos de revisión para ~15 líneas, a dos semanas del freeze. Lo ejecuto en
un solo PR y cada dueño revisa **sus** valores como reviewer.

**Ubicación (de Diana, TL Célula 1, regla 7):** le planteé tres opciones. Eligió la (c): los
`identifier` llevan default **inline** en `sources.yml`, extendiendo el patrón que ya usaban
`formato911`, `formato911_historico` y `cemabe` — su argumento es que tener el nombre de la tabla y
su default en el mismo lugar es más fácil de auditar. Las 4 vars de modelo van a un bloque `vars:`
nuevo en `dbt_project.yml`, porque `sources.yml` no tiene dónde alojarlas. Descartó centralizar las
11 en `dbt_project.yml` por romper el patrón existente sin necesidad.

Ambas quedaron registradas como **DEC-011**.

## Los dos valores que NO se resolvieron

Estos son los que importan, porque la tentación era cerrarlos callados:

- **`bronze_conagua_identifier` → `conagua_no_ingerido`.** No existe ninguna tabla `conagua*` real.
  El nombre es falso a propósito: idea de Diana, para que nadie lo confunda con una tabla real al
  verlo en un log. Deja pasar el parse del proyecto y hace que `agua_region` falle en runtime **de
  forma visible**. D5 sigue `SIN_DATO` explícito.
- **`coneval_periodo_medicion` → `2020`.** Deuda técnica que **acepto yo explícitamente**. No es una
  columna: ninguna tabla `coneval_*` trae año, así que es un entero fijo heredado del ensayo E2E y
  sin confirmar contra la fuente. Si está mal no rompe nada — **etiqueta mal en silencio** el
  período de medición del rezago social. Pendiente de Deni antes del freeze del 6-sep.

## Verificación

Instalé dbt en un venv aparte (no está en el `.venv` del repo) para no entregar el fix sin probarlo:

- **Con `main`, sin el fix:** `dbt parse` aborta con
  `Compilation Error: Required var 'bronze_cct_identifier' not found in config`.
- **Con el fix:** `dbt parse` termina en **exit 0** y genera el manifest completo (979 KB).

Ese mismo comando es ahora el job `dbt-contract` en `ci.yml`, con perfil dummy generado en el propio
step (`parse` no abre conexión, así que no versionamos nada que parezca credencial —
[[07_Security/Secrets_Policy]]). Instala solo `dbt-core`/`dbt-postgres` clavados, no
`requirements/celula-1.txt` completo, que trae Airflow y Great Expectations y tardaría minutos.

## Uso de IA

- **Archivos modificados:** `dbt/models/sources.yml`, `dbt/dbt_project.yml`,
  `.github/workflows/ci.yml`, `06_Quality_Testing/Bug_Register.md`,
  `10_Risk_Governance/Decision_Log.md`, `02_Requirements/Traceability_Matrix.md`,
  `03_Architecture/Data_Lineage_US106.md`, `_DevLog/_index.md`, este archivo.
- **Decisiones autónomas del agente:** ninguna de fondo. El agente encontró la var #11 y el hueco de
  CI, y propuso `id_estacion` para `bronze_conagua_id_column` a partir del esquema documentado en
  `DS-06_CONAGUA_SINA.md` y `src/ingesta/extractor_conagua.py` — marcado explícitamente como **no
  verificado contra datos reales**, porque la fuente no se ingiere. El reparto lo decidí yo; la
  ubicación la decidió Diana.
- **Correcciones manuales:** el agente propuso primero instalar `requirements/celula-1.txt` completo
  en el job de CI; se cambió a instalar solo los dos paquetes de dbt.

## Seguridad / calidad

- [x] `dbt parse` en verde (exit 0) con el fix, y en rojo sin él — regresión demostrada en ambos sentidos
- [x] `python _Meta/scripts/vault_lint.py .` — Vault limpio
- [x] `pytest tests/ -q` — **298 passed, 4 skipped**. Hubo que levantar el `.venv` primero: la
      máquina del PM no lo tenía, y solo traía Python 3.14 por Homebrew cuando el proyecto y el CI
      usan 3.11. Se instaló `python@3.11` y se creó el venv con esa versión, para que un verde en
      local signifique lo mismo que un verde en CI.
- [x] No se versionan credenciales: el perfil de CI se genera en el step con valores dummy
- [x] Cambio a `.github/` (regla 7 — "revisión humana explícita"): la revisa **Diana Alvarez Varela**
      como TL de Célula 1 y ratificadora de DEC-011, no Célula 5. Decisión operativa del PM bajo
      DEC-003 (compuerta única: el PM asume la revisión técnica, los TL revisan sin bloquear).
      Encadenar 5 reviewers ha sido un cuello de botella real del proyecto y quedan dos semanas al
      freeze. Queda registrado aquí para que la revisión de C5 sea una omisión consciente y auditable,
      no un olvido: si Luis Téllez quiere revisar el job `dbt-contract` después del merge, el cambio
      está aislado en un job propio y es reversible sin tocar nada más.

## Próximos pasos

- **Deni (DS-07):** confirmar `coneval_periodo_medicion` y que `coneval_v2` es la tabla buena y no
  `coneval_test`. Es lo único que separa la deuda técnica de un dato correcto. Levantado como
  **RISK-008** con fecha objetivo 6-sep: la casilla del checklist de US-106 vivía en un documento
  en `draft` que nadie reporta, y el tablero PM lee `Risk_Register` pero **no** `Bug_Register`,
  así que un bug habría quedado invisible.
- **Emilio (DS-06/DS-08):** confirmar `conapo_sample` / `grupo_edad`, y `id_estacion` cuando se
  ingiera conagua.
- **Luis García (DS-04/DS-05):** confirmar `sesnsp_test`, `conteo` y las dos tablas SINAICA.
- **Luis Téllez (C5), no bloqueante:** puede revisar el job `dbt-contract` después del merge si
  quiere. Pendiente aparte, ya identificado hoy y ese sí es suyo: `quality_gate.yml` necesita
  `types: [opened, synchronize, reopened, edited]` — sin eso, corregir las casillas de un PR nunca
  vuelve a correr el check y hay que forzar un commit vacío. Se pagó ese peaje tres veces hoy
  (PRs #73, #78, #79).
- **Checklist de freeze (US-106):** con esto se cierra el ítem de BUG-009; queda abierto el de
  `coneval_periodo_medicion`.
