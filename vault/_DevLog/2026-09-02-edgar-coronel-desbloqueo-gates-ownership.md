---
id: DEVLOG-2026-09-02-EDGAR-CORONEL-DESBLOQUEO-GATES
title: "DevLog — El padrón permite lo que la plantilla exige (BUG-039)"
owner: "Edgar Edmundo Coronel Navarrete"
status: filed
version: "1.0"
traces_up: ["vault/02_Requirements/User_Stories", "vault/_Meta/Vault_Rules"]
traces_down: ["vault/_Meta/ownership.yml", "vault/06_Quality_Testing/Bug_Register", "tests/test_check_ownership.py"]
last_reviewed: "2026-09-02"
tags: [devlog, gobernanza, gate, ownership, bug039, celula-po]
---

# DevLog — 2026-09-02 — Edgar Edmundo Coronel Navarrete

**Historia:** `US-001` · Rama fija por persona y consolidación del vault
**Requisito:** `REQ-007` · Trabajo en equipo, Git y documentación
**Bug:** `BUG-039`
**Rama:** `dev/edgar-coronel`
**Herramienta de IA usada:** Claude Code / opus-5

## Qué se pidió

Revisar un handoff de la sesión de Luis Téllez que reportaba dos huecos del gate de propiedad,
y decidir qué corresponde hacer.

## Qué encontré

El handoff acierta en que algo está roto y en el instrumento para arreglarlo (`comunes`), pero
el diagnóstico quedó corto en tres puntos:

**El mecanismo estaba mal atribuido.** El documento sostiene que `vault_lint` reprueba por
documentos huérfanos. No lo hace: los huérfanos se imprimen como informativos y **no suman a
`problems`**. El choque real es con el gate de plantilla (G9), cuya casilla obligatoria exige
«Listado en el `_index.md` de su carpeta». Misma conclusión, causa distinta — y la distinción
importa, porque de otro modo la próxima corrección iría dirigida al linter, que no tiene culpa.

**Faltaba el hueco más grave.** El handoff pospone
`vault/02_Requirements/Traceability_Matrix.md` a «próximos pasos», razonando que al no ser
`merge=union` no admite el mismo tratamiento. Eso mezcla dos cosas independientes:
`merge=union` gobierna **conflictos de fusión**, `ownership.yml` gobierna **quién puede editar**.
La matriz bloquea más que el índice de DevLog —la plantilla la exige en dos casillas
obligatorias, así que reprueba **todo PR que cierre una historia**— y el diseño del vault ya
estaba decidido: la tabla 🟡 de los 21 Agent Contexts dice «actualiza su fila; el PM consolida».
El permiso solo tenía que reflejarlo.

**Había un quinto hueco.** Ocho personas de C1 y C4 tienen un `.md` de `03_Architecture` en
verde sin poder tocar `vault/03_Architecture/_index.md`: no pueden registrar un documento nuevo
ahí, que es la regla 4.

Medido con el propio gate: **20 de 21 personas con 4 rutas obligatorias fuera de alcance**, el
PM con 2. Nadie podía abrir un PR que pasara sus propios gates.

**Y al correr el gate contra esta misma corrección apareció el alcance real.** Reprobó por
`Bug_Register.md` y por `tests/`, lo que llevó a la regla de fondo: `Definition_of_Filed` obliga
a cualquiera a dar de alta el bug, el riesgo, el bloqueo o el hallazgo de seguridad que
encuentre, y **los seis registros de intake estaban cerrados a 0 o 1 persona**. `Bug_Register.md`
no era de nadie. Es decir: la regla que manda reportar un defecto era imposible de cumplir para
20 de 21. Se corrigió por la regla —los seis registros— y no por las dos rutas que este PR
tocaba, que habría dejado los otros cuatro huecos esperando.

## Qué hice

- Once rutas a `comunes` en `ownership.yml`: el índice de DevLog, la matriz de trazabilidad,
  `.gitignore`, `.gitattributes` y los **seis registros de intake** de `Definition_of_Filed`.
- `vault/03_Architecture/_index.md` al amarillo de C1 y C4; `tests/**` al del PM, que mantiene
  `vault/_Meta/scripts/**` y no podía probar su propio código.
- `vault/10_Risk_Governance/**` entra a `criticos`: el PM se entera cuando alguien anexa a un
  registro de gobernanza, sin que eso reprube el PR.
- La matriz **permanece en `criticos`** con el PM como dueño: el gate deja de reprobar pero
  sigue avisando a quién pedirle revisión, que es exactamente el comportamiento que describe
  la regla 7.
- El índice de DevLog sale del verde del PM, donde ya solo era redundante.
- `.venv/` → `.venv*/`, para que cubra `.venv311` y variantes.
- `BUG-039` registrado con su fila completa.

## Qué revisé yo

- Que los huérfanos no sumen a `problems` en `vault_lint.py` — leído en el código, no supuesto.
- Que `BUG-036` y `BUG-037`, los IDs que proponía el handoff, **ya están ocupados** (conteo de
  filas de `cargar_fixture()` y columnas de `sync_semantic_layer.py`). El último registrado era
  `BUG-038`. Usarlos habría violado la regla 3 y DEC-013. Se usa uno solo, `BUG-039`: es un
  defecto de una sola clase y partirlo en dos no aporta trazabilidad.
- Que `.venv311` no existe en esta máquina y `git status` estaba limpio: el fix es defensivo,
  no corrige nada local.

## Pruebas ejecutadas

```
pytest tests/test_check_ownership.py -q     ✅ 40 passed (15 casos nuevos)
pytest tests/ -q                            ✅ 764 passed, 5 skipped
python3 vault/_Meta/scripts/vault_lint.py . ✅ Vault limpio
ruff check .                                ✅ All checks passed
```

Simulación del caso real —Diana cierra US-106 cumpliendo Definition of Filed— sobre el padrón
corregido: las cinco rutas dentro de alcance. Antes fallaban dos.

## IDs tocados

`BUG-039` · `US-001` · `REQ-007` · `TEST-014`

## Próximos pasos

Ninguno pendiente de esta clase. La prueba nueva recorre a los 21 contra cada ruta que la
plantilla exige **y contra cada registro de intake de `Definition_of_Filed`**, así que un hueco
equivalente reprueba en CI antes de llegar a `main`. La lección de método: el gate encontró sus
propios huecos cuando se le corrió contra su corrección — conviene hacerlo siempre.
