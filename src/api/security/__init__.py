"""Capa de seguridad de la API FARO (US-402 OAuth2/JWT · US-403 RBAC).

Módulos:
- `jwt`    — emisión/validación de access y refresh tokens propios.
- `google` — flujo OAuth2 con Google (URL de consentimiento + verificador desacoplado).
- `roles`  — política (provisional) de asignación de rol.
- `deps`   — dependencias FastAPI (`get_current_user`, proveedor del verificador).
"""
