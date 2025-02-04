# GCP Deployment Guide for Data Concierge

## Prerequisites

1. Google Cloud Platform Account
2. GCP Project created
3. Google Cloud SDK installed
4. Required APIs enabled:
   - Cloud Run API
   - Cloud SQL API
   - Secret Manager API
   - Cloud Storage API

## Step-by-Step Deployment Guide

### 1. Initial Setup

```bash
# Login to GCP (if not using Cloud Shell)
gcloud auth login

# Set project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  sql.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com
```

### 2. Create Cloud SQL Instance (PostgreSQL)

```bash
# Create PostgreSQL instance
gcloud sql instances create dataconcierge-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=asia-east1 \
  --root-password=your-root-password

# Create database
gcloud sql databases create dataconcierge \
  --instance=dataconcierge-db

# Create user
gcloud sql users create dataconcierge \
  --instance=dataconcierge-db \
  --password=your-db-password
```

### 3. Set up Secret Manager

```bash
# Create secrets
echo -n "your-django-secret-key" | \
  gcloud secrets create django-secret-key --data-file=-

echo -n "your-openai-api-key" | \
  gcloud secrets create openai-api-key --data-file=-

echo -n "your-db-password" | \
  gcloud secrets create db-password --data-file=-
```

### 4. Create Cloud Storage Bucket

```bash
# Create bucket for static files and media
gcloud storage buckets create gs://$PROJECT_ID-static
gcloud storage buckets create gs://$PROJECT_ID-media
```

### 5. Build and Deploy Docker Image

```bash
# Build using Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/dataconcierge

# Deploy to Cloud Run
gcloud run deploy dataconcierge \
  --image gcr.io/$PROJECT_ID/dataconcierge \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgres://dataconcierge:${DB_PASSWORD}@/dataconcierge?host=/cloudsql/${PROJECT_ID}:asia-east1:dataconcierge-db" \
  --set-env-vars "GS_BUCKET_NAME=${PROJECT_ID}-static" \
  --add-cloudsql-instances ${PROJECT_ID}:asia-east1:dataconcierge-db
```

### 6. Set up Domain and SSL (Optional)

```bash
# Map custom domain
gcloud beta run domain-mappings create \
  --service dataconcierge \
  --domain your-domain.com \
  --region asia-east1
```

## Required Files

### Dockerfile

```dockerfile
# Use official Python runtime as base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 config.wsgi:application
```

### .gcloudignore

```text
.git
.gitignore
.env
*.pyc
__pycache__
.pytest_cache
.coverage
htmlcov/
venv/
*.sqlite3
media/
```

### cloud_sql_proxy.yaml (For local development)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cloud-sql-proxy
spec:
  containers:
  - name: cloud-sql-proxy
    image: gcr.io/cloudsql-docker/gce-proxy:1.17
    command:
      - "/cloud_sql_proxy"
      - "-instances=${PROJECT_ID}:asia-east1:dataconcierge-db=tcp:5432"
    securityContext:
      runAsNonRoot: true
```

## Post-Deployment Steps

1. Run database migrations:
```bash
gcloud run services update dataconcierge \
  --command="python manage.py migrate" \
  --region=asia-east1
```

2. Create superuser:
```bash
gcloud run services update dataconcierge \
  --command='python manage.py createsuperuser --noinput --username admin --email admin@example.com' \
  --region=asia-east1
```

3. Verify deployment:
```bash
# Get service URL
gcloud run services describe dataconcierge \
  --region=asia-east1 \
  --format='value(status.url)'
```

## Monitoring and Maintenance

1. View logs:
```bash
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=dataconcierge"
```

2. Monitor performance:
```bash
gcloud monitoring dashboards create \
  --config-from-file=monitoring-dashboard.json
```

3. Set up alerts:
```bash
gcloud alpha monitoring policies create \
  --config-from-file=alert-policy.json
```

## Cost Optimization

1. Set budget alerts:
```bash
gcloud billing budgets create \
  --billing-account=your-billing-account-id \
  --display-name="DataConcierge Budget" \
  --budget-amount=1000USD \
  --threshold-rules=percent=0.5,percent=0.75,percent=0.9,percent=1.0
```

2. Configure instance scaling:
```bash
gcloud run services update dataconcierge \
  --min-instances=0 \
  --max-instances=10 \
  --region=asia-east1
``` 