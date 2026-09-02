---
project: "FARO"
date: "2026-09-01"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — consolidación Carril C (runtime de las 6 costuras) + fix del bloqueante hallado: /municipios 500 en municipios SIN_DATO (BUG-035)"
touches: ["BUG-035", "P-03", "US-103", "REQ-004"]
tags: [devlog, api, bugfix, sin-dato, carril-c, carril-b, bug035]
---

# DevLog — 2026-09-01 — `/municipios` 500 en municipios SIN_DATO (BUG-035)

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

Durante la **consolidación de Carril C** (reconstrucción limpia §5.1 desde `main` `c042e8e` y
verificación en runtime de las 6 costuras de la remediación) el smoke-test §5.2 de la API destapó un
defecto que **ninguna costura individual mostraba**: `GET /api/v1/municipios` devolvía **HTTP 500**.
Es una interacción cruzada entre dos cambios individualmente correctos y ya mergeados: el fix
**P-03/US-103** (que hizo de `gold.dim_municipio` el universo INEGI de ~317 municipios, con los
atributos de negocio por LEFT JOIN y **NULL/SIN_DATO explícito** donde no hay dato) y el contrato de
la API (`MunicipioOut.poblacion: StrictInt`).

## Diagnóstico (traza real, no deducción)

Traceback del contenedor API en runtime:

```
File "/app/src/api/repositorio_gold.py", line 239, in _municipio_dict
TypeError: int() argument must be ... not 'NoneType'
```

`_municipio_dict` normalizaba `poblacion` (que llega como `Decimal` de Postgres) con
`int(datos["poblacion"])` **sin guardar el NULL**. Tras P-03, `gold.dim_municipio` contiene
municipios del universo geo sin fila CONAPO → `poblacion IS NULL` por diseño (en los fixtures,
**307 de 317**). `int(None)` reventaba, y `MunicipioOut.poblacion` era `StrictInt` (no admitía
`None`). Afectaba tanto `/municipios` (lista) como `/municipios/{cve_mun}` de cualquier municipio
sin dato.

**Demostración decisiva** (mismo stack, tras el fix): `/municipios/09003` (Coyoacán,
`poblacion=55000`) siempre respondió 200; `/municipios/09017` (Venustiano Carranza, sin fila CONAPO)
pasó de **500 → 200** con `poblacion:null`. Es el NULL, no la lógica del endpoint.

## Fix (un defecto, un PR)

Dos líneas, en la frontera con la BD y en el contrato — sin tocar el modelo de datos (P-03 es
correcto: el municipio **no** debe borrarse ni inventarse un 0):

1. `src/api/repositorio_gold.py::_municipio_dict` — null-guard:
   `int(poblacion) if poblacion is not None else None`. Preserva la coacción `Decimal→int` para los
   valores reales y **propaga el `None` explícito** (SIN_DATO).
2. `src/api/schemas.py::MunicipioOut.poblacion` — pasa de `StrictInt` a `StrictInt | None`
   (`default=None, ge=0`), **igual que `indice_rezago_social`/`pobreza_pct` ya lo hacían** en ese
   mismo modelo. El SIN_DATO se expone como `null`, coherente con "nunca cero, nunca nulo silencioso"
   (CLAUDE.md §4): el `null` es la señal, no un hueco escondido.

Los demás campos de `MunicipioOut` no necesitan cambio: `nombre_municipio`/`cve_mun` vienen del
catálogo geo (nunca NULL) y `rezago`/`pobreza` ya eran `| None`. Las coacciones `int()/float()` de
`obtener_kpis` usan `coalesce(...,0)`/`or 0.0`, así que quedan fuera de alcance (otro endpoint, no
disparó); se anotan abajo, no se tocan (§9, un defecto por PR).

## Validación (local, sobre lo desplegado)

- **Stack desplegado** (`docker compose`, API montando `./src` ro, reiniciada): `/municipios` lista
  → **200** (`total=317`, SIN_DATO como `null`); `/municipios/09017` → **200** `poblacion:null`;
  `/municipios/09003` → **200** `poblacion:55000` (sin regresión).
- **Suite completa** (`.venv311`, Python 3.11.16): **669 passed, 5 skipped, 0 failed, 0 errors** —
  cero regresiones.
- `ruff check .` (modo estricto, gate CI) → **All checks passed!** (repo completo y archivos tocados).

## Nota de territorio

El endpoint y su schema son **superficie de API (Carril B / C4)**, la misma que US-411/REQ-004. La
causa raíz es la interacción con P-03 (dato). Rama **`carril-b/fix-municipios-sin-dato`** sobre `main`
fresco, independiente (sin apilar). No mergeo: PR para @edgarcoroneln (PO).

## Fuera de la lista (anotado, no tocado)

- `repositorio_gold.py:291` — `float(fila["indice_completitud_drivers"])` en `obtener_kpis` podría
  reventar si un filtro (`cve_mun`/`cve_ent`) sin escuelas hace que el `AVG` devuelva NULL. No
  disparó en el smoke-test y es **otro endpoint**; se deja como observación para no mezclar defectos.
- Costura C4: los `not_null` de `dim_municipio` (`nombre_entidad`, `poblacion`) **fallan a propósito**
  bajo fixtures (307 SIN_DATO) — es la alarma ruidosa que P-03 diseñó, no una regresión; se resuelve
  con datos reales (P-01).
