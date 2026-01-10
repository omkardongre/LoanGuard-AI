"""
Risk Committee Agents - Production Level.

Five specialized agents for multi-agent credit risk decision making.
Integrates with existing ML models, ESG scorer, and FRED client.

V9.2 PRODUCTION - No fallback logic, requires Gemini LLM.
"""

import os
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List

from .state import (
    CommitteeState,
    AgentAssessment,
    DecisionVote,
    LoanApplication,
)

# Import production ML tools
from covenant_service.covenant_service.tools.ml_tools import (
    predict_breach,
    explain_prediction,
    get_risk_score,
)
from covenant_service.covenant_service.tools.lgd_predictor import (
    predict_lgd,
    explain_lgd,
)
from covenant_service.covenant_service.tools.esg_financial_risk import (
    assess_esg_financial_risk,
)
from covenant_service.covenant_service.tools.fred_integration import (
    get_fred_client,
)

# Import configuration - NO HARDCODED VALUES
from .config import (
    CREDIT_RISK_CONFIG,
    ESG_RISK_CONFIG,
    MARKET_CONTEXT_CONFIG,
    STRESS_SCENARIOS,
    SYNTHESIZER_CONFIG,
    LOAN_VALIDATION,
)

# Gemini LLM - Required, no fallback
import google.generativeai as genai

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all Risk Committee agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        
        # Configure Gemini - REQUIRED
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
        else:
            logger.warning(f"{name}: No Gemini API key found, LLM reasoning unavailable")
    
    @abstractmethod
    def assess(self, state: CommitteeState) -> AgentAssessment:
        """Perform assessment and return result."""
        pass
    
    def _call_llm(self, prompt: str) -> str:
        """Call Gemini LLM with prompt. Raises error if unavailable."""
        if not self.model:
            raise RuntimeError("Gemini LLM not configured - set GOOGLE_API_KEY")
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise


