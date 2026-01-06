"""
FastAPI Application for ESG Service.

Production-level ESG monitoring service with greenwashing detection,
KPI tracking, SPT validation, and ESG ratings.

Run with:
    uvicorn esg_service.esg_service.app:app --port 8083 --reload
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifespan.
    
    Pre-loads greenwashing detector for faster first requests.
    """
    logger.info("Starting ESG Service...")
    
    # Pre-initialize greenwashing detector
    try:
        from esg_service.esg_service.tools import get_greenwashing_detector
        detector = get_greenwashing_detector()
        if detector.available:
            logger.info("Greenwashing detector ready")
        else:
            logger.warning("Greenwashing detector not configured - check API keys")
    except Exception as e:
        logger.warning(f"Could not initialize greenwashing detector: {e}")
    
    logger.info("ESG Service started successfully")
    
    yield  # Application runs here
    
    logger.info("Shutting down ESG Service...")


# Create FastAPI app with metadata
app = FastAPI(
    title="LoanGuard ESG Service API",
    description=(
        "ESG monitoring and greenwashing detection service. "
        "Includes KPI tracking, SPT validation, and ESG ratings."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS configuration for Cloud Run and local development
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "https://*.run.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.run\.app",
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions globally."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else None,
        }
    )


# Include routes
from esg_service.esg_service.routes import router
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "LoanGuard ESG Service",
        "version": "1.0.0",
        "hero_feature": "Greenwashing Detection",
        "docs": "/docs",
        "health": "/api/esg/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("ESG_SERVICE_PORT", 8083))
    uvicorn.run(
        "esg_service.esg_service.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
