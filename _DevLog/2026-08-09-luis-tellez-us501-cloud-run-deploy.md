---
id: DEVLOG-2026-08-09-LUIS-US501
title: "DevLog — US-501 Cloud Run Deploy (Sprint 1)"
author: "Luis Téllez Domínguez"
session_date: "2026-08-09"
ai_tool: "Claude Code (Sonnet 4.5)"
traces_up: ["US-501", "REQ-005"]
affected_ids: ["US-501", "REQ-005", "DOC-CLOUD-RUN-DEPLOY"]
tags: [devlog, ai-assisted, cloud-run, gcp, sprint-1, deploy]
---

# DevLog — US-501: Deploy Hello World a Cloud Run

## Contexto

**Objetivo:** Cumplir con la historia crítica US-501 — desplegar un "hello world" en Cloud Run con URL pública accesible, eliminando el riesgo del techo de 6.0 desde la semana 1.

**Fecha:** Domingo 9 de agosto de 2026  
**Duración:** ~6 horas (17:00 - 23:00)  
**Tool:** Claude Code (Sonnet 4.5)

---

## Qué se pidió a la IA

### Sesión Completa (9 de agosto)

**Contexto inicial:**
```
"Analiza el repo e indicame qué hace el proyecto, así como tareas y dependencias de Luis Téllez"

"Hacer un plan de actividades detallado para cumplir con las tareas de Luis del S1"

"Valida que el plan de despliegue de S1 de Luis puede alinearse a CIS Controls 8"
```

**Prompts principales de desarrollo:**

1. **FastAPI básico:**
   ```
   "Crear FastAPI app con endpoints /, /health, /info con respuesta JSON que incluya 
   timestamp, environment variable y metadata del proyecto FARO"
   ```

2. **Dockerización:**
   ```
   "Escribe un Dockerfile optimizado para FastAPI con healthcheck, puerto 8080 
   para Cloud Run, y sin secrets hardcodeados"
   ```

3. **Scripts de automatización:**
   ```
   "Crea scripts bash para:
   - Build y push de imagen Docker a Artifact Registry
   - Deploy a Cloud Run con configuración de memory, CPU, instances"
   ```

4. **Configuración de GCP:**
   ```
   "Guíame paso a paso para:
   - Instalar gcloud CLI
   - Autenticar
   - Crear proyecto en organización
   - Habilitar APIs necesarias
   - Crear Artifact Registry
   - Deploy a Cloud Run"
   ```

5. **Auditoría de seguridad:**
   ```
   "Valida que lo que vamos a desplegar tenga validación de seguridad de acuerdo 
   a los requerimientos del proyecto (Secrets Policy)"
   ```

6. **Documentación:**
   ```
   "Documenta el procedimiento completo de deploy en Cloud_Run_Deploy.md con 
   frontmatter, comandos exactos, troubleshooting y costos"
   ```

---

## Qué generó la IA

### Código generado (100% asistido por IA)

#### 1. `src/api/main.py` (118 líneas)
```python
# FastAPI app con:
- 3 endpoints: /, /health, /info
- Logging estructurado JSON para Cloud Logging
- Variables de entorno para configuración
- Metadata del proyecto FARO
```
**Revisión:** Ajusté formato de respuesta para incluir más detalles del proyecto.

#### 2. `src/api/__init__.py`
```python
# Módulo init con versión
```
**Sin cambios** (generado correctamente).

#### 3. `docker/api.Dockerfile` (27 líneas)
```dockerfile
# Dockerfile simplificado para Cloud Run
- Base: python:3.11-slim
- Puerto: 8080
- Healthcheck con Python urllib
- Variables de entorno configurables
```
**Revisión:** Tuve que iterar 2 veces:
- Primera versión: usuario no-root (causó problemas de permisos)
- Segunda versión: simplificado sin usuario no-root (funciona, se mejorará en S2)

#### 4. `docker/.dockerignore` (31 líneas)
```
# Excluye archivos innecesarios del build
```
**Sin cambios** (generado correctamente).

#### 5. `infra/build-and-push.sh` (50 líneas)
```bash
# Script automatizado para:
- Build de imagen Docker para amd64
- Push a Artifact Registry
- Tag como :latest
```
**Revisión:** Ajusté colores de output y validación de PROJECT_ID.

#### 6. `infra/deploy-cloud-run.sh` (47 líneas)
```bash
# Script automatizado para:
- Deploy a Cloud Run
- Configuración de resources (512Mi, 1 CPU)
- Límite de 1 instancia máxima
- Variables de entorno
```
**Revisión:** Agregué límite de `max-instances=1` por seguridad.

### Documentación generada (80% asistida por IA)

