"""
FastAPI Application for Covenant Service.

Production-ready REST API with CORS, health checks, and metrics.
Can run standalone or alongside A2A agent server.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from covenant_service.covenant_service.routes import router as covenant_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting Covenant Service API...")
    
    # Pre-load ML model for faster first request
    try:
        from covenant_service.covenant_service.tools.ml_tools import get_predictor
        predictor = get_predictor()
        if predictor.model:
            logger.info(f"ML Model loaded: v{predictor.model_version}")
        else:
            logger.warning("ML Model not loaded - predictions will fail")
    except Exception as e:
        logger.warning(f"Could not pre-load ML model: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Covenant Service API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="LoanGuard Covenant Service API",
        description=(
            "Production-ready API for covenant monitoring, compliance checking, "
            "ML-based breach prediction with SHAP explainability, "
            "risk velocity analysis, and portfolio management."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # CORS configuration for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            # Cloud Run domains
            "https://*.run.app",
        ],
        allow_origin_regex=r"https://.*\.run\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include covenant routes
    app.include_router(covenant_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": "LoanGuard Covenant Service",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "health": "/api/health",
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc) if app.debug else None,
            }
        )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    from common.config import settings
    
    port = getattr(settings, "COVENANT_SERVICE_PORT", 8082)
    
    uvicorn.run(
        "covenant_service.covenant_service.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
