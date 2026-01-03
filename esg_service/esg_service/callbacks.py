"""
Callbacks for ESG Service agents.
"""

import logging
from datetime import datetime
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

logger = logging.getLogger(__name__)


async def post_esg_callback(
    callback_context: CallbackContext,
) -> Optional[LlmResponse]:
    """Callback executed after ESG analysis completes."""
    logger.info("Post-ESG callback triggered")
    
    try:
        state = callback_context.state
        
        esg_results = {
            "loan_id": state.get("loan_id", ""),
            "analysis_timestamp": datetime.now().isoformat(),
            "kpi_tracking": state.get("kpi_tracking", {}),
            "spt_validation": state.get("spt_validation", {}),
            "esg_ratings": state.get("esg_ratings", {}),
            "greenwashing_analysis": state.get("greenwashing_analysis", {}),
        }
        
        # Determine overall ESG status
        greenwashing_risk = state.get("greenwashing_analysis", {}).get("risk_level", "LOW")
        spt_achieved = state.get("spt_validation", {}).get("achieved", True)
        kpis_on_track = state.get("kpi_tracking", {}).get("on_track_count", 0)
        total_kpis = state.get("kpi_tracking", {}).get("total_kpis", 0)
        
        if greenwashing_risk == "HIGH":
            overall_status = "CRITICAL"
        elif not spt_achieved or greenwashing_risk == "MEDIUM":
            overall_status = "WARNING"
        elif total_kpis > 0 and kpis_on_track < total_kpis:
            overall_status = "ATTENTION"
        else:
            overall_status = "COMPLIANT"
        
        esg_results["overall_status"] = overall_status
        esg_results["summary"] = {
            "greenwashing_risk": greenwashing_risk,
            "spt_achieved": spt_achieved,
            "kpis_on_track": kpis_on_track,
            "total_kpis": total_kpis,
        }
        
        state["esg_results"] = esg_results
        
        logger.info(f"ESG analysis complete: {overall_status}")
        
    except Exception as e:
        logger.error(f"Post-ESG callback error: {e}")
        callback_context.state["esg_error"] = str(e)
    
    return None