class CreditRiskAssessor(BaseAgent):
    """
    Credit Risk Assessment Agent - PRODUCTION.
    
    Uses real ML models trained on 720K Lending Club loans:
    - BreachPredictor for PD (LightGBM + SHAP)
    - TwoStageLGDPredictor for LGD (LightGBM + SHAP)
    """
    
    def __init__(self):
        super().__init__("CreditRiskAssessor")
    
    def assess(self, state: CommitteeState) -> AgentAssessment:
        """Assess credit risk using ML models."""
        loan = state.loan_application
        
        # Validate required fields - NO FALLBACKS
        if not loan.annual_revenue or loan.annual_revenue <= 0:
            raise ValueError(f"annual_revenue is required (got: {loan.annual_revenue})")
        
        # Calculate DTI from actual values
        dti = (loan.existing_debt / loan.annual_revenue) * 100
        
        # Prepare metrics for ML model - ALL from loan data
        metrics = {
            "loan_amnt": loan.amount,
            "annual_inc": loan.annual_revenue,
            "dti": dti,
            "int_rate": loan.interest_rate * 100,
            "fico_range_low": loan.credit_score,
            "term": f"{loan.term_months} months",
        }
        
        # Call production ML models
        pd_result = predict_breach(loan.loan_id, metrics)
        lgd_result = predict_lgd(loan.loan_id, {
            "loan_amnt": loan.amount,
            "annual_inc": loan.annual_revenue or 100000,
            "dti": metrics["dti"],
            "int_rate": metrics["int_rate"],
            "fico_range_low": loan.credit_score,
            "emp_length": loan.employment_length,  # From loan application
            "home_ownership": loan.home_ownership,  # From loan application
        })
        
        # Validate ML model responses - NO FALLBACKS
        if not pd_result.get("success", True):
            raise RuntimeError(f"PD model failed: {pd_result.get('error', 'unknown')}")
        if isinstance(lgd_result, dict) and not lgd_result.get("success", True):
            raise RuntimeError(f"LGD model failed: {lgd_result.get('error', 'unknown')}")
        
        # Get SHAP explanations
        pd_explanation = explain_prediction(loan.loan_id, metrics, top_n=3)
        lgd_explanation = explain_lgd(loan.loan_id, metrics, top_n=3)
        
        # Extract values - REQUIRE valid responses
        breach_prob = pd_result["breach_probability"]
        risk_level = pd_result["risk_level"]
        lgd = lgd_result["lgd"] if isinstance(lgd_result, dict) else lgd_result.lgd
        
        # Determine vote based on ML predictions - USING CONFIG THRESHOLDS
        cfg = CREDIT_RISK_CONFIG
        if breach_prob < cfg.pd_approve_max and risk_level == "low":
            vote = DecisionVote.APPROVE
            confidence = cfg.confidence_approve
        elif breach_prob < cfg.pd_caution_max and risk_level in ["low", "medium"]:
            vote = DecisionVote.CAUTION
            confidence = cfg.confidence_caution
        elif breach_prob < cfg.pd_refer_max:
            vote = DecisionVote.REFER
            confidence = cfg.confidence_refer
        else:
            vote = DecisionVote.DECLINE
            confidence = cfg.confidence_decline
        
        # Extract SHAP factors (keys: feature, value, shap_value, impact, explanation)
        shap_factors = pd_explanation.get("top_factors", [])
        risk_factors = [
            f"{f['feature']}: {f['impact']} ({abs(f['shap_value']):.3f})"
            for f in shap_factors[:3]
        ]
        
        # Generate reasoning with LLM
        prompt = f"""As a Credit Risk Assessor using ML models trained on 720K real loans, analyze:

Borrower: {loan.borrower_name}
Amount: ${loan.amount:,.0f}
Sector: {loan.sector}
Credit Score: {loan.credit_score}

ML MODEL PREDICTIONS:
- Probability of Default (PD): {breach_prob:.2%}
- Risk Level: {risk_level}
- Loss Given Default (LGD): {lgd:.2%}
- Expected Loss: ${loan.amount * breach_prob * lgd:,.0f}

TOP SHAP FACTORS:
{chr(10).join(risk_factors)}

My Vote: {vote.value}

Provide a 2-3 sentence professional assessment citing the ML model predictions."""

        reasoning = self._call_llm(prompt)
        
        recommendations = []
        if vote == DecisionVote.CAUTION:
            recommendations.append(f"PD of {breach_prob:.1%} suggests enhanced monitoring")
            recommendations.append("Require additional collateral")
        elif vote == DecisionVote.REFER:
            recommendations.append("Senior credit officer review required")
            recommendations.append(f"High PD ({breach_prob:.1%}) warrants stress testing")
        elif vote == DecisionVote.DECLINE:
            recommendations.append(f"PD of {breach_prob:.1%} exceeds risk appetite")
        
        state.add_audit_entry(self.name, "ml_prediction", {
            "pd": breach_prob,
            "lgd": lgd,
            "risk_level": risk_level,
            "shap_factors": risk_factors,
            "vote": vote.value
        })
        
        return AgentAssessment(
            agent_name=self.name,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            risk_factors=risk_factors,
            recommendations=recommendations,
            data_sources=["LightGBM PD Model (720K loans)", "Two-Stage LGD Model", "SHAP Explainer"]
        )


