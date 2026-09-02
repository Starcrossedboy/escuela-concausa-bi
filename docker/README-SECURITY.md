---
id: DOCKER-SECURITY-WARNINGS
title: "Advertencias de Seguridad — Docker Services"
owner: "Luis Téllez Domínguez"
status: active
version: "1.0"
traces_up: ["US-502", "SEC-THREAT-MODEL"]
tags: [docker, security, warnings, development]
---

# ⚠️ ADVERTENCIAS DE SEGURIDAD — Desarrollo Local

> **IMPORTANTE:** Esta configuración está diseñada EXCLUSIVAMENTE para desarrollo local.
> **NO es segura para ambientes de staging o producción.**
> → Documentación completa: [[vault/07_Security/Threat_Model]]

---

## 🚨 Servicios SIN Autenticación

### MLflow (puerto 5001)
- ❌ **Sin autenticación** — Cualquiera con acceso a la red puede:
  - Ver/modificar/eliminar experimentos
  - Acceder a artifacts de modelos
  - Obtener métricas y parámetros
- ⚠️ **Acción requerida para producción:** Implementar MLflow auth (Sprint 3)

### ChromaDB (puerto 8001)
- ❌ **Sin autenticación** — Cualquiera con acceso a la red puede:
  - Leer/escribir/eliminar colecciones de embeddings
  - Extraer datos del vector store
  - Modificar configuración
- ⚠️ **Acción requerida para producción:** Implementar token auth (Sprint 3)

---

## 🔒 Servicios CON Autenticación

### Superset (puerto 8088)
- ✅ Requiere login con credenciales
- ⚠️ Tráfico HTTP sin cifrar (sin SSL/TLS)
- ⚠️ Sin rate limiting (vulnerable a brute force)

### Airflow (puerto 8080)
- ✅ Requiere login con credenciales
- ⚠️ Tráfico HTTP sin cifrar (sin SSL/TLS)

### FastAPI (puerto 8000)
- ⚠️ Sin autenticación en endpoints públicos
- ✅ OAuth2/JWT implementado (pero no obligatorio en dev)

---

## 🌐 Configuración de Red

### Actual (Desarrollo Local)
```
Todos los puertos vinculados a 0.0.0.0 (todas las interfaces)
→ Accesibles desde cualquier máquina en la red local
```

### Recomendado (desde este commit)
```
Todos los puertos vinculados a 127.0.0.1 (localhost)
→ Solo accesibles desde la máquina host
```

**Cómo aplicarlo:**
```bash
# Editar docker-compose.yml
ports:
  - "127.0.0.1:5001:5000"  # Solo localhost
```

---

## 📋 Mitigaciones por Nivel

| Nivel | Ambiente | Score CIS | Mitigaciones |
|-------|----------|-----------|--------------|
| **Nivel 1** | Desarrollo Local | 7.0/10 | · Bind a localhost<br>· Documentación de riesgos<br>· Warnings al arrancar |
| **Nivel 2** | Staging | 8.5/10 | · Auth en MLflow/ChromaDB<br>· Nginx reverse proxy<br>· SSL/TLS<br>· Rate limiting<br>· Network segmentation |
| **Nivel 3** | Producción (GCP) | 9.5/10 | · GCP Secret Manager<br>· Cloud SQL cifrado<br>· Cloud Armor WAF<br>· Identity-Aware Proxy<br>· Security Command Center |

---

## 🔐 Credenciales en Desarrollo

### ⚠️ Riesgos Conocidos
- Passwords en archivo `.env` (texto plano)
- Accesibles mediante `docker inspect`
- Secret keys estáticas (sin rotación)

### ✅ Aceptable SOLO para desarrollo porque:
1. Datos NO sensibles (fixtures, datos de prueba)
2. No expuesto a Internet
3. Cada desarrollador tiene sus propias credenciales
4. Documentado en `vault/07_Security/Credentials_Policy.md`

### 🏢 En Producción (Sprint 4):
- ✅ GCP Secret Manager para todas las credenciales
- ✅ Rotación automática cada 90 días
- ✅ Auditoría de accesos (Cloud Audit Logs)

---

## 📚 Referencias

- **Política de credenciales:** `vault/07_Security/Credentials_Policy.md`
- **Threat model completo:** `SECURITY.md`
- **Plan de hardening:** `vault/08_CICD_DevOps/Security_Hardening.md` (Sprint 3)

---

**Última actualización:** 2026-08-16  
**Owner:** Luis Téllez Domínguez (Célula 5 - Cloud & DevOps)  
**Revisado por:** Pendiente (Christian Ruiz - Célula 4 - Security)
