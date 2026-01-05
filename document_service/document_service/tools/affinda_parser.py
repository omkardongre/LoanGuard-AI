"""
Affinda Document Parser Tool for Document Service.

V8 Implementation - Replaces Google Document AI.
Uses Affinda for production-grade loan document extraction.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from common.affinda_client import (
    get_affinda_client,
    ExtractedLoanAgreement,
    ExtractedCovenant,
)

logger = logging.getLogger(__name__)


def parse_with_affinda(file_path: str) -> Dict[str, Any]:
    """
    Parse a loan document using Affinda.
    
    This is the primary document parsing method for V8 architecture.
    
    Args:
        file_path: Path to the document file (PDF, DOCX, etc.)
        
    Returns:
        Dictionary containing parsed document data with:
        - success: bool indicating if parsing succeeded
        - data: extracted loan agreement data
        - covenants: list of extracted financial covenants
        - tables: any extracted tables
        - entities: extracted entity information
    """
    client = get_affinda_client()
    
    if not client.available:
        logger.error("Affinda not configured")
        return {
            "success": False,
            "error": "Affinda not configured. Check AFFINDA_API_KEY environment variable.",
            "source": "Affinda",
        }
    
    path = Path(file_path)
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "source": "Affinda",
        }
    
    try:
        logger.info(f"Parsing document with Affinda: {path.name}")
        
        result: ExtractedLoanAgreement = client.parse_document(file_path)
        
        # Format covenants for response
        covenants = []
        for cov in result.covenants:
            covenants.append({
                "type": cov.covenant_type,
                "threshold_value": cov.threshold_value,
                "measurement_frequency": cov.measurement_frequency,
                "raw_text": cov.raw_text,
                "confidence": cov.confidence,
            })
        
        # Build structured response
        extracted_data = {
            "success": True,
            "source": "Affinda",
            "version": "V8",
            "document_id": result.document_id,
            "extraction_confidence": result.extraction_confidence,
            "extracted_at": result.extracted_at,
            
            # Core loan data
            "borrower_name": result.borrower_name,
            "lender_name": result.lender_name,
            "loan_amount": result.loan_amount,
            "currency": result.currency,
            "maturity_date": result.maturity_date,
            "interest_rate": result.interest_rate,
            
            # Covenants
            "covenants": covenants,
            "covenant_count": len(covenants),
            
            # Raw text for further processing
            "text": result.raw_text,
            "text_length": len(result.raw_text),
            
            # Entities extracted (borrower/lender as entities)
            "entities": [
                {
                    "type": "BORROWER",
                    "mention_text": result.borrower_name,
                    "confidence": result.extraction_confidence,
                },
                {
                    "type": "LENDER",
                    "mention_text": result.lender_name,
                    "confidence": result.extraction_confidence,
                },
            ],
        }
        
        logger.info(
            f"Affinda extraction complete: "
            f"borrower={result.borrower_name}, "
            f"amount={result.loan_amount}, "
            f"covenants={len(covenants)}, "
            f"confidence={result.extraction_confidence}"
        )
        
        return extracted_data
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "source": "Affinda",
        }
    except Exception as e:
        logger.error(f"Affinda parsing error: {e}")
        return {
            "success": False,
            "error": str(e),
            "source": "Affinda",
        }


def parse_document_bytes_with_affinda(
    content: bytes,
    filename: str
) -> Dict[str, Any]:
    """
    Parse document from bytes content using Affinda.
    
    Useful for API uploads where file content is in memory.
    
    Args:
        content: File content as bytes
        filename: Original filename
        
    Returns:
        Dictionary containing parsed document data
    """
    client = get_affinda_client()
    
    if not client.available:
        return {
            "success": False,
            "error": "Affinda not configured",
            "source": "Affinda",
        }
    
    try:
        logger.info(f"Parsing document bytes with Affinda: {filename}")
        
        result: ExtractedLoanAgreement = client.parse_document_bytes(
            content, filename
        )
        
        covenants = [
            {
                "type": cov.covenant_type,
                "threshold_value": cov.threshold_value,
                "measurement_frequency": cov.measurement_frequency,
            }
            for cov in result.covenants
        ]
        
        return {
            "success": True,
            "source": "Affinda",
            "version": "V8",
            "document_id": result.document_id,
            "extraction_confidence": result.extraction_confidence,
            "borrower_name": result.borrower_name,
            "lender_name": result.lender_name,
            "loan_amount": result.loan_amount,
            "currency": result.currency,
            "maturity_date": result.maturity_date,
            "interest_rate": result.interest_rate,
            "covenants": covenants,
            "text": result.raw_text,
        }
        
    except Exception as e:
        logger.error(f"Affinda parsing error: {e}")
        return {
            "success": False,
            "error": str(e),
            "source": "Affinda",
        }


def get_extraction_summary(result: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of extraction results.
    
    Args:
        result: Extraction result dictionary
        
    Returns:
        Formatted summary string
    """
    if not result.get("success"):
        return f"Extraction failed: {result.get('error', 'Unknown error')}"
    
    lines = [
        "=== Affinda Extraction Summary ===",
        f"Source: {result.get('source', 'Unknown')}",
        f"Confidence: {result.get('extraction_confidence', 0):.0%}",
        "",
        "--- Loan Details ---",
        f"Borrower: {result.get('borrower_name', 'N/A')}",
        f"Lender: {result.get('lender_name', 'N/A')}",
        f"Amount: {result.get('currency', 'USD')} {result.get('loan_amount', 0):,.2f}",
        f"Maturity: {result.get('maturity_date', 'N/A')}",
        f"Interest Rate: {result.get('interest_rate', 'N/A')}",
        "",
        f"--- Covenants ({result.get('covenant_count', 0)}) ---",
    ]
    
    for cov in result.get("covenants", []):
        lines.append(
            f"  • {cov.get('type', 'Unknown')}: {cov.get('threshold_value', 'N/A')} "
            f"({cov.get('measurement_frequency', 'Quarterly')})"
        )
    
    return "\n".join(lines)
