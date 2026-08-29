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
**Objetivo:** Actualizar el estatus de las historias asignadas a la Célula 5 para remover la etiqueta de retraso en el PM Dashboard, ya que el trabajo operativo fue integrado en commits anteriores.

## 2. Trabajo realizado
1. **Auditoría de US-522a:** Se confirmó en el historial de Git que el entregable físico para esta US ya se encuentra en `main`. El `api.Dockerfile` fue subido en el commit `0bfeb2e` por Luis Téllez, y la integración de Postgres en `docker-compose.yml` fue subida en el commit `1ac8e5e` en el PR #25 (US-521a). Se declara la US-522a como **Done (100%)**.
2. **Auditoría de US-523a:** Se verificó el comportamiento actual del repositorio remoto, confirmando que las reglas de protección de rama (bloqueo de push directo y requirement de PR) están **activas**. Además, se documentó el uso del archivo `.github/CODEOWNERS` y la regla de Compuerta Única del PM (DEC-003) en el artefacto `Branch_Protection.md` añadiendo las trazas requeridas para el Definition of Filed. La historia se marca como **Done (100%)**.
3. **Actualización de Tabla de Sprint:** Se actualizó la Tabla 9 del archivo `12_Roadmap_Sprints/Sprints/5-alejandro-velazquez-mendoza.md` con los porcentajes reales para que el PM Dashboard refleje el avance correcto.

## 3. Decisiones técnicas
- Reclamar completitud de US-522a sin hacer un PR con código redundante, validando únicamente la existencia del código en `main`.
- Actualizar el artefacto `Branch_Protection.md` con las trazas y la regla de Compuerta Única para cumplir el Definition of Filed y cerrar la US-523a al 100%.

## 4. Evidencia
- Commit `0bfeb2e` (api.Dockerfile) y commit `1ac8e5e` (docker-compose).
- Archivo `12_Roadmap_Sprints/Sprints/5-alejandro-velazquez-mendoza.md` modificado.
