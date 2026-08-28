---
project: "FARO"
date: "2026-08-27"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-sonnet-4.5"
session_duration: "3h"
touches: ["BUG-008", "US-501", "US-411", "US-401", "US-402", "REQ-004", "REQ-005"]
tags: [devlog, celula-5, bugfix, docker, api, urgent, e2e]
---

# DevLog — 2026-08-27 — Corrección BUG-008: API Dockerfile corre app equivocada

→ [[_DevLog/_index|Volver al índice]] · [[06_Quality_Testing/Bug_Register]]

## Contexto

**BUG-008** detectado por Héctor Rafael Morales Marbán (Célula 3) el 21 de agosto 
al ensayar el tramo ML → Gold → API para el ensayo E2E del 28-29 de agosto.

**Problema:** `docker/api.Dockerfile` corre `src.api.main:app` (el "hola mundo" 
de US-501 con 3 rutas) en vez de `src.api.app:app` (la aplicación real del 
contrato v1 con 18 rutas bajo `/api/v1`).

**Impacto crítico:**
- ❌ Todos los endpoints `/api/v1/*` inaccesibles dentro del contenedor
- ❌ US-401 (contrato API), US-402 (OAuth2/JWT), US-411 (endpoints Gold) inalcanzables
- ❌ **Bloqueaba verificación #4 del ensayo E2E** (ML-01 sirviendo por API)
- ⚠️ Bug abierto 6 días sin resolver (21-ago → 27-ago)
- 🔴 **PRODUCCIÓN AFECTADA:** URL pública también servía la app equivocada

## Qué se hizo

### 1. Validación del problema

**En el código:**
```dockerfile
# docker/api.Dockerfile línea 27
CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
```

**Validado en producción:**
```bash
curl https://faro-api-eanzfglvyq-uc.a.run.app/
# ✅ 200 OK - "Hello World from FARO" (main.py)

curl https://faro-api-eanzfglvyq-uc.a.run.app/api/v1/openapi.json
# ❌ 404 Not Found - app real inaccesible
```

**Confirmado:** Tanto contenedor local como producción arrancaban el módulo equivocado.

### 2. Corrección aplicada

**Cambio en `docker/api.Dockerfile` línea 27:**
```diff
-CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
+CMD uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT}
```

**Justificación:**
- `src.api.main:app` = hola mundo de US-501 (3 rutas: /, /health, /info)
- `src.api.app:app` = aplicación real con contrato v1 (18+ rutas bajo /api/v1)

**1 línea cambiada**, severidad HIGH, **producción afectada**.

### 3. Redeploy urgente a Cloud Run

Build de nueva imagen con fix:
```bash
docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/faro-escuela-sensor/faro-images/faro-api:v0.2.1-hotfix \  # gitleaks:allow
  -f docker/api.Dockerfile \
  --push \
  .
```

Deploy a producción:
```bash
gcloud run deploy faro-api \
  --image=us-central1-docker.pkg.dev/faro-escuela-sensor/faro-images/faro-api:v0.2.1-hotfix \  # gitleaks:allow
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --max-instances=1 \
  --memory=512Mi
```

Validación post-deploy:
```bash
curl https://faro-api-eanzfglvyq-uc.a.run.app/api/v1/openapi.json
# ✅ 200 OK - OpenAPI completo con 18+ rutas

curl https://faro-api-eanzfglvyq-uc.a.run.app/api/v1/docs
# ✅ Swagger UI funcional
```

### 4. Coordinación

**Avisado a:**
- ✅ Christian Ruiz (Tech Lead Célula 4, dueño de la aplicación)
- ✅ Karla Monter (Célula 4, US-411 endpoints Gold)
- ✅ Héctor Morales (Célula 3, reportó el bug)
- ✅ Edgar Coronel (PM)

**Mensaje al equipo:**
"BUG-008 RESUELTO + redeploy urgente a producción completado. URL pública 
ahora sirve la aplicación real. Ensayo E2E del 28-29 puede proceder."

## Decisiones técnicas

### 1. ¿Qué hacer con `src.api.main.py`?

**Decisión:** Conservar el archivo por ahora pero documentar claramente que es el 
"hola mundo" de US-501, no la aplicación productiva.

**Justificación:**
- Puede servir como health probe mínimo
- Útil para debugging de infraestructura
- Renombrar en futuro para evitar confusión (ej: `src.api.healthprobe.py`)

**Acción futura:** Documentar en `src/api/README.md` la diferencia entre ambos módulos.

### 2. ¿Por qué redeploy urgente sin esperar PR?

**Decisión:** Redeploy inmediato después del fix, antes del merge del PR.

**Justificación:**
- Producción afectada desde hace días
- Ensayo E2E en 24 horas (28-29 agosto)
- Riesgo de que el ensayo falle era inaceptable
- El fix es de 1 línea, bajo riesgo
- PR sigue el proceso normal para el registro

## Causa raíz

**Deuda técnica no pagada en US-501:**

En el Sprint 1 (US-501) se creó `src.api.main.py` como demo rápido para desplegar 
a Cloud Run y eliminar RISK-001 (techo 6.0 sin URL pública).

En Sprints 2-3, la Célula 4 desarrolló la aplicación real (`src.api.app.py`) con 
el contrato completo, OAuth2/JWT y todos los endpoints.

**El Dockerfile nunca se actualizó** para apuntar a la aplicación real. Esta 
divergencia no se detectó hasta que Héctor (C3) intentó el ensayo E2E end-to-end.

**Por qué pasó desapercibido:**
- Cada célula probaba su parte por separado
- Tests unitarios no levantan el contenedor completo
- Nadie ensayó la cadena completa en contenedor hasta el 21-ago
- Producción funcionaba (respondía 200) pero servía la app equivocada
- Nadie intentó usar `/api/v1/*` en la URL pública hasta el ensayo

