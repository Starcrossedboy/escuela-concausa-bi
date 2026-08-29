---
id: RPT-US-VALIDATION-2026-08-28
title: "Seguimiento de validación y cierre de User Stories — 2026-08-28"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: false
traces_up:
  - "12_Roadmap_Sprints/Execution_Status"
  - "02_Requirements/Traceability_Matrix"
  - "02_Requirements/User_Stories"
traces_down:
  - "13_Reports/US_Validation_Followup_2026-08-28.html"
last_reviewed: "2026-08-28"
tags: [report, validation, user-stories, follow-up, meeting]
---

# Seguimiento de validación y cierre de User Stories — 2026-08-28

> Corte de auditoría para la junta de seguimiento. La fuente canónica del estado sigue siendo
> [[12_Roadmap_Sprints/Execution_Status]]; este reporte explica los gates pendientes y el HTML sirve
> para registrar acuerdos localmente. → [[13_Reports/_index|Volver a reportes]]

## Resultado de la reconciliación

- **91 US totales:** 31 `done`, 24 `in_review`, 12 `in_progress` y 24 `planned`.
- **3 cierres administrativos aplicados:** US-323, US-415 y US-523a.
- **US-412 no cierra.** Se propuso cerrarla y la revisión técnica de Héctor Morales encontró la
  asimetría: US-411 se sostiene abierta por BUG-020 y US-412 entrega `/predicciones/*`, que son
  justamente rutas que responden 500 en producción. Se adopta el criterio explícito —ya escrito en
  las reglas de `Execution_Status`— de que **una historia cuyo entregable es una ruta HTTP no cierra
  mientras esa ruta no responda en el despliegue que se va a demostrar**, y una cuyo entregable es un
  contrato o una biblioteca sí. Por eso US-415 (contrato Pydantic) sí cierra y US-412 no.
- **14 historias dejaron de aparecer como `planned/in_progress` pese a tener entrega o PR activo.**
- Un PR mergeado no se interpretó automáticamente como cierre: donde falta E2E, dato real,
  aprobación de seguridad, DevLog o decisión de alcance, la historia permanece en revisión.

Abrir el [reporte HTML interactivo](US_Validation_Followup_2026-08-28.html) para registrar durante
la junta una decisión, notas y el nuevo estado propuesto. Las decisiones se guardan en el navegador
mediante `localStorage` y pueden exportarse a JSON o CSV; **no modifican el repositorio** hasta que el
PM las lleve a `Execution_Status.md` mediante PR.

## Cierres aplicados en esta reconciliación

| US | PR | Evidencia de cierre | Responsable |
|---|---|---|---|
| US-323 | #108 | Set de 20 preguntas, pruebas automatizadas, documento `approved` y DevLog | Carlos Mayorga |
| US-415 | #95 | Contrato Pydantic API↔ML, 11 pruebas, documentación y DevLog | Juan Carlos Macías |
| US-523a | #90/#93 | Ruleset contrastado, documento corregido y `approved`, TEST-002 y DevLog | Alejandro Velázquez |

## Cola de validación para junta