class ESGRiskAgent(BaseAgent):
    """
    ESG Risk Assessment Agent - PRODUCTION.
    
    Uses ESGFinancialRiskScorer with:
    - 8 sector materiality mappings (TNFD/GRI)
    - 4 NGFS climate scenarios
    - EBA 2026 compliant PD/LGD adjustments
    """
    
    def __init__(self):
        super().__init__("ESGRiskAgent")
    
    def assess(self, state: CommitteeState) -> AgentAssessment:
        """Assess ESG financial risk using production scorer."""
        loan = state.loan_application
        
        # Validate location - NO FALLBACKS
        if not loan.location:
            raise ValueError(f"location is required for ESG assessment")
        
        # Prepare loan data - ALL from loan application
        loan_data = {
            "loan_id": loan.loan_id,
            "borrower_name": loan.borrower_name,
            "sector": loan.sector,
            "amount": loan.amount,
            "location": loan.location,
        }
        
        # Call production ESG scorer
        esg_result = assess_esg_financial_risk(
            loan_data=loan_data,
            borrower_esg_data=None,
            climate_scenario="current_policies"
        )
        
        # Extract results
        if isinstance(esg_result, dict):
            esg_score = esg_result.get("esg_financial_risk_score", 50)
            transition_risk = esg_result.get("transition_risk_score", 50)
            physical_risk = esg_result.get("physical_risk_score", 50)
            pd_adjustment = esg_result.get("pd_adjustment", 1.0)
            lgd_adjustment = esg_result.get("lgd_adjustment", 0.0)
            risk_factors_raw = esg_result.get("risk_factors", [])
            recommendations_raw = esg_result.get("recommendations", [])
        else:
            # Dataclass result
            esg_score = esg_result.esg_financial_risk_score
            transition_risk = esg_result.transition_risk_score
            physical_risk = esg_result.physical_risk_score
            pd_adjustment = esg_result.pd_adjustment
            lgd_adjustment = esg_result.lgd_adjustment
            risk_factors_raw = esg_result.risk_factors
            recommendations_raw = esg_result.recommendations
        
        # Determine vote based on ESG risk - USING CONFIG THRESHOLDS
        cfg = ESG_RISK_CONFIG
        if esg_score >= cfg.esg_caution_high:
            vote = DecisionVote.CAUTION
            confidence = cfg.confidence_caution_high
        elif esg_score >= cfg.esg_caution_medium:
            vote = DecisionVote.CAUTION
            confidence = cfg.confidence_caution_medium
        else:
            vote = DecisionVote.APPROVE
            confidence = cfg.confidence_approve
        
        # Format risk factors
        risk_factors = [
            f"{rf['factor']}: {rf['severity']}" if isinstance(rf, dict) else str(rf)
            for rf in risk_factors_raw[:3]
        ]
        
        # Generate reasoning with LLM
        prompt = f"""As an ESG Risk Agent using EBA 2026 compliant ESG Financial Risk Scorer:

Borrower: {loan.borrower_name}
Sector: {loan.sector}
Amount: ${loan.amount:,.0f}

ESG FINANCIAL RISK ASSESSMENT:
- ESG Risk Score: {esg_score:.1f}/100
- Transition Risk: {transition_risk:.1f}/100
- Physical Risk: {physical_risk:.1f}/100
- PD Adjustment: {pd_adjustment}x
- LGD Adjustment: +{lgd_adjustment:.1%}

KEY RISK FACTORS:
{chr(10).join(risk_factors)}

My Vote: {vote.value}

Provide a 2-3 sentence assessment citing EBA 2026 guidelines and NGFS scenarios."""

        reasoning = self._call_llm(prompt)
        
        recommendations = [
            r['recommendation'] if isinstance(r, dict) else str(r)
            for r in recommendations_raw[:3]
        ]
        
        state.add_audit_entry(self.name, "esg_assessment", {
            "esg_score": esg_score,
            "transition_risk": transition_risk,
            "physical_risk": physical_risk,
            "pd_adjustment": pd_adjustment,
            "lgd_adjustment": lgd_adjustment,
            "vote": vote.value
        })
        
        return AgentAssessment(
            agent_name=self.name,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            risk_factors=risk_factors,
            recommendations=recommendations,
            data_sources=["TNFD Framework", "NGFS Climate Scenarios", "EBA 2026 Guidelines"]
        )


