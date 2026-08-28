---
project: "FARO"
date: "2026-08-29"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "claude-sonnet-5"
session_duration: "~1h"
touches: ["US-113", "REQ-001"]
tags: [devlog, dbt, gold, bug016, source, ref]
---

# BUG-016 — `source()` en vez de `ref()` rompía el orden de build de dbt con `threads > 1`

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

Monserrat Olivas encontró que `dbt run` con `threads > 1` (el default) truena en `dim_escuela`,
`dim_municipio` y `dim_tiempo` con `relation does not exist`, aunque su silver de origen se crea
casi al mismo tiempo — con `--threads 1` corre limpio. Su hipótesis: esos modelos no usan
`{{ ref() }}` hacia su fuente silver, así que dbt no los agenda en el orden correcto.

Confirmé la causa raíz de forma estructural, no solo intentando reproducir la carrera: leí
`target/manifest.json` antes del fix y `dim_escuela` dependía de `source.faro.silver.escuela` y
`source.faro.silver.cemabe` — nodos `source`, que dbt trata como frontera externa **sin** garantía
de orden respecto a otros modelos. Pero `silver.escuela` y `silver.cemabe` **sí son modelos de
este mismo proyecto** (`dbt/models/silver/escuela.sql`, `.../cemabe.sql`), no datos externos. Al
declararlos como `source()` en `dbt/models/gold/_gold__sources.yml`, dbt nunca arma la arista de
dependencia real en el grafo.

Y era más grande de lo que Monse alcanzó a ver: no eran solo 3 modelos. Conté **16 usos de
`{{ source('silver', ...) }}` en 6 archivos Gold** (`dim_escuela`, `dim_municipio`, `dim_tiempo`,
`fact_escuela_ciclo`, `features_escuela`, `matricula_municipio_nivel`) — incluido
`features_escuela.sql`, tocado apenas ayer en el PR de `driver_dominante` (US-302).

**Fix:** reemplacé los 16 usos de `source('silver', 'X')` por `ref('X')` en los 6 archivos.
Actualicé también el comentario de `dbt/macros/generate_schema_name.sql`, que documentaba
`dim_tiempo.sql` haciendo `source('silver', 'matricula')` — ya no es cierto, y el override de
esquema sigue siendo necesario por otra razón (evitar el prefijo `dbt_diana_silver` en vez del
esquema literal). `dbt/models/gold/_gold__sources.yml` no se tocó: sigue sirviendo para
documentar las columnas de esas tablas, solo dejó de usarse para resolver dependencias.

## Cómo se verificó

No basta con correr `dbt run` una vez y ver que no truena — una condición de carrera puede no
disparar por suerte. Verifiqué de dos formas:

1. **Estructural (determinista):** leí `target/manifest.json` antes y después del fix.
   Antes: `dim_escuela` depende de `source.faro.silver.escuela` / `source.faro.silver.cemabe`.
   Después: depende de `model.faro.escuela` / `model.faro.cemabe`. Con eso dbt garantiza el
   orden sin importar los threads, no es cuestión de que "esta vez sí corrió".
2. **Comportamiento:** `dbt run --target dev --threads 4 --full-refresh` corrido 3 veces
   seguidas antes del fix y 3 veces después — mismos 8/19 errores conocidos en ambos casos
   (`gold.predicciones`/`recomendaciones` aún no publicadas en este ambiente, `agua_region` sin
   `bronze.conagua_no_ingerido` por DS-06), cero errores nuevos, cero relacionados a los 6
   modelos corregidos.

```
dbt parse --target dev                              # limpio (aviso preexistente no relacionado
                                                        sobre argumentos de test genérico)
dbt run --target dev --threads 4 --full-refresh x3   # PASS=15 ERROR=8 (conocidos) las 3 veces
dbt build --target dev --threads 4 --full-refresh    # PASS=167 ERROR=19 (conocidos) SKIP=158
python _Meta/scripts/vault_lint.py .                 # Vault limpio
```

## Avance entregado

- Corrige lo que Monse registró como `BUG-016` en su rama
  (`feat/monserrat-olivas-us213-db05-db08-dashboards`) — esa rama aún no está en `main`, así que
  no toqué `Bug_Register.md` aquí para no chocar con su fila; falta que alguien la actualice a
  `fixed` cuando ambas ramas converjan.
- **Nota de colisión de IDs, ya escalada a Edgar:** la rama de Monse y la de Héctor
  (`fix/hector-marban-driver-sin-datos`) reclamaron `BUG-015` para cosas distintas sin
  coordinarse — se resuelve al mergear, no es parte de este fix.
- Lo que aún falta: abrir PR, avisar a Monse/Manuel para que revaliden su sync de DB-05/08 con
  esto arriba, y que alguien reconcilie `Bug_Register.md` entre las tres ramas al mergear.

## Uso de IA

Sesión completa asistida por Claude (Cowork): diagnóstico leyendo `manifest.json` directamente en
vez de confiar en si la carrera se reproducía o no en una corrida suelta, localización de los 16
usos con un script en vez de editar a mano, y verificación de que el fix no introdujo errores
nuevos corriendo el build completo antes/después. Todo se corrió y verificó en el ambiente de
Claude antes de entregarlo; revisar línea por línea antes de cada commit, como siempre.
