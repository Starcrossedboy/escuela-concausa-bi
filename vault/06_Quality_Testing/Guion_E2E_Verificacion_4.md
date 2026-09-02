---
id: DOC-GUION-E2E-V4
title: "Guion del ensayo E2E — Verificación #4: ML-01 sirviendo por API"
owner: "Héctor Rafael Morales Marbán"
status: in_review
traces_up: ["vault/12_Roadmap_Sprints/PLAN_MAESTRO", "vault/02_Requirements/User_Stories"]
traces_down: ["US-311", "US-313"]
tags: [qa, e2e, celula-3, ensayo]
---

# Guion del ensayo E2E — Verificación #4

> **Verificación #4** del hito crítico S4 (viernes 28 – sábado 29 de agosto):
> *«≥1 modelo sirviendo por API (ML-01) — `/predicciones` devuelve valor (real o simulado,
> **marcado**)»*. Dueños: Héctor Morales (C3) y Christian Ruiz (C4).
> → [[vault/12_Roadmap_Sprints/PLAN_MAESTRO]] · [[vault/15_ML_Models/Publicacion_Gold]] · [[vault/06_Quality_Testing/Bug_Register]]

## 1. Para qué sirve este documento

El ensayo es en vivo y con criterio go/no-go. Este guion existe para que **el tramo de la Célula 3
no se improvise ese día**: los comandos exactos, en orden, con las trampas de ambiente ya
documentadas.

**El criterio admite datos simulados si están marcados.** Eso importa: la falta de datos reales del
Formato 911 **no bloquea** esta verificación. Lo que sí bloquea son dos defectos de integración.

## 2. Estado de los prerrequisitos

| # | Prerrequisito | Estado | Dueño |
|---|---|---|---|
| 1 | ML-01 entrenado y publicando a Gold | ✅ listo y verificado contra Postgres | C3 |
| 2 | La app real servida por el contenedor | ❌ **BUG-008** — corre el hola mundo de US-501 | C5 + C4 |
| 3 | `/predicciones` leyendo Gold | ✅ **BUG-010 cerrado** — `RepositorioModelos` (PR #95, Juan Macías) | C4 |

**Queda un solo bloqueo: BUG-008.** El endpoint ya lee Gold de verdad (PR #95), pero **no es
alcanzable en el contenedor** porque éste sirve la app equivocada. Con el `CMD` corregido, la
verificación #4 es alcanzable hoy mismo con datos simulados marcados.

## 3. El tramo de la Célula 3, paso a paso

Todo esto ya funciona hoy y es lo que se ejecuta en vivo.

```bash
# 1 · Levantar Postgres
docker compose up -d db

# 2 · Apuntar al Postgres del compose desde el host
#     El .env trae POSTGRES_HOST=db, que es el hostname INTERNO de la red de Docker:
#     desde tu máquina no resuelve. Ver §4.
export DATABASE_URL="postgresql+psycopg2://postgres:<POSTGRES_PASSWORD>@localhost:5432/escuela_concausa_db"

# 3 · Entrenar ML-01 y ML-02 y publicar ambas tablas de Gold
python -m src.modelos.publicar_gold

# 4 · Comprobar lo publicado
docker exec faro-postgres psql -U postgres -d escuela_concausa_db -c \
  "SELECT grano, COUNT(*) FROM gold.predicciones GROUP BY grano;"
docker exec faro-postgres psql -U postgres -d escuela_concausa_db -c \
  "SELECT cct, ROUND(indice_riesgo::numeric,3) riesgo, driver_dominante, prioridad
     FROM gold.predicciones p JOIN gold.recomendaciones r USING (cct, id_ciclo)
    WHERE p.grano='escuela' ORDER BY indice_riesgo DESC LIMIT 5;"
```

Salida esperada: **80 filas** con `grano = escuela` y, si se publicó también el grano agregado,
46 con `municipio_nivel`. El job es idempotente: repetirlo no duplica.

La última consulta es además **la demostración del diferenciador del proyecto**: dos escuelas con
riesgo casi idéntico y driver distinto reciben recomendaciones distintas.

## 4. Trampas de ambiente ya conocidas

Las tres nos costaron tiempo en sesiones previas. Vale la pena no redescubrirlas en vivo.

1. **`POSTGRES_HOST=db` no resuelve desde el host.** Es el hostname interno de la red de Docker.
   Desde la máquina hay que usar `localhost`. Aplica igual a `MLFLOW_TRACKING_URI`, que en `.env`
   apunta a `http://mlflow:5000` mientras el servicio se publica en **`localhost:5001`**.
2. **La app real no está en la raíz.** Publica su OpenAPI en `/api/v1/openapi.json` y sus docs en
   `/api/v1/docs`. Una verificación que consulte `/docs` va a fallar aunque todo esté bien.
3. **`docker compose up -d api` usa la imagen cacheada.** Tras cambiar código de la API hay que
   agregar `--build`.
4. **El ciclo por defecto del endpoint no coincide con el que publica el job.**
   `/api/v1/predicciones/{cct}` usa `CICLO_DEFAULT = "2024-2025"`, pero `publicar_gold` escribe el
   ciclo más reciente del fixture, que es **`2023-2024`**. Sin `?ciclo=2023-2024` explícito el
   endpoint responde **404 aunque el dato esté ahí**. Con datos reales del 911 el default sí
   coincidirá, porque su ciclo más nuevo es 2024-2025 — pero para el ensayo hay que pasarlo a mano:

   ```bash
   curl "http://localhost:8000/api/v1/predicciones/<CCT>?ciclo=2023-2024"
   ```

## 5. Qué hace falta para que la verificación pase

En orden de quién bloquea a quién:

1. **BUG-008** (C5 + C4) — apuntar el `CMD` de `docker/api.Dockerfile` a `src.api.app:app`. Es un
   cambio de una línea y desbloquea la evaluación de tres células, no sólo ésta.
2. **BUG-010** (C4) — que `/predicciones` lea `gold.predicciones` + `gold.recomendaciones` en vez de
   `mock_data`. El mapeo está documentado en el registro de bugs; el único campo sin productor es
   `cluster`, que viene de ML-03 (US-321) y aún no existe.
3. **Marcar el dato como simulado.** El criterio lo permite, pero exige que se marque. Propuesta:
   que la respuesta lo declare explícitamente mientras el 911 multi-ciclo no esté cargado — el
   `mlflow_run_id` ya permite rastrear de qué corrida salió cada predicción.

## 6. Plan B de la Célula 3

Si BUG-008 y BUG-010 no se resuelven a tiempo, el tramo se puede demostrar **sin la API**:
ejecutando el §3 en vivo y mostrando las dos tablas de Gold pobladas por el modelo. No cumple la
verificación #4 como está redactada —que exige la vía API— pero evidencia que el modelo produce y
publica. Conviene acordarlo con el PO antes del 28, no durante.