| US | PR | Descripción corta del PR | Responsable | Acción a realizar | Por quién |
|---|---|---|---|---|---|
| US-004 | #112 y reconciliaciones PM | Matriz y tablero de control | Edgar Coronel | Resolver los acuerdos de esta tabla, regenerar el tablero y cerrar TEST-002 | Edgar Coronel |
| US-113 | #81/#105/#115 | Cubos Gold, carga real y orden dbt | Deni Garrido | Validar DB-10 con DS-06 o aprobar excepción explícita; confirmar cierre | Deni y Diana; excepción Edgar |
| US-121a | #107 abierto | Prueba real DS-06/DS-08 | Emilio Galnares | Revisar evidencia de descarga, checks y merge | Diana Alvarez |
| US-122a | #107 abierto | Extractores DS-06/DS-08 | Emilio Galnares | Ejecutar contra fuentes reales, revisar metadatos y merge | Diana Alvarez |
| US-123a | #107 abierto | Calidad DS-06/DS-08 | Emilio Galnares | Confirmar resultados reales y tratamiento `SIN_DATO` | Diana Alvarez |
| US-124a | #107 abierto | Fixtures/pruebas DS-06/DS-08 | Emilio Galnares | Revisar fixtures ≤500 filas, checks y merge | Diana Alvarez |
| US-204 | #100 | DB-06 Predicciones y DB-09 Recomendaciones | Manuel Serranía | Repetir 15/15 charts con salidas reales de US-313 | Manuel y Héctor |
| US-213 | #114 abierto | DB-05 por driver y DB-08 explorador | Monserrat Miranda | Revalidar `dim_driver`, checks, revisión y merge | Manuel Serranía y Diana Alvarez |
| US-221 | #106 abierto | Gráficos KPI reutilizables | Oscar Quiroz | Revisar artefactos, checks y merge | Manuel Serranía |
| US-302 | #58/#113/#116/#117 | ML-02, driver real y cobertura por ventana | Andrés González | Gold real, Registry Docker, endpoint SHAP y documento `approved` | Andrés y Christian |
| US-304a | #92/#104/#108/#119 | Prompt, guardarraíles y servicio seguro | Andrés González | Conectar `procesar_consulta_con_rag()` al endpoint real de C4 (**BUG-025**), corregir `SELECT … INTO` en el validador (**BUG-024**) y aprobar el documento | Andrés y Christian |
| US-304b | #108/#119 | Recuperación RAG sobre esquema Gold | Carlos Mayorga | Carga diferida y errores tipados ya mergeados; falta probar la recuperación dentro del contenedor | Carlos y Andrés |
| US-305 | #92/#94/#98/#104/#119 | Widget de chat, historial y JWT | Andrés González | E2E widget→API→RAG con login real; resolver BUG-020 y BUG-025 | Andrés, Christian y Carlos |
| US-313 | #41/#83/#96/#111/#117 | Publicación batch a Gold | Héctor Morales | Ratificar ADR-007/BUG-019 y ejecutar `--desde-gold` sobre Gold real | Héctor, Diana y Edgar/Andrés |
| US-324 | #110 | Model cards ML-01/02/03 | Carlos Mayorga | Corregir ficha ML-03 y obtener revisión de los tres dueños | Héctor, Andrés y Estefany |
| US-403 | #97 | RBAC ciudadano/analista | Christian Ruiz | Definir `ANALISTA_EMAILS`, ejecutar 401/403 E2E y registrar revisión de seguridad | Christian y Edgar |
| US-411 | #59/#95/#99 | Endpoints reales sobre Gold | Karla Monter | Resolver BUG-020 en producción y validar endpoints; ratificar `/series` fuera de alcance | Christian y Luis; valida Karla |
| US-412 | #95 | Endpoints de inferencia `/predicciones/*` | Juan Carlos Macías | **Reabierta**: el código y las pruebas están bien, pero las rutas responden 500 en producción. Cierra con BUG-020 resuelto, igual que US-411 | Christian y Luis; valida Juan Carlos |
| US-416 | #101 | Cache TTL, timeout y 503 | Juan Carlos Macías | Ratificar diseño y que el E2E Postgres pertenece a US-422 | Christian y Karla |
| US-521c | #23 | Ambiente local Superset/agente | Edward Ruiz | Convertir el DevLog a `.md` filed, actualizar índice y repetir la guía | Edward; valida Luis |
| US-522a | #90/#99 | Contenedor API/Postgres y app real | Alejandro Velázquez | Ejecutar E2E local Compose API↔Postgres | Alejandro y Luis; valida Christian |
| US-522b | #87 abierto | Contenedor Airflow/jobs ML | Edgar Ulises Jiménez | Resolver checks/revisión y merge | Luis Téllez |
| US-522c | #49/#71 | Contenedor Superset y driver PostgreSQL | Edward Ruiz | Verificar conexión, escribir DevLog y actualizar BUG-004 a `fixed` | Edward y Luis; apoyo Manuel |
| US-524a | #102 abierto | Logs, healthcheck y monitoreo API/Postgres | Alejandro Velázquez | Resolver checks, revisión C5 y merge | Luis Téllez |

## Dependencias todavía en progreso que afectan cierres

| US | Dependencia de cierre | Responsable / validador |
|---|---|---|
| US-106 | US-113 cerrada, RISK-008 confirmado y linaje en `approved` | Diana, Deni y Edgar |
| US-212 | US-313 debe publicar predicciones del mismo ciclo; repetir los bloques ML | Marina, Manuel y Héctor |
| US-311 | Ratificar ADR-007/BUG-019, correr Gold real y confirmar Registry | Héctor, Andrés, Diana y Edgar |
| US-312 | PR #118 **mergeado**; queda ML-03/US-321 con Silhouette | Héctor y Estefany |

## Límites de esta actualización

- No se cambió configuración viva de GitHub ni archivos `.github/**`.
- No se modificaron documentos de Células 1–5 fuera del alcance PM, como `15_ML_Models/**`. Sus
  cambios pendientes aparecen arriba con dueño explícito.
- Sí se tocó `06_Quality_Testing/Bug_Register.md`, que es del PM: se registró **BUG-025** (el agente
  desplegado responde lo mismo a todo) y se corrigió la afirmación de BUG-020 de que la autenticación
  no se podía comprobar en producción — sí se puede, y funciona.
- La autenticación local de GitHub CLI no está vigente; los PR se contrastaron contra el snapshot
  del tablero generado el 28-ago y el historial Git presente en `main`.
