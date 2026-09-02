---
id: SPRINT-DENI-GARRIDO-FRAGOSO
title: "Plan de Sprints — Deni Garrido Fragoso"
owner: "Deni Garrido Fragoso"
status: approved
version: "1.0"
traces_up: ["01_Product/PRD", "02_Requirements/User_Stories"]
traces_down: ["US-111", "US-112", "US-113", "US-114"]
last_reviewed: "2026-08-30"
tags: [sprint, plan, celula-1, nivel-medio]
---

# FARO · Plan de trabajo individual
## Deni Garrido Fragoso

> **Proyecto:** FARO — Escuela como Sensor Social
> **Célula:** Celula 1 — Data Engineering & Quality · **Peso en rúbrica:** 2.5 pts
> **Rol:** Ingeniera de datos · Transformaciones dbt · **Nivel asignado:** Medio
> **Tech Lead de tu célula:** Diana Aracely Alvarez Varela
> **Demo en vivo:** miércoles 9 de septiembre de 2026

---

## 1. Tu misión en una frase

Tienes historias de **complejidad intermedia con autonomía**. Implementas piezas completas apoyándote en el diseño de tu Tech Lead, y apoyas a los perfiles jr de tu célula cuando se atoran.

---

## 2. Mapa de dependencias

| | |
|---|---|
| **Recibes de (inputs)** | Fuentes públicas (externas) · Ambiente y Postgres de la **Célula 5** |
| **Entregas a (outputs)** | **Célula 2** (cubos para Superset) · **Célula 3** (tabla de features) · **Célula 4** (endpoints de datos) |
| **Quién revisa tu código** | Diana Aracely Alvarez Varela (Tech Lead, compuerta técnica) → Edgar Coronel (PM, compuerta de proceso) |
| **Formato de entrega** | Rama `feat/deni-fragoso-...` → PR con plantilla completa → 1 aprobación (PM) → merge a `main` |

> **Regla de desbloqueo:** si un input tuyo no llega a tiempo, **no te quedes esperando**. Trabaja contra
> datos mock o fixtures, avísalo en el standup y registra el bloqueo. Un bloqueo silencioso de 3 días
> con esta ventana de 6 semanas es fatal.

---

## 3. Tus historias de usuario

### `US-111` · Implementar transformaciones Bronze -> Silver con dbt

| | |
|---|---|
| **Sprint** | S2 — Lun 10 - Dom 16 ago |
| **Objetivo** | Limpieza, tipado, deduplicacion y homologacion de catalogos (CCT y clave de municipio INEGI a 5 digitos). |
| **Entregable** | Código en su carpeta + documento en el vault con frontmatter + fila en la matriz |
| **Cómo se entrega** | Rama `feat/deni-fragoso-...` → PR con plantilla → revisión del Tech Lead → merge a `main` |

### `US-112` · Implementar transformaciones Silver -> Gold con dbt

| | |
|---|---|
| **Sprint** | S3 — Lun 17 - Dom 23 ago |
| **Objetivo** | Materializar hechos y dimensiones. Incluye tests nativos de dbt: unique, not_null, relationships, accepted_values. |
| **Entregable** | Código en su carpeta + documento en el vault con frontmatter + fila en la matriz |
| **Cómo se entrega** | Rama `feat/deni-fragoso-...` → PR con plantilla → revisión del Tech Lead → merge a `main` |

### `US-113` · Construir los cubos de agregacion

| | |
|---|---|
| **Sprint** | S3 — Lun 17 - Dom 23 ago |
| **Objetivo** | Vistas materializadas optimizadas para los 10 dashboards. Cada cubo debe exponer la bandera de cobertura para que el slice muestre 'sin dato disponible'. |
| **Entregable** | Código en su carpeta + documento en el vault con frontmatter + fila en la matriz |
| **Cómo se entrega** | Rama `feat/deni-fragoso-...` → PR con plantilla → revisión del Tech Lead → merge a `main` |

