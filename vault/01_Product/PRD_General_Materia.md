---
id: PRD-GENERAL
title: "PRD General de la Materia — Plataforma Integral de BI, Data Engineering y ML"
owner: "Dr. Jose Gustavo Fuentes"
status: approved
source_of_truth: true
tags: [product, prd, rubrica, materia]
---

# Product Requirements Document (PRD)
Plataforma Integral de BI, Data Engineering y Machine Learning
1. Visión General del Proyecto
El objetivo de este proyecto es diseñar, construir y desplegar una plataforma productiva de análisis de datos de extremo a extremo (End-to-End Data Platform) impulsada por datos de libre elección del equipo. La solución debe resolver un problema de negocio o impacto real mediante la ingesta continua de al menos 5 fuentes de datos distintas, procesamiento en capas de calidad, almacenamiento optimizado, modelos de Machine Learning, visualización interactiva de BI, autenticación avanzada y un agente conversacional inteligente.

Todo el sistema estará contenedorizado y desplegado en la nube (AWS o GCP) bajo una URL pública accesible.

2. Estructura de Trabajo Sugerida (Super-Equipo de 20 Personas)
Al ser un equipo de 20 integrantes, es obligatorio dividirse internamente en 5 Células de Trabajo interconectadas con un líder técnico (Tech Lead) por célula:

                                 ┌─────────────────────────────────┐
                                 │       Líder de Proyecto / PO    │
                                 └────────────────┬────────────────┘
                                                  │
 ┌───────────────────┬───────────────────┬────────┴──────────┬───────────────────┐
 │                   │                   │                   │                   │
 ▼                   ▼                   ▼                   ▼                   ▼
Célula Data Eng.    Célula BI / Viz     Célula ML & AI      Célula Backend/Auth Célula Cloud/DevOps
(4 personas)        (4 personas)        (4 personas)        (4 personas)        (4 personas)
Célula 1: Data Engineering & Quality (4) — Scraping/APIs multi-fuente, orchestrator, pipeline continuo, transformaciones de datos, validación y data quality.

Célula 2: Analytics & Business Intelligence (4) — Dashboard interactivo frontend, experiencia de usuario (UX/UI), KPIs, filtros dinámicos.

Célula 3: Machine Learning & AI Agent (4) — Entrenamiento de 3 modelos de ML, APIs de inferencia, implementación del agente conversacional.

Célula 4: Backend, API & Seguridad (4) — Desarrollo de API REST/GraphQL, Autenticación avanzada (OAuth2/RBAC), integración de base de datos.

Célula 5: Cloud Infrastructure & Docker (4) — Arquitectura en AWS/GCP, contenedorización (Docker/Compose), networking, base de datos administrada y dominio público.

3. Especificaciones Técnicas y Requerimientos Funcionales
 ┌────────────────┐     ┌────────────────┐     ┌──────────────────┐     ┌────────────────┐
 │ Ingesta Multi- │    │ Pipeline &     │     │ Storage &        │     │ Consumo        │
 │ fuente (≥5)    │───>│ Data Quality   │───> │ Postgres/Parquet │───> │ API + Auth     │
 │ Continuas      │    │ (Orquestado)   │     │ (Medallón)       │     └───────┬────────┘
 └────────────────┘     └────────────────┘     └──────────────────┘             │
                                                                                ▼
 ┌────────────────┐     ┌────────────────┐                     ┌────────────────┐
 │ Agente Convers.│<───>│ 3 Modelos ML   │<───────────────────>│ Dashboard BI   │
 │ (LLM / RAG)    │     │ (Predictivos)  │                     │ Interactivo    │
 └────────────────┘     └────────────────┘                     └────────────────┘
3.1. Ingesta y Pipelines (Data Engineering)
Datos propios / Tema libre: El equipo debe elegir un dominio (Finanzas, Retail, Salud, Movilidad, Deporte, etc.).

Mínimo 5 Fuentes de Datos Distintas: La solución debe integrar y enriquecer información proveniente de al menos 5 orígenes diferentes.