#### 1. `08_CICD_DevOps/Cloud_Run_Deploy.md` (500+ líneas)
Guía completa con:
- Requisitos previos
- Configuración de GCP paso a paso
- Procedimiento de build y deploy
- Verificación
- Troubleshooting
- Costos
- Próximos pasos

**Revisión:** Enriquecí con:
- URLs reales del proyecto
- IDs específicos (org, proyecto)
- Detalles de costos actualizados
- Enlaces a otros documentos del vault

#### 2. `README.md` - Sección de Despliegue
```markdown
## 🚀 Despliegue
URL de Producción: https://faro-api-eanzfglvyq-uc.a.run.app
```
**Revisión:** Agregué formato y emojis para mejor legibilidad.

#### 3. `requirements.txt` - Actualizado
```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
```
**Sin cambios** (generado correctamente).

---

## Qué se revisó línea por línea

### Código

✅ **Dockerfile:**
- Verificado que no contiene secrets
- Verificado puerto 8080 (Cloud Run standard)
- Verificado healthcheck apunta al endpoint correcto
- Iterado para solucionar problema de permisos de usuario

✅ **main.py:**
- Ajusté respuestas JSON para incluir metadata del proyecto
- Verifiqué logging estructurado (formato JSON)
- Verifiqué uso correcto de `os.getenv()`

✅ **Scripts bash:**
- Añadí `set -euo pipefail` para fail-fast
- Verifiqué nombres de variables
- Probé ejecución local antes de usar

### Seguridad

✅ **Auditoría pre-deploy:**
- Verificado: sin secretos hardcodeados ✅
- Verificado: sin .env en Git ✅
- Verificado: variables de entorno usadas correctamente ✅
- Verificado: solo endpoints informativos ✅
- Verificado: límite de 1 instancia para protección de costos ✅

**Cumple con:** `07_Security/Secrets_Policy.md`

### Comandos ejecutados manualmente (no delegados a IA)

La IA NO puede ejecutar ciertos comandos del sistema. Yo ejecuté:

```bash
# Instalación de gcloud
brew install --cask google-cloud-sdk

# Autenticación
gcloud auth login

# Movimiento del proyecto a organización
# (desde consola web de GCP)
```

---

## Decisiones tomadas (no sugeridas por IA)

### 1. Límite de 1 instancia máxima

**IA sugirió:** `max-instances=10`

**Yo decidí:** `max-instances=1`

**Razón:** Proyecto académico, protección contra abuso/costos. Mejor ser conservador en S1.

### 2. Región us-central1

**IA sugirió:** `us-east1` (más común)

**Yo decidí:** `us-central1`

**Razón:** Ligeramente mejor latencia desde México.

### 3. Mover proyecto a organización

**IA sugirió:** Dejar en cuenta personal (funciona igual)

**Yo decidí:** Mover a `luis-g-roses-org`

**Razón:** Mejor gobernanza, práctica profesional correcta.

### 4. Auditoría de seguridad pre-deploy

**IA NO sugirió** hacer auditoría.

**Yo pedí:** "Valida que lo que vamos a desplegar tenga validación de seguridad"

**Resultado:** Detectamos que todo cumplía, procedimos con confianza.

### 5. Arquitectura de imagen Docker

**Problema:** Primera imagen falló con error "Container manifest type not supported"

**IA propuso:** Rebuild con `--platform linux/amd64`

**Yo ejecuté:** Build específico para amd64 con `docker buildx`

**Resultado:** Funcionó correctamente.

---

## Problemas encontrados y cómo se resolvieron

### Problema 1: Dockerfile con usuario no-root causó error de permisos

**Síntoma:**
```
/bin/sh: 1: uvicorn: Permission denied
```

**Causa:** Usuario no-root no tenía uvicorn en su PATH

**Solución:**
- Simplifiqué Dockerfile para correr como root (Sprint 1)
- Documentado como mejora para Sprint 2
- Cloud Run aísla contenedores de todas formas

**Tiempo perdido:** 10 minutos

### Problema 2: Error "Container manifest type not supported"

**Síntoma:**
```
Cloud Run does not support image manifest type 'application/vnd.oci.image.index.v1+json'
```

**Causa:** Mac M1 genera imágenes arm64 por defecto, Cloud Run requiere amd64

**Solución:**
```bash
docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/faro-escuela-sensor/faro-images/faro-api:v0.1.0-s1 \
  -f docker/api.Dockerfile \
  --push \
  .
```

**Tiempo perdido:** 5 minutos

### Problema 3: gcloud CLI no tenía comando "move" para proyectos

**Síntoma:**
```
ERROR: (gcloud.projects) Invalid choice: 'move'
```

**Causa:** Comando no existe en gcloud CLI

**Solución:** Mover proyecto desde consola web de GCP

**Tiempo:** 2 minutos (muy rápido)

### Problema 4: Docker Desktop no estaba corriendo

**Síntoma:**
```
Cannot connect to Docker daemon
```

