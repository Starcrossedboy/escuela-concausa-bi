"""Política de asignación de rol (US-402/US-403).

⚠️ **PROVISIONAL.** La política definitiva (quién es `analista` vs `ciudadano`) es una decisión de
producto de **Edgar/PO**, aún no documentada. Mientras tanto se aplica **mínimo privilegio**:

- Por defecto **todos** son `ciudadano`.
- Solo son `analista` los correos incluidos explícitamente en la allowlist `ANALISTA_EMAILS`
  (variable de entorno, vacía por defecto).

Así, en ausencia de decisión, nadie obtiene privilegios elevados por accidente.
"""
from __future__ import annotations

from src.api.config import get_settings
from src.api.schemas import Rol


def resolve_role(email: str) -> Rol:
    """Devuelve el rol para un correo según la política provisional de mínimo privilegio."""
    if email.strip().lower() in get_settings().analista_email_set:
        return Rol.analista
    return Rol.ciudadano
