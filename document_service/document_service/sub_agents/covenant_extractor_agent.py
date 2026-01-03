"""
Covenant Extractor Agent - Extracts covenant definitions from loan documents.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from document_service.document_service.config import MODEL
from document_service.document_service.prompts import COVENANT_EXTRACTOR_PROMPT
from document_service.document_service.tools.covenant_parser import (
    extract_financial_covenants,
    extract_esg_covenants,
    classify_covenant_type,
)

logger = logging.getLogger(__name__)

# Create tools for covenant extraction
financial_covenant_tool = FunctionTool(func=extract_financial_covenants)
esg_covenant_tool = FunctionTool(func=extract_esg_covenants)
classify_tool = FunctionTool(func=classify_covenant_type)

covenant_extractor_agent = Agent(
    name="CovenantExtractorAgent",
    model=MODEL,
    description="Extracts and classifies covenant definitions from loan documents",
    instruction=COVENANT_EXTRACTOR_PROMPT,
    tools=[financial_covenant_tool, esg_covenant_tool, classify_tool],
)
