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

El catálogo canónico vive en `src/modelos/recomendaciones.py`. Célula 4 todavía conserva una copia
en `src/api/mock_data.py` (US-401); `test_catalogo_coincide_con_el_de_la_api` falla si divergen.
Cuando C4 retire sus datos simulados, debe importar el catálogo canónico de Célula 3.

## 4. Prioridad

Derivada del `indice_riesgo` reutilizando las **anclas ya ratificadas** de
[[15_ML_Models/Indice_Riesgo_ML01]] — no se introducen umbrales nuevos:

| Prioridad | Condición | Origen del umbral |
|---|---|---|
| `alta` | `indice_riesgo >= 0.60` | umbral de "escuela en riesgo" ratificado por Manuel Serranía (PR #27) |
| `media` | `>= 0.30` | ancla de matrícula estable |
| `baja` | `< 0.30` | |

## 5. Integración con ML-02

`driver_dominante` es salida de **ML-02 (US-302, Andrés González Habib)**. El CLI entrena ML-01 y
ML-02, alinea sus salidas uno-a-uno por `cct` e `id_ciclo`, construye las recomendaciones y publica
ambas tablas. Si falta una fila de features para ML-02, el job falla en vez de inventar un driver.

`--solo-predicciones` conserva la posibilidad explícita de omitir ML-02 cuando se necesite aislar
ML-01 durante diagnóstico.

## 6. Uso

```bash
docker compose up -d db
export DATABASE_URL="postgresql+psycopg2://postgres:...@localhost:5432/escuela_concausa_db"
python -m src.modelos.publicar_gold --features <ruta_features> --run-id <mlflow_run_id>
```

## 7. Pruebas

`tests/test_publicar_gold.py` — 20 casos (`TEST-006`), sobre **SQLite en archivo temporal**: el CI
no necesita Postgres y el UPSERT se ejercita de verdad, no se simula. El código es dialecto-aware,
así que es la misma ruta que corre contra Postgres.

Las que importan:

- `test_es_idempotente` y `test_el_upsert_actualiza_en_vez_de_duplicar` — el requisito central.
- `test_probabilidad_es_nula_en_una_regresion` — `NULL` explícito, nunca 0.
- `test_conserva_la_variacion_cruda_y_el_riesgo` — DEC-005 en ejecución.
- `test_catalogo_coincide_con_el_de_la_api` — vigila la duplicación con la Célula 4.
- `test_rechaza_drivers_fuera_del_catalogo` — un `D9` no se publica en silencio.
- `test_conecta_ml02_con_recomendaciones_del_mismo_ciclo` — alinea ML-01 y ML-02 por llave.
- `test_igual_riesgo_y_distinto_driver_producen_recomendaciones_distintas` — verifica AC-003.6.

## 8. Pendientes

1. **Re-ejecutar con `gold.features_escuela` real** y la etiqueta supervisada confirmada por C1.
2. **Resolver la duplicación del catálogo** con la Célula 4.
3. `03_Architecture/Data_Model.md` **línea 255** conserva la redacción vieja — dice que
   `indice_riesgo` vive en la columna `valor`, lo que contradice el §4.5 tras DEC-005. Es de la
   Célula 1.
