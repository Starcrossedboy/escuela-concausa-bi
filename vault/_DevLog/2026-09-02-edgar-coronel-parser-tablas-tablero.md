---
id: DEVLOG-2026-09-02-EDGAR-CORONEL-PARSER-TABLAS
title: "DevLog — El parser del tablero respeta los pipes escapados (BUG-040)"
owner: "Edgar Edmundo Coronel Navarrete"
status: filed
version: "1.0"
traces_up: ["vault/12_Roadmap_Sprints/Execution_Status", "vault/_Meta/Vault_Rules"]
traces_down: ["vault/_Meta/scripts/generate_pm_dashboard.py", "vault/_Meta/scripts/validate_pm_dashboard.py", "tests/test_generate_pm_dashboard.py"]
last_reviewed: "2026-09-02"
tags: [devlog, tablero-pm, parser, execution-status, bug040, celula-po]
---

# DevLog — 2026-09-02 — Edgar Edmundo Coronel Navarrete

**Historia:** `US-004` · Sembrar y mantener la Traceability_Matrix
**Requisito:** `REQ-007` · Trabajo en equipo, Git y documentación
**Bug:** `BUG-040`
**Rama:** `dev/edgar-coronel`
**Herramienta de IA usada:** Claude Code / opus-5

## Qué se pidió

Evaluar un handoff de la sesión de Luis Téllez que reportaba la fila `US-004` de
`Execution_Status.md` con 8 celdas en vez de 6, y corregirlo.

## Qué encontré

El handoff diagnostica bien el síntoma —verifiqué cada afirmación corriendo el código— y su
observación más fina es correcta: **escapar el pipe con `\|` no arregla el tablero**, porque el
parser tampoco interpretaba el escape. Pero su corrección apunta al lugar equivocado.

**El defecto está en el parser, no en la fila.** `table_cells()` partía la línea cruda por todos
los pipes. El `|` de un wikilink con alias no separa columnas: es sintaxis de Obsidian, y el
vault la escribe escapada **190+ veces**. La usan seis funciones de parseo —`stories`,
`execution`, `people`, `github_directory`, `markdown_rows`, `raci`—, así que la trampa estaba
armada en seis tablas.

**El propio archivo ya tenía la solución.** Diez líneas más abajo, `parse_devlog_authors`
protegía `\|` antes de partir, con un comentario que lo explicaba. Nunca llegó a la función
compartida. Y `clean()` ya sabía resolver `[[ruta|texto]]` a `texto`: solo se le destruía el
enlace antes de que pudiera hacerlo. El diseño siempre quiso soportar alias; era un problema de
orden.

**Al corregir el parser apareció más daño del mismo tipo.** Con un contador que respeta escapes:

- 4 filas del **índice de DevLog** llevaban el pipe sin escapar y atribuían el DevLog a su
  propia descripción. El tablero contaba **25 autores** en vez de 21.
- Normalizadas esas, quedaron 3 **variantes de nombre** —`Serrania` sin ñ, `Gonzalez` sin
  acento, `Carlos Mayorga` en corto—. Como `build_engagement` cruza por coincidencia exacta
  contra el nombre canónico, **Manuel figuraba con 0 DevLogs teniendo 12**, Eloísa con 0 de 3 y
  Carlos con 0 de 1. Es la entropía de identidades otra vez, ahora falseando las métricas por
  persona del tablero que se usa para dirigir el proyecto.
- Mi propia fila de `BUG-040` nació con el defecto: escribí `` `|` `` sin escapar al citar el
  carácter y salió con 9 celdas. La atrapó el contador nuevo antes de commitear.

## Qué hice

- `table_cells()` protege el pipe escapado antes de partir y lo restituye dentro de la celda.
- `parse_devlog_authors` deja su copia y usa la función canónica (regla 1 del vault: un tema,
  un archivo canónico).
- Fila `US-004`: se **escapa** el pipe —queda consistente con las otras 189 filas del vault, no
  como excepción— y se suelta la fecha sobrante. `updated` vuelve a ser `2026-08-29` y la
  evidencia deja de estar truncada con un `[[` sin cerrar.
- 4 filas del índice de DevLog escapan su pipe; 3 variantes de nombre se normalizan al padrón.
- `validate_pm_dashboard.py` valida que `updated` sea una fecha. Antes esta clase de defecto
  pasaba **silenciosa**: el snapshot seguía siendo "válido" porque nadie miraba ese campo.

## Qué revisé yo

- Que el escape no bastara: probé `\|` y `|` contra el parser viejo — ambos dan 7 celdas y
  basura en `cells[5]`. El handoff tenía razón.
- Que el validador nuevo de verdad atrape el defecto: inyecté la fila rota en el JSON y
  confirmé `exit 1` con el mensaje correcto, luego restauré.
- El alcance real: 6 funciones usan `table_cells`; `Traceability_Matrix.md` solo se hashea para
  el fingerprint, así que sus alias no corrompen nada.
- Que las 6 "filas desalineadas" que quedaban en el índice eran **otra tabla** de 2 columnas —
  falso positivo de mi propio escaneo, no un defecto.

## Pruebas ejecutadas

```
pytest tests/ -q                                  ✅ 774 passed, 5 skipped
pytest tests/test_generate_pm_dashboard.py -q     ✅ 10 passed (TEST-015, nuevo)
python3 vault/_Meta/scripts/vault_lint.py .       ✅ Vault limpio
ruff check .                                      ✅ All checks passed
generate + validate_pm_dashboard                  ✅ 91 US, 21 personas, 8 fuentes
```

Sobre la fuente real, después del arreglo: **0 historias** con `updated` fuera de formato,
**0 evidencias** con wikilink sin cerrar, **21 autores** en el índice y todos en el padrón.

## IDs tocados

`BUG-040` · `US-004` · `REQ-007` · `TEST-015`

## Próximos pasos

Ninguno de esta clase en las tablas que alimentan el tablero. Quedan 4 filas de
`Bug_Register.md` (BUG-010, 025, 026, 027) y algunas de `Traceability_Matrix.md` con columnas
desalineadas: **no corrompen datos** —ninguno de los dos se parsea posicionalmente— pero rinden
mal en GitHub. Conviene limpiarlas después del code freeze, no antes.
