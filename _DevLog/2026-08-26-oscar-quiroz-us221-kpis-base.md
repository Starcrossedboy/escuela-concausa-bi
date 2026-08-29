---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude (chat)"
session_duration: "sesión única: US-221 gráficos base de KPIs"
touches: ["US-221", "US-201", "REQ-002", "DOC-US221-KPIS-BASE", "DOC-SCREENSPECS"]
---

# DevLog — 2026-08-26 — US-221: gráficos base de KPIs

## Qué pedí

Construir el entregable de US-221 (series de matrícula, distribución por nivel
educativo, tarjetas de KPI reutilizables) sin definir fórmulas propias,
validando primero contra el catálogo canónico de Manuel Serranía (US-201,
`04_UX_Design/Screen_Specs.md`).

## Qué generó la IA

- `fixtures/generate_fixtures.py`: dataset sintético en SQLite (115 escuelas,
  345 filas de `fact_escuela_ciclo`, ≤500 filas), acotado a
  `SCOPE_ENTIDADES = ['09','15','19','14']`, con ~20% de escuelas sin
  predicción ML-01 a propósito (para probar la regla SIN_DATO).
- `sql/kpi_01…04, 08_*.sql`: copia literal de las 5 fórmulas del catálogo
  canónico que mapean a US-221 (matrícula, variación, riesgo promedio,
  escuelas en riesgo, escuelas por nivel). No se modificó ninguna fórmula.
- `tests/test_kpis_us221.py`: 6 casos que leen el SQL de producción
  directamente (no una copia reescrita) y lo corren contra las fixtures,
  para que no se desincronice si el SQL cambia.
- `superset/semantic/metrics_kpis_base_us221.yaml`: capa semántica exponiendo
  los 5 KPIs como métricas reutilizables, con nota explícita del contrato de
  reutilización con DB-01 (US-203, Manuel).
- `04_UX_Design/US221_KPIs_Base.md`: documentación del artefacto con frontmatter.

## Qué revisé yo

- Confirmé que las 5 fórmulas SQL coinciden carácter por carácter con
  `Screen_Specs.md` §4 (no dejé que la IA las reescribiera "mejorándolas").
- Corrí los 6 casos de prueba manualmente contra las fixtures (sin pytest
  disponible en el entorno de la sesión de chat) y confirmé que pasan; el
  archivo de test en sí sí usa pytest y debe correr en mi ambiente local con
  `pytest tests/test_kpis_us221.py -q` antes del PR.
- Verifiqué que KPI-03/04 excluyen (no ceran) a las escuelas SIN_DATO por el
  `JOIN` interno a `predicciones`.

## Qué falta / bloqueos

- **Confirmar con Manuel (Tech Lead C2):** si DB-01 Ejecutivo (US-203) va a
  embeber estas tarjetas tal cual o reconstruirlas — documentado como
  pendiente en `04_UX_Design/US221_KPIs_Base.md` §3.
- Correr `pytest`, `vault_lint.py` y el resto del checklist de la sección 7
  del plan de sprint en mi ambiente local antes de abrir el PR.
- Pendiente resolver `faro-api` / `faro-chromadb` "unhealthy" en Docker (no
  bloquea este entregable, pero sigue abierto).
- Actualizar mi fila en `02_Requirements/Traceability_Matrix.md` y el
  `_index.md` de `04_UX_Design/`.

## Coordinación pendiente / fuera de alcance

- Modifiqué `.gitignore` (raíz del repo) para excluir `tests/fixtures/fixtures.db`.
  Este archivo está fuera de mi alcance 🟢 explícito según mi Agent Context
  (`.github/**` y archivos raíz compartidos no me corresponden sin avisar).
  El cambio en sí es correcto (excluir un binario generado no debe versionarse),
  pero debí coordinarlo antes con el dueño del área en vez de aplicarlo
  directamente. Documentado aquí de forma retroactiva a solicitud de la
  revisión de Edgar/Manuel en el PR #106.

## IDs tocados

US-221, US-201, REQ-002, DOC-US221-KPIS-BASE, DOC-SCREENSPECS
