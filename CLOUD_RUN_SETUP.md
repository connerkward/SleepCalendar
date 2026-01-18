# Cloud Run Setup Guide

This guide explains how to set up and deploy the Sleep Calendar API to Google Cloud Run.

## Architecture

```
iOS Shortcut → Cloud Run API (POST /sync) → Google Calendar API
                                     ↓
                              Service Account
                           (creates per-user calendars)
```

Each user gets their own calendar: `Sleep Data - user@example.com`

## Prerequisites

1. Google Cloud Project with billing enabled
2. `gcloud` CLI installed and authenticated
3. Service account JSON file (`service-account.json`)
4. Docker installed (for local builds)

## Initial Setup

### 1. Enable Required APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Set Project ID

```bash
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID
```

### 3. Configure Service Account Credentials

You can use either:

**Option A: Environment Variable (Simpler)**
```bash
# Base64 encode service account JSON
export GOOGLE_CALENDAR_CREDENTIALS=$(base64 -i service-account.json)
```

**Option B: Secret Manager (More Secure)**
```bash
./scripts/setup-secrets.sh
```

## Deployment

### Using Local Build (Easiest - No Cloud Build API needed)

Build Docker image locally and push directly to Container Registry:

```bash
# Set credentials as base64
export GOOGLE_CALENDAR_CREDENTIALS=$(base64 -i service-account.json)
export GCP_PROJECT_ID="your-project-id"

# Build and deploy
./scripts/build-and-deploy-local.sh
```

This avoids needing Cloud Build API enabled.

### Using Cloud Build (Alternative)

```bash
gcloud builds submit \
  --config=.cloudbuild.yaml \
  --substitutions=_GOOGLE_CALENDAR_CREDENTIALS="$(base64 -i service-account.json)" \
  --project=$GCP_PROJECT_ID
```

### Using GitHub Actions (CI/CD)

1. Add GitHub Secrets:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Service account JSON for Cloud Build (as base64 or JSON)
   - `GOOGLE_CALENDAR_CREDENTIALS`: Service account JSON for calendar access (base64)

2. Push to `main` or `cloud-run` branch - deployment will trigger automatically.

### Using Local Script

```bash
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_CALENDAR_CREDENTIALS=$(base64 -i service-account.json)
./scripts/deploy.sh
```

## API Usage

### Endpoint

```
POST https://your-service-url.run.app/sync
Content-Type: application/json
```

### Request

```json
{
  "email": "user@example.com",
  "samples": [
    {
      "startDate": "2026-01-17T02:22:00",
      "endDate": "2026-01-17T02:56:00",
      "value": "Core",
      "sourceName": "Apple Health"
    }
  ]
}
```

### Response

```json
{
  "success": true,
  "events_synced": 42,
  "calendar_id": "...@group.calendar.google.com",
  "calendar_url": "https://calendar.google.com/calendar/..."
}
```

### Example with curl

```bash
curl -X POST https://your-service-url.run.app/sync \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "samples": [...]
  }'
```

## Testing

### Local Tests

```bash
./scripts/test-local.sh
```

### Health Check

```bash
curl https://your-service-url.run.app/health
```

## iOS Shortcut Setup

Update your iOS Shortcut to POST to Cloud Run instead of GitHub:

1. **Get Contents of URL** action
   - Method: `POST`
   - URL: `https://your-service-url.run.app/sync`
   - Headers:
     - `Content-Type`: `application/json`
   - Request Body Type: `File` (or `JSON`)
   - Request Body: Dictionary with `email` and `samples` keys

2. Include user email in the dictionary:
   - `email`: User's email address
   - `samples`: Sleep data from HealthKit

## Calendar Naming

Calendars are automatically created with the name: `Sleep Data - {email}`

Each calendar is:
- Owned by the service account
- Shared with the user's email (write access)
- Public read-only (for easy subscription)

## Environment Variables

Cloud Run service uses:
- `GOOGLE_CALENDAR_CREDENTIALS`: Base64-encoded service account JSON (or Secret Manager reference)
- `PORT`: 8080 (Cloud Run default, auto-set)

## Monitoring

View logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sleep-calendar-api" --limit 50
```

View service:
```bash
gcloud run services describe sleep-calendar-api --region us-central1
```

## Troubleshooting

### "Permission denied" errors

Ensure service account has:
- `roles/calendar.admin` or `roles/calendar.events` permission
- Access to Secret Manager (if using Secret Manager)

### "Invalid credentials" errors

Check that `GOOGLE_CALENDAR_CREDENTIALS` is correctly base64-encoded or properly referenced from Secret Manager.

### Deployment fails

Check Cloud Build logs:
```bash
gcloud builds list --limit 5
gcloud builds log <BUILD_ID>
```
