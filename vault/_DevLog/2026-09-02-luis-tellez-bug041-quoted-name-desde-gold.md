---
id: DEVLOG-2026-09-02-LUIS-TELLEZ-BUG041-QUOTED-NAME-DESDE-GOLD
title: "DevLog — BUG-041: el quoted_name de SQLAlchemy vacía feature_names_in_ en el path --desde-gold de ML"
owner: "Luis Téllez Domínguez"
status: filed
version: "1.0"
traces_up: ["vault/02_Requirements/Requirements_Detailed", "vault/02_Requirements/User_Stories", "vault/06_Quality_Testing/Bug_Register"]
traces_down: ["src/modelos/entrenar_ml01.py", "src/modelos/publicar_gold.py", "vault/06_Quality_Testing/Bug_Register"]
last_reviewed: "2026-09-02"
tags: [devlog, ml, bugfix, sin-dato, gold, l0, bug041, celula-3, celula-5]
---

# DevLog — 2026-09-02 — Luis Téllez Domínguez

**Historia:** `US-313` · Integrar predicciones y recomendaciones a Gold (destapado al ejercitar `US-311` · Entrenar ML-01)
**Requisito:** `REQ-003` · Tres modelos de ML integrados vía API
**Bug:** `BUG-041` (reporte + parche preparado y validado en local; el código lo aplica Célula 3)
**Rama:** `dev/luis-tellez`
**Herramienta de IA usada:** Claude Code / claude-opus-4-8

## Qué se pidió

Como operador de reparación de C5 (autorización de Luis Téllez, TL): cerrar la **validación L0 local**
del pipeline ML (§10 del plan, local, ~$0, sin GCP) y **formalizar el bug real** que se destapó al
ejercitarlo end-to-end. C5 reporta y deja el parche preparado y validado; el código vive en `src/modelos/**`,
que es verde de Célula 3, así que **la corrección la lleva C3 en su rama** y el merge lo hace el PO. Este
PR de C5 es **solo la formalización en el vault** (registro, DevLog, índice y matriz) — cero código.

## Qué encontré

Al correr `publicar_gold.py --desde-gold` contra el Gold local con **cobertura parcial real** (D5 agua es
100 % `SIN_DATO` en la ventana), ML-01 **entrena bien** (MAE 0.0844) pero **truena en la predicción**:

```
ValueError: X has 6 features, but HistGradientBoostingRegressor is expecting 5 features
```

**Causa raíz.** `cargar_features_desde_gold` (`entrenar_ml01.py:203`) lee con `pd.read_sql_table(...)`, y
**SQLAlchemy devuelve los nombres de columna como `quoted_name`** —subclase de `str`, no `str` puro—.
scikit-learn detecta los nombres de features exigiendo **`type(x) == str` exacto**, así que trata cada
`quoted_name` como "no-string" y **nunca puebla `modelo.feature_names_in_`**. En la predicción,
`construir_predicciones` hace `getattr(modelo, "feature_names_in_", DRIVERS)` (`publicar_gold.py:267`) → cae
al fallback `DRIVERS` (los 6) → reintroduce el driver descartado por estar 100 % `SIN_DATO` → desajuste de
forma → crash.

**Por qué es un bug NUEVO y no un duplicado.** Es la misma FAMILIA que BUG-015/018/023 —los tres arreglaron
el lado de predicción para **confiar en `feature_names_in_`** con el patrón `getattr(..., DRIVERS)`— pero la
**causa raíz es otra**: aquí ese atributo **nunca se puebla en el path de la BD**, así que el propio fallback
que debía protegernos se dispara y **anula el fix de BUG-015** en producción. El defecto está en el eslabón
que hace fallar al remedio de los otros tres.

**Por qué los tests no lo cazan.** La suite usa **fixtures CSV** (`read_csv` → nombres `str` puros), donde
`feature_names_in_` sí se puebla. **Solo el path real `--desde-gold` (lee de la BD) sufre el `quoted_name`**,
y solo cuando **un driver queda 100 % `SIN_DATO`** en la ventana (si no se descarta ninguno, `DRIVERS`=6
coincide por casualidad). Con datos reales de cobertura parcial —D5 agua regional, D6 aire ~80 zonas— es
**plausible en producción**, no solo en la muestra. Misma lección de BUG-023: un fixture construido para
validar la forma no valida la realidad.

