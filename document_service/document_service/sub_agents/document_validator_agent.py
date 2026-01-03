"""
Document Validator Agent - Validates document completeness and consistency.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from document_service.document_service.config import MODEL
from document_service.document_service.prompts import DOCUMENT_VALIDATOR_PROMPT
from document_service.document_service.tools.validator import (
    validate_document_completeness,
    check_cross_references,
    validate_covenant_definitions,
)

logger = logging.getLogger(__name__)

# Create validation tools
completeness_tool = FunctionTool(func=validate_document_completeness)
cross_ref_tool = FunctionTool(func=check_cross_references)
covenant_validation_tool = FunctionTool(func=validate_covenant_definitions)

document_validator_agent = Agent(
    name="DocumentValidatorAgent",
    model=MODEL,
    description="Validates document completeness and identifies inconsistencies",
    instruction=DOCUMENT_VALIDATOR_PROMPT,
    tools=[completeness_tool, cross_ref_tool, covenant_validation_tool],
)
