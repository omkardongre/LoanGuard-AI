"""
Risk Committee Workflow.

Orchestrates the multi-agent credit risk decision workflow.
Follows a debate-style pattern with consensus synthesis.
"""

from datetime import datetime
from typing import Dict, Any

from .state import CommitteeState, LoanApplication, DecisionVote
from .agents import (
    CreditRiskAssessor,
    ESGRiskAgent,
    MarketContextAgent,
    DevilsAdvocateAgent,
    SynthesizerAgent,
)


class RiskCommitteeWorkflow:
    """
    Multi-Agent Risk Committee Workflow.
    
    Workflow:
    1. CreditRiskAssessor -> Initial credit assessment
    2. ESGRiskAgent -> ESG financial risk overlay
    3. MarketContextAgent -> Market and sector context
    4. DevilsAdvocateAgent -> Challenge the assessments
    5. SynthesizerAgent -> Final consensus decision
    """
    
    def __init__(self):
        self.credit_assessor = CreditRiskAssessor()
        self.esg_agent = ESGRiskAgent()
        self.market_agent = MarketContextAgent()
        self.devils_advocate = DevilsAdvocateAgent()
        self.synthesizer = SynthesizerAgent()
    
    def run(self, loan_application: LoanApplication) -> CommitteeState:
        """
        Run the full risk committee workflow.
        
        Args:
            loan_application: Loan application data
            
        Returns:
            CommitteeState with all assessments and final decision
        """
        # Initialize state
        state = CommitteeState(
            loan_application=loan_application,
            workflow_started=datetime.utcnow()
        )
        
        state.add_audit_entry("Workflow", "started", {
            "loan_id": loan_application.loan_id,
            "borrower": loan_application.borrower_name,
            "amount": loan_application.amount
        })
        
        # Step 1: Credit Risk Assessment
        state.credit_risk_assessment = self.credit_assessor.assess(state)
        
        # Step 2: ESG Risk Assessment
        state.esg_risk_assessment = self.esg_agent.assess(state)
        
        # Step 3: Market Context Assessment
        state.market_context_assessment = self.market_agent.assess(state)
        
        # Step 4: Devil's Advocate Challenge
        state.devils_advocate_assessment = self.devils_advocate.assess(state)
        
        # Step 5: Final Synthesis
        state = self.synthesizer.synthesize(state)
        
        # Step 6: Auto-create approval request if REFER
        if state.final_decision and state.final_decision.value == "refer":
            self._create_approval_request(state, loan_application)
        
        state.add_audit_entry("Workflow", "completed", {
            "final_decision": state.final_decision.value if state.final_decision else None,
            "consensus": state.consensus_achieved,
            "total_agents": len(state.get_all_assessments())
        })
        
        return state
    
    def _create_approval_request(self, state: CommitteeState, loan: LoanApplication):
        """Create an approval request for REFER decision."""
        try:
            from .approval_queue import get_approval_queue
            
            queue = get_approval_queue()
            
            # Calculate vote breakdown
            votes = {}
            for a in state.get_all_assessments():
                v = a.vote.value
                votes[v] = votes.get(v, 0) + 1
            
            request = queue.create_request(
                loan_id=loan.loan_id,
                borrower_name=loan.borrower_name,
                amount=loan.amount,
                sector=loan.sector,
                committee_confidence=state.final_confidence or 0.0,
                committee_reasoning=state.final_reasoning or "",
                vote_breakdown=votes
            )
            
            state.add_audit_entry("ApprovalQueue", "request_created", {
                "request_id": request.request_id,
                "status": "pending"
            })
        except Exception as e:
            # Don't fail workflow if approval creation fails
            state.add_audit_entry("ApprovalQueue", "creation_failed", {
                "error": str(e)
            })


def run_risk_committee(
    loan_id: str,
    borrower_name: str,
    sector: str,
    amount: float,
    annual_revenue: float,  # REQUIRED - no default
    location: str,  # REQUIRED - no default
    term_months: int = 60,
    interest_rate: float = 0.05,
    collateral_value: float = 0.0,
    existing_debt: float = 0.0,
    credit_score: int = 700,
    employment_length: str = "5 years",
    home_ownership: str = "RENT"
) -> Dict[str, Any]:
    """
    Convenience function to run the Risk Committee workflow.
    
    Returns the complete state as a dictionary.
    """
    loan = LoanApplication(
        loan_id=loan_id,
        borrower_name=borrower_name,
        sector=sector,
        amount=amount,
        term_months=term_months,
        interest_rate=interest_rate,
        collateral_value=collateral_value,
        existing_debt=existing_debt,
        annual_revenue=annual_revenue,
        credit_score=credit_score,
        location=location,
        employment_length=employment_length,
        home_ownership=home_ownership
    )
    
    workflow = RiskCommitteeWorkflow()
    state = workflow.run(loan)
    
    result = state.to_dict()
    result["success"] = True
    
    return result


# Quick test
if __name__ == "__main__":
    result = run_risk_committee(
        loan_id="TEST-001",
        borrower_name="Test Corporation",
        sector="energy",
        amount=5000000,
        credit_score=720
    )
    
    import json
    print(json.dumps(result, indent=2, default=str))
