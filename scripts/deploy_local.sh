#!/bin/bash
# Local deployment script for LoanGuard AI Platform

set -e

echo "🚀 Starting LoanGuard AI Local Deployment..."

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys and run again."
    exit 1
fi

# Source environment variables
set -a
source .env
set +a

# Check required environment variables
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY is not set in .env"
    exit 1
fi

echo "✅ Environment variables loaded"

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "✅ Dependencies ready"

# Kill any existing services
pkill -f "document_service" 2>/dev/null || true
pkill -f "covenant_service" 2>/dev/null || true
pkill -f "esg_service" 2>/dev/null || true
pkill -f "alert_service" 2>/dev/null || true

sleep 2

# Start services in background
echo "📄 Starting Document Service on port 8081..."
python -m document_service --port 8081 > logs/document_service.log 2>&1 &
DOCUMENT_PID=$!

echo "📊 Starting Covenant Service on port 8082..."
python -m covenant_service --port 8082 > logs/covenant_service.log 2>&1 &
COVENANT_PID=$!

echo "🌿 Starting ESG Service on port 8083..."
python -m esg_service --port 8083 > logs/esg_service.log 2>&1 &
ESG_PID=$!

echo "🔔 Starting Alert Service on port 8084..."
python -m alert_service --port 8084 > logs/alert_service.log 2>&1 &
ALERT_PID=$!

sleep 3

echo ""
echo "✅ All services started!"
echo ""
echo "Service URLs:"
echo "  📄 Document Service: http://localhost:8081"
echo "  📊 Covenant Service: http://localhost:8082"
echo "  🌿 ESG Service:      http://localhost:8083"
echo "  🔔 Alert Service:    http://localhost:8084"
echo ""
echo "PIDs: Document=$DOCUMENT_PID, Covenant=$COVENANT_PID, ESG=$ESG_PID, Alert=$ALERT_PID"
echo ""
echo "To stop all services: make clean"
echo "Logs are in: logs/"
