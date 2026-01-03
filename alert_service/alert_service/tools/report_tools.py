"""
Report generation tools.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def generate_compliance_report(
    loan_id: str,
    compliance_data: Dict[str, Any],
    esg_data: Dict[str, Any] = None,
    report_type: str = "quarterly",
) -> Dict[str, Any]:
    """
    Generate a comprehensive compliance report.

    Args:
        loan_id: Loan identifier
        compliance_data: Covenant compliance data
        esg_data: ESG compliance data
        report_type: Type of report

    Returns:
        Generated report
    """
    report = {
        "report_id": f"RPT-{loan_id}-{datetime.now().strftime('%Y%m%d')}",
        "loan_id": loan_id,
        "report_type": report_type,
        "generated_at": datetime.now().isoformat(),
        "sections": {},
    }

    # Executive Summary
    overall_status = compliance_data.get("overall_status", "UNKNOWN")
    report["sections"]["executive_summary"] = {
        "overall_status": overall_status,
        "key_findings": [],
        "recommendations": [],
    }

    # Covenant Status
    covenants = compliance_data.get("covenants", [])
    report["sections"]["covenant_status"] = {
        "total_covenants": len(covenants),
        "compliant": sum(1 for c in covenants if c.get("status") == "GREEN"),
        "warning": sum(1 for c in covenants if c.get("status") == "AMBER"),
        "breach": sum(1 for c in covenants if c.get("status") == "RED"),
        "details": covenants,
    }

    # ESG Status
    if esg_data:
        report["sections"]["esg_status"] = {
            "kpi_count": esg_data.get("kpi_count", 0),
            "on_track": esg_data.get("on_track_count", 0),
            "greenwashing_risk": esg_data.get("greenwashing_risk", "LOW"),
            "spt_achieved": esg_data.get("spt_achieved", True),
        }

    # Alerts
    report["sections"]["alerts"] = {
        "active_alerts": compliance_data.get("alerts", []),
        "resolved_alerts": [],
    }

    logger.info(f"Generated compliance report {report['report_id']}")
    
    return {"success": True, "report": report}


def generate_executive_summary(
    loan_id: str,
    compliance_status: str,
    key_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate an executive summary.

    Args:
        loan_id: Loan identifier
        compliance_status: Overall compliance status
        key_metrics: Key metrics to include

    Returns:
        Executive summary
    """
    summary_text = f"""
EXECUTIVE SUMMARY - Loan {loan_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

OVERALL STATUS: {compliance_status}

KEY METRICS:
• Covenant Compliance: {key_metrics.get('covenant_compliance_rate', 'N/A')}%
• Average Breach Probability: {key_metrics.get('avg_breach_probability', 'N/A')}%
• ESG Score: {key_metrics.get('esg_score', 'N/A')}
• Active Alerts: {key_metrics.get('active_alerts', 0)}

RECOMMENDED ACTIONS:
"""
    
    recommendations = []
    if compliance_status == "BREACH":
        recommendations.append("• IMMEDIATE: Contact borrower regarding covenant breach")
        recommendations.append("• Review waiver or amendment options")
    elif compliance_status == "WARNING":
        recommendations.append("• Schedule borrower review within 30 days")
        recommendations.append("• Increase monitoring frequency")
    else:
        recommendations.append("• Continue standard monitoring")

    summary_text += "\n".join(recommendations)

    return {
        "success": True,
        "summary": {
            "loan_id": loan_id,
            "status": compliance_status,
            "text": summary_text,
            "recommendations": recommendations,
        },
    }


def export_report_pdf(
    report: Dict[str, Any],
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Export report to PDF format.

    Args:
        report: Report data
        output_path: Output file path

    Returns:
        Export result
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"Compliance Report - {report.get('loan_id', 'Unknown')}")

        # Generated date
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Generated: {report.get('generated_at', datetime.now().isoformat())}")

        # Status
        c.setFont("Helvetica-Bold", 12)
        y_pos = height - 100
        
        sections = report.get("sections", {})
        if "executive_summary" in sections:
            c.drawString(50, y_pos, f"Status: {sections['executive_summary'].get('overall_status', 'N/A')}")
            y_pos -= 30

        if "covenant_status" in sections:
            cov = sections["covenant_status"]
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Covenant Status")
            y_pos -= 20
            c.setFont("Helvetica", 10)
            c.drawString(70, y_pos, f"Compliant: {cov.get('compliant', 0)}")
            y_pos -= 15
            c.drawString(70, y_pos, f"Warning: {cov.get('warning', 0)}")
            y_pos -= 15
            c.drawString(70, y_pos, f"Breach: {cov.get('breach', 0)}")

        c.save()
        
        pdf_bytes = buffer.getvalue()
        buffer.close()

        if output_path:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            return {"success": True, "path": output_path, "size_bytes": len(pdf_bytes)}
        
        return {"success": True, "pdf_generated": True, "size_bytes": len(pdf_bytes)}

    except ImportError:
        logger.warning("reportlab not installed, PDF export unavailable")
        return {"success": False, "error": "reportlab not installed"}
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        return {"success": False, "error": str(e)}
