"""
Entity Extractor Agent - Extracts key entities from loan documents.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from document_service.document_service.config import MODEL
from document_service.document_service.prompts import ENTITY_EXTRACTOR_PROMPT
from document_service.document_service.tools.entity_parser import (
    extract_parties,
    extract_financial_terms,
    extract_key_dates,
)

logger = logging.getLogger(__name__)

# Create tools for entity extraction
parties_tool = FunctionTool(func=extract_parties)
financial_terms_tool = FunctionTool(func=extract_financial_terms)
dates_tool = FunctionTool(func=extract_key_dates)

entity_extractor_agent = Agent(
    name="EntityExtractorAgent",
    model=MODEL,
    description="Extracts key entities like parties, dates, and amounts from loan documents",
    instruction=ENTITY_EXTRACTOR_PROMPT,
    tools=[parties_tool, financial_terms_tool, dates_tool],
)
