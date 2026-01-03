"""
Callbacks for Covenant Service agents.
"""

import logging
from datetime import datetime
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

logger = logging.getLogger(__name__)


async def post_compliance_callback(
    callback_context: CallbackContext,
) -> Optional[LlmResponse]:
    """
    Callback executed after compliance check completes.
    
    Aggregates results and determines overall loan status.
    """
    logger.info("Post-compliance callback triggered")
    
    try:
        state = callback_context.state
        
        # Aggregate results
        compliance_results = {
            "loan_id": state.get("loan_id", ""),
            "check_timestamp": datetime.now().isoformat(),
            "financial_data": state.get("financial_data", {}),
            "calculated_ratios": state.get("calculated_ratios", {}),
            "compliance_status": state.get("compliance_status", {}),
            "breach_prediction": state.get("breach_prediction", {}),
        }
        
        # Determine overall status
        statuses = []
        for covenant, status in compliance_results.get("compliance_status", {}).items():
            if isinstance(status, dict):
                statuses.append(status.get("status", "unknown"))
        
        if "RED" in statuses:
            overall_status = "BREACH"
        elif "AMBER" in statuses:
            overall_status = "WARNING"
        elif statuses:
            overall_status = "COMPLIANT"
        else:
            overall_status = "UNKNOWN"
        
        compliance_results["overall_status"] = overall_status
        
        # Calculate summary stats
        breach_prob = state.get("breach_prediction", {}).get("probability", 0)
        compliance_results["summary"] = {
            "total_covenants": len(statuses),
            "compliant_count": statuses.count("GREEN"),
            "warning_count": statuses.count("AMBER"),
            "breach_count": statuses.count("RED"),
            "predicted_breach_probability": breach_prob,
        }
        
        state["compliance_results"] = compliance_results
        
        logger.info(
            f"Compliance check complete: {overall_status}, "
            f"Breach probability: {breach_prob:.1%}"
        )
        
    except Exception as e:
        logger.error(f"Post-compliance callback error: {e}")
        callback_context.state["compliance_error"] = str(e)
    
    return None
