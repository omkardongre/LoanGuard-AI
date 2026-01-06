"""
PDF Report Generation for LoanGuard AI Platform.

Uses ReportLab to generate professional compliance reports.
V8 Architecture: P2 Feature - PDF Compliance Reports
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# Custom styles
COLORS = {
    "primary": colors.HexColor("#1e40af"),  # Blue
    "success": colors.HexColor("#15803d"),  # Green
    "warning": colors.HexColor("#ca8a04"),  # Amber
    "danger": colors.HexColor("#dc2626"),   # Red
    "muted": colors.HexColor("#6b7280"),    # Gray
    "background": colors.HexColor("#f8fafc"),
}


class ComplianceReportGenerator:
    """Generate PDF compliance reports for loans and portfolios."""

    def __init__(self, pagesize=A4):
        self.pagesize = pagesize
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            textColor=COLORS["primary"],
            spaceAfter=20,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=self.styles["Heading2"],
            fontSize=14,
            textColor=COLORS["primary"],
            spaceBefore=15,
            spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            name="SubSection",
            parent=self.styles["Heading3"],
            fontSize=11,
            textColor=COLORS["muted"],
            spaceBefore=10,
            spaceAfter=5,
        ))
        self.styles.add(ParagraphStyle(
            name="LGBodyText",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=14,
        ))
        self.styles.add(ParagraphStyle(
            name="LGSmallText",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=COLORS["muted"],
        ))

    def _get_status_color(self, status: str) -> colors.Color:
        """Get color for compliance status."""
        status_upper = status.upper() if status else ""
        if status_upper in ("GREEN", "COMPLIANT", "ON_TRACK", "LOW", "VERIFIED"):
            return COLORS["success"]
        elif status_upper in ("AMBER", "WARNING", "MEDIUM", "QUESTIONABLE"):
            return COLORS["warning"]
        elif status_upper in ("RED", "BREACH", "HIGH", "CRITICAL"):
            return COLORS["danger"]
        return COLORS["muted"]

    def _create_header(self, canvas, doc):
        """Add header to each page."""
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(COLORS["primary"])
        canvas.drawString(doc.leftMargin, doc.pagesize[1] - 30, "LoanGuard AI")
        
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLORS["muted"])
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.pagesize[1] - 30,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        canvas.restoreState()

    def _create_footer(self, canvas, doc):
        """Add footer with page numbers."""
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLORS["muted"])
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            20,
            f"Page {doc.page} | Confidential - LoanGuard AI Compliance Report"
        )
        canvas.restoreState()

    def _on_page(self, canvas, doc):
        """Handle page rendering."""
        self._create_header(canvas, doc)
        self._create_footer(canvas, doc)

    def generate_loan_report(
        self,
        loan_data: Dict[str, Any],
        covenants: List[Dict[str, Any]],
        predictions: Optional[Dict[str, Any]] = None,
        esg_data: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generate comprehensive loan compliance report.
        
        Args:
            loan_data: Loan details
            covenants: List of covenant data with measurements
            predictions: ML breach predictions
            esg_data: ESG compliance data
            
        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            topMargin=50,
            bottomMargin=40,
            leftMargin=40,
            rightMargin=40,
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Loan Compliance Report", self.styles["ReportTitle"]))
        story.append(Spacer(1, 10))
        
        # Loan Summary Section
        story.append(Paragraph("1. Loan Overview", self.styles["SectionTitle"]))
        
        loan_info = [
            ["Loan ID", loan_data.get("loan_id", "N/A")],
            ["Borrower", loan_data.get("borrower_name", "N/A")],
            ["Facility Amount", f"${loan_data.get('facility_amount', 0):,.0f}"],
            ["Currency", loan_data.get("currency", "USD")],
            ["Maturity Date", loan_data.get("maturity_date", "N/A")],
            ["Loan Type", loan_data.get("loan_type", "Term Loan")],
            ["Overall Status", loan_data.get("overall_status", "N/A")],
        ]
        
        loan_table = Table(loan_info, colWidths=[150, 300])
        loan_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), COLORS["background"]),
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(loan_table)
        story.append(Spacer(1, 20))
        
        # Covenant Compliance Section
        story.append(Paragraph("2. Covenant Compliance", self.styles["SectionTitle"]))
        
        if covenants:
            # Summary counts
            compliant = sum(1 for c in covenants if c.get("status", "").upper() == "GREEN")
            warning = sum(1 for c in covenants if c.get("status", "").upper() == "AMBER")
            breach = sum(1 for c in covenants if c.get("status", "").upper() == "RED")
            
            summary_text = f"Total Covenants: {len(covenants)} | Compliant: {compliant} | Warning: {warning} | Breach: {breach}"
            story.append(Paragraph(summary_text, self.styles["LGBodyText"]))
            story.append(Spacer(1, 10))
            
            # Covenant table
            cov_headers = ["Covenant", "Threshold", "Actual", "Buffer %", "Status"]
            cov_data = [cov_headers]
            
            for cov in covenants:
                status = cov.get("status", "N/A")
                cov_data.append([
                    cov.get("name", cov.get("covenant_type", "N/A")),
                    str(cov.get("threshold", "N/A")),
                    str(cov.get("actual", cov.get("actual_value", "N/A"))),
                    f"{cov.get('buffer_pct', 0):.1f}%",
                    status,
                ])
            
            cov_table = Table(cov_data, colWidths=[120, 80, 80, 70, 80])
            cov_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            
            # Color code status cells
            for i, cov in enumerate(covenants, 1):
                status = cov.get("status", "").upper()
                color = self._get_status_color(status)
                cov_table.setStyle(TableStyle([
                    ("TEXTCOLOR", (-1, i), (-1, i), color),
                    ("FONTNAME", (-1, i), (-1, i), "Helvetica-Bold"),
                ]))
            
            story.append(cov_table)
        else:
            story.append(Paragraph("No covenant data available.", self.styles["LGBodyText"]))
        
        story.append(Spacer(1, 20))
        
        # ML Predictions Section
        if predictions:
            story.append(Paragraph("3. ML Breach Predictions", self.styles["SectionTitle"]))
            
            prob = predictions.get("breach_probability", predictions.get("90_day_probability", 0))
            risk_level = "HIGH" if prob > 0.5 else "MEDIUM" if prob > 0.25 else "LOW"
            
            pred_info = [
                ["90-Day Breach Probability", f"{prob * 100:.1f}%"],
                ["Risk Level", risk_level],
                ["Model Confidence", f"{predictions.get('confidence', 0.85) * 100:.0f}%"],
            ]
            
            pred_table = Table(pred_info, colWidths=[180, 150])
            pred_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), COLORS["background"]),
                ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(pred_table)
            
            # Risk factors
            factors = predictions.get("top_risk_factors", predictions.get("risk_factors", []))
            if factors:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Top Risk Factors:", self.styles["SubSection"]))
                for factor in factors[:5]:
                    if isinstance(factor, dict):
                        factor_text = f"• {factor.get('feature', factor.get('name', 'Unknown'))}: {factor.get('importance', 0):.2f}"
                    else:
                        factor_text = f"• {factor}"
                    story.append(Paragraph(factor_text, self.styles["LGBodyText"]))
            
            story.append(Spacer(1, 20))
        
        # ESG Compliance Section
        if esg_data:
            story.append(Paragraph("4. ESG Compliance", self.styles["SectionTitle"]))
            
            esg_status = esg_data.get("overall_status", "N/A")
            story.append(Paragraph(
                f"ESG Status: <b>{esg_status}</b>",
                self.styles["LGBodyText"]
            ))
            story.append(Spacer(1, 10))
            
            kpis = esg_data.get("kpis", [])
            if kpis:
                kpi_headers = ["KPI", "Baseline", "Target", "Current", "Progress", "Status"]
                kpi_data = [kpi_headers]
                
                for kpi in kpis:
                    kpi_data.append([
                        kpi.get("name", "N/A"),
                        str(kpi.get("baseline", "N/A")),
                        str(kpi.get("target", "N/A")),
                        str(kpi.get("current", "N/A")),
                        f"{kpi.get('progress_pct', 0):.0f}%",
                        kpi.get("status", "N/A"),
                    ])
                
                kpi_table = Table(kpi_data, colWidths=[100, 60, 60, 60, 60, 70])
                kpi_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ]))
                story.append(kpi_table)
        
        # Build PDF
        doc.build(story, onFirstPage=self._on_page, onLaterPages=self._on_page)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

    def generate_portfolio_report(
        self,
        summary: Dict[str, Any],
        loans: List[Dict[str, Any]],
        concentration: Optional[Dict[str, Any]] = None,
        velocity: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generate portfolio-level compliance report.
        
        Args:
            summary: Portfolio summary stats
            loans: List of loan data
            concentration: Concentration analysis
            velocity: Portfolio velocity data
            
        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            topMargin=50,
            bottomMargin=40,
            leftMargin=40,
            rightMargin=40,
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Portfolio Compliance Report", self.styles["ReportTitle"]))
        story.append(Spacer(1, 10))
        
        # Executive Summary
        story.append(Paragraph("1. Executive Summary", self.styles["SectionTitle"]))
        
        exec_info = [
            ["Total Loans", str(summary.get("total_loans", 0))],
            ["Total Exposure", f"${summary.get('total_exposure', 0):,.0f}"],
            ["Compliant", str(summary.get("loans_compliant", 0))],
            ["Warning", str(summary.get("loans_warning", 0))],
            ["Breach", str(summary.get("loans_breach", 0))],
            ["Active Alerts", str(summary.get("active_alerts", 0))],
            ["Avg ESG Score", f"{summary.get('esg_average_score', 0):.1f}"],
        ]
        
        exec_table = Table(exec_info, colWidths=[150, 150])
        exec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), COLORS["background"]),
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(exec_table)
        story.append(Spacer(1, 20))
        
        # Concentration Analysis
        if concentration:
            story.append(Paragraph("2. Concentration Analysis", self.styles["SectionTitle"]))
            
            hhi = concentration.get("hhi_index", 0)
            level = concentration.get("concentration_level", "N/A")
            
            story.append(Paragraph(
                f"HHI Index: <b>{hhi:.0f}</b> | Concentration Level: <b>{level}</b>",
                self.styles["LGBodyText"]
            ))
            story.append(Spacer(1, 10))
            
            exposures = concentration.get("top_exposures", [])
            if exposures:
                exp_headers = ["Industry/Category", "Exposure", "Loans", "%"]
                exp_data = [exp_headers]
                
                for exp in exposures[:10]:
                    exp_data.append([
                        exp.get("category", exp.get("value", "N/A")),
                        f"${exp.get('exposure', 0):,.0f}",
                        str(exp.get("loan_count", 0)),
                        f"{exp.get('percentage', 0):.1f}%",
                    ])
                
                exp_table = Table(exp_data, colWidths=[150, 120, 70, 70])
                exp_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ]))
                story.append(exp_table)
            
            story.append(Spacer(1, 20))
        
        # Portfolio Velocity
        if velocity:
            story.append(Paragraph("3. Risk Velocity Analysis", self.styles["SectionTitle"]))
            
            dist = velocity.get("risk_distribution", {})
            story.append(Paragraph(
                f"Critical: {dist.get('CRITICAL', 0)} | High: {dist.get('HIGH', 0)} | Medium: {dist.get('MEDIUM', 0)} | Low: {dist.get('LOW', 0)}",
                self.styles["LGBodyText"]
            ))
            
            worsening = velocity.get("worsening_loans", [])
            if worsening:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Loans Requiring Attention:", self.styles["SubSection"]))
                
                for loan in worsening[:5]:
                    loan_text = f"• {loan.get('loan_id', 'N/A')}: {loan.get('risk_level', 'N/A')} - Breach in {loan.get('nearest_breach', 'N/A')} quarters"
                    story.append(Paragraph(loan_text, self.styles["LGBodyText"]))
            
            story.append(Spacer(1, 20))
        
        # Loan List
        story.append(Paragraph("4. Loan Portfolio", self.styles["SectionTitle"]))
        
        if loans:
            loan_headers = ["Loan ID", "Borrower", "Amount", "Status"]
            loan_data = [loan_headers]
            
            for loan in loans[:20]:  # Limit to 20 for readability
                loan_data.append([
                    loan.get("loan_id", "N/A"),
                    loan.get("borrower_name", "N/A")[:25],
                    f"${loan.get('facility_amount', 0):,.0f}",
                    loan.get("status", loan.get("overall_status", "N/A")),
                ])
            
            loan_table = Table(loan_data, colWidths=[80, 180, 100, 70])
            loan_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ]))
            
            # Color code status
            for i, loan in enumerate(loans[:20], 1):
                status = loan.get("status", loan.get("overall_status", "")).upper()
                color = self._get_status_color(status)
                loan_table.setStyle(TableStyle([
                    ("TEXTCOLOR", (-1, i), (-1, i), color),
                    ("FONTNAME", (-1, i), (-1, i), "Helvetica-Bold"),
                ]))
            
            story.append(loan_table)
        else:
            story.append(Paragraph("No loans in portfolio.", self.styles["LGBodyText"]))
        
        # Disclaimer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "This report is generated by LoanGuard AI and is intended for internal compliance purposes only. "
            "The ML predictions are based on historical data and should be used as guidance only.",
            self.styles["LGSmallText"]
        ))
        
        # Build PDF
        doc.build(story, onFirstPage=self._on_page, onLaterPages=self._on_page)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes


# Singleton instance
_report_generator: Optional[ComplianceReportGenerator] = None


def get_report_generator() -> ComplianceReportGenerator:
    """Get or create report generator singleton."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ComplianceReportGenerator()
    return _report_generator


def generate_loan_pdf(
    loan_data: Dict[str, Any],
    covenants: List[Dict[str, Any]],
    predictions: Optional[Dict[str, Any]] = None,
    esg_data: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Convenience function to generate loan compliance PDF."""
    generator = get_report_generator()
    return generator.generate_loan_report(loan_data, covenants, predictions, esg_data)


def generate_portfolio_pdf(
    summary: Dict[str, Any],
    loans: List[Dict[str, Any]],
    concentration: Optional[Dict[str, Any]] = None,
    velocity: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Convenience function to generate portfolio compliance PDF."""
    generator = get_report_generator()
    return generator.generate_portfolio_report(summary, loans, concentration, velocity)
