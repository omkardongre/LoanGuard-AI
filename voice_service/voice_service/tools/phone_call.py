"""
Phone call tool for LoanGuard AI voice alerts using ElevenLabs Conversational AI.

Implements outbound voice calls via ElevenLabs Twilio integration for:
- Covenant breach alerts
- Borrower outreach
- Payment reminders
- Risk committee briefings
"""
import os
import json
import time
import asyncio
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying with exponential backoff."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay) if asyncio.iscoroutinefunction(func) else time.sleep(delay)
        return wrapper
    return decorator


def validate_us_phone_number(phone_number: str) -> Dict[str, Any]:
    """
    Validate and normalize US phone number to E.164 format.
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Dict with 'valid', 'error', and 'normalized' fields
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\\D', '', phone_number)
    
    # Check for valid US number patterns
    if len(digits_only) == 10:
        # Add +1 prefix for 10-digit numbers
        normalized = f"+1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        # Already has country code
        normalized = f"+{digits_only}"
    else:
        return {
            "valid": False,
            "error": f"Invalid US phone number format: {phone_number}. Expected 10 or 11 digits.",
            "normalized": None
        }
    
    # Basic US number validation (not toll-free, not premium)
    area_code = digits_only[-10:-7]
    if area_code.startswith('0') or area_code.startswith('1'):
        return {
            "valid": False,
            "error": f"Invalid area code: {area_code}. Area codes cannot start with 0 or 1.",
            "normalized": None
        }
    
    return {
        "valid": True,
        "error": None,
        "normalized": normalized
    }


def init_elevenlabs_client():
    """
    Initialize and return the ElevenLabs client and conversational AI subclient.
    
    Returns:
        Tuple of (client, convai) or (None, None) if initialization fails
    """
    try:
        from elevenlabs import ElevenLabs
        from voice_service.voice_service.config import ELEVENLABS_API_KEY
        
        if not ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables.")
            
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        convai = client.conversational_ai
    
        return client, convai
    except ImportError:
        logger.error("ElevenLabs library not available. Please install: pip install elevenlabs")
        return None, None
    except Exception as e:
        logger.error(f"Failed to initialize ElevenLabs client: {e}")
        return None, None


async def make_call(
    to_number: str,
    system_prompt: str,
    first_message: str,
    poll_interval: float = 2.0
) -> Dict[str, Any]:
    """
    Place an outbound call via ElevenLabs Conversational AI → Twilio.
    
    Args:
        to_number: Phone number to call (E.164 format, e.g. +14155551234)
        system_prompt: System prompt for the AI agent
        first_message: First message the agent will say
        poll_interval: Seconds between status polls (default: 2.0)
        
    Returns:
        Dict with status, transcript, conversation_id, and debug_info
    """
    from voice_service.voice_service.config import (
        ELEVENLABS_API_KEY,
        ELEVENLABS_AGENT_ID,
        ELEVENLABS_PHONE_NUMBER_ID
    )
    
    result = {
        "status": "initializing",
        "transcript": [],
        "debug_info": [],
        "error": None,
        "conversation_id": None,
    }
    
    def add_debug(msg: str):
        result["debug_info"].append(msg)
        logger.info(msg)
    
    # Validate environment variables
    for var, val in [
        ("ELEVENLABS_API_KEY", ELEVENLABS_API_KEY),
        ("ELEVENLABS_AGENT_ID", ELEVENLABS_AGENT_ID),
        ("ELEVENLABS_PHONE_NUMBER_ID", ELEVENLABS_PHONE_NUMBER_ID),
    ]:
        if not val:
            err = f"{var} environment variable is not set"
            add_debug(f"ERROR: {err}")
            result.update(status="error", error=err)
            return result
    
    client, convai = init_elevenlabs_client()
    if not client or not convai:
        err = "Failed to initialize ElevenLabs client"
        add_debug(f"ERROR: {err}")
        result.update(status="error", error=err)
        return result
    
    # Initiate the call with retry logic
    add_debug(f"Initiating call → {to_number}")
    
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    async def _make_api_call():
        return convai.twilio.outbound_call(
            agent_id=ELEVENLABS_AGENT_ID,
            agent_phone_number_id=ELEVENLABS_PHONE_NUMBER_ID,
            to_number=to_number,
            conversation_initiation_client_data={
                "conversation_config_override": {
                    "agent": {
                        "prompt": {"prompt": system_prompt},
                        "first_message": first_message,
                    }
                }
            },
        )
    
    try:
        response = await _make_api_call()
    except Exception as exc:
        add_debug(f"Error initiating call after retries: {exc}")
        result.update(status="error", error=str(exc))
        return result
    
    conv_id = getattr(response, "conversation_id", None) or getattr(response, "callSid", None)
    if not conv_id:
        err = "Conversation ID missing in outbound_call response"
        add_debug(f"ERROR: {err}")
        result.update(status="error", error=err)
        return result
    
    result.update(status="initiated", conversation_id=conv_id)
    add_debug(f"Call started (conversation_id = {conv_id})")
    
    # Poll until call is finished (with timeout)
    terminal_statuses = {"done", "failed"}
    max_poll_duration = 600  # 10 minutes maximum
    start_time = time.time()
    
    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > max_poll_duration:
            err = f"Call polling timeout after {max_poll_duration}s"
            add_debug(f"ERROR: {err}")
            result.update(status="timeout", error=err)
            return result
        
        time.sleep(poll_interval)
        try:
            details = convai.conversations.get(conv_id)
            status = getattr(details, "status", "unknown")
            result["status"] = status
            add_debug(f"Polling status: {status} (elapsed: {int(elapsed)}s)")
            if status in terminal_statuses:
                break
        except Exception as exc:
            add_debug(f"Error polling: {exc}")
            result.update(status="error_polling", error=str(exc))
            return result
    
    # Extract transcript
    turns = (
        getattr(details, "transcript", None)
        or getattr(details, "turns", None)
        or []
    )
    formatted = []
    for t in turns:
        role = getattr(t, "role", "unknown")
        msg = (
            t.message if hasattr(t, "message") else
            getattr(t, "text", "unknown")
        )
        if hasattr(msg, "text"):  # ElevenLabs sometimes nests TextObject
            msg = msg.text
        formatted.append({"role": role, "message": msg})
    
    result["transcript"] = formatted
    return result


async def get_call_status(conversation_id: str) -> Dict[str, Any]:
    """
    Get the status of an ongoing or completed call.
    
    Args:
        conversation_id: ElevenLabs conversation ID
        
    Returns:
        Dict with status and transcript (if available)
    """
    client, convai = init_elevenlabs_client()
    if not client or not convai:
        return {"status": "error", "error": "Failed to initialize ElevenLabs client"}
    
    try:
        details = convai.conversations.get(conversation_id)
        status = getattr(details, "status", "unknown")
        
        # Extract transcript if available
        turns = getattr(details, "transcript", None) or getattr(details, "turns", None) or []
        formatted = []
        for t in turns:
            role = getattr(t, "role", "unknown")
            msg = t.message if hasattr(t, "message") else getattr(t, "text", "unknown")
            if hasattr(msg, "text"):
                msg = msg.text
            formatted.append({"role": role, "message": msg})
        
        return {
            "status": status,
            "conversation_id": conversation_id,
            "transcript": formatted,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        return {
            "status": "error",
            "conversation_id": conversation_id,
            "error": str(e)
        }
