# FARO Web (frontend Streamlit)

Capa web integrada del proyecto. Diseño: `vault/03_Architecture/Frontend_Architecture.md` · Decisión:
`vault/03_Architecture/ADRs/ADR-002-frontend-streamlit.md`.

## Estructura (andamiaje)
- `app.py` — entrada, router y sesión.
- `auth.py` — login/logout con el OAuth2/JWT de la API y `require_role()`. **Implementado (US-405)**: el login sale a `/auth/login` de la API y vuelve con un código de un solo uso que se canjea en `/auth/exchange`; los tokens nunca viajan por la URL. Ver [[vault/03_Architecture/ADRs/ADR-010-puente-oauth-frontend|ADR-010]].
- `pages/` — Dashboards (Superset embebido), Panel de ML, Chat del agente.

## Correr en local (cuando esté implementado)
```bash
pip install -r requirements/celula-2.txt   # incluye streamlit
streamlit run src/frontend/app.py
```

## Variables de entorno

| Variable | Default | Para qué |
|---|---|---|
| `FARO_API_BASE_URL` | `http://localhost:8000` | La API de FARO |
| `FARO_FRONTEND_URL` | `http://localhost:8501` | A dónde vuelve la API tras el login. **Debe estar en la allowlist `FRONTEND_REDIRECT_URIS` de la API**, o `/auth/login` responde 400 |
| `SUPERSET_URL`, `SUPERSET_ADMIN_USERNAME`, `SUPERSET_ADMIN_PASSWORD` | ver `superset_client.py` | Embebido de dashboards (US-206) |

> Estado: US-206 (dashboards) y US-405 (auth) implementadas. Quedan US-207 (panel de ML, C2) y el cierre e2e de US-305 (chat, C3).
