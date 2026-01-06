"""
FastAPI REST API Routes for Document Service.

Production-level API endpoints for document parsing using Affinda.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query, Path
from pydantic import BaseModel
import logging
import tempfile
import os

from document_service.document_service.tools.affinda_parser import (
    parse_with_affinda,
    parse_document_bytes_with_affinda,
    get_extraction_summary,
)
from common.affinda_client import get_affinda_client

logger = logging.getLogger(__name__)


# ============================================
# Response Models
# ============================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    service: str = "document-service"
    version: str = "1.0.0"
    parser: str = "Affinda V8"


class ParseResponse(BaseModel):
    """Document parse response."""
    success: bool
    source: str = "Affinda"
    version: str = "V8"
    document_id: Optional[str] = None
    extraction_confidence: Optional[float] = None
    borrower_name: Optional[str] = None
    lender_name: Optional[str] = None
    loan_amount: Optional[float] = None
    currency: Optional[str] = None
    maturity_date: Optional[str] = None
    interest_rate: Optional[str] = None
    covenants: list = []
    error: Optional[str] = None


# ============================================
# API Router
# ============================================

router = APIRouter(prefix="/api/documents", tags=["documents"])


# ============================================
# Health & Status Endpoints
# ============================================

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for document service."""
    return HealthResponse()


@router.get("/status")
async def service_status() -> Dict[str, Any]:
    """Get document service status including Affinda availability."""
    client = get_affinda_client()
    
    return {
        "service": "document-service",
        "version": "1.0.0",
        "parser": "Affinda",
        "status": "healthy",
        "affinda": {
            "available": client.available,
            "workspace_id": client.workspace_id if client.available else None,
        }
    }


# ============================================
# Document Parsing Endpoints
# ============================================

@router.post("/parse", response_model=ParseResponse)
async def parse_document(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, etc.)"),
) -> ParseResponse:
    """
    Parse a loan agreement document using Affinda.
    
    Extracts borrower, lender, loan amount, covenants, and other key data.
    Supports PDF, DOCX, DOC, and image files.
    """
    client = get_affinda_client()
    
    if not client.available:
        raise HTTPException(
            status_code=503,
            detail="Affinda document parser not configured"
        )
    
    try:
        # Read file content
        content = await file.read()
        filename = file.filename or "document.pdf"
        
        logger.info(f"Parsing document: {filename} ({len(content)} bytes)")
        
        # Parse with Affinda
        result = parse_document_bytes_with_affinda(content, filename)
        
        if not result.get("success"):
            return ParseResponse(
                success=False,
                source="Affinda",
                error=result.get("error", "Parse failed")
            )
        
        return ParseResponse(
            success=True,
            source="Affinda",
            version="V8",
            document_id=result.get("document_id"),
            extraction_confidence=result.get("extraction_confidence"),
            borrower_name=result.get("borrower_name"),
            lender_name=result.get("lender_name"),
            loan_amount=result.get("loan_amount"),
            currency=result.get("currency"),
            maturity_date=result.get("maturity_date"),
            interest_rate=result.get("interest_rate"),
            covenants=result.get("covenants", []),
        )
        
    except Exception as e:
        logger.exception(f"Document parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_and_parse(
    file: UploadFile = File(..., description="Document file"),
    store_in_bigquery: bool = Form(False, description="Store extracted data in BigQuery"),
) -> Dict[str, Any]:
    """
    Upload a document, parse it, and optionally store results.
    
    This endpoint is useful for batch processing of loan documents.
    """
    result = await parse_document(file)
    
    response = {
        "success": result.success,
        "parsed_data": result.model_dump() if result.success else None,
        "stored_in_bigquery": False,
    }
    
    if result.success and store_in_bigquery:
        # TODO: Implement BigQuery storage
        # Would create a loan record from the parsed data
        response["stored_in_bigquery"] = False
        response["bigquery_note"] = "BigQuery storage not yet implemented"
    
    return response


@router.get("/{document_id}")
async def get_document(
    document_id: str = Path(..., description="Affinda document identifier"),
) -> Dict[str, Any]:
    """
    Retrieve a previously parsed document by its Affinda ID.
    """
    client = get_affinda_client()
    
    if not client.available:
        raise HTTPException(status_code=503, detail="Affinda not available")
    
    try:
        result = client.get_document(document_id)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        return {
            "success": True,
            "document_id": document_id,
            "data": result,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]
