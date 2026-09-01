"""Configuración tipada de la API FARO (US-402).

Lee variables de entorno (opcionalmente desde `.env`) con `pydantic-settings`. **Nunca** contiene
secretos reales: solo valores por defecto seguros para desarrollo local. En producción los valores
llegan por variables de entorno / Secret Manager (Célula 5); ver `07_Security/Secrets_Policy.md`.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Secreto por defecto SOLO para desarrollo/tests. En producción es obligatorio sobreescribirlo:
# la app se niega a arrancar en `production` con este valor (ver assert_production_ready()).
_DEV_SECRET_INSEGURO = "dev-insecure-secret-change-me-please-0000000000000000"


class Settings(BaseSettings):
    """Parámetros de la API. Los nombres mapean a variables de entorno en MAYÚSCULAS."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # el .env del proyecto tiene muchas otras vars (Airflow, Superset, etc.)
    )

    environment: str = "local"  # local | staging | production

    # ---- JWT propio (HS256 por ahora; RS256 en prod, ver ADR-004) ----
    jwt_secret_key: str = _DEV_SECRET_INSEGURO
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ---- OAuth2 con Google (credenciales las provee la Célula 5 / GCP; vacías en local) ----
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    google_authorization_endpoint: str = "https://accounts.google.com/o/oauth2/v2/auth"

    # ---- Política de rol (PROVISIONAL; la definitiva la decide Edgar/PO) ----
    # Allowlist de correos con rol `analista`. Mínimo privilegio: vacío => todos ciudadano.
    analista_emails: str = ""

    # ---- RBAC de lectura (US-403) ----
    # Interruptor híbrido: mientras el login Google no esté operativo (credenciales pendientes de
    # Célula 5), la LECTURA de datos (gold, predicciones, agente) queda pública para no bloquear la
    # URL viva de la demo. La escritura/admin SIEMPRE exige `analista`, sin importar este flag.
    # Cuando C5 entregue credenciales, se pone AUTH_LECTURA_PUBLICA=false y la lectura pasa a exigir
    # sesión `ciudadano` sin re-tocar código. Ver ADR-004 §RBAC.
    auth_lectura_publica: bool = True

    # ---- Postgres / Gold (US-411) ----
    # Nombres alineados a las vars POSTGRES_* que ya usan Airflow/MLflow/dbt en el .env
    # del equipo (ver .env.example) — una sola fuente de verdad para la conexión local.
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "escuela_concausa_db"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    # ---- Hardening HTTP (US-404) ----
    # CORS: orígenes permitidos (CSV). Default = frontends locales de desarrollo (React, Streamlit,
    # Superset). Los orígenes reales de despliegue los añade C5 por variable de entorno. Vacío =>
    # no se habilita CORS (la API solo responde a same-origin / clientes no-navegador).
    cors_origins: str = "http://localhost:3000,http://localhost:8501,http://localhost:8088"
    # Rate limiting (slowapi). Formato de la librería `limits`: "<n>/<periodo>", p.ej. "120/minute".
    # Se desactiva en pruebas que no lo ejercitan. Es por-proceso/en-memoria (1 instancia); para
    # prod multi-instancia se migra a un backend compartido (Redis) — follow-up documentado en ADR-004.
    rate_limit_enabled: bool = True
    rate_limit_default: str = "120/minute"

    # ---- Ejecutor SQL del agente: read-only sobre Gold (US-404 / BUG-025) ----
    # DSN de un rol PostgreSQL con SOLO SELECT sobre `gold.*` (lo provisiona C5 en Secret Manager
    # como DATABASE_URL_READ_ONLY). Vacío => el ejecutor NO se cablea y el agente degrada seguro.
    # Es una conexión distinta de la de lectura general (postgres_*): mínimo privilegio para el SQL
    # que genera el LLM. Ver `src/api/ejecutor_gold.py` y ADR-004 §Hardening.
    database_url_read_only: str = ""
    agente_sql_timeout_ms: int = 30000

    # ---- LLM del agente: text-to-SQL + redactor (BUG-025 / P-13) ----
    # Secreto (Anthropic) que gobierna el cableado del LLM en la app. Vacío => el LLM NO se cablea:
    # el agente usa los defaults seguros del seam (degrada "no configurado") y CI/local no llaman a
    # Anthropic. Lo provisiona C5 en Secret Manager como ANTHROPIC_API_KEY. El adaptador
    # (`src/agente/llm.py`) lee esta misma variable y la config no secreta (AGENTE_MODELO/
    # AGENTE_MAX_TOKENS/AGENTE_TIMEOUT_S) directamente del entorno. Ver `07_Security/Secrets_Policy.md`.
    anthropic_api_key: str = ""

    # ---- Inferencia ML: cache y timeouts (US-416) ----
    # `/predicciones/*` ya no invoca MLflow en vivo (US-412): lee `gold.predicciones` precalculada.
    # Un timeout aquí es "Postgres no respondió a tiempo", no "MLflow tardó". Ver
    # `src/api/repositorio_modelos.py` y `src/api/cache_predicciones.py`.
    predicciones_timeout_ms: int = 3000
    predicciones_cache_ttl_segundos: int = 30
    predicciones_cache_max_entradas: int = 512

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def analista_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.analista_emails.split(",") if e.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        """Orígenes CORS permitidos, parseados del CSV (sin vacíos)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def secret_es_inseguro(self) -> bool:
        """True si el secreto es el de desarrollo o es demasiado corto para HS256."""
        return self.jwt_secret_key == _DEV_SECRET_INSEGURO or len(self.jwt_secret_key) < 32

    def assert_production_ready(self) -> None:
        """Falla rápido si se intenta correr en producción con un secreto inseguro.

        Evita el error clásico de desplegar con la clave de ejemplo. Se invoca al arrancar la app
        cuando `ENVIRONMENT=production`.
        """
        if self.environment.lower() == "production" and self.secret_es_inseguro:
            raise RuntimeError(
                "JWT_SECRET_KEY inseguro en producción: define una clave propia de ≥32 caracteres "
                "(genera una con scripts/generate-keys.py)."
            )


@lru_cache
def get_settings() -> Settings:
    """Settings cacheados (una sola lectura del entorno por proceso)."""
    return Settings()
