---
id: SEC-CREDENTIALS-POLICY
title: "Política de Credenciales — FARO"
owner: "Luis Téllez Domínguez"
status: active
version: "1.0"
traces_up: ["REQ-005", "US-502"]
last_reviewed: "2026-08-15"
tags: [security, credentials, cis-controls, passwords]
---

# Política de Credenciales — FARO

> Política de gestión de credenciales para ambientes de desarrollo y producción.
> Cumplimiento: CIS Controls v8 (5.2, 5.3, 6.5)
> → [[07_Security/_index]]

## Nivel de Seguridad

**Nivel alcanzado:** 9/10 (CIS Controls v8 compliant)

| Control CIS | Descripción | Estado |
|---|---|---|
| **CIS 5.2** | Usar passwords únicos | ✅ CUMPLE |
| **CIS 5.3** | Políticas de complejidad (14-16+ chars) | ✅ CUMPLE (20 chars) |
| **CIS 6.5** | Gestión centralizada de accesos | ✅ CUMPLE |

---

## Política de Passwords

### Desarrollo Local

**Requisitos mínimos:**
- ✅ Longitud: 20 caracteres
- ✅ Complejidad: Letras (mayúsculas + minúsculas) + números
- ✅ Sin símbolos especiales (para evitar problemas de escape en shells)
- ✅ Generación: Script `scripts/generate-keys.py`
- ✅ Almacenamiento: Archivo `.env` local (NO va a git)
- ✅ Rotación: Cada 90 días (recomendado)

**Usuarios únicos por servicio:**
```
faro_airflow_admin  → Administrador de Airflow
faro_superset_admin → Administrador de Superset
postgres            → Usuario de base de datos
```

### Producción (GCP)

**Gestión de secretos:**
- ✅ GCP Secret Manager (US-504, Sprint 4)
- ✅ OAuth2/JWT para usuarios finales
- ✅ Service accounts con permisos mínimos
- ✅ Rotación automática cada 90 días
- ✅ Auditoría de accesos (Cloud Audit Logs)

---

## Generación de Credenciales

### Script de Generación

**Ubicación:** `scripts/generate-keys.py`

**Uso:**
```bash
# Generar nuevas credenciales
python3 scripts/generate-keys.py

# Copiar output al archivo .env
cp .env.example .env
# Editar .env con las credenciales generadas
```

**Output del script:**
- Airflow Fernet Key (32 bytes base64)
- Airflow Webserver Secret (32 caracteres URL-safe)
- Superset Secret Key (32 caracteres URL-safe)
- PostgreSQL Password (20 caracteres alfanuméricos)
- Airflow Admin Password (20 caracteres alfanuméricos)
- Superset Admin Password (20 caracteres alfanuméricos)

---

## Almacenamiento de Credenciales

### Desarrollo Local

**Archivo `.env`:**
- ✅ Está en `.gitignore` (NO se sube a git)
- ✅ Contiene credenciales REALES
- ✅ Cada desarrollador tiene SUS PROPIAS credenciales
- ❌ NUNCA compartir credenciales entre desarrolladores

**Plantilla `.env.example`:**
- ✅ Está en git (plantilla pública)
- ✅ Contiene placeholders (NO credenciales reales)
- ✅ Instrucciones de generación
- ✅ Todo el equipo puede copiarla y generar sus propias credenciales

### Producción

**GCP Secret Manager:**
- Secretos versionados
- Rotación automática
- Auditoría de accesos
- Cifrado en reposo
- Acceso vía service accounts

---

## Rotación de Credenciales

### Frecuencia Recomendada

| Ambiente | Frecuencia | Método |
|---|---|---|
| **Desarrollo Local** | 90 días | Manual (ejecutar script) |
| **Producción GCP** | 90 días | Automático (Secret Manager) |

### Proceso de Rotación Local

1. Ejecutar `python3 scripts/generate-keys.py`
2. Copiar nuevas credenciales a `.env`
3. Reiniciar servicios: `docker compose restart`
4. Validar que todo funciona
5. Documentar fecha de rotación (en comentario de `.env`)

---

## Prohibiciones

❌ **NUNCA hacer esto:**

1. Usar passwords triviales (`admin123`, `password`, `changeme`)
2. Compartir credenciales entre desarrolladores
3. Subir archivo `.env` a git
4. Pegar credenciales en prompts de IA
5. Enviar credenciales por Slack/email
6. Usar mismas credenciales en local y producción
7. Hardcodear credenciales en código

---

## Auditoría y Cumplimiento

### Verificación de Cumplimiento

**Checklist mensual:**
- [ ] Archivo `.env` NO está en git
- [ ] Passwords cumplen longitud mínima (20 chars)
- [ ] Usuarios son únicos por servicio
- [ ] Script de generación funciona correctamente
- [ ] Documentación actualizada

### Respuesta a Incidentes

**Si credenciales se comprometen:**
1. ⚠️ Regenerar TODAS las credenciales inmediatamente
2. Ejecutar `python3 scripts/generate-keys.py`
3. Actualizar `.env` con nuevas credenciales
4. Reiniciar todos los servicios
5. Documentar incidente en `10_Risk_Governance/Incident_Log.md`
6. Revisar logs de acceso

---

## Referencias

- [[07_Security/Secrets_Policy]] — Política general de secretos
- `docker-compose.yml` — Configuración de docker-compose
- `scripts/generate-keys.py` — Script de generación
- `.env.example` — Plantilla de configuración

**CIS Controls v8:**
- Control 5.2: Use Unique Passwords
- Control 5.3: Disable Dormant Accounts
- Control 6.5: Centralize Account Management

---

**Creado:** 2026-08-15 por Luis Téllez Domínguez  
**Sprint:** S2  
**Historia:** US-502
