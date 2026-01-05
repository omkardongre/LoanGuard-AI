"""
Affinda Document AI Client for LoanGuard V8.

Production-grade document extraction using Affinda API.
Replaces Google Document AI for loan agreement parsing.

API Docs: https://docs.affinda.com/reference/getting-started
SDK: https://github.com/affinda/affinda-python
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Environment configuration
AFFINDA_API_KEY = os.getenv("AFFINDA_API_KEY", "")
AFFINDA_WORKSPACE_ID = os.getenv("AFFINDA_WORKSPACE_ID", "")
AFFINDA_COLLECTION_ID = os.getenv("AFFINDA_COLLECTION_ID", "")


@dataclass
class ExtractedCovenant:
    """Structured covenant data extracted from loan document."""
    
    covenant_type: str
    threshold_value: str
    measurement_frequency: str = "Quarterly"
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class ExtractedLoanAgreement:
    """Complete loan agreement extraction result."""
    
    borrower_name: str = "Unknown Borrower"
    lender_name: str = "Unknown Lender"
    loan_amount: float = 0.0
    currency: str = "USD"
    maturity_date: str = ""
    interest_rate: str = ""
    covenants: List[ExtractedCovenant] = field(default_factory=list)
    raw_text: str = ""
    extraction_confidence: float = 0.0
    document_id: str = ""
    extraction_source: str = "Affinda"
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class AffindaClient:
    """
    Production-grade Affinda client for loan document extraction.
    
    Uses the official Affinda Python SDK for reliable document parsing.
    Configured for credit agreement / loan document extraction.
    """
    
    def __init__(self):
        """Initialize Affinda client with environment credentials."""
        self.api_key = AFFINDA_API_KEY
        self.workspace_id = AFFINDA_WORKSPACE_ID
        self.collection_id = AFFINDA_COLLECTION_ID
        self._client = None
        self._credential = None
        
    @property
    def available(self) -> bool:
        """Check if Affinda is properly configured."""
        return bool(self.api_key and self.workspace_id)
    
    def _get_client(self):
        """
        Get or create Affinda API client.
        
        Uses lazy initialization to avoid import errors when SDK not installed.
        """
        if self._client is None:
            try:
                from affinda import AffindaAPI, TokenCredential
                
                self._credential = TokenCredential(token=self.api_key)
                self._client = AffindaAPI(credential=self._credential)
                logger.info("Affinda client initialized successfully")
            except ImportError:
                logger.error(
                    "affinda package not installed. "
                    "Install with: pip install affinda"
                )
                raise ImportError(
                    "affinda package required. Install with: pip install affinda"
                )
        return self._client
    
    def parse_document(self, file_path: str) -> ExtractedLoanAgreement:
        """
        Parse a loan agreement document using Affinda.
        
        Args:
            file_path: Path to the PDF/DOCX/TXT file
            
        Returns:
            ExtractedLoanAgreement with all structured data
            
        Raises:
            ValueError: If client not configured
            FileNotFoundError: If file doesn't exist
            Exception: If API call fails
        """
        if not self.available:
            raise ValueError(
                "Affinda not configured. Set AFFINDA_API_KEY and "
                "AFFINDA_WORKSPACE_ID environment variables."
            )
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        client = self._get_client()
        
        try:
            logger.info(f"Parsing document: {path.name}")
            
            with path.open("rb") as f:
                doc = client.create_document(
                    file=f,
                    file_name=path.name,
                    workspace=self.workspace_id,
                    collection=self.collection_id if self.collection_id else None,
                    wait=True,  # Wait for processing to complete
                )
            
            logger.info(f"Document parsed successfully: {doc.meta.identifier}")
            return self._process_response(doc)
            
        except Exception as e:
            logger.error(f"Affinda parsing error: {e}")
            raise
    
    def parse_document_bytes(
        self, 
        content: bytes, 
        filename: str
    ) -> ExtractedLoanAgreement:
        """
        Parse a loan agreement from bytes content.
        
        Useful for API uploads where file is in memory.
        
        Args:
            content: File content as bytes
            filename: Original filename (for MIME type detection)
            
        Returns:
            ExtractedLoanAgreement with all structured data
        """
        if not self.available:
            raise ValueError(
                "Affinda not configured. Set AFFINDA_API_KEY and "
                "AFFINDA_WORKSPACE_ID environment variables."
            )
        
        client = self._get_client()
        
        try:
            logger.info(f"Parsing document bytes: {filename}")
            
            doc = client.create_document(
                file=content,
                file_name=filename,
                workspace=self.workspace_id,
                collection=self.collection_id if self.collection_id else None,
                wait=True,
            )
            
            logger.info(f"Document parsed successfully: {doc.meta.identifier}")
            return self._process_response(doc)
            
        except Exception as e:
            logger.error(f"Affinda parsing error: {e}")
            raise
    
    def _process_response(self, doc) -> ExtractedLoanAgreement:
        """
        Process Affinda API response into structured loan data.
        
        Extracts borrower, lender, amounts, dates, and covenants
        from the parsed document response.
        """
        data = doc.data if hasattr(doc, 'data') else {}
        
        # Handle both dict and object responses
        if hasattr(data, '__dict__'):
            data = self._object_to_dict(data)
        
        # Extract main fields using flexible field access
        borrower_name = self._extract_field(data, [
            "borrowerName", "borrower_name", "borrower", 
            "partyName", "party_name", "companyName"
        ], "Unknown Borrower")
        
        lender_name = self._extract_field(data, [
            "lenderName", "lender_name", "lender",
            "creditor", "bankName", "bank_name"
        ], "Unknown Lender")
        
        loan_amount = self._extract_numeric_field(data, [
            "loanAmount", "loan_amount", "principalAmount",
            "facilityAmount", "facility_amount", "amount", "total"
        ], 0.0)
        
        currency = self._extract_field(data, [
            "currency", "currencyCode", "currency_code"
        ], "USD")
        
        maturity_date = self._extract_field(data, [
            "maturityDate", "maturity_date", "expirationDate",
            "expiration_date", "endDate", "end_date"
        ], "")
        
        interest_rate = self._extract_field(data, [
            "interestRate", "interest_rate", "rate", "margin"
        ], "")
        
        # Extract covenants
        covenants = self._extract_covenants(data)
        
        # Get raw text
        raw_text = ""
        if hasattr(doc, 'meta') and hasattr(doc.meta, 'raw_text'):
            raw_text = doc.meta.raw_text or ""
        elif isinstance(data, dict) and "rawText" in data:
            raw_text = data["rawText"]
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            borrower_name, lender_name, loan_amount, 
            maturity_date, interest_rate, covenants
        )
        
        # Get document ID
        doc_id = ""
        if hasattr(doc, 'meta') and hasattr(doc.meta, 'identifier'):
            doc_id = doc.meta.identifier or ""
        
        return ExtractedLoanAgreement(
            borrower_name=borrower_name,
            lender_name=lender_name,
            loan_amount=loan_amount,
            currency=currency,
            maturity_date=maturity_date,
            interest_rate=interest_rate,
            covenants=covenants,
            raw_text=raw_text,
            extraction_confidence=confidence,
            document_id=doc_id,
        )
    
    def _object_to_dict(self, obj) -> Dict[str, Any]:
        """Convert Affinda response object to dictionary."""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    if hasattr(value, '__dict__'):
                        result[key] = self._object_to_dict(value)
                    elif isinstance(value, list):
                        result[key] = [
                            self._object_to_dict(v) if hasattr(v, '__dict__') else v
                            for v in value
                        ]
                    else:
                        result[key] = value
            return result
        return obj
    
    def _extract_field(
        self, 
        data: Dict[str, Any], 
        field_names: List[str], 
        default: str
    ) -> str:
        """
        Extract field value trying multiple possible field names.
        
        Handles both direct values and nested {parsed: ..., raw: ...} structures.
        """
        for name in field_names:
            value = data.get(name)
            if value is not None:
                # Handle nested structure
                if isinstance(value, dict):
                    return str(value.get("parsed") or value.get("raw") or default)
                if value:
                    return str(value)
        return default
    
    def _extract_numeric_field(
        self, 
        data: Dict[str, Any], 
        field_names: List[str], 
        default: float
    ) -> float:
        """Extract numeric field value with proper parsing."""
        for name in field_names:
            value = data.get(name)
            if value is not None:
                # Handle nested structure
                if isinstance(value, dict):
                    value = value.get("parsed") or value.get("raw")
                
                if value is not None:
                    try:
                        # Clean string values
                        if isinstance(value, str):
                            value = (
                                value.replace("$", "")
                                .replace(",", "")
                                .replace(" ", "")
                                .replace("€", "")
                                .replace("£", "")
                            )
                        return float(value)
                    except (ValueError, TypeError):
                        continue
        return default
    
    def _extract_covenants(self, data: Dict[str, Any]) -> List[ExtractedCovenant]:
        """
        Extract financial covenants from parsed document.
        
        Looks for covenant data in various possible field structures.
        """
        covenants = []
        
        # Try different field names for covenants
        covenant_fields = [
            "financialCovenants", "financial_covenants", "covenants",
            "terms", "conditions", "obligations"
        ]
        
        for field_name in covenant_fields:
            covenant_data = data.get(field_name, [])
            
            if isinstance(covenant_data, list):
                for item in covenant_data:
                    if isinstance(item, dict):
                        covenant = ExtractedCovenant(
                            covenant_type=self._extract_field(
                                item, 
                                ["covenantType", "type", "name", "metric"],
                                "Unknown"
                            ),
                            threshold_value=self._extract_field(
                                item,
                                ["thresholdValue", "threshold", "value", "limit"],
                                ""
                            ),
                            measurement_frequency=self._extract_field(
                                item,
                                ["measurementFrequency", "frequency", "period"],
                                "Quarterly"
                            ),
                            raw_text=item.get("rawText", ""),
                            confidence=float(item.get("confidence", 0.0)),
                        )
                        covenants.append(covenant)
                
                if covenants:
                    break  # Found covenants, stop searching
        
        # Also check for tables that might contain covenant data
        tables = data.get("tables", [])
        for table in tables:
            if self._is_covenant_table(table):
                table_covenants = self._extract_covenants_from_table(table)
                covenants.extend(table_covenants)
        
        return covenants
    
    def _is_covenant_table(self, table: Dict[str, Any]) -> bool:
        """Check if a table likely contains covenant information."""
        headers = table.get("headers", [])
        header_text = " ".join(str(h).lower() for h in headers)
        
        covenant_keywords = [
            "covenant", "ratio", "threshold", "metric",
            "minimum", "maximum", "limit", "requirement"
        ]
        
        return any(kw in header_text for kw in covenant_keywords)
    
    def _extract_covenants_from_table(
        self, 
        table: Dict[str, Any]
    ) -> List[ExtractedCovenant]:
        """Extract covenant data from an identified covenant table."""
        covenants = []
        rows = table.get("rows", [])
        
        for row in rows:
            if len(row) >= 2:
                covenant = ExtractedCovenant(
                    covenant_type=str(row[0]) if row[0] else "Unknown",
                    threshold_value=str(row[1]) if len(row) > 1 else "",
                    measurement_frequency=(
                        str(row[2]) if len(row) > 2 else "Quarterly"
                    ),
                )
                covenants.append(covenant)
        
        return covenants
    
    def _calculate_confidence(
        self,
        borrower: str,
        lender: str,
        amount: float,
        maturity: str,
        rate: str,
        covenants: List[ExtractedCovenant],
    ) -> float:
        """
        Calculate overall extraction confidence score.
        
        Based on how many critical fields were successfully extracted.
        """
        fields_found = 0
        total_fields = 6
        
        if borrower and borrower != "Unknown Borrower":
            fields_found += 1
        if lender and lender != "Unknown Lender":
            fields_found += 1
        if amount > 0:
            fields_found += 1
        if maturity:
            fields_found += 1
        if rate:
            fields_found += 1
        if covenants:
            fields_found += 1
        
        return round(fields_found / total_fields, 2)
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a previously parsed document by ID.
        
        Args:
            document_id: Affinda document identifier
            
        Returns:
            Document data or None if not found
        """
        if not self.available:
            return None
        
        try:
            client = self._get_client()
            doc = client.get_document(identifier=document_id)
            return self._object_to_dict(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {e}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from Affinda.
        
        Args:
            document_id: Affinda document identifier
            
        Returns:
            True if deleted successfully
        """
        if not self.available:
            return False
        
        try:
            client = self._get_client()
            client.delete_document(identifier=document_id)
            logger.info(f"Deleted document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False


# Singleton instance
_affinda_client: Optional[AffindaClient] = None


def get_affinda_client() -> AffindaClient:
    """Get or create Affinda client singleton."""
    global _affinda_client
    if _affinda_client is None:
        _affinda_client = AffindaClient()
    return _affinda_client


async def parse_loan_document(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a loan document.
    
    Returns a dictionary suitable for API responses.
    
    Args:
        file_path: Path to the document
        
    Returns:
        Dictionary with parsed data or error info
    """
    client = get_affinda_client()
    
    if not client.available:
        return {
            "success": False,
            "error": "Affinda not configured",
            "source": "Affinda",
        }
    
    try:
        result = client.parse_document(file_path)
        
        return {
            "success": True,
            "source": "Affinda",
            "version": "V8",
            "document_id": result.document_id,
            "extraction_confidence": result.extraction_confidence,
            "data": {
                "borrower_name": result.borrower_name,
                "lender_name": result.lender_name,
                "loan_amount": result.loan_amount,
                "currency": result.currency,
                "maturity_date": result.maturity_date,
                "interest_rate": result.interest_rate,
                "covenants": [
                    {
                        "type": c.covenant_type,
                        "threshold": c.threshold_value,
                        "frequency": c.measurement_frequency,
                    }
                    for c in result.covenants
                ],
            },
            "extracted_at": result.extracted_at,
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "source": "Affinda",
        }
    except Exception as e:
        logger.error(f"Document parsing failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "source": "Affinda",
        }
