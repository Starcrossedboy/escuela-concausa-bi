#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# FARO — Script de Verificación de Docker Compose
# ═══════════════════════════════════════════════════════════════════════
# Verifica que todos los servicios estén funcionando correctamente
#
# Uso:
#   ./scripts/verify-docker-compose.sh
#
# Creado: 2026-08-15
# Owner: Luis Téllez Domínguez (Célula 5)
# Historia: US-502
# ═══════════════════════════════════════════════════════════════════════

set -e  # Detener si algún comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 FARO — Verificación de Docker Compose"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ALL_OK=true

# ═══════════════════════════════════════════════════════════════════════
# FUNCIÓN: Verificar servicio HTTP
# ═══════════════════════════════════════════════════════════════════════
check_http() {
    local name=$1
    local url=$2
    local timeout=${3:-5}

    if curl -sf --max-time "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC} — OK"
        return 0
    else
        echo -e "${RED}❌ $name${NC} — FAIL (no responde en $url)"
        ALL_OK=false
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════
# FUNCIÓN: Verificar puerto TCP
# ═══════════════════════════════════════════════════════════════════════
check_port() {
    local name=$1
    local port=$2

    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✅ $name${NC} — OK (puerto $port abierto)"
        return 0
    else
        echo -e "${RED}❌ $name${NC} — FAIL (puerto $port cerrado)"
        ALL_OK=false
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════
# FUNCIÓN: Verificar contenedor Docker
# ═══════════════════════════════════════════════════════════════════════
check_container() {
    local name=$1

    if docker ps --format '{{.Names}}' | grep -q "^$name$"; then
        local status=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null || echo "no-healthcheck")

        if [ "$status" = "healthy" ]; then
            echo -e "${GREEN}✅ $name${NC} — healthy"
            return 0
        elif [ "$status" = "no-healthcheck" ]; then
            echo -e "${YELLOW}⚠️  $name${NC} — running (no healthcheck)"
            return 0
        else
            echo -e "${RED}❌ $name${NC} — unhealthy (status: $status)"
            ALL_OK=false
            return 1
        fi
    else
        echo -e "${RED}❌ $name${NC} — not running"
        ALL_OK=false
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════
# 1. VERIFICAR CONTENEDORES
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BLUE}📦 Verificando contenedores...${NC}"
echo ""

check_container "faro-postgres"
check_container "faro-api"
check_container "faro-airflow-webserver"
check_container "faro-airflow-scheduler"

# Verificar que airflow-init terminó correctamente
if docker ps -a --format '{{.Names}}\t{{.Status}}' | grep "faro-airflow-init" | grep -q "Exited (0)"; then
    echo -e "${GREEN}✅ faro-airflow-init${NC} — exited successfully"
else
    echo -e "${RED}❌ faro-airflow-init${NC} — did not exit cleanly"
    ALL_OK=false
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# 2. VERIFICAR CONECTIVIDAD HTTP
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BLUE}🌐 Verificando endpoints HTTP...${NC}"
echo ""

check_http "Postgres (TCP)" "localhost" 5432 || check_port "Postgres" 5432
check_http "API FastAPI" "http://localhost:8000/health" 5
check_http "Airflow Webserver" "http://localhost:8080/health" 10

echo ""

# ═══════════════════════════════════════════════════════════════════════
# 3. VERIFICAR BASES DE DATOS
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BLUE}🗄️  Verificando bases de datos...${NC}"
echo ""

DATABASES=("escuela_concausa_db" "airflow" "mlflow" "superset")

for db in "${DATABASES[@]}"; do
    if docker exec faro-postgres psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db"; then
        echo -e "${GREEN}✅ Base de datos: $db${NC} — existe"
    else
        echo -e "${RED}❌ Base de datos: $db${NC} — NO existe"
        ALL_OK=false
    fi
done

echo ""

# ═══════════════════════════════════════════════════════════════════════
# 4. VERIFICAR LOGS (solo errores críticos)
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BLUE}📋 Buscando errores críticos en logs...${NC}"
echo ""

CRITICAL_ERRORS=$(docker compose logs --since 5m 2>&1 | grep -iE "fatal|critical|error.*failed" | wc -l)

if [ "$CRITICAL_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ Sin errores críticos en los últimos 5 minutos${NC}"
else
    echo -e "${YELLOW}⚠️  Se encontraron $CRITICAL_ERRORS errores en logs (revisar con: docker compose logs)${NC}"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}🎉 TODOS LOS SERVICIOS ESTÁN FUNCIONANDO CORRECTAMENTE${NC}"
    echo ""
    echo "📍 Accede a los servicios:"
    echo "   • Airflow UI:  http://localhost:8080"
    echo "     Usuario:     faro_airflow_admin"
    echo "     Password:    (ver archivo .env)"
    echo ""
    echo "   • API FastAPI: http://localhost:8000/docs"
    echo "   • Postgres:    localhost:5432"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  ALGUNOS SERVICIOS TIENEN PROBLEMAS${NC}"
    echo ""
    echo "🔧 Comandos útiles para debuggear:"
    echo "   docker compose ps                    # Ver estado de todos los servicios"
    echo "   docker compose logs <servicio>       # Ver logs de un servicio"
    echo "   docker compose logs -f               # Ver logs en tiempo real"
    echo "   docker compose restart <servicio>    # Reiniciar un servicio"
    echo ""
    exit 1
fi
