"""
Callbacks for Alert Service agents.
"""

import logging
from datetime import datetime
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

logger = logging.getLogger(__name__)


async def post_alert_callback(
    callback_context: CallbackContext,
) -> Optional[LlmResponse]:
    """Callback executed after alert processing completes."""
    logger.info("Post-alert callback triggered")
    
    try:
        state = callback_context.state
        
        alert_results = {
            "loan_id": state.get("loan_id", ""),
            "timestamp": datetime.now().isoformat(),
            "alerts_generated": state.get("alerts_generated", []),
            "report_generated": state.get("report_generated", False),
            "notifications_sent": state.get("notifications_sent", []),
        }
        
        alert_count = len(alert_results.get("alerts_generated", []))
        notification_count = len(alert_results.get("notifications_sent", []))
        
        alert_results["summary"] = {
            "alert_count": alert_count,
            "notification_count": notification_count,
            "report_generated": alert_results["report_generated"],
        }
        
        state["alert_results"] = alert_results
        
        logger.info(f"Alert processing complete: {alert_count} alerts, {notification_count} notifications")
        
    except Exception as e:
        logger.error(f"Post-alert callback error: {e}")
        callback_context.state["alert_error"] = str(e)
    
    return None
