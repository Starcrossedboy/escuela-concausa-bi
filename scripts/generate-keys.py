#!/usr/bin/env python3
"""
FARO - Generador de claves seguras para docker-compose y el API

Alineado con CIS Controls v8 5.2 (Use Unique Passwords): usuarios y passwords
únicos por servicio, longitud >= 14 chars.

Características:
- Passwords de 20 caracteres (letras + números)
- Usuarios únicos por servicio
- Alta entropía (2^120 combinaciones)
- Sin símbolos especiales (evita problemas de escape en shells)
- Solo stdlib (secrets, base64, string): sin dependencia de `cryptography`,
  para que corra en cualquier host sin instalar paquetes.
"""
import base64
import secrets
import string

def generate_secure_password(length=20):
    """Genera password seguro con letras y números (sin símbolos)"""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_unique_username(service):
    """Genera username único por servicio"""
    suffix = secrets.token_hex(4)  # 8 caracteres hex
    return f"faro_{service}_admin_{suffix}"

print("=== GENERADOR DE CLAVES SEGURAS - FARO ===")
print("Alineado con CIS Controls v8 5.2 (Use Unique Passwords)\n")

# 1. Airflow Fernet Key (para cifrar conexiones en la DB)
# Una Fernet key es exactamente 32 bytes aleatorios en base64 url-safe; la
# generamos con stdlib para no depender del paquete `cryptography`.
fernet_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
print(f"AIRFLOW__CORE__FERNET_KEY={fernet_key}")

# 2. Airflow Webserver Secret (para sesiones web)
airflow_secret = secrets.token_urlsafe(32)
print(f"AIRFLOW__WEBSERVER__SECRET_KEY={airflow_secret}")

# 3. Superset Secret Key (para sesiones y CSRF)
superset_secret = secrets.token_urlsafe(32)
print(f"SUPERSET_SECRET_KEY={superset_secret}")

# 4. JWT Secret Key (para firmar los tokens OAuth2/JWT del API)
jwt_secret = secrets.token_urlsafe(48)
print(f"JWT_SECRET_KEY={jwt_secret}")

# 5. PostgreSQL password (20 caracteres)
postgres_password = generate_secure_password(20)
print(f"\nPOSTGRES_PASSWORD={postgres_password}")

# 6. Airflow Admin User (único)
airflow_user = "faro_airflow_admin"
airflow_password = generate_secure_password(20)
print(f"\n_AIRFLOW_WWW_USER_USERNAME={airflow_user}")
print(f"_AIRFLOW_WWW_USER_PASSWORD={airflow_password}")

# 7. Superset Admin User (único)
superset_user = "faro_superset_admin"
superset_password = generate_secure_password(20)
print(f"\nSUPERSET_ADMIN_USERNAME={superset_user}")
print(f"SUPERSET_ADMIN_PASSWORD={superset_password}")

print("\n" + "="*60)
print("✅ Claves generadas exitosamente")
print("🔐 Alineado con CIS Controls v8 5.2 (Use Unique Passwords)")
print("📋 Copiar estas líneas al archivo .env")
print("⚠️  NUNCA compartir estas credenciales")
print("🔄 Rotación recomendada: cada 90 días")
print("="*60)