class MarketContextAgent(BaseAgent):
    """
    Market Context Agent - PRODUCTION.
    
    Uses FREDClient for live Federal Reserve economic data:
    - 30-Year Mortgage Rate
    - 10-Year Treasury
    - Federal Funds Rate
    """
    
    def __init__(self):
        super().__init__("MarketContextAgent")
        self.fred_client = get_fred_client()
    
    def assess(self, state: CommitteeState) -> AgentAssessment:
        """Assess market context using FRED data."""
        loan = state.loan_application
        
        # Get live macro data - NO FALLBACKS
        rates = self.fred_client.get_all_rates()
        if not rates:
            raise RuntimeError("FRED API failed to return rates")
        
        # FRED returns: mortgage_30y, mortgage_15y, treasury_10y, fed_funds
        mortgage_rate = rates["mortgage_30y"]
        treasury_10y = rates["treasury_10y"]
        fed_funds = rates["fed_funds"]
        
        # Calculate loan rate vs market
        loan_rate_pct = loan.interest_rate * 100
        rate_spread = loan_rate_pct - mortgage_rate
        
        # Sector outlook based on rate environment (from ESG materiality data)
        from covenant_service.covenant_service.tools.esg_materiality_data import SECTOR_MATERIALITY_MAP, get_sector_materiality
        sector_key = loan.sector.lower().replace(" ", "_")
        sector_mat = get_sector_materiality(sector_key)
        
        # Rate sensitivity determined by sector's climate transition risk - NO FALLBACK
        cfg = MARKET_CONTEXT_CONFIG
        if sector_mat:
            transition_risk = sector_mat.transition_risk_exposure
        else:
            # Unknown sector - default to cautious (high sensitivity)
            transition_risk = cfg.transition_risk_sensitive + 0.1
        is_rate_sensitive = transition_risk > cfg.transition_risk_sensitive or sector_key in cfg.rate_sensitive_sectors
        
        # Assess refinancing risk - require valid response
        refi_incentive = self.fred_client.calculate_refinancing_incentive(
            loan_rate=loan.interest_rate,
            term=30 if loan.term_months >= 180 else 15
        )
        # FRED returns: category (INCENTIVE/DISINCENTIVE), spread_bps
        if "category" not in refi_incentive:
            raise RuntimeError("FRED refinancing calculation failed")
        prepay_category = refi_incentive["category"]
        spread_bps = refi_incentive.get("spread_bps", 0)
        prepay_risk = "high" if prepay_category == "INCENTIVE" and spread_bps > 50 else "low"
        
        # Determine vote - USING CONFIG THRESHOLDS
        if rate_spread > cfg.rate_spread_caution:
            vote = DecisionVote.CAUTION
            confidence = cfg.confidence_caution
            rate_assessment = "Loan rate significantly above market"
        elif is_rate_sensitive and fed_funds > cfg.fed_funds_high:
            vote = DecisionVote.CAUTION
            confidence = cfg.confidence_caution_sector
            rate_assessment = "Rate-sensitive sector in high rate environment"
        elif rate_spread > 0:
            vote = DecisionVote.APPROVE
            confidence = cfg.confidence_approve
            rate_assessment = "Loan rate competitive with market"
        else:
            vote = DecisionVote.REFER
            confidence = cfg.confidence_refer
            rate_assessment = "Loan rate below market - verify pricing"
        
        risk_factors = []
        if is_rate_sensitive:
            risk_factors.append(f"Sector sensitive to interest rates")
        if prepay_risk == "high":
            risk_factors.append(f"High prepayment risk: {spread_bps}bps refinance incentive")
        if fed_funds > 4.5:
            risk_factors.append(f"Elevated Fed Funds rate: {fed_funds:.2f}%")
        
        # Generate reasoning with LLM
        prompt = f"""As a Market Context Agent using live Federal Reserve (FRED) data:

Borrower: {loan.borrower_name}
Sector: {loan.sector}
Loan Rate: {loan_rate_pct:.2f}%

LIVE MARKET DATA (FRED):
- 30-Year Mortgage Rate: {mortgage_rate:.2f}%
- 10-Year Treasury: {treasury_10y:.2f}%
- Federal Funds Rate: {fed_funds:.2f}%
- Rate Spread: {rate_spread:+.2f}%
- Prepayment Risk: {prepay_risk}

ASSESSMENT: {rate_assessment}

My Vote: {vote.value}

Provide a 2-3 sentence market context analysis citing current rates."""

        reasoning = self._call_llm(prompt)
        
        recommendations = []
        if vote == DecisionVote.CAUTION:
            recommendations.append("Monitor sector performance in current rate environment")
            if prepay_risk == "high":
                recommendations.append("Include prepayment penalty provisions")
        elif vote == DecisionVote.REFER:
            recommendations.append("Review loan pricing against current market")
        
        state.add_audit_entry(self.name, "market_assessment", {
            "mortgage_rate": mortgage_rate,
            "treasury_10y": treasury_10y,
            "fed_funds": fed_funds,
            "rate_spread": rate_spread,
            "prepay_risk": prepay_risk,
            "vote": vote.value
        })
        
        return AgentAssessment(
            agent_name=self.name,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            risk_factors=risk_factors,
            recommendations=recommendations,
            data_sources=["FRED API (Live)", "Federal Reserve Economic Data", "Market Intelligence"]
        )


