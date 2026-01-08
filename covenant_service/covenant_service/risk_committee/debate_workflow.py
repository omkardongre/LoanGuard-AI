"""
Multi-Round Debate Workflow - Production Level.

Implements iterative agent debate with convergence detection.
Agents can challenge each other and revise their assessments.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .state import CommitteeState, LoanApplication, AgentAssessment, DecisionVote
from .config import DEBATE_CONFIG
from .agents import (
    CreditRiskAssessor,
    ESGRiskAgent,
    MarketContextAgent,
    DevilsAdvocateAgent,
    SynthesizerAgent,
)


class MultiRoundDebateWorkflow:
    """
    Enhanced workflow with multi-round agent debate.
    
    Agents assess in rounds, with later agents able to challenge
    earlier assessments. The workflow continues until:
    1. Consensus is achieved (75%+ agreement)
    2. Maximum rounds reached
    3. No significant confidence improvement
    """
    
    def __init__(self, max_rounds: int = None):
        """
        Initialize the debate workflow.
        
        Args:
            max_rounds: Maximum debate rounds (default from config)
        """
        self.max_rounds = max_rounds or DEBATE_CONFIG.max_rounds
        
        # Initialize agents
        self.credit_assessor = CreditRiskAssessor()
        self.esg_agent = ESGRiskAgent()
        self.market_agent = MarketContextAgent()
        self.devils_advocate = DevilsAdvocateAgent()
        self.synthesizer = SynthesizerAgent()
    
    def run(self, loan_application: LoanApplication) -> CommitteeState:
        """
        Run multi-round debate workflow.
        
        Args:
            loan_application: Loan application data
            
        Returns:
            CommitteeState with debate history and final decision
        """
        # Initialize state
        state = CommitteeState(
            loan_application=loan_application,
            workflow_started=datetime.utcnow(),
            max_rounds=self.max_rounds
        )
        
        state.add_audit_entry("DebateWorkflow", "started", {
            "loan_id": loan_application.loan_id,
            "max_rounds": self.max_rounds
        })
        
        # Run debate rounds
        for round_num in range(1, self.max_rounds + 1):
            state.current_round = round_num
            
            state.add_audit_entry("DebateWorkflow", f"round_{round_num}_started", {
                "round": round_num
            })
            
            # Run all agents for this round
            state = self._run_round(state, round_num)
            
            # Record round results
            round_result = self._record_round_result(state, round_num)
            state.round_history.append(round_result)
            
            # Check for convergence
            if self._check_convergence(state, round_num):
                state.convergence_achieved = True
                state.convergence_round = round_num
                state.add_audit_entry("DebateWorkflow", "convergence_achieved", {
                    "round": round_num,
                    "consensus": round_result["consensus_rate"]
                })
                break
            
            # If not last round, prepare for next round
            if round_num < self.max_rounds:
                state.add_audit_entry("DebateWorkflow", "continuing_debate", {
                    "reason": "No consensus achieved",
                    "current_consensus": round_result["consensus_rate"]
                })
        
        # Final synthesis
        state = self.synthesizer.synthesize(state)
        
        # Handle REFER approval creation
        if state.final_decision and state.final_decision.value == "refer":
            self._create_approval_request(state, loan_application)
        
        state.workflow_completed = datetime.utcnow()
        state.add_audit_entry("DebateWorkflow", "completed", {
            "final_decision": state.final_decision.value if state.final_decision else None,
            "rounds_completed": state.current_round,
            "convergence_achieved": state.convergence_achieved
        })
        
        return state
    
    def _run_round(self, state: CommitteeState, round_num: int) -> CommitteeState:
        """Run a single debate round with actual agent reassessment."""
        # All rounds: run full assessments (agents consider previous context)
        if round_num == 1:
            # Round 1: Initial assessments
            state.credit_risk_assessment = self.credit_assessor.assess(state)
            state.esg_risk_assessment = self.esg_agent.assess(state)
            state.market_context_assessment = self.market_agent.assess(state)
            state.devils_advocate_assessment = self.devils_advocate.assess(state)
        else:
            # Round 2+: Re-assess with challenge context
            # Store previous round's state for comparison
            prev_credit = state.credit_risk_assessment
            prev_esg = state.esg_risk_assessment
            prev_market = state.market_context_assessment
            prev_devil = state.devils_advocate_assessment
            
            # Devil's Advocate re-challenges with knowledge of current positions
            state.devils_advocate_assessment = self.devils_advocate.assess(state)
            
            # Check if strong challenge was raised
            strong_challenge = (
                state.devils_advocate_assessment and 
                state.devils_advocate_assessment.vote == DecisionVote.CAUTION and
                state.devils_advocate_assessment.confidence > 0.7
            )
            
            if strong_challenge:
                state.add_audit_entry("DebateWorkflow", "strong_challenge", {
                    "round": round_num,
                    "challenger": "DevilsAdvocateAgent",
                    "challenge_confidence": state.devils_advocate_assessment.confidence,
                    "challenge_reasoning": state.devils_advocate_assessment.key_concerns[:2] if state.devils_advocate_assessment.key_concerns else []
                })
                
                # Other agents actually re-assess with challenge context
                # They will see Devil's Advocate's concerns in state
                state.credit_risk_assessment = self.credit_assessor.assess(state)
                state.esg_risk_assessment = self.esg_agent.assess(state)
                state.market_context_assessment = self.market_agent.assess(state)
                
                # Track which agents changed their votes
                changes = []
                if prev_credit and state.credit_risk_assessment.vote != prev_credit.vote:
                    changes.append({"agent": "CreditRiskAssessor", 
                                   "from": prev_credit.vote.value, 
                                   "to": state.credit_risk_assessment.vote.value})
                if prev_esg and state.esg_risk_assessment.vote != prev_esg.vote:
                    changes.append({"agent": "ESGRiskAgent", 
                                   "from": prev_esg.vote.value, 
                                   "to": state.esg_risk_assessment.vote.value})
                if prev_market and state.market_context_assessment.vote != prev_market.vote:
                    changes.append({"agent": "MarketContextAgent", 
                                   "from": prev_market.vote.value, 
                                   "to": state.market_context_assessment.vote.value})
                
                if changes:
                    state.add_audit_entry("DebateWorkflow", "votes_changed", {
                        "round": round_num,
                        "changes": changes
                    })
                
                # Apply additional confidence pressure if no votes changed
                if not changes:
                    self._apply_challenge_pressure(state, prev_credit, prev_esg, prev_market)
            else:
                # Moderate challenge - just refresh Devil's Advocate
                state.add_audit_entry("DebateWorkflow", "moderate_challenge", {
                    "round": round_num,
                    "challenger": "DevilsAdvocateAgent",
                    "no_reassessment_needed": True
                })
        
        return state
    
    def _apply_challenge_pressure(self, state: CommitteeState, 
                                  prev_credit=None, prev_esg=None, prev_market=None):
        """Apply pressure from Devil's Advocate challenge."""
        # Reduce confidence of APPROVE votes when challenged
        for assessment in [state.credit_risk_assessment, state.esg_risk_assessment, 
                          state.market_context_assessment]:
            if assessment and assessment.vote == DecisionVote.APPROVE:
                # Reduce confidence by 10%
                original_confidence = assessment.confidence
                assessment.confidence = max(0.5, assessment.confidence - 0.10)
                
                state.add_audit_entry("DebateWorkflow", "confidence_adjusted", {
                    "agent": assessment.agent_name,
                    "original": original_confidence,
                    "adjusted": assessment.confidence,
                    "reason": "Devil's Advocate challenge"
                })
    
    def _record_round_result(self, state: CommitteeState, round_num: int) -> Dict[str, Any]:
        """Record the result of a debate round."""
        votes = state.get_vote_summary()
        assessments = state.get_all_assessments()
        
        total_votes = sum(votes.values())
        majority_vote = max(votes, key=votes.get)
        consensus_rate = votes[majority_vote] / total_votes if total_votes > 0 else 0
        
        avg_confidence = sum(a.confidence for a in assessments) / len(assessments) if assessments else 0
        
        return {
            "round": round_num,
            "votes": votes,
            "majority_vote": majority_vote,
            "consensus_rate": consensus_rate,
            "average_confidence": avg_confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _check_convergence(self, state: CommitteeState, round_num: int) -> bool:
        """Check if agents have converged on a decision."""
        if round_num < DEBATE_CONFIG.min_rounds:
            return False
        
        if not state.round_history:
            return False
        
        latest = state.round_history[-1]
        
        # Check if consensus threshold met
        if latest["consensus_rate"] >= DEBATE_CONFIG.consensus_threshold:
            return True
        
        # Check if confidence isn't improving
        if len(state.round_history) >= 2:
            prev = state.round_history[-2]
            confidence_improvement = latest["average_confidence"] - prev["average_confidence"]
            
            if confidence_improvement < DEBATE_CONFIG.confidence_improvement_min:
                # Not improving, stop debate
                return True
        
        return False
    
    def _create_approval_request(self, state: CommitteeState, loan: LoanApplication):
        """Create approval request for REFER decisions."""
        try:
            from .approval_queue import get_approval_queue
            
            queue = get_approval_queue()
            votes = state.get_vote_summary()
            
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
            state.add_audit_entry("ApprovalQueue", "creation_failed", {
                "error": str(e)
            })


def run_multi_round_debate(
    loan_id: str,
    borrower_name: str,
    sector: str,
    amount: float,
    credit_score: int,
    annual_revenue: float,
    location: str,
    interest_rate: float = 0.05,
    employment_length: str = "5 years",
    home_ownership: str = "OWN",
    term_months: int = 36,
    collateral_value: float = None,
    existing_debt: float = 0,
    max_rounds: int = 2
) -> Dict[str, Any]:
    """
    Convenience function to run multi-round debate.
    
    Args:
        loan_id: Unique loan identifier
        borrower_name: Name of the borrower
        sector: Business sector
        amount: Loan amount
        credit_score: FICO credit score
        annual_revenue: Annual revenue
        location: Location for ESG assessment
        interest_rate: Interest rate (decimal)
        employment_length: Employment history
        home_ownership: Home ownership status
        term_months: Loan term in months
        collateral_value: Collateral value
        existing_debt: Existing debt
        max_rounds: Maximum debate rounds
        
    Returns:
        Dictionary with debate results
    """
    loan = LoanApplication(
        loan_id=loan_id,
        borrower_name=borrower_name,
        sector=sector,
        amount=amount,
        credit_score=credit_score,
        annual_revenue=annual_revenue,
        interest_rate=interest_rate,
        employment_length=employment_length,
        home_ownership=home_ownership,
        term_months=term_months,
        collateral_value=collateral_value or amount * 0.8,
        existing_debt=existing_debt,
        location=location
    )
    
    workflow = MultiRoundDebateWorkflow(max_rounds=max_rounds)
    state = workflow.run(loan)
    
    return state.to_dict()
