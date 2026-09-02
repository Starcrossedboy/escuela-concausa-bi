---
id: SEC-POLICY
title: "Secrets Policy"
owner: "Luis Téllez Domínguez"
status: approved
version: "1.0"
source_of_truth: true
traces_up: ["vault/07_Security/Security_Model"]
traces_down: ["vault/08_CICD_DevOps/Environments", "vault/05_Engineering/Environment_Setup"]
last_reviewed: "2026-08-03"
tags: [security, secrets, policy]
---

# Secrets Policy — Manejo de credenciales y secretos

> Documento canónico sobre secretos. Resuelve los enlaces desde
> [[vault/08_CICD_DevOps/Environments]], [[vault/07_Security/_index]], [[vault/05_Engineering/Environment_Setup]]
> y [[vault/11_Operations/Runbooks]].
> → [[vault/07_Security/_index|Volver a Security]]

## Regla absoluta

**Ningún secreto se sube al repositorio. Nunca. Bajo ninguna circunstancia.**

Esto incluye: credenciales de GCP, llaves de API, contraseñas de base de datos, tokens de OAuth,
client secrets de Google, cadenas de conexión con password, y el archivo `.env` completo.

## Qué se considera secreto

| Tipo | Ejemplo | Dónde vive |
|---|---|---|
| Credenciales de GCP | Service account JSON | Secret Manager / local fuera del repo |
| Contraseña de Postgres | `POSTGRES_PASSWORD` | `.env` local · Secret Manager en prod |
| OAuth de Google | `GOOGLE_CLIENT_SECRET` | `.env` local · Secret Manager en prod |
| Firma de JWT | `JWT_SECRET_KEY` | Generada por ambiente, nunca compartida |
| Tokens de API de datos | Si alguna fuente lo requiere | `.env` local |

> Las 8 fuentes de datos del proyecto son **públicas y abiertas**, por lo que en general no requieren
> llaves. Si alguna llegara a requerirla, aplica esta política sin excepción.

## Cómo se manejan

### Local (desarrollo)
1. Cada integrante copia la plantilla: `cp .env.example .env`
2. Llena sus valores en `.env`
3. `.env` está en `.gitignore` — **verifica antes de cada commit** que no aparezca en `git status`

### Producción (GCP)
- Los secretos viven en **Google Secret Manager**.
- Cloud Run los inyecta como variables de entorno en tiempo de ejecución.
- **Nunca** se escriben en el `Dockerfile` ni en el `docker-compose.yml` versionado.

### En CI (GitHub Actions)
- Se usan **GitHub Secrets** del repositorio.
- Se referencian como `${{ secrets.NOMBRE }}`.
- Nunca se imprimen en logs.

## Reglas para el trabajo con IA

- **Prohibido pegar el contenido de `.env`, credenciales o datos reales en un prompt** de Claude Code,
  Copilot o cualquier LLM.
- Si necesitas que la IA te ayude con configuración, usa valores de ejemplo (`XXXXX`, `tu-proyecto-id`).
- Si accidentalmente expusiste un secreto en un prompt, **rótalo de inmediato** y regístralo como `SEC-###`
  en [[vault/07_Security/Security_Audit_Log]].

## Si un secreto se filtra al repositorio

Borrar el archivo **no basta**: queda en el historial de git.

1. **Rota el secreto inmediatamente** (invalida el viejo, genera uno nuevo).
2. Avisa al Tech Lead de Cloud/DevOps y al PO.
3. Registra el incidente como `SEC-###` en [[vault/07_Security/Security_Audit_Log]].
4. Limpia el historial con `git filter-repo` o BFG (solo el Tech Lead de Cloud).
5. Documenta la causa raíz en [[vault/10_Risk_Governance/Incident_Log]].

## Verificación antes de cada PR

- [ ] `git status` no muestra `.env` ni archivos de credenciales
- [ ] No hay cadenas que parezcan llaves o contraseñas en el diff
- [ ] Los valores sensibles se leen de variables de entorno, no están hardcodeados
- [ ] `.gitignore` cubre cualquier archivo nuevo de configuración sensible