**Solución:**
```bash
open -a Docker
# Esperar 15 segundos
```

**Tiempo perdido:** 1 minuto

---

## IDs afectados

- **US-501** — Historia principal ✅ **COMPLETADA**
- **REQ-005** — Requisito de despliegue GCP ✅ **CUMPLIDO**
- **DOC-CLOUD-RUN-DEPLOY** — Nuevo documento de procedimiento ✅

---

## Archivos creados/modificados

### Creados (10 archivos)

**Código:**
1. `src/api/__init__.py`
2. `src/api/main.py`
3. `docker/api.Dockerfile`
4. `docker/.dockerignore`
5. `infra/build-and-push.sh`
6. `infra/deploy-cloud-run.sh`

**Documentación:**
7. `08_CICD_DevOps/Cloud_Run_Deploy.md`
8. `_DevLog/2026-08-09-luis-tellez-us501-cloud-run-deploy.md` (este archivo)

### Modificados (3 archivos)

1. `requirements.txt` — Agregados fastapi, uvicorn
2. `README.md` — Sección de despliegue
3. `08_CICD_DevOps/_index.md` — Enlace al documento de deploy

---

## Configuración de GCP realizada

### Proyecto

- **ID:** faro-escuela-sensor
- **Número:** 526490367142
- **Organización:** luis-g-roses-org (ID: 196009726606)
- **Billing:** Habilitado (cuenta: 0139AB-5BB3B4-1F3792)

### APIs habilitadas

- ✅ run.googleapis.com (Cloud Run)
- ✅ artifactregistry.googleapis.com (Artifact Registry)
- ✅ cloudbuild.googleapis.com (Cloud Build)

### Artifact Registry

- **Repositorio:** faro-images
- **Formato:** Docker
- **Ubicación:** us-central1
- **URL:** us-central1-docker.pkg.dev/faro-escuela-sensor/faro-images

### Cloud Run

- **Servicio:** faro-api
- **Región:** us-central1
- **URL:** https://faro-api-eanzfglvyq-uc.a.run.app
- **Imagen:** us-central1-docker.pkg.dev/faro-escuela-sensor/faro-images/faro-api:v0.1.0-s1
- **Configuración:**
  - Memory: 512Mi
  - CPU: 1 vCPU
  - Min instances: 0 (scale to zero)
  - Max instances: 1 (protección de costos)
  - Timeout: 300s
  - Port: 8080
  - Allow unauthenticated: true (Sprint 1)
  - Environment: ENVIRONMENT=production

---

## Verificación final

### Endpoints funcionando

✅ **Endpoint raíz:**
```bash
curl https://faro-api-eanzfglvyq-uc.a.run.app
```
```json
{
  "message": "Hello World from FARO",
  "project": "Escuela como Sensor Social",
  "description": "Plataforma de BI end-to-end para predicción de matrícula escolar",
  "timestamp": "2026-08-09T23:53:37.270629",
  "environment": "production",
  "version": "0.1.0",
  "sprint": "S1",
  "status": "operational"
}
```

✅ **Health check:**
```bash
curl https://faro-api-eanzfglvyq-uc.a.run.app/health
```
```json
{
  "status": "healthy",
  "service": "faro-api",
  "version": "0.1.0",
  "timestamp": "2026-08-09T23:53:37.723250",
  "uptime_seconds": 11.98,
  "environment": "production"
}
```

✅ **Swagger UI accesible:**
https://faro-api-eanzfglvyq-uc.a.run.app/docs

### Infraestructura

- ✅ Proyecto en organización correcta
- ✅ Billing habilitado
- ✅ APIs funcionando
- ✅ Artifact Registry con imagen
- ✅ Cloud Run desplegado
- ✅ Límite de 1 instancia configurado
- ✅ Logs en Cloud Logging
- ✅ URL pública accesible desde cualquier navegador

### Seguridad

- ✅ Sin secretos hardcodeados
- ✅ Variables de entorno usadas correctamente
- ✅ `.env` NO en Git
- ✅ Límite de instancias configurado
- ✅ Cumple con Secrets Policy

### Documentación

- ✅ Cloud_Run_Deploy.md completo
- ✅ README.md actualizado
- ✅ Índices actualizados
- ✅ DevLog escrito
- ✅ Commits con mensajes convencionales

---

## Métricas de la sesión

**Tiempo total:** ~6 horas

**Desglose:**
- Configuración inicial: 1 hora
- Desarrollo (FastAPI + Docker): 1.5 horas
- Setup de GCP: 1 hora
- Build y deploy: 1 hora
- Troubleshooting: 30 minutos
- Documentación: 1 hora

**Líneas de código generadas:** ~500 (código + scripts + docs)