Ejemplos de fuentes: APIs REST públicas/privadas, Web Scraping de sitios dinámicos, fuentes geoespaciales, API de clima/meteorología, datos macroeconómicos, datasets estáticos en la nube, feeds en streaming, etc.

Ingesta Continua Automatizada: El pipeline no puede ser manual. Debe ejecutarse de manera programada/continua (ej. ejecuciones diarias o por eventos mediante cronjobs, Airflow, Prefect, GitHub Actions o agentes en streaming).

Calidad de Datos ("Datos Limpísimos"): Implementación de una arquitectura organizada (ej. tipo Medallón: Bronze -> Silver -> Gold) con auditoría explícita de calidad (nulos, duplicados, límites físicos, tipos de datos) usando herramientas como Great Expectations, Polars, DuckDB o Pydantic.

3.2. Machine Learning (Mínimo 3 Modelos)
El sistema debe incorporar al menos 3 modelos de ML distintos que agreguen valor real al dominio elegido. Ejemplos de combinaciones válidas:

Modelo 1 (Supervisado - Regresión/Series de Tiempo): Predicción o forecasting de métricas futuras (ej. ventas, demanda, precios).

Modelo 2 (Supervisado - Clasificación): Detección de anomalías, churn de usuarios, clasificación de riesgo, etc.

Modelo 3 (No Supervisado - Clustering): Segmentación de clientes, agrupamiento de zonas geográficas o patrones de comportamiento.

Inferencia: Los modelos deben estar expuestos vía API para realizar predicciones en tiempo real o batch, integrándose en el Frontend/BI.

3.3. Agente Conversacional (AI Agent)
Funcionalidad: Implementación de un asistente conversacional dentro de la interfaz web que permita a los usuarios interactuar con los datos o métricas del sistema mediante lenguaje natural (Text-to-SQL básico, RAG sobre los datos, o un agente alimentado con métricas calculadas).

Alcance: Debe responder preguntas clave del negocio (ej. "¿Cuál fue la entidad con mayor demanda el mes pasado?", "Dame la predicción para mañana con base en el modelo 1").

3.4. Backend y Autenticación Avanzada (AuthN / AuthZ)
Framework: Elección libre (FastAPI, Node.js/Express, Django, Go, etc.).

Autenticación Avanzada:

OAuth2 con JWT / Login Social (Google, GitHub) o Proveedor de Auth (Supabase Auth, Auth0, Firebase).

Manejo seguro de tokens (Refresh/Access Tokens).

Autorización (RBAC - Role-Based Access Control): Al menos 2 roles distintos con diferentes privilegios:

Usuario estándar / Cliente: Solo visualiza dashboards públicos y consulta al agente.

Analista / Admin: Puede ejecutar pipelines de datos, consultar endpoints de ML avanzados o exportar datos en bruto.

3.5. Frontend & Business Intelligence Interactivo
Interfaz Dinámica: React, Next.js, Vue, Svelte, o un Dashboard customizado (Plotly/Dash, Streamlit avanzado, HTML/JS con librerías modernas).

Componentes clave:

KPIs globales en tiempo real.

Gráficos interactivos (series de tiempo, distribución, mapas si aplica).

Panel de Machine Learning: Interfaz interactiva donde el usuario puede ingresar parámetros y recibir predicciones de los 3 modelos.

Widget del Agente Conversacional: Ventana de chat flotante o dedicada.

Módulo de Gestión de Usuarios/Auth: Login, Logout y vistas protegidas por rol.

3.6. Infraestructura y Despliegue Cloud
Nube: AWS o GCP.

Contenedores: Todo el ecosistema (Frontend, Backend, DB, Agente/ML, Pipeline) debe estar Dockerizado (ej. docker-compose o desplegado en servicios como ECS, Cloud Run, GKE, App Runner, EC2/GCE con Docker).

Acceso Público: Desplegado y funcional en una URL pública (dominio propio o subdominio asignado por la nube/IP pública configurable).

Nota: No se exige pipeline de CI/CD automatizado, pero el despliegue en nube debe ser 100% estable.

