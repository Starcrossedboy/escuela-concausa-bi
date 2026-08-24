---
project: "FARO"
date: "2026-08-23"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "3h"
touches: ["US-313", "US-311", "DEC-010", "DEC-007", "REQ-003", "TEST-006", "DOC-PUBLICACION-GOLD"]
tags: [devlog, celula-3, gold, dec-010]
---

# DevLog — 2026-08-23 — Grano dual de `gold.predicciones` (DEC-010)

→ [[_DevLog/_index|Volver al índice]]

## Contexto

En el PR #56 dejé abierta una pregunta de contrato: si ML-01 predice a `municipio × nivel`
(DEC-007), ¿la predicción **se reparte** a las escuelas del grupo o la tabla **admite ambos granos**?

Diana Alvarez la resolvió como **DEC-010** el 23 de agosto, eligiendo el grano dual: se agrega el
discriminador `grano` con `cve_mun`+`nivel` como llaves alternativas a `cct`, en vez de repartir.
El razonamiento quedó en el `Data_Model` §4.5: *repartir le atribuiría a una escuela un valor que no
se midió ahí, el mismo tipo de dato inventado que las reglas de `SIN_DATO` prohíben*.

Esta sesión lo implementa.

## Lo entregado

- `PrediccionGold` gana `grano`, `cve_mun` y `nivel`, con un `model_validator` que exige
  **exactamente una** llave según el grano.
- `construir_predicciones()` declara `grano = escuela`.
- **Nueva** `construir_predicciones_municipio_nivel()`, que cierra el circuito con
  `target_hibrido.agregar_a_municipio_nivel()` de DEC-007.
- La tabla gana un `CHECK` y **dos índices únicos parciales**, uno por grano.
- `escribir()` elige su objetivo de conflicto según el grano del lote.
- 12 pruebas nuevas (TEST-006 pasa de 20 a **32** casos).

### Tres capas para una sola regla

La restricción de §4.5 se hace cumplir en tres lugares a propósito:

1. **Pydantic** rechaza la fila antes de escribirla — protege al job.
2. **El `CHECK` en la base** la rechaza aunque alguien escriba por SQL directo, sin pasar por el job.
3. **Dos índices únicos parciales** dan la unicidad: no hay llave primaria posible, porque una PK no
   admite nulos y las dos llaves se excluyen entre sí.

El UPSERT **rechaza lotes que mezclen granos**: con dos índices, un lote mixto haría ambiguo contra
cuál resolver el conflicto. Es mejor un error que una escritura silenciosamente incorrecta.

## Un hallazgo del camino

Al intentar entrenar sobre el grano agregado, `entrenar_y_evaluar()` fallaba con `KeyError: 'cct'`:
su desglose de error por entidad derivaba la entidad **siempre del CCT**, así que **el entrenador no
podía correr sobre el grano de DEC-007** en absoluto.

Se generalizó con `_entidades_de()`: toma la entidad de `cct` a nivel escuela o de `cve_mun` en el
grano agregado. Ambas claves INEGI empiezan con la entidad, así que el desglose de US-312 funciona en
los dos granos **sin pedir columnas nuevas a la Célula 1**.

Era un bloqueo silencioso: DEC-007 estaba decidido y la agregación implementada, pero nadie había
intentado entrenar sobre ella.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/publicar_gold.py`, `src/modelos/entrenar_ml01.py`,
  `tests/test_publicar_gold.py`, `15_ML_Models/Publicacion_Gold.md`
- **Decisiones autónomas del agente:**
  - Índices únicos parciales en vez de una PK con columnas nulas o una llave sintética: es la forma
    natural de expresar "una llave por grano" en PostgreSQL y SQLite.
  - Duplicar la regla en el `CHECK` además del validador: el job no es el único que puede escribir.
  - Rechazar lotes de grano mixto en vez de intentar resolverlos por fila.
  - Generalizar `_entidades_de()` en vez de crear un entrenador aparte para el grano agregado.
- **Correcciones manuales:** revisión línea por línea. Dos errores propios: un reemplazo automático
  de `dict()` a literal rompió la sintaxis de tres pruebas (cambió las aperturas y sólo un cierre),
  reescritas después con un helper `_fila_base()` que deja ver qué varía cada caso; y una prueba
  entrenaba con objetivo constante, cambiada a una serie simulada.

## Verificación

- Suite completa **310 passed, 4 skipped** · `ruff` limpio en archivos propios · `vault_lint` ✅
- El `CHECK` y los índices parciales se ejercitaron con **SQLite**, que también los aplica: hay
  pruebas de que la base rechaza una fila con ambas llaves y una sin ninguna.

> **Pendiente:** la comprobación contra **Postgres** no se pudo hacer — Docker Desktop no estaba
> corriendo en esta sesión. El código es dialecto-aware y los `postgresql_where` están declarados,
> pero conviene correrlo contra Postgres antes de darlo por cerrado.

## Pendiente

1. **Verificar el grano dual contra Postgres** (ver arriba).
2. **Forma exacta del contrato de la API:** DEC-010 la deja pendiente con Christian Ruiz, dueño de
   `PrediccionOut`, que hoy asume grano escuela.
3. **BUG-008 sigue `open`** y el `CMD` del Dockerfile intacto: el contenedor sigue sirviendo el hola
   mundo. Quedan **5 días** para el ensayo E2E del 28–29, que evalúa la URL pública.
4. La serie SNIEE / el extractor multi-ciclo del 911 sigue siendo lo que separa estas métricas de
   ser reales.