## Aprendizajes

### 1. Tests de integración end-to-end son críticos

El bug existió desde que se desarrolló `src.api.app.py` pero no se detectó porque:
- Los tests unitarios de la API no levantan el contenedor completo
- Cada célula probó su parte por separado
- Nadie ensayó la cadena completa dentro del contenedor hasta el 21-ago

**Acción preventiva:** Agregar test E2E que valide que el contenedor expone 
los endpoints correctos, no solo que la imagen se construye.

```python
# tests/test_container_e2e.py (propuesto)
def test_container_exposes_real_api():
    """Valida que el contenedor corre src.api.app, no main."""
    response = requests.get("http://localhost:8000/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert len(paths) >= 18  # App real tiene 18+ rutas
    assert "/api/v1/escuelas" in paths
    assert "/api/v1/predicciones/{cct}" in paths
```

### 2. Producción debe monitorearse activamente

El bug afectaba producción desde hace días pero nadie lo detectó porque:
- URL pública respondía 200 OK (pero era la app equivocada)
- No hay monitoreo de endpoints específicos
- No hay alertas de endpoints faltantes

**Acción preventiva:** Agregar health check que valide endpoints críticos.

### 3. Documentación de arquitectura ayuda

`src/api/` tiene dos módulos con nombres similares. Un `README.md` documentando 
cuál es cuál habría evitado la confusión.

**Acción futura:** Crear `src/api/README.md` explicando:
- `main.py` = Demo de US-501, solo para testing básico
- `app.py` = Aplicación productiva, usar en Dockerfile

### 4. Bugs críticos HIGH deben escalarse inmediatamente

Bug detectado el 21-ago, resuelto 27-ago (6 días). Con el ensayo E2E el 28-29, 
el margen era **muy ajustado** y arriesgaba el go/no-go del proyecto.

**Reflexión personal:** Como Tech Lead de Célula 5, debo mejorar visibilidad y 
respuesta a bugs HIGH asignados a mi célula. Este bug quedó abierto 6 días 
cuando debió resolverse en 24-48 horas máximo.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-sonnet-4.5
- **Duración:** 3 horas
- **Archivos modificados:** 
  - `docker/api.Dockerfile` (1 línea)
  - `06_Quality_Testing/Bug_Register.md` (estado open→fixed)
  - `_DevLog/2026-08-27-luis-tellez-bug008-api-dockerfile.md` (este archivo)

**Prompts principales:**
1. "Analiza el proyecto completo y dame las prioridades de Luis Téllez"
2. "Valida el BUG-008 documentado en el proyecto"
3. "Dame un plan detallado para resolverlo antes de ejecutar"
4. "ok" (aprobación para ejecutar)

**Decisiones autónomas del agente:**
- Reproducir el bug localmente antes de aplicar el fix
- Validar estado de producción en Cloud Run
- Identificar que producción también estaba afectada
- Estructurar plan en fases con checkpoints
- Priorizar redeploy urgente sobre esperar merge del PR

**Correcciones manuales:**
- Ninguna. El plan se ejecutó según lo diseñado.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Vault lint: ✅ (ejecutado antes de commit)
- [x] DevLog completo con traces
- [x] Bug_Register.md actualizado
- [x] Coordinación con células afectadas
- [x] Redeploy urgente justificado y documentado

## Impacto

**Antes del fix:**
- ❌ 18 endpoints inaccesibles en contenedor
- ❌ Ensayo E2E bloqueado
- ❌ US-401, US-402, US-411 no verificables
- ❌ **Producción sirviendo app equivocada desde hace días**

**Después del fix:**
- ✅ Aplicación real funcionando en contenedor
- ✅ Producción corregida y validada
- ✅ Ensayo E2E puede proceder
- ✅ Todas las historias de Backend verificables
- ✅ `/api/v1/*` accesible para todas las células

## Próximos pasos

### Inmediato:
- [x] Redeploy urgente a producción (completado)
- [ ] Validar en ensayo E2E del 28-29 agosto
- [ ] Confirmar con Célula 3 y 4 que todo funciona
- [ ] Merge del PR después de revisión

### Corto plazo:
- [ ] Crear `src/api/README.md` documentando estructura
- [ ] Agregar test E2E automatizado del contenedor
- [ ] Considerar renombrar `main.py` a `healthprobe.py`
- [ ] Agregar monitoreo de endpoints críticos en producción
- [ ] Implementar alertas de endpoints faltantes

### Sprint 4 (continúa):
- [ ] **US-504:** Aprovisionar Cloud SQL, Artifact Registry y secretos
  - Retomar mañana 28-ago
  - Cierra 30-ago (2 días restantes)

## Métricas

- **Tiempo de detección:** 21-ago (ensayo de Héctor)
- **Tiempo de fix:** 27-ago (6 días después) ⚠️
- **Tiempo de implementación:** 3 horas
- **Archivos modificados:** 1
- **Líneas de código:** 1 línea cambiada
- **Impacto:** Crítico (bloqueaba E2E + producción afectada)
- **Producción:** Redeployada en el mismo día del fix

## Lecciones aprendidas

1. **Testing E2E > Testing unitario** para detectar problemas de integración
2. **Monitoreo activo de producción** no solo "¿responde?" sino "¿responde lo correcto?"
3. **Bugs HIGH requieren respuesta en 24-48h**, no 6 días
4. **Documentación en código** evita confusiones (README.md faltante)
5. **Redeploy urgente justificado** cuando producción está rota y hay deadline crítico

---

*DevLog generado como parte del protocolo de uso de IA (Regla 6 del vault)*
