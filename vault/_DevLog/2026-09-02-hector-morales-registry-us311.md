---
project: "FARO"
date: "2026-09-02"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1 sesión — confirmación del registry (US-311) y pipeline local para US-313"
touches: ["US-311", "US-313", "AC-003.4", "REQ-003", "BUG-041", "BUG-013", "BUG-012"]
tags: [devlog, celula-3, ml, mlflow, registry, gold]
---

# DevLog — 2026-09-02 — La corrida de confirmación de US-311 encontró que AC-003.4 nunca se cumplió

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/06_Quality_Testing/Bug_Register|Bug Register]]
· [[vault/15_ML_Models/ML01_Entrenamiento]]

## Encargo

Edgar pidió dos cosas: **re-correr ML-01 y confirmar que el modelo llega al registry** (US-311, el
fix de MLflow lleva mergeado desde el 18-ago sin corrida de confirmación) y **cerrar US-313**.

## Lo que encontré

**El modelo nunca llegó al registry.** La corrida de confirmación no confirmó: reprobó.

Las métricas se registraron perfecto —3 ventanas, MAE 0.0141 ± 0.0012, RMSE 0.0177 ± 0.0008,
idénticas a las de PR #28— y `log_model()` reventó con
`OSError: [Errno 30] Read-only file system: '/mlflow'`.

**Aclaro la atribución antes de seguir:** la causa de configuración **ya estaba diagnosticada** en
[[vault/15_ML_Models/ML01_Entrenamiento]] §4 desde el 29-ago, con el fix probado. No la descubrí
hoy. Lo que descubrí es por qué, sabiéndolo, seguíamos creyendo que AC-003.4 estaba cumplido.

La causa conocida: el servidor arranca con
`--default-artifact-root /mlflow/artifacts`, una ruta **interna del contenedor**, y sin
`--serve-artifacts` MLflow se la entrega al cliente para que escriba ahí él mismo. El cliente
—macOS, o el CI— intenta crear `/mlflow` en la raíz de su propio disco.

Lo grave no es el error, que al menos es ruidoso. Es lo que pasa con la fila del Registry:

> `mlflow.register_model()` **crea la versión de todas formas**. Queda `READY`, visible en la UI,
> apuntando a un artefacto que no existe.

Eso es **`ML01_RegresionMatricula` v1, creada el 18-ago** —el mismo día del fix de versiones— y en
verde desde entonces:

```
$ python -m src.modelos.verificar_registry --modelo ML01_RegresionMatricula
ML01_RegresionMatricula: versión 1            # ✅ lo que veníamos leyendo

$ mlflow.sklearn.load_model("models:/ML01_RegresionMatricula/1")
MlflowException: No such artifact: 'MLmodel'  # ❌ lo que realmente había
```

**AC-003.4 llevaba 15 días dado por cumplido sin estarlo**, y con él la ruta de inferencia de C4,
que carga por `models:/…`. Queda como **BUG-041 (critical)**.

Y el artefacto lo sostenía: `ML01_Entrenamiento` §4 afirmaba que *«AC-003.4 ya se verificó
localmente»*. Era cierto pero engañoso — se verificó contra un **SQLite temporal**, no contra el
servidor que vamos a demostrar. Corregí esa afirmación en el artefacto: es la misma familia de
defecto que ya me señalaron en §5 y que yo mismo reporté en el índice de US-312, y no por ser mía
deja de serlo.

## Lo que arreglé (y lo que no me toca)

**Mío: la guarda que debió atraparlo.** `verificar_modelos_registrados()` preguntaba si existía la
fila y daba verde. Nunca intentó traer el modelo de vuelta. Agregué
`verificar_artefactos_descargables()`, que carga cada versión con `mlflow.pyfunc` —la misma ruta que
usa la API de C4— y reprueba nombrando modelo, versión y causa probable. `verificar_registry` la
corre por defecto; `--sin-artefacto` conserva la verificación débil pero **el reporte dice que es
débil**, para que nadie vuelva a confundirla con la fuerte.

**De C5: el `command:` del servicio.** `docker-compose.yml` es de Célula 5, así que **no lo toqué**.
Probé el arreglo con un override fuera del repo y quedó verificado en los dos sentidos:

| Servidor | `log_model` | `load_model` | `verificar_registry` |
|---|---|---|---|
| como está hoy | ❌ `Read-only file system` | ❌ `No such artifact` | ❌ **reprueba** (correcto) |
| con `--serve-artifacts` | ✅ registra **v2** | ✅ carga y predice | ✅ pasa |

Lo que C5 tiene que agregar es `--serve-artifacts --artifacts-destination /mlflow/artifacts`.

