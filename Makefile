# Makefile for LoanGuard AI Platform

# Check if .env file exists and source it
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: help setup install clean deploy_local deploy_cloud test lint format check_env

help:
	@echo "LoanGuard AI Platform - Available Commands:"
	@echo ""
	@echo "  make setup                - Create virtual environment and install dependencies"
	@echo "  make install              - Install dependencies only"
	@echo "  make deploy_local         - Deploy all services locally"
	@echo "  make deploy_cloud         - Deploy to Google Cloud Run"
	@echo "  make test                 - Run tests"
	@echo "  make lint                 - Run linter"
	@echo "  make format               - Format code"
	@echo "  make clean                - Kill all running services"
	@echo "  make check_env            - Check environment variables"
	@echo ""

check_env:
	@echo "Checking environment variables..."
	@if [ -z "$(GOOGLE_API_KEY)" ]; then \
		echo "❌ GOOGLE_API_KEY is not set"; \
		exit 1; \
	else \
		echo "✅ GOOGLE_API_KEY is set"; \
	fi
	@if [ -n "$(GOOGLE_CLOUD_PROJECT)" ]; then echo "✅ GOOGLE_CLOUD_PROJECT is set"; else echo "⚠️  GOOGLE_CLOUD_PROJECT is not set"; fi
	@if [ -n "$(SENDGRID_API_KEY)" ]; then echo "✅ SENDGRID_API_KEY is set"; else echo "⚠️  SENDGRID_API_KEY is not set (optional)"; fi

setup:
	@echo "🔧 Setting up development environment..."
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "✅ Setup complete. Activate with: source .venv/bin/activate"

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

deploy_local: clean check_env
	@echo "🚀 Deploying all services locally..."
	@chmod +x ./scripts/deploy_local.sh
	@./scripts/deploy_local.sh

deploy_cloud: check_env
	@echo "☁️  Deploying services to Cloud Run..."
	@chmod +x ./scripts/deploy_cloud.sh
	@./scripts/deploy_cloud.sh

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

lint:
	@echo "🔍 Running linter..."
	ruff check .

format:
	@echo "✨ Formatting code..."
	ruff format .

clean:
	@echo "🧹 Cleaning up..."
	@pkill -f "uvicorn" 2>/dev/null || true
	@pkill -f "document_service" 2>/dev/null || true
	@pkill -f "covenant_service" 2>/dev/null || true
	@pkill -f "esg_service" 2>/dev/null || true
	@pkill -f "alert_service" 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Service-specific commands
run_document_service:
	@echo "📄 Starting Document Service..."
	cd document_service && python -m document_service

run_covenant_service:
	@echo "📊 Starting Covenant Service..."
	cd covenant_service && python -m covenant_service

run_esg_service:
	@echo "🌿 Starting ESG Service..."
	cd esg_service && python -m esg_service

run_alert_service:
	@echo "🔔 Starting Alert Service..."
	cd alert_service && python -m alert_service

run_ui:
	@echo "🖥️  Starting UI Client..."
	cd ui_client && npm run dev
