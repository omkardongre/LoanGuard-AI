"""
FastAPI Application for Document Service.

Document parsing and extraction using Affinda.
V8 Architecture - Production-grade loan document processing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from document_service.document_service.routes import router

# Create FastAPI app
app = FastAPI(
    title="LoanGuard Document Service",
    description="Document parsing with Affinda for loan agreement extraction",
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
        "service": "LoanGuard Document Service",
        "version": "1.0.0",
        "parser": "Affinda V8",
        "docs": "/docs",
        "health": "/api/documents/health",
    }


# Export
__all__ = ["app"]
