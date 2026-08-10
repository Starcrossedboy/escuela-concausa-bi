#!/bin/bash
# FARO - Deploy to Cloud Run
set -euo pipefail

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
PROJECT_ID=$(gcloud config get-value project 2>/dev/null) || {
  echo "❌ Error: No se pudo obtener PROJECT_ID"
  exit 1
}

REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-faro-api}"
IMAGE_NAME="${IMAGE_NAME:-faro-api}"
IMAGE_TAG="${1:-latest}"

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/faro-images/${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${BLUE}🚀 Desplegando FARO API a Cloud Run...${NC}"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${SERVICE_NAME}"
echo "   Image: ${IMAGE_URL}"
echo ""

gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_URL} \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300s \
  --set-env-vars="ENVIRONMENT=production"

echo ""
echo -e "${GREEN}✅ Deploy completado${NC}"
echo ""
echo -e "${GREEN}🌐 URL del servicio:${NC}"
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)'
