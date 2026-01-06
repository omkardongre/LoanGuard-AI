"""
FastAPI Application for Alert Service.

Alert management, notification delivery, and compliance reporting.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alert_service.alert_service.routes import router

# Create FastAPI app
app = FastAPI(
    title="LoanGuard Alert Service",
    description="Alert management, notifications, and compliance reporting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "LoanGuard Alert Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/alerts/health",
    }


# Export
__all__ = ["app"]
