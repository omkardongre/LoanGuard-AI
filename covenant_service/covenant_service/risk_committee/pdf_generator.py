"""
PDF Credit Decision Report Generator - Production Level.

Generates professional PDF reports for Risk Committee decisions.
Uses ReportLab for PDF generation with custom LoanGuard branding.
"""

import io
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from .state import CommitteeState, DecisionVote


class LoanGuardTemplate:
    """Custom page template for LoanGuard AI branding."""
    
    # Brand colors
    PRIMARY_BLUE = HexColor('#2563eb')
    SUCCESS_GREEN = HexColor('#10b981')
    WARNING_AMBER = HexColor('#f59e0b')
    DANGER_RED = HexColor('#ef4444')
    GRAY_900 = HexColor('#111827')
    GRAY_700 = HexColor('#374151')
    GRAY_200 = HexColor('#e5e7eb')
    GRAY_100 = HexColor('#f3f4f6')
    
    def __init__(self, doc, loan_id: str, borrower_name: str):
        self.doc = doc
        self.loan_id = loan_id
        self.borrower_name = borrower_name
        self.page_count = 0
    
    def __call__(self, canvas, doc):
        """Draw page template on each page."""
        self.page_count += 1
        canvas.saveState()
        
        width, height = A4
        self._draw_header(canvas, width, height)
        self._draw_footer(canvas, width, height)
        
        canvas.restoreState()
    
    def _draw_header(self, canvas, width, height):
        """Draw LoanGuard AI header."""
        # Header background
        canvas.setFillColor(self.PRIMARY_BLUE)
        canvas.rect(0, height - 2.5*cm, width, 2.5*cm, fill=1, stroke=0)
        
        # Logo/Title
        canvas.setFont("Helvetica-Bold", 18)
        canvas.setFillColor(white)
        canvas.drawString(2*cm, height - 1.5*cm, "LoanGuard AI")
        
        # Subtitle
        canvas.setFont("Helvetica", 10)
        canvas.drawString(2*cm, height - 2*cm, "Multi-Agent Risk Committee Decision Report")
        
        # Loan ID on right
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawRightString(width - 2*cm, height - 1.5*cm, f"Loan: {self.loan_id}")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(width - 2*cm, height - 2*cm, self.borrower_name)
    
    def _draw_footer(self, canvas, width, height):
        """Draw page footer with page number and timestamp."""
        # Footer line
        canvas.setStrokeColor(self.GRAY_200)
        canvas.setLineWidth(0.5)
        canvas.line(2*cm, 1.5*cm, width - 2*cm, 1.5*cm)
        
        # Page number
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(self.GRAY_700)
        canvas.drawCentredString(width / 2, 1*cm, f"Page {self.page_count}")
        
        # Generated timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        canvas.drawString(2*cm, 1*cm, f"Generated: {timestamp}")
        
        # Confidential notice
        canvas.drawRightString(width - 2*cm, 1*cm, "CONFIDENTIAL")


