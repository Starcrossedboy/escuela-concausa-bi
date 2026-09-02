---
project: "FARO"
date: "2026-08-27"
author_human: "Juan Carlos Macías Mayen"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "~2h"
touches: ["US-416", "US-412", "US-415", "REQ-004"]
tags: [devlog]
---

# DevLog — 2026-08-27 — US-416: cache TTL y timeouts de Postgres en inferencia

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo
- Confirmé el estado real de mis 3 historias antes de empezar: **US-412** y **US-415** ya estaban
  mergeadas a `main` (PR #95, 2026-08-27), aunque mi propia tabla de seguimiento y
  `Execution_Status.md` seguían diciendo "PR pendiente de abrir". La única historia realmente
  pendiente era **US-416**.
- `src/api/config.py`: nuevos settings `predicciones_timeout_ms` (3000),
  `predicciones_cache_ttl_segundos` (30), `predicciones_cache_max_entradas` (512).
- `src/api/repositorio_modelos.py`: nueva excepción `RepositorioModelosNoDisponible`.
  `RepositorioModelosPostgres` ahora ejecuta cada consulta dentro de `engine.begin()` con
  `SET LOCAL statement_timeout` (valor interpolado, no bind param -- `SET` no acepta params de
  protocolo extendido de forma confiable con psycopg2/poolers; es seguro porque el valor sale de
  `Settings`, nunca de input de usuario). `SET LOCAL` y no `SET`: su efecto muere con la
  transacción, así que nunca fuga al motor compartido con `RepositorioGoldPostgres` (US-411)
  cuando la conexión vuelve al pool. Un `OperationalError` se traduce a
  `RepositorioModelosNoDisponible`.
- `src/api/cache_predicciones.py` (nuevo): `RepositorioModelosCacheado`, cache TTL **por fila**
  `(cct, id_ciclo)` compartido entre `obtener_prediccion` y `listar_predicciones` (`cachetools.TTLCache`).
  Decisión de diseño (validada con un agente de planeación, confirmada con el usuario): cache por
  fila en vez de cachear el lote completo por la tupla exacta de CCTs pedidos -- esto último casi
  nunca tendría cache-hit real (distintos clientes rara vez piden exactamente la misma lista). Con
  cache por fila, un batch que se solapa con uno anterior solo consulta Postgres por los CCT
  faltantes, y el unitario y el batch quedan consistentes entre sí.
  - Cache negativo (`_SIN_FILA`): un CCT confirmado sin predicción no vuelve a golpear Postgres
    dentro del TTL.
  - Las excepciones nunca se cachean.
  - El timeout de un batch es **atómico**: si la consulta por los CCT faltantes falla, toda la
    petición falla (503) aunque parte ya estuviera en cache -- preferible fallar completo antes que
    devolver una página parcial que parezca completa sin indicarlo (regla SIN_DATO).
  - `threading.Lock` alrededor del `TTLCache`: las rutas son `def` síncronas (Starlette las corre
    en su threadpool), así que hay concurrencia real de hilos sobre la instancia singleton.
- `src/api/repositorio_modelos.py::get_repositorio_modelos()`: ahora `@lru_cache` (mismo patrón que
  `get_engine`/`get_settings`), para que el cache TTL persista entre requests del mismo proceso.
- `src/api/v1/predicciones.py`: ambas rutas capturan `RepositorioModelosNoDisponible` y responden
  `HTTPException(503, ...)` en vez de dejarla caer al handler genérico (que la mapearía a un 500
  menos específico).
- `src/api/app.py`: `503`/`service_unavailable` agregado a `_ERROR_POR_STATUS`/`_MENSAJE_SEGURO`.
- No se tocó `PrediccionOut`: evalué y descarté agregar una bandera de cobertura a nivel de fila --
  la degradación de esta historia es el sobre de error uniforme (`ErrorOut`), no un valor
  inventado dentro de una respuesta 200.
- `requirements/celula-4.txt`: agregado `cachetools>=5.3` (ya es dependencia probada del proyecto
  en `celula-1.txt`/`celula-3.txt`).
- `vault/03_Architecture/API_Specification.md`: §5 (fila 503) y §3.4 (columna Códigos de ambas rutas).
- Corregí el estado obsoleto de US-412/US-415 en mi propio plan de sprint (§9): pasan de
  "PR pendiente de abrir" a "Terminado", referenciando el PR #95 ya mergeado.
- Pruebas nuevas: `tests/test_cache_predicciones.py` (hit/miss/TTL/cache negativo/excepción nunca
  cacheada/batch atómico, con un espía y un timer inyectado -- sin `sleep` real; traducción de
  `OperationalError` mockeando el límite de SQLAlchemy, **sin** SQLite como sustituto de Postgres);
  `tests/fixtures_modelos.py::RepositorioModelosNoDisponibleFake`; dos casos nuevos en
  `test_api_contract.py` (503 uniforme en unitario y batch).
- Suite completa: 390 passed, 5 skipped. `vault_lint.py` limpio.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code (Sonnet 5)
- **Archivos creados/modificados:**
  - `src/api/cache_predicciones.py` (nuevo), `tests/test_cache_predicciones.py` (nuevo)
  - `src/api/config.py`, `src/api/repositorio_modelos.py`, `src/api/v1/predicciones.py`, `src/api/app.py`
  - `tests/fixtures_modelos.py`, `tests/test_api_contract.py`
  - `requirements/celula-4.txt`
  - `vault/03_Architecture/API_Specification.md`
  - `vault/12_Roadmap_Sprints/Sprints/4-juan-carlos-macias-mayen.md`
- **Decisiones autónomas del agente:**
  - Cache por fila en vez de por lote (validado con un agente de planeación por el hit-rate real
    esperado; la elección final entre ambos diseños se confirmó conmigo antes de codificar).
  - `SET LOCAL` con valor interpolado en vez de bind param, para no depender de que `SET` soporte
    params de protocolo extendido con todos los drivers/poolers.
  - No agregar bandera de cobertura a `PrediccionOut`: la degradación es el sobre de error, no un
    campo nuevo en la respuesta 200.
- **Correcciones manuales:** ninguna aún -- revisión línea por línea pendiente antes de abrir el PR.
- **Prompt inicial:** "Contextualízate con 00_Start_Here y empieza a trabajar en la historia de
  usuario pendiente de Juan Carlos Macías Mayen" -- se investigó primero el estado real de las 3
  historias (git log, PRs, DevLogs, Traceability_Matrix) antes de codificar, porque el plan de
  sprint tenía el estado de US-412/415 desactualizado.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Tests agregados/actualizados (`tests/test_cache_predicciones.py`, 2 casos nuevos en
      `test_api_contract.py`, `RepositorioModelosNoDisponibleFake`)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- La decisión de diseño del cache (por fila vs. por lote) no se confirmó con Karla Alejandra
  Monter Benitez (Tech Lead C4) ni con Manuel Serranía (C2, dueño del consumo real de
  `/predicciones/batch` desde Superset/dashboard) por falta de tiempo -- no hay documentado en
  `Screen_Specs.md` ni `API_Specification.md` el patrón real de consumo del batch. Registrado el
  bloqueo en vez de esperar (regla de desbloqueo del plan de sprint); avisar en el próximo standup.
- Igual que en US-412: `RepositorioModelosPostgres` (incluido el timeout nuevo) no se probó contra
  Postgres real con el esquema `gold` materializado -- eso es US-422 (Eloisa González Rubio).

## Próximos pasos
- Avisar en el standup del bloqueo de diseño del cache (arriba) y a C2/C3 del código de error
  nuevo `service_unavailable` (503) en el catálogo del §5 -- es aditivo, no rompe `PrediccionOut`.
- Actualizar `vault/02_Requirements/Traceability_Matrix.md` (fila REQ-004) -- coordinar con Edgar Coronel
  (PM), zona amarilla de mi Agent Context. Hoy tampoco refleja el cierre de US-412/US-415.
- Abrir PR de US-416 con Karla Monter como revisora.
