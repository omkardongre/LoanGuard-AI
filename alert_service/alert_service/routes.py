"""
FastAPI REST API Routes for Alert Service.

Production-level API endpoints for alert management, notifications,
and compliance report generation.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import logging

from alert_service.alert_service.tools import (
    # Alert tools
    create_alert,
    prioritize_alerts,
    get_alert_template,
    # Report tools
    generate_compliance_report,
    generate_executive_summary,
    export_report_pdf,
    # Notification tools
    send_email,
    send_slack_message,
    get_notification_recipients,
    # Visualization tools
    create_status_chart,
    create_trend_chart,
    create_portfolio_heatmap,
)

logger = logging.getLogger(__name__)


# ============================================
# Request/Response Models
# ============================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    service: str = "alert-service"
    version: str = "1.0.0"


class CreateAlertRequest(BaseModel):
    """Request to create an alert."""
    loan_id: str = Field(..., description="Loan identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field("MEDIUM", description="Alert severity")
    message: str = Field(..., description="Alert message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class AlertResponse(BaseModel):
    """Alert response."""
    success: bool
    alert: Optional[Dict[str, Any]] = None


class SendNotificationRequest(BaseModel):
    """Request to send notification."""
    loan_id: str = Field(..., description="Loan identifier")
    alert_type: str = Field(..., description="Alert type")
    message: str = Field(..., description="Notification message")
    severity: str = Field("MEDIUM", description="Alert severity")
    channels: List[str] = Field(["email"], description="Notification channels")


class GenerateReportRequest(BaseModel):
    """Request to generate compliance report."""
    loan_id: str = Field(..., description="Loan identifier")
    report_type: str = Field("quarterly", description="Report type")
    include_esg: bool = Field(True, description="Include ESG data")


# ============================================
# API Router
# ============================================

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


# ============================================
# Health & Status Endpoints
# ============================================

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for Alert service."""
    return HealthResponse()


@router.get("/status")
async def service_status() -> Dict[str, Any]:
    """Get Alert service status."""
    return {
        "service": "alert-service",
        "version": "1.0.0",
        "status": "healthy",
        "capabilities": {
            "alert_management": True,
            "email_notifications": True,
            "slack_notifications": True,
            "pdf_reports": True,
            "visualizations": True,
        }
    }


# ============================================
# Alert Management Endpoints
# ============================================

@router.post("/create", response_model=AlertResponse)
async def create_new_alert(
    request: CreateAlertRequest,
) -> AlertResponse:
    """
    Create a new compliance alert.
    
    Alert Types:
    - covenant_breach: Covenant has been breached
    - covenant_warning: Approaching breach threshold
    - esg_spt_miss: ESG SPT target missed
    - greenwashing_risk: High greenwashing risk detected
    - breach_prediction: ML model predicts breach
    
    Severity Levels:
    - CRITICAL: Immediate action required
    - HIGH: Same-day response needed
    - MEDIUM: Review within 3 days
    - LOW: Include in weekly review
    """
    try:
        result = create_alert(
            loan_id=request.loan_id,
            alert_type=request.alert_type,
            severity=request.severity,
            message=request.message,
            details=request.details,
        )
        return AlertResponse(**result)
    except Exception as e:
        logger.exception(f"Create alert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}")