class CreditDecisionPDFGenerator:
    """
    Generate professional PDF reports for credit committee decisions.
    
    Includes:
    - Executive summary
    - ML prediction details with SHAP factors
    - ESG assessment
    - Agent votes and reasoning
    - Complete audit trail
    """
    
    def __init__(self):
        self.styles = self._create_styles()
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles."""
        base_styles = getSampleStyleSheet()
        
        custom = {}
        
        # Section headers
        custom['SectionHeader'] = ParagraphStyle(
            'SectionHeader',
            parent=base_styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#2563eb'),
            fontName='Helvetica-Bold'
        )
        
        custom['SubHeader'] = ParagraphStyle(
            'SubHeader',
            parent=base_styles['Heading2'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=12,
            textColor=HexColor('#374151'),
            fontName='Helvetica-Bold'
        )
        
        # Body text
        custom['Body'] = ParagraphStyle(
            'Body',
            parent=base_styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=HexColor('#374151'),
            leading=14
        )
        
        custom['BodySmall'] = ParagraphStyle(
            'BodySmall',
            parent=base_styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            textColor=HexColor('#6b7280'),
            leading=12
        )
        
        # Decision styles
        custom['DecisionApprove'] = ParagraphStyle(
            'DecisionApprove',
            parent=base_styles['Normal'],
            fontSize=16,
            textColor=HexColor('#10b981'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        custom['DecisionDecline'] = ParagraphStyle(
            'DecisionDecline',
            parent=base_styles['Normal'],
            fontSize=16,
            textColor=HexColor('#ef4444'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        custom['DecisionRefer'] = ParagraphStyle(
            'DecisionRefer',
            parent=base_styles['Normal'],
            fontSize=16,
            textColor=HexColor('#f59e0b'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        custom['DecisionCaution'] = ParagraphStyle(
            'DecisionCaution',
            parent=base_styles['Normal'],
            fontSize=16,
            textColor=HexColor('#f59e0b'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        return custom
    
    def generate(self, committee_state: CommitteeState) -> bytes:
        """
        Generate PDF report from committee state.
        
        Args:
            committee_state: The complete committee state with all assessments
            
        Returns:
            PDF document as bytes
        """
        buffer = io.BytesIO()
        
        loan = committee_state.loan_application
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3.5*cm,
            bottomMargin=2.5*cm
        )
        
        template = LoanGuardTemplate(doc, loan.loan_id, loan.borrower_name)
        
        story = []
        
        # Build sections
        story.extend(self._executive_summary(committee_state))
        story.extend(self._loan_details(committee_state))
        story.extend(self._ml_predictions(committee_state))
        story.extend(self._esg_assessment(committee_state))
        story.extend(self._agent_votes(committee_state))
        story.extend(self._audit_trail(committee_state))
        
        doc.build(story, onFirstPage=template, onLaterPages=template)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _executive_summary(self, state: CommitteeState) -> List:
        """Generate executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb')))
        elements.append(Spacer(1, 12))
        
        # Decision box
        decision = state.final_decision.value if state.final_decision else "pending"
        decision_style = self.styles.get(f'Decision{decision.title()}', self.styles['DecisionRefer'])
        
        decision_text = f"DECISION: {decision.upper()}"
        elements.append(Paragraph(decision_text, decision_style))
        elements.append(Spacer(1, 8))
        
        # Confidence
        confidence = state.final_confidence or 0.0
        elements.append(Paragraph(
            f"<b>Confidence:</b> {confidence:.0%}",
            self.styles['Body']
        ))
        
        # Vote summary
        votes = {}
        for assessment in state.get_all_assessments():
            vote = assessment.vote.value
            votes[vote] = votes.get(vote, 0) + 1
        
        vote_text = " | ".join([f"{v.title()}: {c}" for v, c in votes.items()])
        elements.append(Paragraph(f"<b>Agent Votes:</b> {vote_text}", self.styles['Body']))
        
        # Reasoning
        if state.final_reasoning:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph("<b>Summary:</b>", self.styles['Body']))
            elements.append(Paragraph(state.final_reasoning, self.styles['BodySmall']))
        
        return elements
    
    def _loan_details(self, state: CommitteeState) -> List:
        """Generate loan details section."""
        elements = []
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Loan Details", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb')))
        elements.append(Spacer(1, 12))
        
        loan = state.loan_application
        
        # Loan details table
        data = [
            ["Field", "Value"],
            ["Loan ID", loan.loan_id],
            ["Borrower", loan.borrower_name],
            ["Sector", loan.sector],
            ["Amount", f"${loan.amount:,.2f}"],
            ["Term", f"{loan.term_months} months"],
            ["Interest Rate", f"{loan.interest_rate * 100:.2f}%"],
            ["Credit Score", str(loan.credit_score)],
            ["Annual Revenue", f"${loan.annual_revenue:,.2f}" if loan.annual_revenue else "N/A"],
            ["Location", loan.location or "N/A"],
        ]
        
        table = Table(data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#374151')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [None, HexColor('#f9fafb')]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _ml_predictions(self, state: CommitteeState) -> List:
        """Generate ML predictions section."""
        elements = []
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("ML Risk Predictions", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb')))
        elements.append(Spacer(1, 12))
        
        # Find ML prediction in audit trail
        ml_data = {}
        for entry in state.audit_trail:
            if entry.get("action") == "ml_prediction":
                ml_data = entry.get("details", {})
                break
        
        if ml_data:
            pd = ml_data.get("pd", 0)
            lgd = ml_data.get("lgd", 0)
            risk_level = ml_data.get("risk_level", "unknown")
            shap_factors = ml_data.get("shap_factors", [])
            
            # Predictions table
            data = [
                ["Metric", "Value", "Risk Level"],
                ["Probability of Default (PD)", f"{pd:.2%}", risk_level.upper()],
                ["Loss Given Default (LGD)", f"{lgd:.2%}", "-"],
                ["Expected Loss", f"${state.loan_application.amount * pd * lgd:,.0f}", "-"],
            ]
            
            table = Table(data, colWidths=[6*cm, 4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ]))
            
            elements.append(table)
            
            # SHAP factors
            if shap_factors:
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("Top SHAP Risk Factors", self.styles['SubHeader']))
                
                for i, factor in enumerate(shap_factors[:5], 1):
                    elements.append(Paragraph(f"{i}. {factor}", self.styles['BodySmall']))
        else:
            elements.append(Paragraph("ML predictions not available", self.styles['Body']))
        
        return elements
    
    def _esg_assessment(self, state: CommitteeState) -> List:
        """Generate ESG assessment section."""
        elements = []
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("ESG Financial Risk Assessment", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb')))
        elements.append(Spacer(1, 12))
        
        # Find ESG data in audit trail
        esg_data = {}
        for entry in state.audit_trail:
            if entry.get("action") == "esg_assessment":
                esg_data = entry.get("details", {})
                break
        
        if esg_data:
            data = [
                ["Metric", "Score", "Impact"],
                ["ESG Financial Risk Score", f"{esg_data.get('esg_score', 0):.1f}/100", "-"],
                ["Transition Risk", f"{esg_data.get('transition_risk', 0):.1f}/100", "-"],
                ["Physical Risk", f"{esg_data.get('physical_risk', 0):.1f}/100", "-"],
                ["PD Adjustment", f"{esg_data.get('pd_adjustment', 1.0):.2f}x", "Multiplier"],
                ["LGD Adjustment", f"+{esg_data.get('lgd_adjustment', 0):.1%}", "Add-on"],
            ]
            
            table = Table(data, colWidths=[6*cm, 4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("ESG assessment not available", self.styles['Body']))
        
        return elements
    
    def _agent_votes(self, state: CommitteeState) -> List:
        """Generate agent votes section."""
        elements = []
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Risk Committee Agent Deliberation", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb')))
        elements.append(Spacer(1, 12))
        
        assessments = state.get_all_assessments()
        
        if assessments:
            # Agent votes table
            data = [["Agent", "Vote", "Confidence"]]
            
            for a in assessments:
                vote_color = {
                    "approve": "#10b981",
                    "decline": "#ef4444",
                    "refer": "#f59e0b",
                    "caution": "#f59e0b"
                }.get(a.vote.value, "#6b7280")
                
                data.append([
                    a.agent_name,
                    a.vote.value.upper(),
                    f"{a.confidence:.0%}"
                ])
            
            table = Table(data, colWidths=[6*cm, 4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [None, HexColor('#f9fafb')]),
            ]))
            
            elements.append(table)
            
            # Individual reasoning
            elements.append(Spacer(1, 16))
            elements.append(Paragraph("Agent Reasoning", self.styles['SubHeader']))
            
            for a in assessments:
                elements.append(Spacer(1, 8))
                elements.append(Paragraph(f"<b>{a.agent_name}:</b>", self.styles['Body']))
                if a.reasoning:
                    # Truncate long reasoning
                    reasoning = a.reasoning[:500] + "..." if len(a.reasoning) > 500 else a.reasoning
                    elements.append(Paragraph(reasoning, self.styles['BodySmall']))
        else:
            elements.append(Paragraph("No agent assessments available", self.styles['Body']))
        
        return elements
    
    def _audit_trail(self, state: CommitteeState) -> List:
        """Generate audit trail section."""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Audit Trail", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb')))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            "<i>Complete record of all actions for EU AI Act compliance.</i>",
            self.styles['BodySmall']
        ))
        elements.append(Spacer(1, 12))
        
        if state.audit_trail:
            data = [["Timestamp", "Agent", "Action"]]
            
            for entry in state.audit_trail:
                timestamp = entry.get("timestamp", "")
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime("%H:%M:%S")
                elif timestamp:
                    timestamp = str(timestamp)[:19]
                
                agent = entry.get("agent", "-")
                action = entry.get("action", "-")
                
                data.append([timestamp, agent, action])
            
            table = Table(data, colWidths=[4*cm, 5*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [None, HexColor('#f9fafb')]),
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("No audit trail available", self.styles['Body']))
        
        # Signature block
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="40%", thickness=0.5, color=HexColor('#6b7280')))
        elements.append(Paragraph("Authorized Signature", self.styles['BodySmall']))
        
        return elements


# Convenience function
def generate_credit_decision_pdf(committee_state: CommitteeState) -> bytes:
    """
    Generate PDF report from committee state.
    
    Args:
        committee_state: The complete committee state
        
    Returns:
        PDF document as bytes
    """
    generator = CreditDecisionPDFGenerator()
    return generator.generate(committee_state)