### `US-114` · Optimizar consultas y crear indices

| | |
|---|---|
| **Sprint** | S5 — Lun 31 ago - Dom 6 sep |
| **Objetivo** | Perfilar queries lentas de dashboards y API; indices en Postgres; documentar el antes/despues. |
| **Entregable** | Código en su carpeta + documento en el vault con frontmatter + fila en la matriz |
| **Cómo se entrega** | Rama `feat/deni-fragoso-...` → PR con plantilla → revisión del Tech Lead → merge a `main` |


---

## 4. Ambiente local — hazlo ANTES del primer standup

Todos trabajamos con el mismo ambiente para evitar el clásico "en mi máquina sí corre".

### 4.1 Requisitos previos
- **Python 3.11** (`python3 --version`)
- **Docker Desktop** corriendo
- **Git** configurado con tu nombre real y el correo **verificado en tu cuenta de GitHub** (no necesariamente el institucional); es lo que atribuye tus commits a tu perfil y los cuenta como evidencia de participación. Si prefieres no exponerlo, usa tu `@users.noreply.github.com` (Settings → Emails).
- **VS Code** (o tu editor) con la extensión de Python

### 4.2 Clonar y crear tu ambiente virtual

```bash
# 1. Clona el repositorio
git clone https://github.com/edgarcoroneln/escuela-concausa-bi.git
cd escuela-concausa-bi

# 2. Crea tu ambiente virtual (NO se sube al repo, está en .gitignore)
python3 -m venv .venv

# 3. Actívalo
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows PowerShell

# 4. Verifica que estás dentro del venv (debe aparecer (.venv) en tu prompt)
which python

# 5. Actualiza pip e instala dependencias base
pip install --upgrade pip
pip install -r requirements.txt

# 6. Dependencias específicas de tu célula
pip install airflow dbt-core dbt-postgres great-expectations pandas polars pyarrow requests

# 7. Congela lo que instalaste (si agregaste algo nuevo)
pip freeze > requirements/celula-1.txt
```

### 4.3 Variables de entorno

```bash
cp .env.example .env
```

Abre `.env` y llena los valores. **NUNCA subas el `.env` al repositorio** — está en `.gitignore` y
las reglas de `07_Security/Secrets_Policy.md` lo prohíben explícitamente.

### 4.4 Levantar los servicios locales

```bash
docker compose up -d          # levanta Postgres, Airflow, Superset, MLflow
docker compose ps             # verifica que todos estén "healthy"
docker compose logs -f <servicio>   # si algo falla
```

### 4.5 Verificación final (tu ambiente está listo si esto pasa)

```bash
python -c "import sys; print(sys.version)"     # 3.11.x
docker compose ps                               # todos Up
pytest tests/ -q                                # las pruebas base pasan
python _Meta/scripts/vault_lint.py .            # ✅ Vault limpio
```

Si algo falla, escribe en el canal de tu célula **antes** del standup. No pierdas un día atorado en
setup: es el error más caro de la semana 1.

---

## 5. Prompts sugeridos — funcionan en cualquier LLM

> Puedes usar **Claude Code, ChatGPT, Gemini, Copilot o el que prefieras**. Los prompts están escritos para ser agnósticos.

> Adapta los `<PLACEHOLDERS>`. **Todo lo que genere la IA lo revisas tú antes de commitear, y cada sesión genera una entrada de DevLog** (regla 6 del vault).

**Contexto que debes pegar al inicio de tu sesión, sea cual sea el LLM:**

```
Estoy trabajando en FARO, una plataforma de BI end-to-end sobre datos abiertos de México
(escuelas + pobreza + inseguridad + infraestructura + agua + aire). Arquitectura medallon
(bronze/silver/gold en Postgres), Airflow, dbt, Great Expectations, MLflow, FastAPI,
Superset, Docker y GCP. Python 3.11. Alcance: CDMX, Edomex, Nuevo Leon y Jalisco.
La llave que une todo es el CCT (centro de trabajo) y la clave INEGI de municipio a 5 digitos.
Responde en espanol, con codigo comentado y explicando tus decisiones.
```

