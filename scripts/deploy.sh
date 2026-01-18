#!/bin/bash
# Deploy to Cloud Run using gcloud CLI

set -e

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="sleep-calendar-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable not set"
    exit 1
fi

if [ -z "$GOOGLE_CALENDAR_CREDENTIALS" ]; then
    echo "Error: GOOGLE_CALENDAR_CREDENTIALS environment variable not set"
    exit 1
fi

echo "Building Docker image..."
docker build -t "${IMAGE_NAME}:latest" .

echo "Pushing to Container Registry..."
docker push "${IMAGE_NAME}:latest"

echo "Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}:latest" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CALENDAR_CREDENTIALS=${GOOGLE_CALENDAR_CREDENTIALS}" \
    --project "${PROJECT_ID}"

echo "✅ Deployment complete!"
gcloud run services describe "${SERVICE_NAME}" \
    --region "${REGION}" \
    --format='value(status.url)' \
    --project "${PROJECT_ID}"
