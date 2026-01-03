"""
Main agent definition for Document Service.
"""

import logging
from google.adk.agents import SequentialAgent

from document_service.document_service.config import MODEL
from document_service.document_service.sub_agents.document_parser_agent import document_parser_agent
from document_service.document_service.sub_agents.covenant_extractor_agent import covenant_extractor_agent
from document_service.document_service.sub_agents.entity_extractor_agent import entity_extractor_agent
from document_service.document_service.sub_agents.document_validator_agent import document_validator_agent
from document_service.document_service.callbacks import post_extraction_callback

logger = logging.getLogger(__name__)

# Create the root document agent as a sequential pipeline
document_agent = SequentialAgent(
    name="DocumentAgent",
    description="Sequential agent for parsing loan documents and extracting covenants",
    sub_agents=[
        document_parser_agent,
        covenant_extractor_agent,
        entity_extractor_agent,
        document_validator_agent,
    ],
    after_agent_callback=post_extraction_callback,
)

root_agent = document_agent