**Diseño de extractor**
```
Actúa como ingeniero de datos senior. Necesito un extractor en Python para la fuente <FUENTE> que: (1) descargue el archivo desde <URL>, (2) valide que el archivo no esté vacío, (3) lo guarde como Parquet en la capa bronze con las columnas de metadatos `_ingested_at`, `_source`, `_source_url`, (4) sea idempotente y (5) tenga manejo de errores y logging. Sigue PEP 8 y agrega docstrings. No uses librerías fuera de: pandas, pyarrow, requests.
```

**Modelo dbt**
```
Escribe un modelo dbt para transformar la tabla bronze `<TABLA>` a silver. Requisitos: tipado explícito, deduplicación por <LLAVE>, homologación de la clave de municipio a 5 dígitos INEGI, y `not_null`/`unique` en el schema.yml. Explica cada decisión en comentarios.
```

**Great Expectations**
```
Genera una suite de Great Expectations para la tabla <TABLA> de la capa <CAPA>. Valida: nulos en columnas críticas, unicidad de <LLAVE>, rangos físicos plausibles para <COLUMNA>, y que los valores de <CATALOGO> estén en el catálogo válido. Devuelve el código y explica qué falla capturaría cada expectativa.
```


---

## 6. Reglas del repositorio — obligatorias, sin excepción

> Estas reglas vienen de `_Meta/Vault_Rules.md` y `05_Engineering/Engineering_Workflow.md`.
> Romperlas cuesta puntos de la rúbrica (0.5 pts de trabajo en equipo se evalúan por commits repartidos).

### 6.1 PROHIBIDO hacer commits directos a `main`
La rama `main` está protegida. Todo cambio entra por Pull Request revisado. Si intentas
`git push origin main` te será rechazado.

### 6.2 Flujo correcto, paso a paso

```bash
# 1. Actualiza tu main local
git checkout main && git pull origin main

# 2. Crea tu rama con la convención de Naming_Conventions.md
git checkout -b feat/{tu-nombre}-{descripcion-corta}
#   Tipos válidos: feat/ fix/ chore/ docs/ sec/

# 3. Trabaja y haz commits pequeños con Conventional Commits
git add <archivos-especificos>        # NUNCA uses git add . a ciegas
git commit -m "feat(bronze): extractor de Formato 911 (US-122)"
#   Formato: <tipo>(<scope>): <descripción> (ID-de-la-historia)

# 4. Sube tu rama
git push -u origin feat/{tu-nombre}-{descripcion-corta}

# 5. Abre el PR en GitHub usando la plantilla (se carga sola)
```

### 6.3 Reglas del Pull Request
- Usa **`.github/PULL_REQUEST_TEMPLATE.md`** — se llena solo al abrir el PR. Complétalo TODO.
- El PR debe referenciar el **ID de la historia** (`US-###`) y el requisito (`REQ-###`).
- **No puedes aprobar tu propio PR.** Lo revisa tu Tech Lead (o el PO si eres Tech Lead).
- Los checks de CI deben estar **verdes** (lint, pruebas y `vault_lint.py`).
- Si tu cambio toca seguridad, esquema de datos o CI/CD, requiere aprobación humana explícita del
  dueño del área (regla 7 de `Vault_Rules.md`).

### 6.4 DevLog — obligatorio en cada sesión con IA
Toda sesión con Claude Code, Copilot o cualquier LLM **genera una entrada de DevLog antes del push**
(regla 6 de `Vault_Rules.md`). Usa `_Templates/DevLog_template.md` y guárdala en `_DevLog/` como
`YYYY-MM-DD-tu-nombre-descripcion.md`. Debe registrar: qué pediste, qué generó la IA, qué revisaste
tú y qué IDs tocaste.

