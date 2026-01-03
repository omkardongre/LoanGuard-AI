"""
Sub-agents for Document Service.
"""

from document_service.document_service.sub_agents.document_parser_agent import document_parser_agent
from document_service.document_service.sub_agents.covenant_extractor_agent import covenant_extractor_agent
from document_service.document_service.sub_agents.entity_extractor_agent import entity_extractor_agent
from document_service.document_service.sub_agents.document_validator_agent import document_validator_agent

__all__ = [
    "document_parser_agent",
    "covenant_extractor_agent",
    "entity_extractor_agent",
    "document_validator_agent",
]
