---
project: "FARO"
date: "2026-09-04"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — redeploy correctivo de BUG-044 (matrícula triplicada) en la URL pública"
touches: ["BUG-044", "US-411", "US-505", "REQ-004", "REQ-005"]
tags: [devlog, deploy, cloud-run, bug, matricula, ciclo, prod]
---

# DevLog — 2026-09-04 — BUG-044: redeploy correctivo (matrícula del ciclo vigente en prod)

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

En **L1** (2026-09-03) dejé la URL pública con Gold real y OAuth vivos, sellando la imagen `e8ec818`
(revisión `faro-api-00008-nrj`). En esa imagen `/kpis` reportaba **matrícula 20,638,574 · variación
−1.81%**, y yo lo di por bueno porque coincidía **byte a byte** con el de-risk local. Coincidía, pero
**ambos estaban mal**.

**Karla Monter (US-411) encontró la causa y la corrigió en código: BUG-044 (critical).** `/kpis` y
`/escuelas` **sin `ciclo` explícito no filtraban**: sumaban los **tres** ciclos que hoy conviven en
`gold.fact_escuela_ciclo`. La matrícula salía **triplicada** y las escuelas **duplicadas**. Su fix
(PR #210, `_ciclo_mas_reciente()` como valor por defecto + 3 pruebas de regresión) ya estaba **mergeado
en `main`**, pero **prod seguía sirviendo la imagen anterior** (`00008-nrj`, sin el fix). Es el mismo
patrón de siempre: el código correcto en `main` no llega solo a la URL pública — **hay que sellar y
redesplegar** (parte deploy/C5, criterio DEC-012).

Aritmética que confirma que era una suma de ciclos (no un dato inflado en origen):

| ciclo | matrícula | escuelas |
|---|---|---|
| 2022-2023 | 7,025,984 | 44,160 |
| 2023-2024 | 6,908,361 | 44,292 |
| **2024-2025 (vigente)** | **6,704,229** | **44,114** |
| **suma (lo que servía prod)** | **20,638,574** | **132,566** |

La cifra honesta del **ciclo vigente 2024-2025** es **6,704,229 alumnos · 44,114 escuelas · variación
−2.86%** (no −1.81%, que era otro artefacto de las tres series encimadas).

## Qué se hizo

- **Validación local primero (regla LOCAL-FIRST de Luis).** Antes de tocar prod, corrí la app con el
  código de `main` (que ya trae el fix de Karla) contra la base real `escuela_real` en local (imagen con
  dependencias + `./src` montado de solo lectura, puerto 8091, `AUTH_LECTURA_PUBLICA=true`). `/kpis` sin
  `ciclo` → **6,704,229** (ya no 20.6M); `/kpis?ciclo=2022-2023` → **7,025,984**. El default discrimina y
  el filtro explícito también. **GREEN en local** → recién entonces propuse el redeploy.
- **Rebuild `linux/amd64` desde contexto limpio de `origin/main`.** `git archive origin/main` →
  `docker buildx build --platform linux/amd64 --build-arg GIT_SHA=38be8f2…` → push a Artifact Registry
  (`faro-api:38be8f2…`). El `--platform` es obligatorio: sin él la imagen sale arm64 y **no arranca en
  Cloud Run** (aprendizaje de L1). El `--build-arg GIT_SHA` sella `/version` con el commit real.
- **`gcloud run services update faro-api --image …:38be8f2…` (NO el deploy completo).** Elegí `update
  --image` a propósito: **cambia solo la imagen y preserva** env vars, secrets, service account
  (`faro-api-sa`, mínimo privilegio) y VPC connector de las revisiones anteriores. Así **no re-inyecto
  `ANALISTA_EMAILS`** (el correo del PO sigue **efímero**, solo en la revisión, nunca en el repo) ni
  toco OAuth/RBAC. → nueva revisión **`faro-api-00009-svt`** al **100%** del tráfico.

## Cómo lo probé (verificación manual en la URL pública)

`BASE=https://faro-api-eanzfglvyq-uc.a.run.app`

```
$ curl -s $BASE/api/v1/version
{"api":"v1","commit":"38be8f27f5079d7f3079929d774dbd3403f4e77c"}   # nueva imagen sellada (era e8ec818)

$ curl -s $BASE/api/v1/kpis
matrícula 6,704,229 · variación -2.86% · completitud 0.1966        # ciclo vigente, ya NO 20.6M/-1.81%

$ curl -s "$BASE/api/v1/kpis?ciclo=2022-2023"
matrícula 7,025,984                                                # el filtro discrimina por ciclo

$ curl -s -o /dev/null -w "%{http_code}\n" $BASE/api/v1/auth/login   # 302 → Google (OAuth intacto)
$ curl -s -o /dev/null -w "%{http_code}\n" $BASE/api/v1/admin/export # 401 sin token (RBAC intacto)
$ curl -s -o /dev/null -w "%{http_code}\n" $BASE/api/v1/municipios   # 200 (BUG-035 sigue cerrado)
302
401
200
```

`update --image` cumplió lo prometido: **el dato quedó corregido y OAuth/RBAC/`/municipios` siguen
exactamente igual** que tras L1.

## Dependencias y handoffs

- **⚠️ Superset (C2) NO pasa por la API.** Los 10 dashboards de Superset consultan la base de datos
  **directamente** (cubos `gold.cubo_*`), no a través de `/kpis`. Por eso **este fix de la API NO cubre
  los tableros**: si un cubo agrega `fact_escuela_ciclo` sin filtrar por ciclo, hereda la misma
  triplicación. **Handoff a C2 (Manuel / Oscar):** verificar que los cubos de matrícula filtran por
  `id_ciclo = MAX(...)` o exponen el ciclo como filtro. Los KPIs en Superset deben concordar con el
  **6,704,229** del ciclo vigente, no con la suma.
- **US-411 (Karla) puede cerrar la parte de prod:** el redeploy y la reverificación en vivo que pedía su
  DevLog (mismo criterio DEC-012 que US-412/US-416) ya están hechos. El cierre administrativo de US-411
  y su reflejo en la matriz son de C4 (no los toco desde aquí).

## Aprendizajes

- **Coincidir con el de-risk local no prueba que el dato sea correcto — solo que es el mismo dato.** En
  L1 validé *paridad* (prod == local) pero no *veracidad* (¿es la cifra del ciclo vigente?). Un KPI sin
  el filtro de ciclo se veía plausible (~20M) y pasó. La lección: para un agregado, verificar contra una
  **verdad independiente** (el conteo por ciclo de la propia tabla), no solo contra otra copia del mismo
  cálculo.
- **`update --image` es la herramienta correcta para un hotfix de imagen** cuando la config de la
  revisión ya es la buena: mínimo blast radius, cero riesgo de perder secrets/SA/VPC y cero manejo del
  correo del PO. El deploy completo (`deploy-cloud-run.sh`) queda para cuando cambia la *configuración*,
  no solo el código.

---

*Sin cambios de código en este trabajo: el fix es de Karla (PR #210, `main`); esto es la operación de
sellar la imagen de `main` y redesplegarla (C5). El correo del PO no se versiona (Secrets_Policy).*