### 6.5 Gobernanza de IA
- Tu `09_AI_Governance/Agent_Contexts/{tu-nombre}.md` define tu alcance. **No trabajes fuera de él**
  sin avisar a tu Tech Lead.
- **Todo código generado por IA se revisa línea por línea antes de commitear.** Eres responsable de lo
  que subes, lo haya escrito la IA o tú.
- Prohibido pegar datos reales, credenciales o `.env` en un prompt de IA.
- Registra los prompts que funcionaron bien en `09_AI_Governance/Prompt_Library.md` para que el equipo
  los reutilice.

### 6.6 Definition of Filed (antes de decir "ya quedó")
Nada está terminado hasta que: tiene **ID**, está en su **carpeta**, tiene **frontmatter** con `owner`
y `status`, enlaza a su origen (`traces_up`) y a lo que lo resuelve (`traces_down`), aparece en el
**`_index.md`** de su carpeta, y su fila en la **Traceability_Matrix** está actualizada.

---

## 7. Checklist de entrega (por cada historia que cierres)

Marca todo antes de pedir revisión. Si algo queda sin marcar, la historia **no está Done**.

- [ ] El código corre en mi ambiente local sin errores
- [ ] Escribí/actualicé las pruebas y `pytest` pasa en verde
- [ ] Corrí `python _Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [ ] Documenté el artefacto en su carpeta del vault con frontmatter completo
- [ ] Agregué el documento al `_index.md` de su carpeta
- [ ] Actualicé mi fila en `02_Requirements/Traceability_Matrix.md`
- [ ] Escribí mi entrada de DevLog si usé IA
- [ ] Actualicé el `README.md` si mi cambio afecta cómo se instala o se usa el proyecto
- [ ] Mis commits siguen Conventional Commits e incluyen el ID de la historia
- [ ] Verifiqué la autoría: `git log -1 --format='%an <%ae>'` coincide con mi cuenta de GitHub
- [ ] Abrí el PR con la plantilla completa y lo asigné a mi Tech Lead
- [ ] Los checks de CI están verdes
- [ ] NO subí datos reales, `.env`, llaves ni archivos pesados

---

## 8. Datos de prueba — mantén limpio el repositorio

El repositorio **no debe contener datos reales pesados**. Para que CI y las pruebas corran sin
descargar gigabytes:

- Los datos reales viven en `data/raw/` que está **en `.gitignore`** — nunca se suben.
- Las pruebas usan **fixtures**: muestras pequeñas y deterministas en `tests/fixtures/`.
- Si necesitas un dataset de prueba nuevo, genera una muestra de ≤500 filas, **anonimizada y sin datos
  personales**, y documéntala en `06_Quality_Testing/`.
- Regla de oro para la puesta en producción: **si un archivo pesa más de 5 MB, no va al repositorio.**
  Va a Cloud Storage y en el repo queda solo la referencia.

---

## 9. Seguimiento de tu avance

Actualiza esta tabla **antes de cada standup**. El PM la revisa para el tablero de control.

| ID | Historia | Estado | % | Bloqueado por | Fecha compromiso |
|---|---|---|---|---|---|
| `US-111` | Implementar transformaciones Bronze -> Sil | ✅ Terminado | 100% | — | Cerrada 25 ago |
| `US-112` | Implementar transformaciones Silver -> Gol | ✅ Terminado | 100% | — | Cerrada 25 ago |
| `US-113` | Construir los cubos de agregacion | 🔵 En revisión | 100% | DB-10 depende de DS-06; validar o acordar excepción | Revisión 28 ago |
| `US-114` | Optimizar consultas y crear indices | ⬜ Por iniciar | 0% | — | Dom 6 sep |

**Estados válidos:** ⬜ Por iniciar · 🟡 En curso · 🔵 En revisión (PR abierto) · ✅ Terminado · 🔴 Bloqueado

### Si tu historia queda a medias
No pasa nada — lo grave es no decirlo. Si al cierre del sprint tu historia va parcial:
1. Marca el % real, no el que te gustaría
2. Abre el PR igual con lo que sí funciona (mejor 3 PRs chicos que 1 gigante al final)
3. Anota en la tabla **qué falta exactamente** y por qué
4. Dilo en el standup

## 10. Calendario y standups

| Sprint | Fechas | Foco |
|---|---|---|
| **S1** | Lun 3 - Dom 9 ago | Cimientos, fuentes y despliegue temprano |
| **S2** | Lun 10 - Dom 16 ago | Ingesta continua y capa Bronze |
| **S3** | Lun 17 - Dom 23 ago | Silver, Gold, Great Expectations y cubos |
| **S4** | Lun 24 - Dom 30 ago | Modelos ML, FastAPI, Auth y Dashboards |
| **S5** | Lun 31 ago - Dom 6 sep | Agente RAG, integracion y CODE FREEZE |
| **S6** | Lun 7 - Mar 8 sep | Pruebas finales, seguridad, GCP y ensayo |

- **Semanas 1-3 (semanal, jueves):** 6, 13 y 20 de agosto - 19:00 hrs, 45 min.
- **Semanas 4-6 (3 por semana, L-Mi-V):** 24, 26, 28 ago · 31 ago, 2, 4 sep · 7 y 8 sep - 19:00 hrs, 30 min.
- **Formato:** cada celula responde 3 preguntas (que cerre, que sigue, que me bloquea). El PO actualiza la
  Traceability_Matrix al cierre de cada standup.

> **CODE FREEZE: domingo 6 de septiembre.** A partir de ahí no entran funcionalidades nuevas, solo
> correcciones. **Demo en vivo: miércoles 9 de septiembre de 2026.**

---

## 11. Si algo sale mal

| Situación | Qué hacer |
|---|---|
| No logro levantar el ambiente | Escribe en el canal de tu célula el mismo día. No pierdas 2 días. |
| Mi input no llegó | Trabaja con fixtures/mock, registra el bloqueo y avísalo en el standup. |
| Rompí algo en `main` | Avisa de inmediato al Tech Lead de Cloud/DevOps; hay runbook de rollback. |
| Mi PR lleva 2 días sin revisión | Etiqueta a tu Tech Lead; si no responde, escala al PO. |
| No entiendo mi historia | Pregunta ANTES de codificar. Una hora de duda cuesta menos que 3 días de trabajo equivocado. |

---

*Documento generado para el proyecto FARO · Maestría MTIIA · Universidad Anáhuac · Dr. José Gustavo Fuentes*

---

## 9. Evidencia de cierre runtime — US-113

**Fecha:** 2026-08-30
**Estado técnico:** runtime real validado; pendiente únicamente revisión/PR y actualización de la
matriz de trazabilidad por su owner (PM).

- 9/9 cubos Gold materializados con filas.
- 134/134 tests dbt de cubos en PASS.
- `missing=[]`, `empty=[]`, `dbt_test_rc=0`.
- DS-07 real nacional llega a D1/Gold.
- DS-06 real queda trazado en DB-10 sin fabricar D5.
- ML publicado desde `gold.features_escuela` real tras la normalización de ADR-007.
- Evidencia detallada: [[_DevLog/2026-08-30-deni-garrido-us113-runtime-real-cierre|DevLog de cierre runtime US-113]].

**Filas runtime:** `cubo_matricula=90`, `cubo_riesgo_territorial=90`,
`cubo_escuela_360=145`, `cubo_comparador_municipio=90`, `cubo_driver=540`,
`cubo_completitud=540`, `cubo_pivot=870`, `cubo_recomendaciones=145`,
`cubo_pipeline=9`.

> La matriz de trazabilidad no se modifica desde esta rama porque
> `02_Requirements/Traceability_Matrix.md` pertenece al PM y declara que el PM la mantiene.