4. Entregables del Proyecto
Repositorio de Código (GitHub/GitLab): Estructura limpia, commits de todos los integrantes, archivo README.md detallado con instrucciones de ejecución local y arquitectura.

URL Pública Viva: Enlace accesible donde el profesor y la audiencia puedan probar la plataforma desplegada en AWS/GCP.

Diagrama de Arquitectura: Esquema visual que detalle el flujo de las 5 fuentes de datos (Ingesta Multi-fuente $\rightarrow$ Almacenamiento $\rightarrow$ API $\rightarrow$ ML $\rightarrow$ BI / Agente).

Demostración en Vivo (Pitch): Presentación del equipo mostrando el valor de la plataforma, arquitectura y casos de uso.

5. Rúbrica de Calificación (Escala 0 a 10)
La evaluación está significativamente cargada hacia la Ingeniería de Datos (DE) y Business Intelligence (BI).

Criterio / Módulo	Peso	Descripción y Niveles de Desempeño
1. Data Engineering & Pipelines Multi-fuente	2.5 pts	
(2.5 pts): Integración continua 100% automatizada de al menos 5 fuentes de datos distintas. Arquitectura de almacenamiento en capas (ej. Medallón) limpia y funcional. Datos sin inconsistencias, con auditoría/validación de calidad explícita.


(1.5 pts): Integra de 3 a 4 fuentes de datos, o el pipeline está automatizado pero es frágil / carece de validaciones de calidad sólidas.


(0.5 pts): Integra menos de 3 fuentes, carga datos de forma estática (CSV local) o sin automatizar.

2. Frontend BI & Inteligencia de Negocios	2.5 pts	
(2.5 pts): Dashboard dinámico, intuitivo y estético. Visualización avanzada de KPIs, tendencias, componentes interactivos y filtros que consolidan las 5 fuentes. Excelente experiencia de usuario.


(1.5 pts): Visualizaciones básicas o poco interactivas, errores de maquetación.


(0.5 pts): Pantalla estática con gráficos rígidos sin interacción.

3. Modelos de Machine Learning (3 modelos)	1.5 pts	
(1.5 pts): 3 modelos distintos bien justificados, entrenados e integrados a la API/Frontend para inferencias en tiempo real/batch.


(1.0 pt): Solo 1 o 2 modelos integrados, o modelos triviales sin integración real.


(0.0 pts): No incluye modelos de ML.

4. Backend, API & Autenticación Avanzada	1.5 pts	
(1.5 pts): API robusta, rápida y parametrizada. Autenticación avanzada (OAuth2 / JWT) con Roles (RBAC) funcionando correctamente en vistas protegidas.


(1.0 pt): API funcional con autenticación básica (sin roles o sin OAuth2).


(0.5 pts): API frágil, vulnerabilidades evidentes o auth parcial.

5. Despliegue en AWS/GCP & Dockerización	1.0 pt	
(1.0 pt): Todos los servicios corren en contenedores Docker y están desplegados en AWS o GCP en una URL pública totalmente funcional.


(0.5 pts): Desplegado en plataformas PaaS simples (Render/Heroku) o con fallas en la URL pública.


(0.0 pts): Solo funciona en localhost.

6. Agente Conversacional (AI Agent)	0.5 pts	
(0.5 pts): Agente funcional integrado en la UI que responde preguntas de negocio usando los datos consolidado de las fuentes mediante lenguaje natural.


(0.25 pts): Chatbot desconectado del contexto de los datos o incompleto.


(0.0 pts): No implementado.

7. Trabajo en Equipo, Git & Documentación	0.5 pts	
(0.5 pts): Commits distribuidos equitativamente entre los 20 miembros. README impecable, diagramas claros y entrega organizada.


(0.25 pts): Commits concentrados en pocas personas, documentación pobre.


(0.0 pts): Sin repositorio ni documentación.

TOTAL	10.0 pts	
Nota de penalización: Si la solución no está desplegada en una URL pública funcional al momento de la evaluación, la calificación máxima alcanzable será de 6.0 / 10.