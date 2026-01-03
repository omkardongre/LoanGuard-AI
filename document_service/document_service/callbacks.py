"""
Callbacks for Document Service agents.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

logger = logging.getLogger(__name__)


async def post_extraction_callback(
    callback_context: CallbackContext,
) -> Optional[LlmResponse]:
    """
    Callback executed after document extraction completes.
    
    Aggregates results from all sub-agents and prepares final output.
    """
    logger.info("Post-extraction callback triggered")
    
    try:
        # Get session state
        state = callback_context.state
        
        # Aggregate results from sub-agents
        extraction_results = {
            "document_id": state.get("document_id", ""),
            "parsed_content": state.get("parsed_content", {}),
            "covenants": state.get("extracted_covenants", []),
            "entities": state.get("extracted_entities", {}),
            "validation_results": state.get("validation_results", {}),
            "extraction_timestamp": datetime.now().isoformat(),
            "status": "completed",
        }
        
        # Calculate extraction statistics
        covenant_count = len(extraction_results.get("covenants", []))
        entity_count = len(extraction_results.get("entities", {}))
        
        extraction_results["statistics"] = {
            "covenant_count": covenant_count,
            "entity_count": entity_count,
            "sections_parsed": len(extraction_results.get("parsed_content", {}).get("sections", [])),
        }
        
        # Store aggregated results in state
        state["extraction_results"] = extraction_results
        
        logger.info(
            f"Extraction complete: {covenant_count} covenants, "
            f"{entity_count} entities extracted"
        )
        
        # Log validation issues if any
        validation = extraction_results.get("validation_results", {})
        if validation.get("issues"):
            for issue in validation["issues"]:
                severity = issue.get("severity", "INFO")
                message = issue.get("message", "Unknown issue")
                logger.warning(f"Validation {severity}: {message}")
        
    except Exception as e:
        logger.error(f"Post-extraction callback error: {e}")
        callback_context.state["extraction_error"] = str(e)
    
    return None


async def log_agent_step(
    callback_context: CallbackContext,
) -> Optional[LlmResponse]:
    """
    Generic logging callback for agent steps.
    """
    agent_name = callback_context.agent_name if hasattr(callback_context, 'agent_name') else "Unknown"
    logger.info(f"Agent step completed: {agent_name}")
    return None
