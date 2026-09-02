---
project: "FARO"
date: "2026-08-28"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["US-312", "US-311", "REQ-003", "TEST-007", "BUG-015", "BUG-023"]
tags: [devlog, celula-3, ml, evaluacion]
---

# DevLog — 2026-08-28 — Los drivers excluidos salen del print y entran al artefacto

→ [[vault/_DevLog/_index|Volver al índice]]

## Lo que pidió el PM

Que "el modelo entrena con 5 de 6 drivers porque DS-06 no tiene descarga verificada" esté en un
artefacto publicado y no en un `print`. Tiene razón en el fondo: un driver que no aporta nada es una
fuente que no está llegando, y eso es un hallazgo del proyecto.

## Lo que encontré al ir a hacerlo

**El reporte ni siquiera podía generarse en ese escenario.** `error_por_entidad` y
`cobertura_y_error` predecían con los seis drivers aunque el modelo se hubiera entrenado con cinco:

```
❌ error_por_entidad: ValueError: The feature names should match those that were passed during fit.
   Feature names unseen at fit time: - d5_agua
```

Es exactamente el defecto que le señalé a Andrés en la revisión de #116 —predecir con columnas
distintas a las del entrenamiento— y lo tenía yo, en el archivo que hace el reporte, sin verlo. Lo
señalé en el código ajeno el mismo día que estaba en el mío.

No apareció antes porque el fixture tiene los seis drivers completos: el escenario que rompe es el
único que el fixture no representa. Es la tercera vez esta semana.

## Lo que quedó

**En `Evaluacion_Modelos.md`**, sección 5 nueva: tabla de qué driver entró a cada modelo, la frase
en prosa —`ML-01 entrena con 5 de 6 drivers; queda fuera d5_agua`— y un 5.1 con las **exclusiones
por ventana**, que mantiene viva la distinción que costó dos vueltas en BUG-015: un driver ausente
siempre es un hueco de fuente que alguien debe ir a buscar; uno ausente sólo en las ventanas viejas
se resuelve solo al cargar más ciclos. No son el mismo problema ni tienen el mismo dueño.

Cuando no falta ninguno, el texto **lo afirma** en vez de dejar una tabla vacía: una tabla vacía se
lee como "no se midió".

**En MLflow**, verificado contra un backend sqlite real:

```
params.drivers_usados      ['d1_pobreza', 'd2_inseguridad', 'd3_infraestructura', 'd4_conectividad', 'd6_aire']
params.drivers_excluidos   ['d5_agua']
params.n_drivers_usados    5
tags.cobertura_drivers     5 de 6
params.drivers_sin_datos   ['d5_agua']        ← en cada corrida hija, por ventana
```

Así la pregunta "¿con qué datos se entrenó esto?" tiene respuesta meses después, cuando el print de
la consola ya no exista.

## Segunda pasada, tras la revisión del PM

Edgar señaló tres cosas y las tres eran ciertas:

**1. El artefacto publicaba lo contrario de lo pedido.** El reporte se genera contra el fixture, que
trae los seis drivers, así que §5 decía "ningún driver quedó fuera". La maquinaria estaba bien pero
la afirmación publicada era la negación de la que iba a citarse en la demo. El `[!warning]` de
arriba acota *las cifras*, y §5 no es una cifra: es una afirmación de hecho sobre cobertura de
fuentes. Ahora §5 lleva un bloque que acota la tabla a la corrida que la generó y dice el estado
real: `features_escuela.sql` fija `d5_agua = NULL` y nadie consume `silver.agua_region`, así que
contra Gold real serán 5 de 6 y D5 será el que falte.

**2. §5.1 publicaba exactamente la tabla vacía que yo declaro ilegible tres párrafos antes.** Apliqué
mi propio criterio en §5 y no en §5.1. Es el mismo `if` vacío, y no lo vi porque el fixture tampoco
produce exclusiones. Ahora hay `_md_o_prosa()` y lo dice con palabras.

**3. El defecto de `evaluar.py` no estaba en el registro.** BUG-015 y BUG-018 sí; éste no —y es el
que sostiene la lección que le estoy predicando al equipo. Queda como **BUG-023**; el 022 se deja
libre a propósito para Monserrat Miranda, porque un hueco de numeración es barato y una colisión ya
nos mordió dos veces.

De las dos menores que marcó como no bloqueantes atendí las dos: corregí el título del PR —"y a
MLflow" prometía ML-01 y ML-02 cuando sólo es ML-01— y **le puse pruebas a las 14 líneas de MLflow**,
que era literalmente el hueco que denuncia mi propio párrafo final. Se prueban con un doble inyectado
en `sys.modules`, no con el paquete real: el CI instala sólo `requirements.txt`, donde `mlflow` no
está, así que una prueba que lo importara se omitiría en silencio. Verifiqué que no fueran vacuas
quitando el `log_param` y viéndolas fallar.

## Verificación

Suite **510 passed, 5 skipped**. **9 pruebas nuevas**: la regresión del reporte que no podía
construirse, las tres de registro en MLflow y las de prosa cuando no hay exclusiones. Ruff limpio en `src/modelos/`, `vault_lint` limpio. Reporte regenerado.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/evaluar.py`, `src/modelos/entrenar_ml01.py`,
  `tests/test_evaluar.py`, `vault/06_Quality_Testing/Automated/Evaluacion_Modelos.md` (regenerado),
  `vault/02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:**
  - Arreglar el `predict` antes de agregar la sección: la funcionalidad pedida era imposible sin eso.
  - Afirmar la ausencia de exclusiones en prosa en vez de dejar una tabla vacía.
  - Registrar la exclusión también **por ventana** en las corridas hijas, no sólo el agregado.
- **Correcciones manuales:** revisión línea por línea.

## Pendiente

1. **BUG-020** con C4/C5 — el 500 de la URL pública. Es lo que topa la nota en 6.0.
2. **ADR-007** sin ratificar.
3. Sugerir a Andrés que ML-02 imprima sus exclusiones como ML-01, y que
   `excluidos_por_ventana` deje de ser `None` por omisión.
