"""
Tools for Document Service agents.
"""

from document_service.document_service.tools.pdf_parser import (
    parse_pdf_file,
    identify_sections,
)
from document_service.document_service.tools.document_ai import (
    process_document_with_ai,
    extract_text_from_document,
    extract_entities_from_document,
    extract_tables_from_document,
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
    validate_cross_references,
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
    "parse_pdf_file",
    "identify_sections",
    "process_document_with_ai",
    "extract_text_from_document",
    "extract_entities_from_document",
    "extract_tables_from_document",
    "extract_financial_covenants",
    "extract_esg_covenants",
    "classify_covenant_type",
    "extract_parties",
    "extract_financial_terms",
    "extract_key_dates",
    "validate_document_completeness",
    "validate_cross_references",
    "validate_covenant_definitions",
    "extract_money_amounts",
    "extract_dates",
    "extract_percentages",
    "extract_definitions",
    "extract_covenant_clauses",
    "analyze_document",
]