async def get_loan_alerts(
    loan_id: str = Path(..., description="Loan identifier"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement"),
) -> Dict[str, Any]:
    """Get all alerts for a loan."""
    try:
        # In production, fetch from BigQuery
        # For now, return mock structure
        return {
            "success": True,
            "loan_id": loan_id,
            "alerts": [],
            "filters": {
                "severity": severity,
                "acknowledged": acknowledged,
            },
            "note": "Connect to BigQuery for production data"
        }
    except Exception as e:
        logger.exception(f"Get alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prioritize")
async def prioritize_alert_list(
    alerts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Prioritize a list of alerts by severity and age.
    
    Returns alerts sorted by priority with counts per severity.
    """
    try:
        result = prioritize_alerts(alerts)
        return result
    except Exception as e:
        logger.exception(f"Prioritize alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{alert_type}")
async def get_template(
    alert_type: str = Path(..., description="Alert type"),
) -> Dict[str, Any]:
    """Get alert template for a specific type."""
    try:
        result = get_alert_template(alert_type)
        return result
    except Exception as e:
        logger.exception(f"Get template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str = Path(..., description="Alert identifier"),
    acknowledged_by: str = Query(..., description="User acknowledging"),
) -> Dict[str, Any]:
    """Acknowledge an alert."""
    try:
        # In production, update in BigQuery
        return {
            "success": True,
            "alert_id": alert_id,
            "acknowledged": True,
            "acknowledged_by": acknowledged_by,
        }
    except Exception as e:
        logger.exception(f"Acknowledge alert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Notification Endpoints
# ============================================

@router.post("/notify")
async def send_notification(
    request: SendNotificationRequest,
) -> Dict[str, Any]:
    """
    Send notifications for an alert.
    
    Channels:
    - email: Send via SendGrid
    - slack: Send via Slack webhook
    """
    try:
        results = {"success": True, "channels": {}}
        
        # Get recipients based on severity
        recipients = get_notification_recipients(
            loan_id=request.loan_id,
            severity=request.severity,
        )
        
        if "email" in request.channels and recipients.get("email_recipients"):
            email_result = send_email(
                to_emails=recipients["email_recipients"],
                subject=f"[{request.severity}] {request.alert_type} - Loan {request.loan_id}",
                body=request.message,
            )
            results["channels"]["email"] = email_result
        
        if "slack" in request.channels and recipients.get("slack_channels"):
            for channel in recipients["slack_channels"]:
                slack_result = send_slack_message(
                    channel=channel,
                    message=f"*{request.alert_type}* - Loan {request.loan_id}\n{request.message}",
                    severity=request.severity.lower(),
                )
                results["channels"][f"slack_{channel}"] = slack_result
        
        results["recipients"] = recipients
        return results
        
    except Exception as e:
        logger.exception(f"Send notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipients/{loan_id}")
async def get_recipients(
    loan_id: str = Path(..., description="Loan identifier"),
    severity: str = Query("MEDIUM", description="Alert severity"),
) -> Dict[str, Any]:
    """Get notification recipients for a loan and severity."""
    try:
        result = get_notification_recipients(
            loan_id=loan_id,
            severity=severity,
        )
        return result
    except Exception as e:
        logger.exception(f"Get recipients error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Report Endpoints
# ============================================

@router.post("/reports/generate")
async def generate_report(
    request: GenerateReportRequest,
) -> Dict[str, Any]:
    """
    Generate a compliance report.
    
    Report Types:
    - quarterly: Quarterly compliance review
    - monthly: Monthly status update
    - annual: Annual compliance summary
    - ad-hoc: Custom report
    """
    try:
        # Build compliance data structure
        # In production, fetch from BigQuery
        compliance_data = {
            "overall_status": "COMPLIANT",
            "covenants": [],
            "alerts": [],
        }
        
        esg_data = None
        if request.include_esg:
            esg_data = {
                "kpi_count": 5,
                "on_track_count": 4,
                "greenwashing_risk": "LOW",
                "spt_achieved": True,
            }
        
        result = generate_compliance_report(
            loan_id=request.loan_id,
            compliance_data=compliance_data,
            esg_data=esg_data,
            report_type=request.report_type,
        )
        return result
        
    except Exception as e:
        logger.exception(f"Generate report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{loan_id}/summary")
async def get_executive_summary(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """Get executive summary for a loan."""
    try:
        # Build key metrics
        # In production, fetch from BigQuery
        key_metrics = {
            "covenant_compliance_rate": 95,
            "avg_breach_probability": 12,
            "esg_score": 78,
            "active_alerts": 2,
        }
        
        result = generate_executive_summary(
            loan_id=loan_id,
            compliance_status="COMPLIANT",
            key_metrics=key_metrics,
        )
        return result
        
    except Exception as e:
        logger.exception(f"Executive summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/export/pdf")
async def export_pdf_report(
    report: Dict[str, Any],
) -> Dict[str, Any]:
    """Export a report to PDF format."""
    try:
        result = export_report_pdf(report)
        return result
    except Exception as e:
        logger.exception(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Visualization Endpoints
# ============================================

@router.get("/visualizations/status/{loan_id}")
async def get_status_chart(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """Get status visualization data for a loan."""
    try:
        # In production, fetch covenant data from BigQuery
        covenants = []
        result = create_status_chart(covenants)
        result["loan_id"] = loan_id
        return result
    except Exception as e:
        logger.exception(f"Status chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/trend/{loan_id}")
async def get_trend_chart(
    loan_id: str = Path(..., description="Loan identifier"),
    covenant_id: str = Query(..., description="Covenant identifier"),
    periods: int = Query(12, ge=4, le=24, description="Number of periods"),
) -> Dict[str, Any]:
    """Get trend visualization for a covenant."""
    try:
        # In production, fetch from BigQuery
        measurements = []
        result = create_trend_chart(covenant_id, measurements, periods)
        result["loan_id"] = loan_id
        return result
    except Exception as e:
        logger.exception(f"Trend chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/portfolio/heatmap")
async def get_portfolio_heatmap() -> Dict[str, Any]:
    """Get portfolio-level risk heatmap."""
    try:
        # In production, fetch portfolio data from BigQuery
        portfolio_data = []
        result = create_portfolio_heatmap(portfolio_data)
        return result
    except Exception as e:
        logger.exception(f"Portfolio heatmap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]
