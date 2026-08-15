---
id: DOC-PUBLICACION-GOLD
title: "Publicación de predicciones y recomendaciones a Gold"
owner: "Héctor Rafael Morales Marbán"
status: in_review
traces_up: ["02_Requirements/User_Stories", "03_Architecture/Data_Model", "15_ML_Models/Indice_Riesgo_ML01"]
traces_down: ["US-313"]
tags: [ml, celula-3, gold, batch]
---

# Publicación de predicciones y recomendaciones a Gold

> Job batch de [[02_Requirements/User_Stories|US-313]]: escribe `gold.predicciones` y
> `gold.recomendaciones`, las tablas que alimentan **DB-06** y **DB-09** y los endpoints de
> inferencia de la Célula 4.
> → [[15_ML_Models/_index]] · [[15_ML_Models/ML01_Entrenamiento]] · [[03_Architecture/Data_Model]]

## 1. Contrato

Conforme a [[03_Architecture/Data_Model]] §4.5 tras **DEC-005/006**, que resolvió la ambigüedad que
señalamos en [[15_ML_Models/Indice_Riesgo_ML01]] §4: la tabla guarda **las dos cosas**.

| `gold.predicciones` | Tipo | Notas |
|---|---|---|
| `cct`, `id_ciclo`, `modelo` | — | llave primaria compuesta |
| `valor` | float | **variación cruda**; conserva la unidad para MAE/RMSE |
| `indice_riesgo` | float [0,1] | derivado, calculado en `src/modelos/riesgo.py` |
| `probabilidad` | float \| NULL | ML-01 es regresión: siempre `NULL`, nunca 0 |
| `mlflow_run_id` | str | corrida que produjo el modelo |
| `generado_at` | timestamptz | |

| `gold.recomendaciones` | Tipo | Notas |
|---|---|---|
| `cct`, `id_ciclo` | — | llave primaria compuesta |
| `driver_dominante` | str | `D1`…`D6`; **salida de ML-02** |
| `recomendacion` | str | del catálogo prescriptivo (§3) |
| `prioridad` | enum | `alta` / `media` / `baja` (§4) |

## 2. Idempotencia

El job se corre N veces con el mismo resultado. Escribe con **UPSERT** (`ON CONFLICT DO UPDATE`)
sobre la llave natural: **no borra particiones ni trunca tablas**. Tras reentrenar, la corrida
siguiente actualiza `valor`, `indice_riesgo` y `mlflow_run_id` en su sitio.

Verificado contra Postgres real (el `docker-compose.yml` del equipo): dos corridas seguidas dejan
**80 filas / 80 escuelas**, no 160.

## 3. Catálogo prescriptivo

Es el corazón del proyecto: dos escuelas con el mismo riesgo reciben recomendaciones distintas
según su driver dominante.

| Driver | Recomendación |
|---|---|
| D1 · Pobreza | Priorizar programas de becas y apoyo alimentario en la zona. |
| D2 · Inseguridad | Coordinar con seguridad pública rutas escolares seguras y entornos protegidos. |
| D3 · Infraestructura | Gestionar rehabilitación de infraestructura escolar prioritaria. |
| D4 · Conectividad | Ampliar conectividad y dotación de equipo de cómputo. |
| D5 · Agua | Asegurar suministro de agua y planes de contingencia hídrica. |
| D6 · Aire | Activar protocolos por contingencia de calidad del aire. |

**No se inventó:** es literalmente el catálogo que la Célula 4 ya usa en `src/api/mock_data.py`
(US-401). Hoy está duplicado en los dos módulos; `test_catalogo_coincide_con_el_de_la_api` falla si
divergen. **Propuesta:** cuando la C4 quite sus datos simulados, que importe de
`src/modelos/publicar_gold.py`, porque el texto prescriptivo es dato de negocio de la Célula 3.

## 4. Prioridad

Derivada del `indice_riesgo` reutilizando las **anclas ya ratificadas** de
[[15_ML_Models/Indice_Riesgo_ML01]] — no se introducen umbrales nuevos:

| Prioridad | Condición | Origen del umbral |
|---|---|---|
| `alta` | `indice_riesgo >= 0.60` | umbral de "escuela en riesgo" ratificado por Manuel Serranía (PR #27) |
| `media` | `>= 0.30` | ancla de matrícula estable |
| `baja` | `< 0.30` | |

## 5. Lo que falta: ML-02

`driver_dominante` es salida de **ML-02 (US-302, Andrés González Habib)**, que aún no existe. Por eso
`construir_recomendaciones()` **lo recibe como argumento en vez de calcularlo**, y el CLI publica
sólo `gold.predicciones`.

Es una decisión deliberada: **antes de inventar un driver, no se publica la fila**. Una
recomendación prescriptiva con un driver inventado es peor que ninguna recomendación — es
exactamente el tipo de dato que un tomador de decisiones usaría para asignar presupuesto.

Cuando ML-02 aterrice, se conecta su predicción a `construir_recomendaciones()` y el resto de la
maquinaria (catálogo, prioridad, contrato, upsert, pruebas) ya está.

## 6. Uso

```bash
docker compose up -d db
export DATABASE_URL="postgresql+psycopg2://postgres:...@localhost:5432/escuela_concausa_db"
python -m src.modelos.publicar_gold --solo-predicciones --run-id <mlflow_run_id>
```

## 7. Pruebas

`tests/test_publicar_gold.py` — 18 casos (`TEST-006`), sobre **SQLite en archivo temporal**: el CI
no necesita Postgres y el UPSERT se ejercita de verdad, no se simula. El código es dialecto-aware,
así que es la misma ruta que corre contra Postgres.

Las que importan:

- `test_es_idempotente` y `test_el_upsert_actualiza_en_vez_de_duplicar` — el requisito central.
- `test_probabilidad_es_nula_en_una_regresion` — `NULL` explícito, nunca 0.
- `test_conserva_la_variacion_cruda_y_el_riesgo` — DEC-005 en ejecución.
- `test_catalogo_coincide_con_el_de_la_api` — vigila la duplicación con la Célula 4.
- `test_rechaza_drivers_fuera_del_catalogo` — un `D9` no se publica en silencio.

## 8. Pendientes

1. **ML-02** para poblar `gold.recomendaciones` (US-302).
2. **Re-ejecutar con `gold.features_escuela` real** (US-104, Diana, vence 23 ago).
3. **Resolver la duplicación del catálogo** con la Célula 4.
4. `03_Architecture/Data_Model.md` **línea 255** conserva la redacción vieja — dice que
   `indice_riesgo` vive en la columna `valor`, lo que contradice el §4.5 tras DEC-005. Es de la
   Célula 1.
