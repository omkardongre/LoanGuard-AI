"""
FastAPI routes for Voice Service.

Provides API endpoints for triggering voice calls and checking call status.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from voice_service.voice_service.agent import VoiceAlertAgent
from voice_service.voice_service.tools.phone_call import get_call_status

logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Service", version="1.0.0")

# Initialize voice agent
voice_agent = VoiceAlertAgent()


# Request models
class CovenantBreachCallRequest(BaseModel):
    loan_id: str
    breach_type: str
    severity: str
    phone_number: str
    threshold: Optional[str] = None
    actual_value: Optional[str] = None


class BorrowerOutreachCallRequest(BaseModel):
    loan_id: str
    borrower_name: str
    phone_number: str
    warning_indicators: List[str]


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "voice_service"}


@app.post("/api/voice/covenant-breach")
async def trigger_covenant_breach_call(request: CovenantBreachCallRequest):
    """
    Trigger a voice call to alert about a covenant breach.
    
    Args:
        request: Covenant breach call request with loan details
        
    Returns:
        Call result with status and conversation_id
    """
    try:
        result = await voice_agent.make_covenant_breach_call(
            loan_id=request.loan_id,
            breach_type=request.breach_type,
            severity=request.severity,
            phone_number=request.phone_number,
            threshold=request.threshold,
            actual_value=request.actual_value
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering covenant breach call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/borrower-outreach")
async def trigger_borrower_outreach_call(request: BorrowerOutreachCallRequest):
    """
    Trigger a proactive outreach call to a borrower.
    
    Args:
        request: Borrower outreach call request
        
    Returns:
        Call result with status and conversation_id
    """
    try:
        result = await voice_agent.make_borrower_outreach_call(
            loan_id=request.loan_id,
            borrower_name=request.borrower_name,
            phone_number=request.phone_number,
            warning_indicators=request.warning_indicators
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering borrower outreach call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/status/{conversation_id}")
async def get_voice_call_status(conversation_id: str):
    """
    Get the status of an ongoing or completed voice call.
    
    Args:
        conversation_id: ElevenLabs conversation ID
        
    Returns:
        Call status and transcript (if available)
    """
    try:
        result = await get_call_status(conversation_id)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
