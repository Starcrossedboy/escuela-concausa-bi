#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# FARO — Script de Verificación de Servicios
# ═══════════════════════════════════════════════════════════════════════
# Verifica que todos los servicios estén respondiendo correctamente
#
# Uso: ./scripts/verificar-servicios.sh

# Ubicarse en la raíz del repo para que `docker compose` resuelva el proyecto
# correcto (los contenedores se nombran <proyecto>-<servicio>-<N>).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || { echo "No se pudo ubicar la raíz del repo"; exit 1; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 VERIFICACIÓN DE SERVICIOS FARO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar un servicio
verificar_servicio() {
    local nombre=$1
    local url=$2
    local descripcion=$3

    printf "%-30s " "$nombre"

    if curl -s -f -o /dev/null --max-time 5 "$url"; then
        echo -e "${GREEN}✅ OK${NC} - $url"
        echo "   └─ $descripcion"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} - $url"
        echo "   └─ $descripcion"
        return 1
    fi
}

echo "📊 Verificando servicios web..."
echo ""

# PostgreSQL (no HTTP, solo Docker)
printf "%-30s " "PostgreSQL"
if docker compose exec -T db pg_isready -U postgres &>/dev/null; then
    echo -e "${GREEN}✅ OK${NC} - localhost:5432"
    echo "   └─ Base de datos principal (4 DBs)"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# MLflow
verificar_servicio "MLflow" "http://localhost:5001/health" "Tracking de modelos ML"

# Airflow
verificar_servicio "Airflow Webserver" "http://localhost:8080/health" "Orquestación de DAGs"

# Superset
verificar_servicio "Superset" "http://localhost:8088/health" "Dashboards de BI"

# FastAPI
verificar_servicio "FastAPI" "http://localhost:8000/health" "API REST"

# ChromaDB
verificar_servicio "ChromaDB" "http://localhost:8001/api/v1/heartbeat" "Vector DB para RAG"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 URLs para explorar en el navegador:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  MLflow UI:     http://localhost:5001"
echo "  Airflow UI:    http://localhost:8080"
echo "  Superset UI:   http://localhost:8088"
echo "  API Docs:      http://localhost:8000/docs"
echo ""
echo "  Credenciales en: .env"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
