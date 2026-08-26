#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# FARO — Script de Inicialización de Superset
# ═══════════════════════════════════════════════════════════════════════
# Ejecuta las migraciones de base de datos, crea el usuario admin
# (si no existe) e inicia el servidor de Superset.
#
# Creado: 2026-08-15
# Owner: Luis Téllez Domínguez (Célula 5)
# Historia: US-502
# ═══════════════════════════════════════════════════════════════════════

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 FARO — Inicializando Superset"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Mostrar warning si está en modo desarrollo
if [ "${ENVIRONMENT:-local}" = "local" ]; then
    cat << 'EOF'

⚠️  ADVERTENCIA DE SEGURIDAD — Modo DESARROLLO

   Configuración actual:
   • Autenticación: ✅ Sí (login requerido)
   • Cifrado TLS: ❌ No (tráfico HTTP en texto plano)
   • Rate limiting: ❌ No (vulnerable a brute force)
   • SECRET_KEY: Estático (sin rotación)

   ⚠️  NO USAR EN PRODUCCIÓN

   Para producción:
   ✅ SSL/TLS con certificados válidos
   ✅ Rate limiting en login
   ✅ Rotación automática de SECRET_KEY
   ✅ WAF (Cloud Armor en GCP)

   Ver: docker/README-SECURITY.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
fi

# ═══════════════════════════════════════════════════════════════════════
# 1. MIGRAR BASE DE DATOS
# ═══════════════════════════════════════════════════════════════════════
echo "📦 Ejecutando migraciones de base de datos..."
superset db upgrade
echo "✅ Migraciones completadas"

# ═══════════════════════════════════════════════════════════════════════
# 2. CREAR USUARIO ADMIN (si no existe)
# ═══════════════════════════════════════════════════════════════════════
echo "👤 Verificando usuario admin..."

# Intentar crear el admin (falla silenciosamente si ya existe)
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME}" \
  --firstname FARO \
  --lastname Admin \
  --email "${SUPERSET_ADMIN_EMAIL}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" 2>&1 | grep -v "already exists" || true

echo "✅ Usuario admin configurado"

# ═══════════════════════════════════════════════════════════════════════
# 3. INICIALIZAR SUPERSET (roles, permisos)
# ═══════════════════════════════════════════════════════════════════════
echo "🔐 Inicializando roles y permisos..."
superset init
echo "✅ Superset inicializado"

# ═══════════════════════════════════════════════════════════════════════
# 4. ARRANCAR SERVIDOR
# ═══════════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Superset listo — escuchando en puerto 8088"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exec superset run -h 0.0.0.0 -p 8088 --with-threads --reload
