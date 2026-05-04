#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
BILLING_ACCOUNT_ID="${BILLING_ACCOUNT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-rrhh-api}"
AR_REPO="${AR_REPO:-rrhh}"
DATABASE_URL="${DATABASE_URL:-}"
JWT_SECRET="${JWT_SECRET:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
OPENAI_MODEL="${OPENAI_MODEL:-gpt-4.1-mini}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Missing PROJECT_ID. Example: PROJECT_ID=rrhh-mvp-123 ./scripts/gcp-bootstrap.sh"
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is required. Run this script in Google Cloud Shell."
  exit 1
fi

if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
  echo "Creating project $PROJECT_ID..."
  gcloud projects create "$PROJECT_ID" --name="$PROJECT_ID"
fi

gcloud config set project "$PROJECT_ID"

if [[ -n "$BILLING_ACCOUNT_ID" ]]; then
  echo "Linking billing account..."
  gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT_ID"
else
  echo "BILLING_ACCOUNT_ID not provided. If APIs fail to enable, link billing manually."
fi

echo "Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

if ! gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" >/dev/null 2>&1; then
  echo "Creating Artifact Registry repository..."
  gcloud artifacts repositories create "$AR_REPO" \
    --repository-format=docker \
    --location="$REGION"
fi

create_or_update_secret() {
  local name="$1"
  local value="$2"

  if [[ -z "$value" ]]; then
    echo "Skipping secret $name because value is empty."
    return
  fi

  if gcloud secrets describe "$name" >/dev/null 2>&1; then
    printf "%s" "$value" | gcloud secrets versions add "$name" --data-file=-
  else
    printf "%s" "$value" | gcloud secrets create "$name" --data-file=-
  fi
}

echo "Creating or updating secrets..."
create_or_update_secret "rrhh-database-url" "$DATABASE_URL"
create_or_update_secret "rrhh-jwt-secret" "$JWT_SECRET"
create_or_update_secret "rrhh-openai-api-key" "$OPENAI_API_KEY"

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
CLOUD_BUILD_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"
RUNTIME_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

echo "Granting IAM permissions..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/run.admin" >/dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/iam.serviceAccountUser" >/dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/artifactregistry.writer" >/dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

if [[ -z "$DATABASE_URL" || -z "$JWT_SECRET" || -z "$OPENAI_API_KEY" ]]; then
  echo "Bootstrap finished, but deploy was skipped because one or more secrets were empty."
  echo "Set DATABASE_URL, JWT_SECRET and OPENAI_API_KEY, then rerun this script."
  exit 0
fi

echo "Deploying to Cloud Run via Cloud Build..."
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions "_REGION=$REGION,_SERVICE=$SERVICE,_AR_REPO=$AR_REPO,_OPENAI_MODEL=$OPENAI_MODEL"

SERVICE_URL="$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)')"
echo "Deployed: $SERVICE_URL"
echo "Health check: $SERVICE_URL/health"
