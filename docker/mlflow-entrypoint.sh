#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# FARO — MLflow Entrypoint con Security Warnings
# ═══════════════════════════════════════════════════════════════════════

set -e

# Mostrar warning si está en modo desarrollo
if [ "${ENVIRONMENT:-local}" = "local" ]; then
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  MLFLOW — ADVERTENCIA DE SEGURIDAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Este servicio está corriendo en modo DESARROLLO

   Configuración actual:
   • Sin autenticación (acceso sin credenciales)
   • Sin cifrado TLS (tráfico HTTP en texto plano)
   • Puerto expuesto: 5001 (solo localhost)

   ⚠️  NO USAR EN PRODUCCIÓN

   Para producción, implementar:
   ✅ Autenticación básica (MLflow 2.9+)
   ✅ SSL/TLS con certificados válidos
   ✅ Rate limiting
   ✅ Network segmentation

   Ver: docker/README-SECURITY.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
fi

# Ejecutar comando original
exec "$@"
