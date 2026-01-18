#!/bin/bash
# Instructions and helper script for setting up Google Cloud secrets

set -e

PROJECT_ID="${GCP_PROJECT_ID:-}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable not set"
    exit 1
fi

echo "Setting up Google Secret Manager for Cloud Run..."

if [ ! -f "service-account.json" ]; then
    echo "Error: service-account.json not found"
    echo "Please create a service account JSON file first."
    exit 1
fi

# Create secret in Secret Manager
SECRET_NAME="sleep-calendar-credentials"

echo "Creating secret: ${SECRET_NAME}"
gcloud secrets create "${SECRET_NAME}" \
    --data-file=service-account.json \
    --project="${PROJECT_ID}" || \
gcloud secrets versions add "${SECRET_NAME}" \
    --data-file=service-account.json \
    --project="${PROJECT_ID}"

echo "Granting Cloud Run service account access to secret..."
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}"

echo "✅ Secret created: ${SECRET_NAME}"
echo ""
echo "To use in Cloud Run, update .cloudbuild.yaml to reference this secret:"
echo "  --set-secrets=GOOGLE_CALENDAR_CREDENTIALS=${SECRET_NAME}:latest"
