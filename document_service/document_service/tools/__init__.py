"""
Tools for Document Service agents.

V8 Architecture: Affinda is the primary parser.
"""

from document_service.document_service.tools.pdf_parser import (
    parse_pdf_document,
    extract_text_from_pages,
)
from document_service.document_service.tools.document_ai import (
    process_with_document_ai,
)
from document_service.document_service.tools.affinda_parser import (
    parse_with_affinda,
    parse_document_bytes_with_affinda,
    get_extraction_summary,
)
from document_service.document_service.tools.covenant_parser import (
    extract_financial_covenants,
    extract_esg_covenants,
    classify_covenant_type,
)
from document_service.document_service.tools.entity_parser import (
    extract_parties,
    extract_financial_terms,
    extract_key_dates,
)
from document_service.document_service.tools.validator import (
    validate_document_completeness,
    check_cross_references,
    validate_covenant_definitions,
)
from document_service.document_service.tools.lexnlp_tools import (
    extract_money_amounts,
    extract_dates,
    extract_percentages,
    extract_definitions,
    extract_covenant_clauses,
    analyze_document,
)

__all__ = [
    # V8 - Primary parser (Affinda)
    "parse_with_affinda",
    "parse_document_bytes_with_affinda",
    "get_extraction_summary",
    # Legacy parsers
    "parse_pdf_document",
    "extract_text_from_pages",
    "process_with_document_ai",
    # Covenant extraction
    "extract_financial_covenants",
    "extract_esg_covenants",
    "classify_covenant_type",
    # Entity extraction
    "extract_parties",
    "extract_financial_terms",
    "extract_key_dates",
    # Validation
    "validate_document_completeness",
    "check_cross_references",
    "validate_covenant_definitions",
    # LexNLP tools
    "extract_money_amounts",
    "extract_dates",
    "extract_percentages",
    "extract_definitions",
    "extract_covenant_clauses",
    "analyze_document",
]
