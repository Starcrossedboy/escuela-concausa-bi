#!/usr/bin/env bash
# FARO — Provisionamiento GCP Fase 1 (US-504)
# ---------------------------------------------------------------------------
# Aprovisiona la BASE segura del entorno GCP para servir datos/ML sin exponer
# la base de datos a Internet:
#   1. Habilita las APIs necesarias.
#   2. Red privada: VPC + subnet + Private Services Access (peering) + Serverless
#      VPC Access connector (para que Cloud Run llegue a la DB por IP privada).
#   3. Cloud SQL PostgreSQL con IP privada (SIN IP pública), backups + PITR.
#   4. Secret Manager: JWT, Fernet y password de DB (generados aquí, NUNCA impresos).
#   5. Service account de mínimo privilegio para el API (Cloud Run).
#   6. Audit logs (Data Access) para Cloud SQL y Secret Manager.
#
# IDEMPOTENTE: cada recurso se crea sólo si no existe. Re-ejecutarlo sobre un
# proyecto ya aprovisionado no altera secretos ni la contraseña de la DB.
#
# NO crea: Load Balancer / Cloud Armor (Fase 4), VM Airflow + IAP (Fase 3),
# ni redepliega el API con conexión a la DB (Fase 2). Artifact Registry
# (faro-images) ya existía y no se toca aquí.
#
# Requisitos: gcloud autenticado; billing habilitado; permisos de Owner/Editor.
# Uso:   ./provision-gcp-fase1.sh
# Config por variables de entorno (con defaults):
#   PROJECT_ID  REGION  DB_TIER  DB_VERSION
# ---------------------------------------------------------------------------
set -euo pipefail

# ── Colores ────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[0;33m'; NC='\033[0m'
info()  { echo -e "${BLUE}▶ $*${NC}"; }
ok()    { echo -e "${GREEN}✔ $*${NC}"; }
skip()  { echo -e "${YELLOW}↷ $* (ya existe, se omite)${NC}"; }

# ── Configuración ────────────────────────────────────────────────────────────
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
DB_VERSION="${DB_VERSION:-POSTGRES_16}"
DB_TIER="${DB_TIER:-db-custom-1-3840}"   # Enterprise, 1 vCPU / 3.75 GB (~$50/mo)

VPC="faro-vpc"
SUBNET="faro-subnet"
SUBNET_RANGE="10.10.0.0/24"
PSA_RANGE_NAME="google-managed-services-faro-vpc"   # rango /16 para peering de Cloud SQL
CONNECTOR="faro-connector"
CONNECTOR_RANGE="10.8.0.0/28"                        # /28 sin traslape con subnet ni PSA
SQL_INSTANCE="faro-postgres"
DB_NAME="faro"
DB_USER="faro_app"
SA_NAME="faro-api-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "❌ No hay PROJECT_ID. Ejecuta: gcloud config set project <id>"; exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo " FARO — Provisionamiento GCP Fase 1 (US-504)"
echo "   Proyecto : ${PROJECT_ID}"
echo "   Región   : ${REGION}"
echo "   Cloud SQL: ${SQL_INSTANCE} (${DB_VERSION}, ${DB_TIER}, IP privada)"
echo "════════════════════════════════════════════════════════════════"

# ── Paso 1 · Habilitar APIs ──────────────────────────────────────────────────
info "1) Habilitando APIs necesarias"
gcloud services enable \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  sqladmin.googleapis.com \
  vpcaccess.googleapis.com \
  secretmanager.googleapis.com \
  --project="${PROJECT_ID}" --quiet
ok "APIs habilitadas"

# ── Paso 2 · Red privada (VPC + subnet + PSA + peering) ──────────────────────
info "2) Red privada"
if gcloud compute networks describe "${VPC}" --project="${PROJECT_ID}" &>/dev/null; then
  skip "VPC ${VPC}"
else
  gcloud compute networks create "${VPC}" --subnet-mode=custom --project="${PROJECT_ID}"
  ok "VPC ${VPC} creada"
fi