**Alcance del impacto.** Todos los consumidores que confían en `feature_names_in_`, todos en archivos de C3:
`publicar_gold.construir_predicciones` (:267) y `construir_predicciones_municipio_nivel` (:335),
`entrenar_ml02` (:245, :302) y `evaluar.py` (:212, :244).

## Qué hice

- **Diagnostiqué la traza real** en el path `--desde-gold` (no en el fixture) y aislé la causa al borde donde
  entra el `quoted_name`.
- **Preparé el parche (4 líneas)** y lo **apliqué solo en local** (Luis autorizó "solo fix local" para cerrar
  L0 ahora) — **sin commit**. Normaliza los nombres a `str` puro justo después de la lectura:
  ```python
  df = pd.read_sql_table(tabla, engine, schema=esquema)
  df.columns = [str(c) for c in df.columns]  # SQLAlchemy da quoted_name; sklearn solo
                                              # puebla feature_names_in_ con str puro (BUG-041)
  ```
- **Registré BUG-041** en `vault/06_Quality_Testing/Bug_Register.md` (ruta `comunes`; `Definition_of_Filed`
  obliga a cualquiera a registrar el bug que encuentre), con test de regresión propuesto para que lo numere C3.
- **No metí el código en este PR:** `src/modelos/**` es verde de C3; un PR de `dev/luis-tellez` que lo tocara
  reprobaría `check_ownership.py`. Este PR es documental. El patrón es el de BUG-018/BUG-008 (uno reporta,
  aplica quien es dueño).
- Dejé el seguimiento honesto vivo en `_local/L0_ML_realidad_vs_prueba.md` §5 (qué es real del proyecto vs.
  andamiaje de prueba) y el kit de verificación manual en `_local/verificar_L0_local.sh`.

## Pruebas ejecutadas

La validación del fix fue **local, leyendo la BD y la API reales** (no re-ejecuté la suite; este PR es
documental). Con el parche aplicado en local:

```
feature_names_in_ (ML-01)     5 drivers usables (D5 agua descartado por 100% SIN_DATO), sin fallback
construir_predicciones        55 filas (ciclo 2024-2025); indice_riesgo ∈ [0.084, 0.742], sin saturar
gold.predicciones             55 (ML-01, MAE 0.0844)   ·  gold.recomendaciones  55 (ML-02, F1 0.6458)
gold.fact_escuela_ciclo       145 = features_escuela 145 (3 ciclos 60/30/55; tras rebuild completo de Gold)
GET /api/v1/kpis              escuelas_en_riesgo = 2 ; indice_completitud_drivers ≈ 0.645
diferenciador prescriptivo    15DJN0049A → D1 (becas/apoyo alimentario) ; 09DSN0042A → D2 (rutas seguras)
vault_lint.py .               Vault limpio (este DevLog + registro + índice + matriz)
```

Las métricas ML **validan que el pipeline corre E2E**, no que el modelo prediga bien (datos de muestra,
drivers estáticos, 1 ventana): esa distinción queda documentada en `_local/L0_ML_realidad_vs_prueba.md` §2.

## Propiedad / gobernanza

`entrenar_ml01.py` está bajo `src/modelos/**`, **verde de Célula 3** (Andrés González —TL—, Héctor Morales,
Estefany Hernández, Carlos Mayorga). Lo natural es que el fix lo lleve **Héctor Morales** (`dev/hector-morales`),
dueño de `US-311`/`US-313`, con la coordinación del TL **Andrés González**. Alternativa más defensiva
(follow-up de C3): pasar `drivers_usados` explícito a `construir_predicciones` en vez de depender de un
atributo que un tipo de columna puede dejar sin poblar. C5 no toca la rama de otra célula; el merge lo hace
el PO (Edgar Coronel).

## IDs tocados

`BUG-041` · `US-313` · `US-311` · `REQ-003`

## Próximos pasos

- **Célula 3** aplica el parche (4 líneas) + numera el **test de regresión** propuesto (leer features vía
  `read_sql_table` o simular nombres `quoted_name`; afirmar que `construir_predicciones` puebla
  `feature_names_in_` con los drivers usables y no cae al fallback `DRIVERS`) en su rama; el PO mergea.
- Al cerrar el fix con su test, BUG-041 pasa `open → fixed → closed` en el registro.
- L1–L5 (GCP) siguen **gated** al go por bloque de Luis; L0 (local) queda cerrada.
