---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión: verificación BUG-031, corrección de nota US-221, cierre de status"
touches: ["US-221", "US-224", "BLOCK-004"]
tags: [devlog]
---

# DevLog — 2026-09-04 — Verificación de BUG-031 y actualización de status

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué pedí

Un mensaje de Teams (inicialmente atribuido por error a Marina, luego confirmado como
efectivamente suyo tras revisar la captura) decía que BUG-031 pasaba a `fixed` y que la parte de
Célula 2 (Manuel/Oscar) ya estaba hecha — por Luis, no por Manuel. Pedí verificar contra el repo
si eso implicaba algún cambio de código pendiente de mi lado, en vez de aceptarlo sin más.

## Qué hizo la IA

- Confirmó con `git log`/`git merge-base` que los commits del fix (`f013b20`, `b74a700`, Luis
  Téllez, 31-ago) ya son ancestros de `dev/oscar-quiroz` — no hay nada por mergear.
- Verificó el contenido real de `metrics_db01_db02.yaml`, `metrics_db03_db04.yaml` y
  `metrics_db06_db09.yaml`: la fórmula ya es razón de sumas, sin `variacion_x_matricula` activa.
  Las dos aserciones que `Bug_Register.md` marcaba como "pendientes" ya existen y ya pasan.
- Encontró que `metrics_kpis_base_us221.yaml` (mi archivo, US-221) traía una `nota` con la fórmula
  vieja y rota de KPI-02 — inicialmente pensé que se sincronizaba a Superset como `description`
  real del metric; **verifiqué directo contra la base de metadatos de Superset** (no solo el log
  del script) y confirmé que ese archivo no lo lee `sync_semantic_layer.py` (estructura
  `tarjetas:`, no `datasets:`), así que el dato expuesto en Superset nunca estuvo mal — corregí mi
  propia conclusión antes de seguir.
- Corrigió la `nota` de todos modos, porque sigue siendo documentación viva validada por
  `tests/test_kpis_us221.py` y describía una fórmula que ya no existe.
- Corrió `pytest tests/test_kpis_us221.py` (4/4) y `sync_semantic_layer.py` completo (10/10
  tableros, sin abortos ni HTTP 422) como confirmación de que nada se rompió.

## Qué revisé yo

- No acepté la atribución del mensaje sin ver la captura real (dos idas y vueltas: primero asumí
  que era de Edgar por el banner fijado del canal, el usuario corrigió con evidencia y confirmé
  que sí era de Marina).
- No acepté mi propia primera conclusión sobre `sync_semantic_layer.py:465` sin probarla contra
  Superset real — encontré que estaba equivocada y lo dije explícitamente en vez de dejarlo pasar.

## Qué falta / bloqueos

- Ninguno de mi lado. `BLOCK-004` sigue resuelto (ver DevLog 2026-09-04 anterior). BUG-031 no
  tiene ningún pendiente de Célula 2.
- Pendiente de terceros, no de código: PR #212 sigue en `Awaiting approval` de Edgar Coronel.
- `vault/06_Quality_Testing/Bug_Register.md` (fuera de mi alcance) sigue mostrando BUG-031 como
  `open` con "Pendiente C2 · Manuel Serranía" — desactualizado frente al código real; reportado al
  dueño del área en vez de editarlo directamente.

## IDs tocados

US-221, US-224, BLOCK-004
