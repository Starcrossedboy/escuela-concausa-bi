#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# FARO — ChromaDB Security Warning
# ═══════════════════════════════════════════════════════════════════════

# Mostrar warning si está en modo desarrollo
if [ "${ENVIRONMENT:-local}" = "local" ]; then
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CHROMADB — ADVERTENCIA DE SEGURIDAD CRÍTICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Este servicio está corriendo en modo DESARROLLO

   Configuración actual:
   • Sin autenticación (API completamente abierta)
   • Sin cifrado TLS (tráfico HTTP en texto plano)
   • Sin cifrado en reposo (datos en texto plano)
   • Puerto expuesto: 8001 (solo localhost)

   🚨 RIESGO CRÍTICO — NO USAR EN PRODUCCIÓN

   Para producción, implementar:
   ✅ Token authentication
   ✅ SSL/TLS con certificados válidos
   ✅ Cifrado de volumen (GCP CMEK)
   ✅ Network segmentation
   ✅ API Gateway con rate limiting

   Ver: docker/README-SECURITY.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
fi