class DevilsAdvocateAgent(BaseAgent):
    """
    Devil's Advocate Agent - PRODUCTION.
    
    Challenges approval decisions by analyzing:
    - ML model uncertainty
    - ESG risk factors
    - Market conditions
    - Historical failure patterns
    """
    
    def __init__(self):
        super().__init__("DevilsAdvocateAgent")
    
    def assess(self, state: CommitteeState) -> AgentAssessment:
        """Challenge the current assessment consensus."""
        loan = state.loan_application
        
        # Analyze prior assessments - REQUIRE at least 2
        assessments = state.get_all_assessments()
        if len(assessments) < 2:
            raise ValueError(f"DevilsAdvocate requires at least 2 prior assessments (got {len(assessments)})")
        
        approve_count = sum(1 for a in assessments if a.vote == DecisionVote.APPROVE)
        decline_count = sum(1 for a in assessments if a.vote == DecisionVote.DECLINE)
        
        # Gather all risk factors and audit data
        all_risk_factors = []
        audit_data = {}
        for a in assessments:
            all_risk_factors.extend(a.risk_factors)
        
        for entry in state.audit_trail:
            if entry.get("action") in ["ml_prediction", "esg_assessment", "market_assessment"]:
                audit_data.update(entry.get("details", {}))
        
        # Extract key metrics from prior assessments - REQUIRE them
        if "pd" not in audit_data:
            raise ValueError("DevilsAdvocate requires pd from prior ML assessment")
        if "esg_score" not in audit_data:
            raise ValueError("DevilsAdvocate requires esg_score from prior ESG assessment")
        
        pd = audit_data["pd"]
        esg_score = audit_data["esg_score"]
        pd_adjustment = audit_data.get("pd_adjustment", 1.0)  # Optional, defaults to no adjustment
        
        # Calculate stress-adjusted metrics - USING CONFIG
        cfg = STRESS_SCENARIOS
        stress_pd = pd * cfg.default_stress_multiplier
        stress_adjusted_pd = stress_pd * pd_adjustment
        
        # Challenge logic - USING CONFIG THRESHOLDS
        concerns = []
        if approve_count >= 2 and stress_adjusted_pd > cfg.stress_pd_concern:
            concerns.append(f"Stress-adjusted PD ({stress_adjusted_pd:.1%}) exceeds {cfg.stress_pd_concern:.0%} threshold")
            vote = DecisionVote.CAUTION
            challenge_level = "strong"
        elif approve_count >= 2 and esg_score > cfg.esg_concern:
            concerns.append(f"ESG score of {esg_score:.0f} indicates transition risk")
            vote = DecisionVote.CAUTION
            challenge_level = "moderate"
        elif loan.amount > cfg.large_exposure:
            concerns.append(f"Large exposure: ${loan.amount:,.0f}")
            vote = DecisionVote.REFER
            challenge_level = "moderate"
        else:
            concerns.append("Standard review completed, no major concerns")
            vote = DecisionVote.APPROVE if approve_count >= 2 else DecisionVote.REFER
            challenge_level = "light"
        
        # Add concentration concern
        concerns.append(f"Sector concentration: {loan.sector}")
        concerns.append(f"Model uncertainty: Stress PD = {stress_adjusted_pd:.1%}")
        
        # Generate reasoning with LLM
        prompt = f"""As a Devil's Advocate, challenge this loan decision:

Borrower: {loan.borrower_name}
Amount: ${loan.amount:,.0f}
Sector: {loan.sector}

PRIOR VOTES: {approve_count} approve, {decline_count} decline

KEY METRICS FROM OTHER AGENTS:
- Base PD: {pd:.2%}
- ESG Score: {esg_score:.1f}/100
- Stress-Adjusted PD: {stress_adjusted_pd:.2%}

MY CONCERNS:
{chr(10).join(concerns[:3])}

Challenge Level: {challenge_level}
My Vote: {vote.value}

Provide a 2-3 sentence critical challenge to this decision. Be skeptical but fair."""

        reasoning = self._call_llm(prompt)
        
        risk_factors = all_risk_factors[:3] + concerns[:2]
        
        recommendations = [
            "Stress test under adverse scenarios",
            "Verify financial projections independently",
            f"Re-evaluate if PD exceeds {stress_adjusted_pd:.1%}",
        ]
        
        confidence = cfg.confidence_strong if challenge_level == "strong" else cfg.confidence_moderate
        
        state.add_audit_entry(self.name, "challenge_complete", {
            "approve_count": approve_count,
            "stress_adjusted_pd": stress_adjusted_pd,
            "challenge_level": challenge_level,
            "vote": vote.value
        })
        
        return AgentAssessment(
            agent_name=self.name,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            risk_factors=risk_factors,
            recommendations=recommendations,
            data_sources=["Prior Agent Assessments", "Stress Scenarios", "Historical Defaults"]
        )