if gcloud compute networks subnets describe "${SUBNET}" --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  skip "Subnet ${SUBNET}"
else
  gcloud compute networks subnets create "${SUBNET}" \
    --network="${VPC}" --region="${REGION}" --range="${SUBNET_RANGE}" --project="${PROJECT_ID}"
  ok "Subnet ${SUBNET} (${SUBNET_RANGE})"
fi

if gcloud compute addresses describe "${PSA_RANGE_NAME}" --global --project="${PROJECT_ID}" &>/dev/null; then
  skip "Rango PSA ${PSA_RANGE_NAME}"
else
  gcloud compute addresses create "${PSA_RANGE_NAME}" \
    --global --purpose=VPC_PEERING --prefix-length=16 \
    --network="${VPC}" --project="${PROJECT_ID}"
  ok "Rango PSA ${PSA_RANGE_NAME} reservado"
fi

if gcloud services vpc-peerings list --network="${VPC}" --project="${PROJECT_ID}" \
     --format="value(peering)" 2>/dev/null | grep -q .; then
  skip "Peering servicenetworking"
else
  gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges="${PSA_RANGE_NAME}" \
    --network="${VPC}" --project="${PROJECT_ID}"
  ok "Peering privado a servicenetworking"
fi

# ── Paso 3 · Serverless VPC Access connector ─────────────────────────────────
info "3) Serverless VPC Access connector"
if gcloud compute networks vpc-access connectors describe "${CONNECTOR}" \
     --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  skip "Connector ${CONNECTOR}"
else
  gcloud compute networks vpc-access connectors create "${CONNECTOR}" \
    --region="${REGION}" --network="${VPC}" --range="${CONNECTOR_RANGE}" \
    --min-instances=2 --max-instances=3 --machine-type=e2-micro \
    --project="${PROJECT_ID}"
  ok "Connector ${CONNECTOR} (${CONNECTOR_RANGE})"
fi

# ── Paso 4 · Cloud SQL PostgreSQL (IP privada) ───────────────────────────────
info "4) Cloud SQL PostgreSQL (IP privada, backups + PITR)"
if gcloud sql instances describe "${SQL_INSTANCE}" --project="${PROJECT_ID}" &>/dev/null; then
  skip "Instancia ${SQL_INSTANCE}"
else
  gcloud sql instances create "${SQL_INSTANCE}" \
    --edition=ENTERPRISE \
    --database-version="${DB_VERSION}" \
    --tier="${DB_TIER}" \
    --region="${REGION}" \
    --availability-type=zonal \
    --no-assign-ip \
    --network="projects/${PROJECT_ID}/global/networks/${VPC}" \
    --storage-type=SSD --storage-size=10GB --storage-auto-increase \
    --backup --backup-start-time=07:00 \
    --enable-point-in-time-recovery \
    --project="${PROJECT_ID}"
  ok "Instancia ${SQL_INSTANCE} creada"
fi

if gcloud sql databases describe "${DB_NAME}" --instance="${SQL_INSTANCE}" --project="${PROJECT_ID}" &>/dev/null; then
  skip "Base de datos ${DB_NAME}"
else
  gcloud sql databases create "${DB_NAME}" --instance="${SQL_INSTANCE}" --project="${PROJECT_ID}"
  ok "Base de datos ${DB_NAME}"
fi

# ── Paso 5 · Secret Manager (valores generados, NUNCA impresos) ──────────────
info "5) Secret Manager"

create_secret_if_absent() {  # $1=nombre  $2=comando-que-emite-el-valor-a-stdout
  local name="$1"; shift
  if gcloud secrets describe "${name}" --project="${PROJECT_ID}" &>/dev/null; then
    skip "Secret ${name}"
  else
    "$@" | gcloud secrets create "${name}" --data-file=- \
      --replication-policy=automatic --project="${PROJECT_ID}" >/dev/null
    ok "Secret ${name} creado (valor no impreso)"
  fi
}

