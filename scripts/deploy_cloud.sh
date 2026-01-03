#!/bin/bash
# Cloud Run deployment script for LoanGuard AI Platform

set -e

echo "☁️  LoanGuard AI Cloud Run Deployment"

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${CLOUD_PROJECT_REGION:-us-central1}"
SERVICES=("document-service" "covenant-service" "esg-service" "alert-service")

if [ -z "$PROJECT_ID" ]; then
    echo "❌ GOOGLE_CLOUD_PROJECT is not set"
    exit 1
fi

echo "📋 Project: $PROJECT_ID"
echo "📍 Region: $REGION"
echo ""

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3

    echo "🔨 Building $service_name..."
    
    # Build and push container
    gcloud builds submit \
        --project="$PROJECT_ID" \
        --tag="gcr.io/$PROJECT_ID/$service_name" \
        --quiet \
        .

    echo "🚀 Deploying $service_name to Cloud Run..."
    
    gcloud run deploy "$service_name" \
        --project="$PROJECT_ID" \
        --image="gcr.io/$PROJECT_ID/$service_name" \
        --platform=managed \
        --region="$REGION" \
        --port="$port" \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --concurrency=80 \
        --min-instances=0 \
        --max-instances=10 \
        --set-env-vars="GOOGLE_API_KEY=$GOOGLE_API_KEY" \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
        --allow-unauthenticated \
        --quiet

    echo "✅ $service_name deployed"
}

# Deploy each service
echo "📄 Deploying Document Service..."
deploy_service "loanguard-document" "document_service" 8081

echo "📊 Deploying Covenant Service..."
deploy_service "loanguard-covenant" "covenant_service" 8082

echo "🌿 Deploying ESG Service..."
deploy_service "loanguard-esg" "esg_service" 8083

echo "🔔 Deploying Alert Service..."
deploy_service "loanguard-alert" "alert_service" 8084

echo ""
echo "✅ All services deployed to Cloud Run!"
echo ""
echo "Service URLs:"
gcloud run services list --project="$PROJECT_ID" --region="$REGION" --format="table(SERVICE,URL)"
