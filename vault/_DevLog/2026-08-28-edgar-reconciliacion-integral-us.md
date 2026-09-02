---
project: "FARO"
date: "2026-08-28"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Codex"
model: "GPT-5"
session_duration: "larga — auditoría integral de 91 US, reconciliación y reporte de junta"
touches: ["US-004", "US-106", "US-113", "US-121a", "US-122a", "US-123a", "US-124a", "US-204", "US-212", "US-213", "US-221", "US-302", "US-304a", "US-304b", "US-305", "US-311", "US-312", "US-313", "US-323", "US-324", "US-403", "US-411", "US-412", "US-415", "US-416", "US-521c", "US-522a", "US-522b", "US-522c", "US-523a", "US-524a", "REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005", "REQ-006", "REQ-007", "PLAN-EXEC-STATUS", "RPT-US-VALIDATION-2026-08-28"]
tags: [devlog, pm, status, validation, user-stories, dashboard]
---

# DevLog — 2026-08-28 — Reconciliación integral de US y seguimiento para junta

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/12_Roadmap_Sprints/Execution_Status]] ·
[[vault/13_Reports/US_Validation_Followup_2026-08-28]]

## Objetivo

Actualizar el estado completo del repositorio, contrastar las 91 User Stories con el historial de
PR, DevLogs, pruebas y artefactos disponibles, y dejar una herramienta operativa para que el PM
pueda cerrar o cambiar el estado de las US pendientes durante reuniones con sus responsables.

## Resultado

- El corte queda en **32 `done`, 23 `in_review`, 12 `in_progress` y 24 `planned`**.
- Se cerraron administrativamente **US-323, US-412, US-415 y US-523a**, porque ya contaban con
  entrega mergeada, evidencia técnica, pruebas y DevLog suficientes.
- Se llevaron a `in_review` las entregas con PR abierto/mergeado que aún requieren validación,
  dato real, E2E, aprobación de seguridad, DevLog o una decisión explícita de alcance.
- Se actualizaron `Execution_Status`, la matriz de trazabilidad y los 16 planes de sprint
  afectados para eliminar contradicciones entre vistas.
- Se creó un reporte canónico en Markdown y una vista HTML autocontenida con filtros, notas,
  estado propuesto, persistencia local y exportación JSON/CSV/Markdown.
- Se regeneró el tablero PM desde las fuentes canónicas; la actividad GitHub conservó el último
  snapshot publicado porque la autenticación local de `gh` no está vigente.

## Criterio de cierre aplicado

Un PR mergeado no se consideró cierre automático. Las historias permanecen en revisión cuando
falta una prueba E2E, ejecución con datos reales, corrección de un bug crítico, aprobación de
seguridad, documento `approved`, DevLog Filed o decisión del PM sobre una excepción de alcance.
El detalle por US, PR, responsable, acción y validador está en
[[vault/13_Reports/US_Validation_Followup_2026-08-28]].

## Alcance y límites

- No se cambió configuración viva de GitHub ni `.github/**`.
- No se editaron artefactos propiedad de otras células fuera del alcance PM, en particular
  `vault/15_ML_Models/**` y `vault/06_Quality_Testing/Bug_Register.md`; el reporte asigna esas acciones a sus
  responsables.
- El HTML guarda acuerdos en `localStorage`; no modifica automáticamente
  `Execution_Status.md`. Después de cada junta, el PM debe llevar los acuerdos al documento
  canónico mediante PR y regenerar el tablero.
- La inspección visual automatizada no estuvo disponible porque la sesión no tenía un navegador
  conectado; se cubrió la entrega con validación HTML5, sintaxis JavaScript y revisión estructural.

## Validaciones ejecutadas

- `python3 vault/_Meta/scripts/generate_pm_dashboard.py .`
- `python3 vault/_Meta/scripts/validate_pm_dashboard.py .`
- `python3 vault/_Meta/scripts/vault_lint.py .`
- Validación sintáctica del JavaScript embebido en el HTML con Node.js.
- Validación HTML5 con `tidy -errors -quiet -utf8`.
- `git diff --check`.

