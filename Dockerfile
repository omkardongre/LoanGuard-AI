# LoanGuard AI API Gateway - Google Cloud Run Dockerfile
# Best practices: https://cloud.google.com/run/docs/quickstarts/build-and-deploy/python
FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Environment variables for Cloud Run
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Expose Cloud Run default port
EXPOSE 8080

# Use gunicorn with uvicorn workers for production
# Cloud Run sets PORT env variable automatically
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 -k uvicorn.workers.UvicornWorker api_gateway.main:app