**Secuela que hay que recordar al aplicarlo:** un experimento graba su `artifact_location` al
crearse y no se recalcula. `ML-01-regresion-matricula` quedó fijado a `/mlflow/artifacts/1` y
**seguirá roto aunque el servidor se arregle**; hay que recrear el experimento y re-registrar los
tres modelos. Por eso la v2 la registré en `ML-01-regresion-matricula-v2`.

## US-313: hasta dónde llegó

Levanté la cadena completa en local siguiendo los 7 pasos que Marina dejó escritos el 27-ago
(BUG-012 sigue abierto: `dbt/README.md` continúa siendo el scaffold por defecto). Bronze 11 tablas →
Silver → **`gold.fact_escuela_ciclo` 25 filas · `gold.features_escuela` 25 filas**, las mismas
cifras que reportó Marina.

**Lo que sí quedó verificado del job:**

- Publica contra Postgres real: **80 predicciones + 80 recomendaciones**.
- **Idempotente de verdad**: dos corridas seguidas, **0 duplicados** en la llave natural.
- Escribe el **`mlflow_run_id` real** de la corrida registrada hoy, no un marcador.
- Convive con el grano `municipio_nivel` sin pisarlo (DEC-010): 80 filas `escuela` y 46
  `municipio_nivel` en la misma tabla, cada una con su llave.

**Lo que no pude cerrar, y por qué.** `--desde-gold` sigue reprobando con
`ValueError: Con 1 ciclos no se puede hacer backtesting`. Es BUG-013, ya registrado. Lo que **no**
estaba escrito es la causa, y la encontré:

| Tabla | Ciclos |
|---|---|
| `silver.matricula` | **2** |
| `silver.matricula_historica` | **6** |

`features_escuela.sql` §42 arma su base desde `{{ ref('matricula') }}`, no desde
`matricula_historica`. **La serie histórica que ML necesita ya está en Silver** —la dejó ahí
BUG-026— y se pierde en el salto a Gold. No falta ninguna fuente: falta un `ref`.

No lo arreglé porque `dbt/**` es de Célula 1. Queda documentado bajo BUG-013 con la propuesta, para
Diana.

## Decisión que tomé y podría discutirse

Dejé la corrección de `verificar_registry` **reprobando por defecto**. Eso significa que quien corra
la verificación contra el servidor tal como está hoy va a ver un fallo. Es intencional: un verde
falso durante 15 días costó más que un rojo honesto, y el rojo dice exactamente qué agregar y quién
lo hace.

## Verificación

- Suite completa: **780 passed, 5 skipped** (~18 min). **7 pruebas nuevas.**
- `ruff check src/modelos/ tests/` → limpio.
- `vault_lint.py` → limpio.
- ML-01 v2 registrada y **cargada de vuelta** desde un cliente limpio; predice.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/mlflow_utils.py`, `src/modelos/verificar_registry.py`,
  `tests/test_mlflow_utils.py`, `tests/test_verificar_registry.py`,
  `vault/06_Quality_Testing/Bug_Register.md`, este DevLog.
- **🟡 `tests/**` (compartido):** los dos archivos tocados son los de mis propios módulos. Las
  pruebas del CLI **tuve que arreglarlas porque yo las rompí**: al agregar la verificación de
  artefactos al CLI, sus dobles dejaron de cubrirla y salían a la red real contra
  `http://mlflow:5000`; la suite se colgaba en vez de fallar. Ahora se interceptan las dos
  verificaciones y corren en 0.08 s.
- **🔴 Fuera de alcance, ejecutado pero NO modificado:** `docker-compose.yml` y `docker/**` (C5),
  `dbt/**` (C1). El override de MLflow y el `profiles.yml` viven en un directorio temporal fuera del
  repositorio.
- **Manejo de secretos:** el `.env` se generó en local con `scripts/generate-keys.py` y está cubierto
  por `.gitignore`; la contraseña se leyó por variable de entorno, nunca se escribió en un archivo
  versionado ni en un prompt.
- **Decisiones autónomas del agente:** verificar con `pyfunc` y no con el sabor concreto; reprobar
  por defecto en vez de advertir; registrar la v2 en un experimento nuevo en vez de borrar el viejo.
- **Correcciones manuales:** revisión línea por línea.

## Pendientes

1. **BUG-041 → C5 (Luis Téllez / Edward Ruiz):** agregar `--serve-artifacts` y **recrear el
   experimento**. Sin esto, AC-003.4 sigue sin cumplirse y la inferencia de C4 no puede cargar
   modelos.
2. **BUG-013 → C1 (Diana Alvarez):** que `features_escuela` tome la serie de `matricula_historica`.
   Es lo único que falta para cerrar US-313 contra Gold real.
3. **BUG-012 sigue abierto:** `dbt/README.md` es el scaffold por defecto. Los pasos de Marina
   siguen sin estar en el repo; hoy los volví a necesitar y los volví a sacar de su DevLog.
4. **BUG-020 sigue abierto** y sigue bloqueando el E2E de la URL pública.