## Uso de IA

- **Archivos modificados:** `vault/12_Roadmap_Sprints/Execution_Status.md`, 16 planes individuales de
  sprint, `vault/02_Requirements/Traceability_Matrix.md`, `vault/13_Reports/_index.md`, el reporte Markdown,
  el HTML de seguimiento, el snapshot/tablero PM generado, `vault/_DevLog/_index.md` y esta entrada.
- **Decisiones autónomas:** clasificación conservadora de estados a partir de evidencia local;
  no se cerró ninguna historia con un gate material pendiente.
- **Acción humana pendiente:** revisar la cola del reporte con cada responsable y registrar en PR
  los acuerdos definitivos de estado.

---

## Segunda pasada — revisión de Héctor y resolución de conflictos

Héctor Morales dio VoBo técnico verificando contra los archivos, no contra la descripción del PR:
los conteos cuadran, los cierres tienen evidencia, el HTML no puede tocar la fuente canónica
(3 usos de `localStorage`, cero `fetch`/`XHR`/`sendBeacon`/`<form>`) y los gates de Célula 3 están
bien descritos. Levantó dos cosas.

**1. Evidencia envejecida en horas.** US-312 decía «PR #118 abierto»; se mergeó el mismo día a las
21:42. Al revisar encontré que no era la única: US-304a afirmaba que existía «una rama remota sin
merge» de la integración RAG y US-304b que faltaba «corregir/mergear la carga perezosa» — ambas
resueltas por PR #119, mergeado a las 21:44. Las tres actualizadas.

**2. US-411 y US-412 tratadas distinto ante el mismo bloqueo.** Tenía razón. Las dos entregan rutas
HTTP contra el mismo despliegue roto; una se sostenía abierta por BUG-020 y la otra se cerraba
difiriendo el E2E a US-422, que está `planned`. Peor: dentro de las tres historias de un mismo
dueño, US-412 cerraba y US-416 no, con el mismo diferimiento a US-422.

Se adopta un criterio explícito, escrito en las reglas de `Execution_Status`:

> Una historia cuyo entregable es **una ruta HTTP** no cierra mientras esa ruta no responda en el
> despliegue que se va a demostrar. Una cuyo entregable es **un contrato, un esquema o una
> biblioteca** sí cierra con evidencia de código, porque no tiene superficie desplegada que verificar.

Con eso US-412 vuelve a `in_review` y US-415 (contrato Pydantic) se mantiene `done`. Conteos nuevos:
**31 `done`, 24 `in_review`, 12 `in_progress`, 24 `planned` = 91.**

## Lo que apareció al verificar el despliegue

Al comprobar BUG-020 de primera mano —no confiando en el reporte— salieron dos cosas que el registro
tenía mal:

**La autenticación sí funciona en producción.** El texto de BUG-020 afirmaba que no se podía
comprobar «y eso toca US-402». No es cierto: `/auth/login` responde 302, `/auth/me` responde 401 sin
token y `/version` responde 200. Lo que no se puede comprobar es el 401 **de las rutas de datos**,
porque revientan antes. BUG-020 corregido; US-402 no queda tocada.

**BUG-025 — el agente desplegado responde lo mismo a todo.** `/agente/consulta` responde 200, lo que
parecía buena noticia. No lo es: devuelve la misma cadena, byte por byte, a «cuántas escuelas hay en
riesgo», «cuál es la capital de Francia», «Borra la tabla de predicciones» y «zzzz qqq 12345». Es el
stub de `src/api/v1/agente.py` —documentado como tal— pero nadie había registrado su consecuencia:
su filtro busca `"borrar"` por subcadena, así que **«Borra la tabla…» no lo dispara** y recibe la
respuesta normal con `fuera_de_alcance: false` y un `sql_generado` impreso al lado. Los guardarraíles
reales de `src/agente/guardrails.py` sí rechazan esa frase; la API no los llama. Mitigación de dos
líneas mientras llega la integración de US-304a: que el stub use `pregunta_en_alcance()`.