gen_jwt()    { python3 -c "import secrets;print(secrets.token_urlsafe(48))"; }
gen_fernet() { python3 -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"; }
gen_dbpw()   { python3 -c "import secrets;print(secrets.token_urlsafe(32))"; }

create_secret_if_absent "jwt-secret-key" gen_jwt
create_secret_if_absent "fernet-key"     gen_fernet

# Password de DB: si el secret NO existe, se genera una vez, se guarda y se
# aplica al usuario. Si YA existe, no se toca (para no desincronizar la DB).
if gcloud secrets describe "db-password" --project="${PROJECT_ID}" &>/dev/null; then
  skip "Secret db-password"
else
  DBPW="$(gen_dbpw)"
  printf '%s' "${DBPW}" | gcloud secrets create "db-password" --data-file=- \
    --replication-policy=automatic --project="${PROJECT_ID}" >/dev/null
  if gcloud sql users list --instance="${SQL_INSTANCE}" --project="${PROJECT_ID}" \
       --format="value(name)" | grep -qx "${DB_USER}"; then
    gcloud sql users set-password "${DB_USER}" --instance="${SQL_INSTANCE}" \
      --password="${DBPW}" --project="${PROJECT_ID}" >/dev/null
  else
    gcloud sql users create "${DB_USER}" --instance="${SQL_INSTANCE}" \
      --password="${DBPW}" --project="${PROJECT_ID}" >/dev/null
  fi
  DBPW=""; unset DBPW
  ok "Secret db-password + usuario ${DB_USER} (password no impreso)"
fi

# ── Paso 6 · Service account de mínimo privilegio ────────────────────────────
info "6) Service account ${SA_NAME}"
if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
  skip "SA ${SA_NAME}"
else
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="FARO API (Cloud Run) - minimo privilegio" --project="${PROJECT_ID}"
  ok "SA ${SA_NAME} creada"
fi

for ROLE in roles/cloudsql.client roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" --role="${ROLE}" \
    --condition=None --quiet >/dev/null
  ok "Rol ${ROLE} → ${SA_NAME}"
done

for S in jwt-secret-key fernet-key db-password; do
  gcloud secrets add-iam-policy-binding "${S}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}" --quiet >/dev/null
  ok "secretAccessor sobre ${S} → ${SA_NAME}"
done

# ── Paso 7 · Audit logs (Data Access) ────────────────────────────────────────
info "7) Audit logs (Data Access) para Cloud SQL y Secret Manager"
POLICY="$(mktemp)"
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json > "${POLICY}"
# El script Python añade auditConfigs SOLO si faltan (preserva bindings y etag)
# e imprime APPLY/NOOP en la última línea para decidir si aplicar.
RESULT="$(python3 - "${POLICY}" <<'PY'
import json, sys
path = sys.argv[1]
d = json.load(open(path))
want = {"cloudsql.googleapis.com", "secretmanager.googleapis.com"}
logtypes = [{"logType": t} for t in ("ADMIN_READ", "DATA_READ", "DATA_WRITE")]
ac = d.get("auditConfigs", [])
existing = {c["service"] for c in ac}
changed = False
for svc in want:
    if svc not in existing:
        ac.append({"service": svc, "auditLogConfigs": logtypes}); changed = True
if changed:
    d["auditConfigs"] = ac
    json.dump(d, open(path, "w"), indent=2)
print("APPLY" if changed else "NOOP")
PY
)"
if [[ "${RESULT}" == "APPLY" ]]; then
  gcloud projects set-iam-policy "${PROJECT_ID}" "${POLICY}" >/dev/null
  ok "Audit Data Access aplicado"
else
  skip "Audit Data Access"
fi
rm -f "${POLICY}"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN} ✅ Fase 1 completa.${NC}"
echo "   Cloud SQL IP privada:"
gcloud sql instances describe "${SQL_INSTANCE}" --project="${PROJECT_ID}" \
  --format="value(ipAddresses[0].ipAddress)" 2>/dev/null
echo "   Siguiente: Fase 2 — conectar/poblar Gold en Cloud SQL y redeploy del API."
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
