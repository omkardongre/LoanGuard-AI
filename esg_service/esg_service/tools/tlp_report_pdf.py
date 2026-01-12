"""
TLP Report PDF Generator - Generate LMA-Compliant Transition Loan Reports.

Production-level implementation based on LMA TLP Principle 5: Reporting.
Generates professional PDF reports in official LMA format.
"""

import io
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
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

from esg_service.esg_service.tools.tlp_report import TLPReportAgent, get_tlp_report_agent

logger = logging.getLogger(__name__)


# Colors matching common/pdf_report_generator.py
COLORS = {
    "primary": colors.HexColor("#1e40af"),   # Blue
    "success": colors.HexColor("#15803d"),   # Green
    "warning": colors.HexColor("#ca8a04"),   # Amber
    "danger": colors.HexColor("#dc2626"),    # Red
    "muted": colors.HexColor("#6b7280"),     # Gray
    "background": colors.HexColor("#f8fafc"),
    "white": colors.white,
    "black": colors.black,
}


class TLPReportPDFGenerator:
    """
    Generate LMA-Compliant TLP PDF Reports.
    
    Based on LMA Transition Loan Principles (October 2025):
    - Principle 5: Reporting (Mandatory)
    
    LMA Mandatory Reporting Requirements:
    1. List of Transition Projects financed
    2. Amounts allocated to each project
    3. Expected impact of each project
    4. Achieved impact of each project (when available)
    """
    
    def __init__(self):
        """Initialize TLP PDF generator."""
        self.tlp_agent = get_tlp_report_agent()
        self.styles = getSampleStyleSheet()
        self._setup_tlp_styles()
    
    def _setup_tlp_styles(self):
        """Setup custom styles for TLP report."""
        self.styles.add(ParagraphStyle(
            name="TLPTitle",
            parent=self.styles["Heading1"],
            fontSize=28,
            textColor=COLORS["primary"],
            spaceAfter=30,
            alignment=1,  # Center
        ))
        self.styles.add(ParagraphStyle(
            name="TLPSubtitle",
            parent=self.styles["Normal"],
            fontSize=14,
            textColor=COLORS["muted"],
            spaceAfter=10,
            alignment=1,
        ))
        self.styles.add(ParagraphStyle(
            name="TLPSection",
            parent=self.styles["Heading2"],
            fontSize=16,
            textColor=COLORS["primary"],
            spaceBefore=20,
            spaceAfter=10,
            leftIndent=0,
        ))
        self.styles.add(ParagraphStyle(
            name="TLPSubSection",
            parent=self.styles["Heading3"],
            fontSize=12,
            textColor=COLORS["muted"],
            spaceBefore=10,
            spaceAfter=5,
        ))
        self.styles.add(ParagraphStyle(
            name="TLPBody",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=14,
        ))
        self.styles.add(ParagraphStyle(
            name="TLPSmall",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=COLORS["muted"],
        ))
    
    def _get_status_color(self, status: str) -> colors.Color:
        """Get color for compliance status."""
        if not status:
            return COLORS["muted"]
        
        status_upper = status.upper()
        if status_upper in ("PASS", "COMPLIANT", "ON_TRACK", "LOW", "VERIFIED"):
            return COLORS["success"]
        elif status_upper in ("PENDING", "WARNING", "MEDIUM", "IN_PROGRESS"):
            return COLORS["warning"]
        elif status_upper in ("FAIL", "NON_COMPLIANT", "HIGH", "CRITICAL"):
            return COLORS["danger"]
        return COLORS["muted"]
    
    def _create_header(self, canvas, doc):
        """Add header to each page."""
        canvas.saveState()
        # Header line
        canvas.setStrokeColor(COLORS["primary"])
        canvas.setLineWidth(2)
        canvas.line(40, doc.pagesize[1] - 35, doc.pagesize[0] - 40, doc.pagesize[1] - 35)
        
        # LoanGuard AI text
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(COLORS["primary"])
        canvas.drawString(40, doc.pagesize[1] - 28, "LoanGuard AI | TLP Compliance Report")
        
        # Date
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLORS["muted"])
        canvas.drawRightString(
            doc.pagesize[0] - 40,
            doc.pagesize[1] - 28,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        canvas.restoreState()
    
    def _create_footer(self, canvas, doc):
        """Add footer to each page."""
        canvas.saveState()
        # Footer line
        canvas.setStrokeColor(COLORS["muted"])
        canvas.setLineWidth(0.5)
        canvas.line(40, 35, doc.pagesize[0] - 40, 35)
        
        # Page number
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLORS["muted"])
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            22,
            f"Page {doc.page} | Confidential | Prepared in accordance with LMA TLP October 2025"
        )
        canvas.restoreState()
    
    def _on_page(self, canvas, doc):
        """Handle page rendering."""
        self._create_header(canvas, doc)
        self._create_footer(canvas, doc)
    
    def _create_cover_page(self, report: Dict[str, Any]) -> List:
        """Create cover page elements."""
        story = []
        
        # Spacer for visual balance
        story.append(Spacer(1, 60))
        
        # Title
        story.append(Paragraph(
            "TRANSITION LOAN<br/>PROGRESS REPORT",
            self.styles["TLPTitle"]
        ))
        story.append(Spacer(1, 20))
        
        # Report info table
        loan_id = report.get("loan_id", "N/A")
        generation_date = report.get("generation_date", str(date.today()))
        
        info_data = [
            ["Report ID:", report.get("report_id", "N/A")],
            ["Loan ID:", loan_id],
            ["Report Date:", generation_date],
            ["Report Type:", "TLP Compliance Report"],
        ]
        
        info_table = Table(info_data, colWidths=[120, 200])
        info_table.setStyle(TableStyle([
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 40))
        
        # Compliance statement
        story.append(Paragraph(
            "<b>Prepared in accordance with:</b><br/>"
            "LMA Transition Loan Principles<br/>"
            "October 2025 Edition",
            self.styles["TLPSubtitle"]
        ))
        
        story.append(PageBreak())
        return story
    
    def _create_executive_summary(self, report: Dict[str, Any]) -> List:
        """Create executive summary section."""
        story = []
        
        story.append(Paragraph("1. Executive Summary", self.styles["TLPSection"]))
        
        exec_summary = report.get("executive_summary", {})
        
        # Summary metrics
        metrics_data = [
            ["TLP Compliance Score", f"{exec_summary.get('tlp_compliance_score', 0):.0f}%"],
            ["Compliance Status", exec_summary.get("compliance_status", "N/A")],
            ["Total Transition Projects", str(exec_summary.get("total_projects", 0))],
            ["Total Amount Allocated", f"${exec_summary.get('total_allocated', 0):,.0f}"],
            ["Expected GHG Reduction (tCO2)", f"{exec_summary.get('expected_ghg_reduction_tco2', 0):,.0f}"],
            ["Achieved GHG Reduction (tCO2)", f"{exec_summary.get('achieved_ghg_reduction_tco2', 0):,.0f}"],
            ["Achievement Rate", f"{exec_summary.get('achievement_rate', 0):.1f}%"],
            ["DNSH Status", exec_summary.get("dnsh_status", "N/A")],
            ["Carbon Lock-in Risk", exec_summary.get("carbon_lockin_risk", "N/A")],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[200, 200])
        metrics_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), COLORS["background"]),
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_project_list_section(self, report: Dict[str, Any]) -> List:
        """Create project list section (LMA Requirement 1)."""
        story = []
        
        story.append(Paragraph(
            "2. List of Transition Projects Financed",
            self.styles["TLPSection"]
        ))
        story.append(Paragraph(
            "<i>LMA TLP Principle 5 - Requirement 1</i>",
            self.styles["TLPSmall"]
        ))
        story.append(Spacer(1, 10))
        
        projects = report.get("project_list", [])
        
        if not projects:
            story.append(Paragraph(
                "No transition projects have been recorded for this loan.",
                self.styles["TLPBody"]
            ))
            return story
        
        # Project table
        headers = ["Project Name", "Category", "Type", "Status", "Pathway Aligned"]
        table_data = [headers]
        
        for project in projects:
            table_data.append([
                project.get("project_name", "N/A"),
                project.get("category", "N/A"),
                project.get("type", "N/A"),
                project.get("eligibility_status", "N/A"),
                "Yes" if project.get("pathway_aligned") else "No",
            ])
        
        table = Table(table_data, colWidths=[120, 100, 80, 80, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_allocation_section(self, report: Dict[str, Any]) -> List:
        """Create allocation section (LMA Requirement 2)."""
        story = []
        
        story.append(Paragraph(
            "3. Allocation of Proceeds",
            self.styles["TLPSection"]
        ))
        story.append(Paragraph(
            "<i>LMA TLP Principle 5 - Requirement 2</i>",
            self.styles["TLPSmall"]
        ))
        story.append(Spacer(1, 10))
        
        allocation = report.get("allocation_summary", {})
        
        # Total allocation
        story.append(Paragraph(
            f"<b>Total Amount Allocated:</b> ${allocation.get('total_allocated', 0):,.0f}",
            self.styles["TLPBody"]
        ))
        story.append(Spacer(1, 10))
        
        # By category
        by_category = allocation.get("by_category", {})
        if by_category:
            story.append(Paragraph("Allocation by Category:", self.styles["TLPSubSection"]))
            cat_data = [["Category", "Amount", "% of Total"]]
            total = allocation.get("total_allocated", 1) or 1
            
            for cat, amount in by_category.items():
                pct = (amount / total) * 100
                cat_data.append([cat, f"${amount:,.0f}", f"{pct:.1f}%"])
            
            cat_table = Table(cat_data, colWidths=[180, 120, 80])
            cat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]))
            story.append(cat_table)
        
        story.append(Spacer(1, 20))
        
        # Project allocations
        project_alloc = allocation.get("project_allocations", [])
        if project_alloc:
            story.append(Paragraph("Individual Project Allocations:", self.styles["TLPSubSection"]))
            
            alloc_data = [["Project", "Allocated Amount", "Allocation Date"]]
            for proj in project_alloc:
                alloc_data.append([
                    proj.get("project_name", "N/A"),
                    f"${proj.get('allocated_amount', 0):,.0f}",
                    str(proj.get("allocation_date", "N/A")),
                ])
            
            alloc_table = Table(alloc_data, colWidths=[180, 120, 100])
            alloc_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ]))
            story.append(alloc_table)
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_impact_section(self, report: Dict[str, Any]) -> List:
        """Create impact section (LMA Requirements 3 & 4)."""
        story = []
        
        story.append(Paragraph(
            "4. Impact Assessment",
            self.styles["TLPSection"]
        ))
        story.append(Paragraph(
            "<i>LMA TLP Principle 5 - Requirements 3 & 4: Expected and Achieved Impact</i>",
            self.styles["TLPSmall"]
        ))
        story.append(Spacer(1, 10))
        
        impact = report.get("impact_metrics", {})
        summary = impact.get("summary", {})
        
        # Summary
        summary_text = (
            f"<b>Total Expected GHG Reduction:</b> {summary.get('total_expected_ghg_reduction', 0):,.0f} tCO2<br/>"
            f"<b>Total Achieved GHG Reduction:</b> {summary.get('total_achieved_ghg_reduction', 0):,.0f} tCO2<br/>"
            f"<b>Verified Projects:</b> {summary.get('verified_count', 0)}"
        )
        story.append(Paragraph(summary_text, self.styles["TLPBody"]))
        story.append(Spacer(1, 15))
        
        # By project
        by_project = impact.get("by_project", [])
        if by_project:
            story.append(Paragraph("Impact by Project:", self.styles["TLPSubSection"]))
            
            impact_data = [["Project", "Expected (tCO2)", "Achieved (tCO2)", "Rate", "Verified"]]
            for proj in by_project:
                impact_data.append([
                    proj.get("project_name", "N/A"),
                    f"{proj.get('expected_ghg_reduction_tco2', 0):,.0f}",
                    f"{proj.get('achieved_ghg_reduction_tco2', 0):,.0f}",
                    f"{proj.get('achievement_rate', 0):.1f}%",
                    "✓" if proj.get("impact_verified") else "✗",
                ])
            
            impact_table = Table(impact_data, colWidths=[140, 90, 90, 60, 60])
            impact_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ]))
            story.append(impact_table)
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_dnsh_section(self, report: Dict[str, Any]) -> List:
        """Create DNSH assessment section."""
        story = []
        
        story.append(Paragraph(
            "5. Do No Significant Harm (DNSH) Assessment",
            self.styles["TLPSection"]
        ))
        story.append(Spacer(1, 10))
        
        dnsh = report.get("dnsh_assessment", {})
        
        # Overall status
        overall_status = dnsh.get("overall_status", "PENDING")
        status_color = self._get_status_color(overall_status)
        
        story.append(Paragraph(
            f"<b>Overall DNSH Status:</b> {overall_status}",
            self.styles["TLPBody"]
        ))
        story.append(Spacer(1, 10))
        
        # By objective
        by_objective = dnsh.get("by_objective", {})
        if by_objective:
            dnsh_data = [["Environmental Objective", "Status"]]
            
            objective_names = {
                "climate_mitigation": "Climate Change Mitigation",
                "climate_adaptation": "Climate Change Adaptation",
                "water": "Sustainable Use of Water Resources",
                "circular_economy": "Transition to Circular Economy",
                "pollution": "Pollution Prevention and Control",
                "biodiversity": "Protection of Biodiversity",
            }
            
            for key, status in by_objective.items():
                name = objective_names.get(key, key.replace("_", " ").title())
                dnsh_data.append([name, status])
            
            dnsh_table = Table(dnsh_data, colWidths=[300, 100])
            dnsh_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            # Color code status cells
            for i, (_, status) in enumerate(list(by_objective.items()), 1):
                color = self._get_status_color(status)
                if i < len(dnsh_data):
                    dnsh_table.setStyle(TableStyle([
                        ("TEXTCOLOR", (1, i), (1, i), color),
                        ("FONTNAME", (1, i), (1, i), "Helvetica-Bold"),
                    ]))
            
            story.append(dnsh_table)
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_carbon_lockin_section(self, report: Dict[str, Any]) -> List:
        """Create carbon lock-in assessment section."""
        story = []
        
        story.append(Paragraph(
            "6. Carbon Lock-in Risk Assessment",
            self.styles["TLPSection"]
        ))
        story.append(Spacer(1, 10))
        
        lockin = report.get("carbon_lockin_assessment", {})
        
        risk_level = lockin.get("risk_level", "NOT_ASSESSED")
        risk_score = lockin.get("risk_score", 0)
        status_color = self._get_status_color(risk_level)
        
        lockin_data = [
            ["Risk Level", risk_level],
            ["Risk Score", f"{risk_score:.0f}/100"],
            ["Project Lifetime (Years)", str(lockin.get("project_lifetime_years", "N/A"))],
            ["Emissions Trajectory", lockin.get("emissions_trajectory", "N/A")],
            ["Displaceability", lockin.get("displaceability", "N/A")],
            ["Reversibility", lockin.get("reversibility", "N/A")],
            ["Best Available Technology", lockin.get("best_available_tech", "N/A")],
        ]
        
        lockin_table = Table(lockin_data, colWidths=[200, 200])
        lockin_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), COLORS["background"]),
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(lockin_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_recommendations_section(self, report: Dict[str, Any]) -> List:
        """Create recommendations section."""
        story = []
        
        story.append(Paragraph(
            "7. Recommendations",
            self.styles["TLPSection"]
        ))
        story.append(Spacer(1, 10))
        
        recommendations = report.get("recommendations", [])
        
        if not recommendations:
            story.append(Paragraph(
                "No specific recommendations generated for this loan.",
                self.styles["TLPBody"]
            ))
            story.append(Spacer(1, 20))
            return story
        
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles["TLPBody"]))
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_appendix(self) -> List:
        """Create appendix with methodology."""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Appendix: Methodology & Definitions", self.styles["TLPSection"]))
        story.append(Spacer(1, 15))
        
        # LMA TLP Principles
        story.append(Paragraph(
            "<b>LMA Transition Loan Principles (October 2025)</b>",
            self.styles["TLPSubSection"]
        ))
        story.append(Paragraph(
            "This report is prepared in accordance with the five core Transition Loan Principles:<br/>"
            "1. Entity-Level Transition Strategy<br/>"
            "2. Use of Proceeds<br/>"
            "3. Project Evaluation and Selection<br/>"
            "4. Management of Proceeds<br/>"
            "5. Reporting (this document)",
            self.styles["TLPBody"]
        ))
        story.append(Spacer(1, 15))
        
        # DNSH Framework
        story.append(Paragraph(
            "<b>Do No Significant Harm (DNSH) Framework</b>",
            self.styles["TLPSubSection"]
        ))
        story.append(Paragraph(
            "Assessment based on EU Taxonomy Regulation six environmental objectives.",
            self.styles["TLPBody"]
        ))
        story.append(Spacer(1, 15))
        
        # Carbon Lock-in
        story.append(Paragraph(
            "<b>Carbon Lock-in Assessment</b>",
            self.styles["TLPSubSection"]
        ))
        story.append(Paragraph(
            "Evaluates risk that transition projects may lock in emissions or delay decarbonization.<br/>"
            "Factors: project lifetime, emissions trajectory, displaceability, reversibility, "
            "and best available technology adoption.",
            self.styles["TLPBody"]
        ))
        story.append(Spacer(1, 15))
        
        # Disclaimer
        story.append(Paragraph(
            "<b>Disclaimer</b>",
            self.styles["TLPSubSection"]
        ))
        story.append(Paragraph(
            "This report is generated by LoanGuard AI for internal compliance monitoring purposes. "
            "The assessment is based on available data and should be used as guidance only. "
            "Final regulatory submissions may require additional verification and review.",
            self.styles["TLPSmall"]
        ))
        
        return story
    
    def generate_pdf_report(self, loan_id: str) -> bytes:
        """
        Generate LMA-compliant TLP PDF report.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            PDF file as bytes
        """
        # Get TLP JSON data from existing agent
        result = self.tlp_agent.generate_loan_report(loan_id)
        
        if not result.get("success"):
            raise ValueError(f"Failed to get TLP data: {result.get('error')}")
        
        report = result["report"]
        
        # Build PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=50,
            bottomMargin=40,
            leftMargin=40,
            rightMargin=40,
        )
        
        story = []
        
        # Build sections
        story.extend(self._create_cover_page(report))
        story.extend(self._create_executive_summary(report))
        story.extend(self._create_project_list_section(report))
        story.extend(self._create_allocation_section(report))
        story.extend(self._create_impact_section(report))
        story.extend(self._create_dnsh_section(report))
        story.extend(self._create_carbon_lockin_section(report))
        story.extend(self._create_recommendations_section(report))
        story.extend(self._create_appendix())
        
        # Build document
        doc.build(story, onFirstPage=self._on_page, onLaterPages=self._on_page)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated TLP PDF report for loan {loan_id}")
        
        return pdf_bytes
    
    def generate_portfolio_pdf_report(self) -> bytes:
        """
        Generate portfolio-level TLP PDF report.
        
        Returns:
            PDF file as bytes
        """
        # Get portfolio data
        result = self.tlp_agent.get_portfolio_report()
        
        if not result.get("success"):
            raise ValueError(f"Failed to get portfolio data: {result.get('error')}")
        
        # Build PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=50,
            bottomMargin=40,
            leftMargin=40,
            rightMargin=40,
        )
        
        story = []
        
        # Cover page
        story.append(Spacer(1, 60))
        story.append(Paragraph(
            "TRANSITION LOAN<br/>PORTFOLIO REPORT",
            self.styles["TLPTitle"]
        ))
        story.append(Spacer(1, 20))
        
        info_data = [
            ["Report Date:", result.get("report_date", str(date.today()))],
            ["Report Type:", "TLP Portfolio Summary"],
        ]
        info_table = Table(info_data, colWidths=[120, 200])
        info_table.setStyle(TableStyle([
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(PageBreak())
        
        # Loan Summary
        story.append(Paragraph("1. Loan Portfolio Summary", self.styles["TLPSection"]))
        
        loan_summary = result.get("loan_summary", {})
        loan_data = [
            ["Total Transition Loans", str(loan_summary.get("total_loans", 0))],
            ["Average TLP Score", f"{loan_summary.get('avg_tlp_score', 0):.1f}%"],
            ["TLP Compliant Loans", str(loan_summary.get("compliant_count", 0))],
            ["DNSH Pass Count", str(loan_summary.get("dnsh_pass_count", 0))],
            ["Low Carbon Lock-in Count", str(loan_summary.get("low_lockin_count", 0))],
        ]
        
        loan_table = Table(loan_data, colWidths=[200, 150])
        loan_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), COLORS["background"]),
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(loan_table)
        story.append(Spacer(1, 20))
        
        # Project Summary
        story.append(Paragraph("2. Transition Projects Summary", self.styles["TLPSection"]))
        
        project_summary = result.get("project_summary", {})
        project_data = [
            ["Total Projects", str(project_summary.get("total_projects", 0))],
            ["Total Amount Allocated", f"${project_summary.get('total_allocated', 0):,.0f}"],
            ["Expected GHG Reduction (tCO2)", f"{project_summary.get('total_expected_ghg_reduction_tco2', 0):,.0f}"],
            ["Achieved GHG Reduction (tCO2)", f"{project_summary.get('total_achieved_ghg_reduction_tco2', 0):,.0f}"],
        ]
        
        project_table = Table(project_data, colWidths=[200, 150])
        project_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), COLORS["background"]),
            ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(project_table)
        
        # Build document
        doc.build(story, onFirstPage=self._on_page, onLaterPages=self._on_page)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info("Generated TLP portfolio PDF report")
        
        return pdf_bytes


# Singleton instance
_tlp_pdf_generator: Optional[TLPReportPDFGenerator] = None


def get_tlp_pdf_generator() -> TLPReportPDFGenerator:
    """Get or create TLP PDF generator singleton."""
    global _tlp_pdf_generator
    if _tlp_pdf_generator is None:
        _tlp_pdf_generator = TLPReportPDFGenerator()
    return _tlp_pdf_generator


def generate_tlp_pdf(loan_id: str) -> bytes:
    """Convenience function to generate TLP PDF report."""
    generator = get_tlp_pdf_generator()
    return generator.generate_pdf_report(loan_id)


def generate_tlp_portfolio_pdf() -> bytes:
    """Convenience function to generate portfolio TLP PDF report."""
    generator = get_tlp_pdf_generator()
    return generator.generate_portfolio_pdf_report()