## Conflictos resueltos al traer `main`

`vault/_DevLog/_index.md` se resolvió solo por `merge=union` — vale registrarlo, porque las veces
anteriores GitHub lo reportó como conflicto irresoluble desde la web. Los cuatro reales:

| Archivo | Resolución |
|---|---|
| `vault/02_Requirements/Traceability_Matrix.md` | Unión de los dos bloques de evidencia del 28-ago |
| `vault/12_Roadmap_Sprints/Sprints/3-andres-gonzalez-habib.md` | Gana el lado de Andrés (su archivo, dato posterior a #119); se conserva BUG-020 en US-305 |
| `vault/13_Reports/TABLERO_CONTROL_PM.html` | Regenerado |
| `vault/13_Reports/data/pm-dashboard.json` | Regenerado |

## Validaciones de esta pasada

- `python3 vault/_Meta/scripts/generate_pm_dashboard.py .` → 91 US, 21 personas, 8 fuentes
- `python3 vault/_Meta/scripts/validate_pm_dashboard.py .` → TEST-002 válido
- `python3 vault/_Meta/scripts/vault_lint.py .` → vault limpio
- `pytest tests/ -q`
- Verificación en vivo de las 18 rutas del despliegue con `curl`

## Los dos checks en rojo tras resolver el conflicto

Aparecieron **al resolver el conflicto**, no por la resolución: mientras el PR estuvo `CONFLICTING`
GitHub no pudo construir el merge ref y ningún workflow corrió (`no checks reported`). Los dos
fallos venían del commit original.

**GitLeaks — falso positivo.** La línea 239 de `US_Validation_Followup_2026-08-28.html` declaraba la
llave de `localStorage` en una constante cuyo nombre terminaba en *Key*. La regla `generic-api-key`
busca un identificador con `key`/`api`/`token`/`secret`/`auth` a la izquierda de una asignación con
una cadena larga: eso basta para dispararla aunque no haya ningún secreto. Renombrada a
`claveAlmacen`, que además sigue la convención en español del repo. Verificado reproduciendo la
regla: el nombre anterior coincide, el nuevo no, y el archivo completo queda en **0 coincidencias**.
No se tocó configuración de seguridad ni se añadió `.gitleaks.toml`, que sería un cambio de CI/CD
sujeto a la regla 7.

**Segundo intento fallido, y la lección.** El primer arreglo no bastó por dos razones que conviene
dejar escritas. La primera: **este DevLog citaba la línea infractora literalmente**, así que documentar
el hallazgo volvió a introducir el patrón —ahora en un `.md`—. Un escáner de secretos no distingue
entre una credencial y la cita de una credencial; al describir un hallazgo de este tipo hay que
parafrasear, nunca pegar la línea. La segunda: `gitleaks-action` escanea el **rango de commits** del
PR (`git log -p` sobre `base^..HEAD`), no el árbol final. El commit original seguía **añadiendo** esa
línea dentro del rango, así que renombrarla en un commit posterior no podía limpiarlo: mientras ese
commit exista en la rama, el hallazgo persiste. Se resolvió reescribiendo la rama a un único commit
con el contenido final, sin `.gitleaksignore` ni allowlist.

**Plantilla del PR — hueco real del gate de BUG-014.** El cuerpo del PR quedó **indentado dos
espacios** en todas sus líneas menos la primera. El gate recorta la sección de aprobación con
`sed '/^## Aprobaci/,$d'`, anclado a columna 0, así que con `  ## Aprobación` no recortó nada y las
dos casillas del PM contaron como pendientes. No es un problema de este PR: es que **la corrección de
BUG-014 asumió que el encabezado empieza en columna 0**. Queda anotado como pendiente para un PR
propio contra `.github/**` —con revisión de C5 por la regla 7—: anclar con
`^[[:space:]]*##[[:space:]]*Aprobaci`.
