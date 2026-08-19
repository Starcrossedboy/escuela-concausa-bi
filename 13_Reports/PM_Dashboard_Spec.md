---
id: RPT-PM-SPEC
title: "Especificación del tablero de control PM — FARO"
owner: "Edgar Edmundo Coronel Navarrete"
status: in_review
version: "2.4"
source_of_truth: true
traces_up: ["US-004", "REQ-007", "12_Roadmap_Sprints/PLAN_MAESTRO", "00_Start_Here/Developer_Onboarding"]
traces_down: ["13_Reports/TABLERO_CONTROL_PM.html", "TEST-002"]
last_reviewed: "2026-08-06"
tags: [reports, dashboard, pm, metrics, specification]
---

# Especificación del tablero de control PM — FARO

> Contrato de métricas, fuentes y frescura del tablero. El HTML es una **proyección generada**, nunca
> una fuente de verdad. → [[13_Reports/_index]] · [[12_Roadmap_Sprints/Execution_Status]]

## Objetivo y audiencia

Dar al PO, Tech Leads y profesor una lectura auditable de avance, flujo, dependencias, rúbrica y
preparación de la demo, sin duplicar información del vault ni convertir actividad en desempeño.

## Arquitectura

```text
Fuentes canónicas Markdown + Git local/GitHub
                 ↓
_Meta/scripts/generate_pm_dashboard.py
                 ↓
13_Reports/data/pm-dashboard.json (snapshot auditable)
                 ↓
13_Reports/TABLERO_CONTROL_PM.html (autocontenido y offline)
```

El generador inserta el snapshot dentro del HTML para que funcione con `file://`. El JSON se conserva
para auditoría y consumo futuro. Ninguno se edita manualmente.

## Fuentes canónicas

| Dominio | Fuente | Campos consumidos |
|---|---|---|
| Requisitos y puntos | [[02_Requirements/User_Stories]] · [[02_Requirements/Traceability_Matrix]] | REQ, rúbrica, cobertura |
| Catálogo de trabajo | [[02_Requirements/User_Stories]] | US, título, responsable, célula, sprint |
| Ejecución | [[12_Roadmap_Sprints/Execution_Status]] | estado, fechas, bloqueo, evidencia |
| Plan individual | [[12_Roadmap_Sprints/Sprints/_index]] | misión, objetivos, inputs, outputs, revisor y entregables |
| Directorio GitHub | [[00_Start_Here/Developer_Onboarding]] | usuario GitHub confirmado o pendiente por integrante |
| Responsabilidad | [[12_Roadmap_Sprints/RACI]] | R/A/C/I y gate |
| Dependencias | [[12_Roadmap_Sprints/PLAN_MAESTRO]] · [[10_Risk_Governance/Blocker_Register]] | cadena, bloqueo, aging |
| Entrega final | [[12_Roadmap_Sprints/PLAN_MAESTRO]] | `delivery_date`, etiqueta y zona horaria del contador |
| Riesgos | [[10_Risk_Governance/Risk_Register]] | probabilidad, impacto, respuesta, trigger |
| Fuentes de datos | [[14_Data_Sources/_index]] y notas `DS-*.md` | owner, frecuencia, prueba, cobertura |
| Calidad y gobierno | [[05_Engineering/Definition_of_Done]] · [[_DevLog/_index]] | gates, evidencia |
| Actividad Git | snapshot efímero generado por `_Meta/scripts/collect_github_activity.py` | PR autorados y CI; nunca determina `done` por sí sola |

## Pestañas