**% asistido por IA:** ~85%
- Código: 95% generado por IA, 5% ajustes
- Documentación: 80% generada por IA, 20% enriquecimiento
- Comandos GCP: 50% sugeridos por IA, 50% ejecutados manualmente

**Commits realizados:** 2
1. `feat(cloud): FastAPI hello world + Dockerfile funcional`
2. `docs(cloud): documenta procedimiento de deploy a Cloud Run`

---

## Costos incurridos

**Costo del deploy de hoy:** $0

**Desglose:**
- Cloud Run: $0 (free tier, <100 requests)
- Artifact Registry: $0 (free tier, 0.5 GB)
- Cloud Build: $0 (free tier, 1 build)

**Costo mensual estimado:** $0-2 (dentro de free tier)

---

## Próximos pasos (siguientes sprints)

### Sprint 2 (10-16 agosto)
- US-502: docker-compose completo con 6 servicios
- US-503: CI/CD pipeline en GitHub Actions
- Mejora: Usuario no-root en Dockerfile

### Sprint 4 (24-30 agosto)
- US-504: Cloud SQL provisionado
- VPC peering (Cloud Run ↔ Cloud SQL)
- Secret Manager para credenciales
- OAuth2/JWT en endpoints

### Sprint 6 (7-8 septiembre)
- US-505: Deploy final productivo
- Uptime checks y alertas
- Observabilidad completa
- Sistema estable para demo del 9 de septiembre

---

## Lecciones aprendidas

### 1. Hacer deploy crítico en S1 fue la decisión correcta

✅ **Elimina el riesgo del 6.0** (sin URL pública, nota máxima = 6.0)  
✅ **Da confianza al equipo** (sabemos que el deploy funciona)  
✅ **Facilita desarrollo incremental** (siguiente sprint mejora, no construye desde cero)

### 2. Auditoría de seguridad pre-deploy es esencial

Pedí explícitamente auditoría antes de desplegar. Resultado:
- Sin secretos expuestos
- Configuración correcta
- Límites de protección en lugar

**No confiar ciegamente en la IA.** Siempre validar seguridad.

### 3. Scripts de automatización desde el inicio ahorran tiempo

Los scripts `build-and-push.sh` y `deploy-cloud-run.sh` facilitan:
- Re-deploys rápidos (30 segundos)
- Menos errores (comandos estandarizados)
- Onboarding del equipo (otros pueden deployar fácilmente)

### 4. Dockerfile simple > Dockerfile perfecto (para Sprint 1)

Intenté usuario no-root (best practice) pero causó problemas.

**Decisión:** Simplificar para S1, mejorar en S2.

**Razón:** Cloud Run aísla contenedores de todas formas. Seguridad aceptable para S1.

### 5. Build específico para amd64 es necesario en Mac M1/M2

Sin `--platform linux/amd64`, Cloud Run rechaza la imagen.

**Aprendizaje:** Siempre especificar plataforma en Macs con Apple Silicon.

### 6. Mover proyecto a organización es más fácil por consola web

gcloud CLI no tiene comando directo. Consola web lo hace en 2 clicks.

### 7. Límite de 1 instancia es buena práctica para proyectos académicos

Protege contra:
- Abuso/DDoS
- Costos inesperados
- "Olvidar apagar" el servicio

**Costo máximo con 1 instancia:** ~$2-5/mes (muy controlado)

### 8. IA acelera, pero no reemplaza criterio humano

La IA generó el 85% del código/docs, PERO:
- Yo decidí límite de instancias
- Yo pedí auditoría de seguridad
- Yo ajusté configuración para el proyecto específico
- Yo moví el proyecto a organización

**No delegar el pensamiento crítico a la IA.**

---

## Validación contra Definition of Filed

- [x] Tiene ID único (`DEVLOG-2026-08-09-LUIS-US501`)
- [x] Tiene owner (`Luis Téllez Domínguez`)
- [x] Tiene frontmatter completo
- [x] Enlaza a origen (`traces_up: US-501, REQ-005`)
- [x] Está en su carpeta (`_DevLog/`)
- [x] Se agregará a `_DevLog/_index.md` en próximo commit

---

## Conclusión

**US-501 ✅ COMPLETADA**

- ✅ URL pública funcionando: https://faro-api-eanzfglvyq-uc.a.run.app
- ✅ FastAPI desplegado en Cloud Run
- ✅ Infraestructura GCP configurada
- ✅ Documentación completa
- ✅ Código en GitHub
- ✅ Riesgo del 6.0 eliminado

**El objetivo crítico del Sprint 1 está cumplido.**

Próximo paso: Abrir Pull Request para revisión del equipo.

---

**Fecha:** 2026-08-09  
**Hora de finalización:** 23:00  
**Estado:** ✅ Sesión completada exitosamente  
**Siguiente sesión:** Sprint 2 (docker-compose + CI/CD)
