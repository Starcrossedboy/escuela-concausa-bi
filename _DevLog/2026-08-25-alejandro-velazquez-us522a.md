---
id: DEVLOG-2026-08-25-ALEJANDRO-VELAZQUEZ-US522A
title: "US-522a y US-523a: Actualización de estatus de Contenedores y Branch Protection"
author: "Alejandro Velázquez Mendoza"
date: "2026-08-25"
---

# DevLog: US-522a y US-523a

## 1. Contexto de la sesión
**Historias:** US-522a (Contenerizar API y Postgres) y US-523a (Branch Protection).
**Requisitos:** REQ-005 y REQ-007
**Objetivo:** Actualizar estatus, documentar Branch Protection y corregir BUG-008 en el arranque de la API.

## 2. Trabajo realizado
1. **Resolución de BUG-008 en US-522a:** Se corrigió el comando de inicio en `api.Dockerfile`. El contenedor estaba ejecutando `src.api.main:app` (que solo contenía 3 rutas de prueba de US-501). Se cambió a `src.api.app:app` para levantar la aplicación real que contiene los endpoints del contrato v1 necesarios para Célula 4. Con esto, la contenerización de la API (US-522a) queda **Done (100%)**.
2. **Auditoría de US-523a:** Se verificó el comportamiento actual del repositorio remoto, confirmando que las reglas de protección de rama (bloqueo de push directo y requirement de PR) están activas. Además, se documentó el uso del archivo `.github/CODEOWNERS` y la regla de Compuerta Única del PM (DEC-003) en el artefacto `Branch_Protection.md` añadiendo las trazas requeridas para el Definition of Filed. La historia se marca como **Done (100%)**.
3. **Actualización de Tabla de Sprint:** Se actualizó la Tabla 9 del archivo `12_Roadmap_Sprints/Sprints/5-alejandro-velazquez-mendoza.md` con los porcentajes reales (100% para ambas).

## 3. Decisiones técnicas
- **BUG-008:** En lugar de declarar el bloqueo y dejar la US-522a pendiente, se decidió aplicar el fix directamente en el Dockerfile (`src.api.app:app`) aprovechando este PR para destrabar inmediatamente a la Célula 4 de cara al ensayo E2E.
- **Branch Protection:** Se respetó la autoría original de Edgar en el documento `Branch_Protection.md`, enfocándose únicamente en documentar la implementación técnica del archivo `CODEOWNERS` y enlazar las trazas (REQ-007, US-523a, DEC-003).

## 4. Evidencia
- **BUG-008:** Modificación de `CMD` en `docker/api.Dockerfile` para invocar `src.api.app:app`, y actualización de la ruta del `HEALTHCHECK` a `/api/v1/health` para evitar fallos de monitoreo.
- **Branch Protection:** Se intentó realizar un push directo a la rama `main` en local, el cual fue rechazado por el servidor de GitHub con el mensaje `protected branch hook declined`, validando empíricamente el enforcement de las reglas documentadas.
