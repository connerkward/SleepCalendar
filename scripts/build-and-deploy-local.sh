#!/bin/bash
# Build Docker image locally and push to Google Container Registry, then deploy to Cloud Run

set -e

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="sleep-calendar-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GCP_PROJECT_ID not set and no default project configured"
    echo "   Set GCP_PROJECT_ID environment variable or run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

if [ -z "$GOOGLE_CALENDAR_CREDENTIALS" ]; then
    echo "❌ Error: GOOGLE_CALENDAR_CREDENTIALS environment variable not set"
    echo "   Export it with: export GOOGLE_CALENDAR_CREDENTIALS=\$(base64 -i service-account.json)"
    exit 1
fi

echo "🚀 Building and deploying ${SERVICE_NAME} to Cloud Run"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo ""

# Build Docker image
echo "📦 Building Docker image..."
docker build -t "${IMAGE_NAME}:latest" .

# Tag with commit hash if available
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
docker tag "${IMAGE_NAME}:latest" "${IMAGE_NAME}:${COMMIT_SHA}"

# Push to Container Registry
echo "⬆️  Pushing to Container Registry..."
docker push "${IMAGE_NAME}:latest"
docker push "${IMAGE_NAME}:${COMMIT_SHA}"

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}:${COMMIT_SHA}" \
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

# Get service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region "${REGION}" \
    --format='value(status.url)' \
    --project "${PROJECT_ID}")

echo ""
echo "✅ Deployment complete!"
echo "   Service URL: ${SERVICE_URL}"
echo "   Health check: ${SERVICE_URL}/health"
