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

# NOTA: sin `set -e` a propósito — este script corre TODAS las verificaciones y
# resume al final con exit 0/1 (ALL_OK). Con `set -e` abortaría al primer
# servicio caído y no veríamos el panorama completo.

# Ubicarse en la raíz del repo (donde vive docker-compose.yml) para que
# `docker compose` resuelva el proyecto correcto sin importar el CWD desde el
# que se invoque el script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || { echo "No se pudo ubicar la raíz del repo"; exit 1; }

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
# FUNCIÓN: Verificar contenedor Docker (por NOMBRE DE SERVICIO de Compose)
# ═══════════════════════════════════════════════════════════════════════
# Resuelve el contenedor vía `docker compose ps` en lugar de un nombre fijo,
# de modo que funciona con el nombre real `<proyecto>-<servicio>-<N>` que
# Compose asigna (los `container_name` fijos se eliminaron; ver docker-compose.yml).
check_container() {
    local service=$1
    local cid
    cid=$(docker compose ps -q "$service" 2>/dev/null | head -n1)

    # ¿Existe y está corriendo?
    if [ -z "$cid" ] || ! docker ps -q --no-trunc | grep -q "^$cid"; then
        echo -e "${RED}❌ $service${NC} — not running"
        ALL_OK=false
        return 1
    fi

    local status
    status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$cid" 2>/dev/null)

    if [ "$status" = "healthy" ]; then
        echo -e "${GREEN}✅ $service${NC} — healthy"
        return 0
    elif [ "$status" = "no-healthcheck" ] || [ -z "$status" ]; then
        echo -e "${YELLOW}⚠️  $service${NC} — running (no healthcheck)"
        return 0
    else
        echo -e "${RED}❌ $service${NC} — unhealthy (status: $status)"
        ALL_OK=false
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════
# 1. VERIFICAR CONTENEDORES
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BLUE}📦 Verificando contenedores...${NC}"
echo ""

check_container "db"
check_container "api"
check_container "airflow-webserver"
check_container "airflow-scheduler"
check_container "mlflow"
check_container "superset"
check_container "chromadb"

# Verificar que airflow-init terminó correctamente (salió con código 0)
INIT_CID=$(docker compose ps -aq airflow-init 2>/dev/null | head -n1)
if [ -n "$INIT_CID" ] && docker inspect --format='{{.State.Status}} {{.State.ExitCode}}' "$INIT_CID" 2>/dev/null | grep -q "^exited 0$"; then
    echo -e "${GREEN}✅ airflow-init${NC} — exited successfully"
else
    echo -e "${RED}❌ airflow-init${NC} — did not exit cleanly"
    ALL_OK=false
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# 2. VERIFICAR CONECTIVIDAD HTTP
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BLUE}🌐 Verificando endpoints HTTP...${NC}"
echo ""

# Postgres no habla HTTP: se verifica solo el puerto TCP (evita un ❌ espurio que
# antes envenenaba ALL_OK al llamar check_http contra un puerto no-HTTP).
check_port "Postgres" 5432
# La ruta de salud del API es /api/v1/health (200); /health devuelve 404.
check_http "API FastAPI" "http://localhost:8000/api/v1/health" 5
check_http "Airflow Webserver" "http://localhost:8080/health" 10
check_http "MLflow" "http://localhost:5001/health" 10
check_http "Superset" "http://localhost:8088/health" 15
check_http "ChromaDB" "http://localhost:8001/api/v2/heartbeat" 5

echo ""

# ═══════════════════════════════════════════════════════════════════════
# 3. VERIFICAR BASES DE DATOS
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BLUE}🗄️  Verificando bases de datos...${NC}"
echo ""

DATABASES=("escuela_concausa_db" "airflow" "mlflow" "superset")

for db in "${DATABASES[@]}"; do
    if docker compose exec -T db psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db"; then
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
    echo "   • Airflow UI:   http://localhost:8080"
    echo "     Usuario:      faro_airflow_admin"
    echo "     Password:     (ver .env: _AIRFLOW_WWW_USER_PASSWORD)"
    echo ""
    echo "   • Superset UI:  http://localhost:8088"
    echo "     Usuario:      faro_superset_admin"
    echo "     Password:     (ver .env: SUPERSET_ADMIN_PASSWORD)"
    echo ""
    echo "   • MLflow UI:    http://localhost:5001"
    echo "   • API FastAPI:  http://localhost:8000/docs"
    echo "   • ChromaDB API: http://localhost:8001/api/v1/heartbeat"
    echo "   • Postgres:     localhost:5432"
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