| Vista | Pregunta que responde | Componentes |
|---|---|---|
| **Ejecutivo 360°** | ¿Cómo va todo el proyecto de un vistazo? | semáforo por módulo (rúbrica), avance ponderado, burndown corregido, cumplimiento PRD, mapa de calor de riesgos, riesgos críticos y pendientes en turno |
| **Roadmap semáforo** | ¿Cómo avanza cada sprint? | progreso por sprint con semáforo (verde/ámbar/rojo) |
| **Performance equipo** | ¿Quién va en tiempo y quién arrastra retraso? | heatmap integrante × sprint + engagement (avance ponderado, commits/PR) |
| **Engagement** | ¿Quién ha trabajado y quién no? | dos columnas (han trabajado / sin actividad) con evidencia real por persona: PR mergeados + DevLogs firmados + US propias en estado activo (bloque `engagement`) |
| **Cumplimiento PRD** | ¿Cubrimos lo que pide el profesor? | los 7 criterios de la rúbrica: diseño vs. ejecución |
| Resumen | ¿Llegamos y qué requiere decisión? | confianza, avance, alertas, decisiones y frescura |
| Sprint y flujo | ¿Terminamos o acumulamos trabajo? | burndown, burn-up, CFD, WIP, aging, velocidad |
| Calendario | ¿Qué historias caen en cada sprint y quién las lleva? | historias por sprint coloreadas por célula, con **responsable visible** (avatar de iniciales + nombre corto, campo `owner_short`) y pie de responsables por sprint |
| Células | ¿Cómo está integrado y cargado cada equipo? | composición, roles, estado, entregables y revisión |
| Equipo | ¿Quién integra cada célula y qué tiene asignado? | color por célula, directorio GitHub, US asignadas y PR enviados |
| Plan por célula/persona | ¿Qué debe hacer cada integrante y de quién depende? | selector, misión, actividades, avance, inputs, outputs y revisor |
| Dependencias | ¿Quién espera a quién? | cadena crítica, contratos, bloqueos y alternativa mock |
| Rúbrica y demo | ¿Qué puntos tienen evidencia? | 10 puntos, gates y readiness |
| Fuentes | ¿Son utilizables las ocho fuentes? | prueba, cobertura, frecuencia, dueño y frescura |
| Riesgos | ¿Qué amenaza la entrega? | heat map 5×5, US relacionada, dueño, severidad, fecha objetivo de mitigación y estado |
| Gobernanza | ¿El trabajo es auditable? | vault, CI, pruebas, DevLogs y ciclo de PR |
| Explorador | ¿Qué ocurre con una US específica? | filtros por sprint, célula, persona, REQ y estado |

## Definiciones de métricas

| Métrica | Fórmula | Interpretación |
|---|---|---|
| Avance | `(0·planned + .35·in_progress + .65·in_review + .35·blocked + 1·done) / US` | Tendencia; no sustituye Done |
| Cuenta regresiva | diferencia de días calendario entre hoy en `delivery_timezone` y `delivery_date` | Visible permanentemente; se recalcula en el navegador y nunca queda congelada por el snapshot |
| Burndown | US no `done` por fecha de snapshot | Línea real contra ideal del sprint |
| Burn-up | US `done` contra alcance total | Hace visible el cambio de alcance |
| WIP | `in_progress + in_review + blocked` | Límite recomendado: máximo 2 por persona |
| Aging | días desde inicio o bloqueo | alerta amarilla ≥2; roja ≥4 |
| Velocidad | US `done` por sprint | Solo comparable después de cerrar ≥2 sprints |
| Confianza | gates críticos con evidencia, penalizados por aging/bloqueos | Alta ≥80, media 60–79, baja <60 |
| Readiness | gates demostrables / gates totales | Cada gate enlaza evidencia; sin enlace = pendiente |
| PR enviados por integrante | cantidad de PR cuyo `author.login` coincide, sin distinguir mayúsculas, con su GitHub User | Se muestra `sin datos` si no existe snapshot; no determina desempeño ni `done` |

## Reglas RAG

- **Verde:** en plan, evidencia vigente y sin bloqueo vencido.
- **Ámbar:** desviación o evidencia incompleta recuperable dentro del sprint.
- **Rojo:** gate crítico vencido, bloqueo ≥48 h o evidencia ausente que compromete la demo.
- Todo indicador muestra `generado_en`, commit y fuente; snapshot >24 h se marca vencido.

## Readiness de demo

| Gate | Evidencia exigida | Peso |
|---|---|---|
| URL pública y healthcheck | URL + ejecución fechada | 15 |
| ≥5 fuentes, incluida una continua | prueba de descarga/ingesta | 15 |
| Bronze/Silver/Gold y calidad | corrida + reporte GE | 15 |
| Tres modelos | métricas + registro MLflow | 15 |
| API y auth | tests de endpoints + dos roles | 10 |
| Diez dashboards | checklist funcional | 10 |
| Agente | set de evaluación | 10 |
| Demo y contingencia | dry-run + plan B | 10 |

## Restricciones

- Sin tokens, `.env`, datos reales ni llamadas autenticadas desde el navegador.
- Funcional offline; sin fuentes o librerías remotas obligatorias.
- Accesible con teclado, contraste AA, `aria-label` y tablas legibles.
- GitHub aporta actividad y tiempos, no autoridad sobre el estado de una US.
- El conteo por persona requiere que el usuario del directorio coincida con el autor del PR; cuentas
  pendientes o un snapshot local ausente nunca se interpretan como cero actividad.
- Cambios a `.github/**` requieren revisión explícita de la Célula 5.
