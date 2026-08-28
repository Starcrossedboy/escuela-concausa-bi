---
project: "FARO"
date: "2026-08-27"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "2h"
touches: ["BUG-013", "US-313", "US-311", "REQ-003", "TEST-005", "TEST-006"]
tags: [devlog, celula-3, gold, bug-013]
---

# DevLog — 2026-08-27 — `--desde-gold`: publicar desde la tabla real (BUG-013)

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Diana avisó que ya cargó **4 ciclos reales (2021-2022 a 2024-2025)** en Bronze con el loader del
PR #105, y que `gold.features_escuela` se materializó contra esos cuatro. Pidió correr
`publicar_gold.py` apuntando a la tabla real en vez del fixture, para resolver el `JOIN` en cero de
DB-03.

**BUG-013 está asignado a C3 + C1.** Al revisarlo, la parte de la Célula 3 resultó ser un hueco de
código: **`publicar_gold` no podía leer de una tabla en absoluto**. `cargar_features()` sólo abría
CSV o Parquet desde una ruta, así que "apuntarlo al Gold real" no era una cuestión de configuración
sino de una función que no existía.

## Lo entregado

- `cargar_features_desde_gold(engine, esquema, tabla)` en `entrenar_ml01.py` — lee
  `gold.features_escuela` por SQLAlchemy y valida el mismo contrato §5.3 que la ruta de archivo.
- **`--desde-gold`** en el CLI de `publicar_gold`.
- ML-02 ahora parte **del mismo DataFrame** que ML-01 en vez de releer del disco: antes
  `cargar_features_ml02(args.features)` habría seguido leyendo el fixture aunque ML-01 viniera de
  Gold, publicando recomendaciones de un universo distinto al de las predicciones.
- 4 pruebas nuevas en TEST-005.

### Tres errores distintos, tres mensajes distintos

La función no falla genéricamente. Distingue **tabla ausente** —con la instrucción de correr
`dbt run`—, **tabla vacía** y **contrato incumplido**, nombrando la columna que falta. Son tres
situaciones con causas y responsables distintos, y un mensaje único obligaría a investigar cuál es.

El caso importante: si Gold no está materializada, el job **falla** en vez de caer de vuelta al
fixture. Publicar en silencio desde datos sintéticos cuando se pidió la tabla real es justo cómo se
llega a un tablero que parece funcionar y no lo hace — que es el origen de BUG-013.

## Verificación

Materialicé el contenido del fixture como `gold.features_escuela` en el Postgres local para
ejercitar **el mecanismo** de lectura, y el camino completo corrió:

```
Features desde gold.features_escuela: 400 filas · 80 escuelas · ciclos [2019-2020 … 2023-2024]
gold.predicciones:    80 filas publicadas (upsert idempotente)
gold.recomendaciones: 80 filas publicadas (upsert idempotente)
```

La tabla simulada se eliminó después, para que nadie la confunda con la real.

> **Lo que no pude verificar:** la corrida contra los **datos reales de Diana**. Reproducir su carga
> exige descargar los cuatro CSV del 911 (~460 MB), instalar dbt y correr Bronze → Silver → Gold en
> mi máquina; su materialización vive en su ambiente, no en el mío. **El código está listo y
> probado; falta correrlo donde Gold esté materializada.**

Suite completa: **471 passed, 5 skipped**.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/entrenar_ml01.py`, `src/modelos/publicar_gold.py`,
  `tests/test_entrenar_ml01.py`, `15_ML_Models/Publicacion_Gold.md`
- **Decisiones autónomas del agente:**
  - Fallar en vez de caer de vuelta al fixture cuando se pide `--desde-gold` y la tabla no está.
  - Hacer que ML-02 parta del mismo DataFrame que ML-01; leer dos veces de fuentes distintas era un
    error latente que sólo se habría notado con datos reales.
  - Diferenciar los tres modos de fallo con mensajes propios.
  - No intentar reproducir la carga real: son ~460 MB y dbt sin instalar, a un día del ensayo.
- **Correcciones manuales:** revisión línea por línea; se verificó el camino nuevo contra Postgres
  real materializando una tabla de prueba, y se limpió después.

## Pendiente

1. **Correr `--desde-gold` donde Gold esté materializada** — con Diana, o cuando la carga esté en un
   ambiente compartido.
2. **BUG-008** sigue `open` con el `CMD` intacto. **El ensayo es mañana** y es el único bloqueo de
   la verificación #4.
3. Si la tabla real trae los 4 ciclos que Diana reporta, el backtesting sube a 3 ventanas con datos
   reales y las métricas de US-311 dejan de ser sintéticas por primera vez.
