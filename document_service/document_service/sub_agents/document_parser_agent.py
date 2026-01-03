"""
Document Parser Agent - Parses loan documents and extracts structured content.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from document_service.document_service.config import MODEL
from document_service.document_service.prompts import DOCUMENT_PARSER_PROMPT
from document_service.document_service.tools.pdf_parser import parse_pdf_document
from document_service.document_service.tools.document_ai import process_with_document_ai

logger = logging.getLogger(__name__)

# Create tools for the parser agent
pdf_parser_tool = FunctionTool(func=parse_pdf_document)
document_ai_tool = FunctionTool(func=process_with_document_ai)

document_parser_agent = Agent(
    name="DocumentParserAgent",
    model=MODEL,
    description="Parses loan agreement documents and extracts structured text content",
    instruction=DOCUMENT_PARSER_PROMPT,
    tools=[pdf_parser_tool, document_ai_tool],
)