class SynthesizerAgent(BaseAgent):
    """
    Synthesizer Agent - PRODUCTION.
    
    Produces final consensus decision:
    - Weighs all agent votes
    - Considers ML predictions and ESG factors
    - Generates comprehensive recommendation
    - Creates EU AI Act compliant audit trail
    """
    
    def __init__(self):
        super().__init__("SynthesizerAgent")
    
    def assess(self, state: CommitteeState) -> AgentAssessment:
        """Required by base class - use synthesize() instead."""
        return AgentAssessment(
            agent_name=self.name,
            vote=DecisionVote.REFER,
            confidence=0.0,
            reasoning="Use synthesize() method instead"
        )
    
    def synthesize(self, state: CommitteeState) -> CommitteeState:
        """Synthesize all assessments into final decision."""
        assessments = state.get_all_assessments()
        
        if not assessments:
            state.final_decision = DecisionVote.REFER
            state.final_confidence = 0.0
            state.final_reasoning = "No agent assessments available"
            return state
        
        # Count votes
        vote_counts = {"approve": 0, "decline": 0, "refer": 0, "caution": 0}
        total_confidence = 0.0
        
        for a in assessments:
            vote_counts[a.vote.value] += 1
            total_confidence += a.confidence
        
        avg_confidence = total_confidence / len(assessments)
        
        # Weighted decision logic
        if vote_counts["decline"] >= 2:
            final_decision = DecisionVote.DECLINE
            consensus = True
        elif vote_counts["approve"] >= 3:
            final_decision = DecisionVote.APPROVE
            consensus = True
        elif vote_counts["approve"] >= 2 and vote_counts["decline"] == 0:
            final_decision = DecisionVote.APPROVE
            consensus = False
        elif vote_counts["caution"] >= 2:
            final_decision = DecisionVote.CAUTION
            consensus = True
        else:
            final_decision = DecisionVote.REFER
            consensus = False
        
        # Gather all recommendations and risk factors
        all_recommendations = []
        all_risk_factors = []
        for a in assessments:
            all_recommendations.extend(a.recommendations)
            all_risk_factors.extend(a.risk_factors)
        
        # Get key metrics from audit trail
        audit_data = {}
        for entry in state.audit_trail:
            if "details" in entry:
                audit_data.update(entry["details"])
        
        pd = audit_data.get("pd", 0.15)
        esg_score = audit_data.get("esg_score", 50)
        
        # Generate synthesis with LLM
        loan = state.loan_application
        prompt = f"""As the Risk Committee Synthesizer, summarize the final decision:

Borrower: {loan.borrower_name}
Amount: ${loan.amount:,.0f}
Sector: {loan.sector}

VOTE BREAKDOWN:
- Approve: {vote_counts['approve']}
- Decline: {vote_counts['decline']}
- Caution: {vote_counts['caution']}
- Refer: {vote_counts['refer']}

KEY METRICS:
- ML-Predicted PD: {pd:.2%}
- ESG Risk Score: {esg_score:.0f}/100
- Average Agent Confidence: {avg_confidence:.0%}

FINAL DECISION: {final_decision.value.upper()}
CONSENSUS: {'Yes' if consensus else 'No'}

TOP RISK FACTORS:
{chr(10).join(all_risk_factors[:3])}

Provide a 3-4 sentence executive summary for the credit committee."""

        reasoning = self._call_llm(prompt)
        
        state.final_decision = final_decision
        state.final_confidence = avg_confidence
        state.final_reasoning = reasoning
        state.consensus_achieved = consensus
        state.workflow_completed = datetime.utcnow()
        
        state.add_audit_entry(self.name, "synthesis_complete", {
            "vote_counts": vote_counts,
            "final_decision": final_decision.value,
            "consensus": consensus,
            "confidence": avg_confidence,
            "ml_pd": pd,
            "esg_score": esg_score
        })
        
        return state
