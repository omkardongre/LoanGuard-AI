"""
Loan Pricing Optimizer using RAROC.
V9 - Risk-Adjusted Return on Capital for optimal loan pricing.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class PricingResult:
    """RAROC-based pricing result."""
    loan_id: str
    
    # Input parameters
    loan_amount: float
    loan_term_years: float
    
    # Risk metrics (from ML models)
    pd: float
    lgd: float
    
    # Calculated values
    expected_loss: float
    economic_capital: float
    funding_cost: float
    operating_cost: float
    
    # Pricing outputs
    minimum_rate: float
    recommended_rate: float
    raroc: float
    raroc_target: float = 0.15  # 15% target RAROC
    
    # Breakdown
    risk_premium: float
    funding_spread: float
    profit_margin: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LoanPricingOptimizer:
    """
    RAROC-based loan pricing optimizer.
    
    RAROC = (Net Income - Expected Loss) / Economic Capital
    
    Where:
    - Net Income = Interest Income - Funding Cost - Operating Cost
    - Expected Loss = PD × LGD × EAD
    - Economic Capital = VaR(99%) - Expected Loss (typically 8-12% of EAD for banks)
    """
    
    def __init__(
        self,
        funding_rate: float = 0.045,  # 4.5% base funding cost
        operating_cost_pct: float = 0.015,  # 1.5% of loan amount
        target_raroc: float = 0.15,  # 15% target return
        capital_ratio: float = 0.10,  # 10% economic capital requirement
    ):
        self.funding_rate = funding_rate
        self.operating_cost_pct = operating_cost_pct
        self.target_raroc = target_raroc
        self.capital_ratio = capital_ratio
        
        # Lazy load ML predictors
        self._pd_predictor = None
        self._lgd_predictor = None
    
    @property
    def pd_predictor(self):
        """Lazy load Breach Predictor for PD."""
        if self._pd_predictor is None:
            from covenant_service.covenant_service.tools.ml_tools import get_predictor
            self._pd_predictor = get_predictor()
        return self._pd_predictor
    
    @property
    def lgd_predictor(self):
        """Lazy load LGD Predictor."""
        if self._lgd_predictor is None:
            from covenant_service.covenant_service.tools.lgd_predictor import get_lgd_predictor
            self._lgd_predictor = get_lgd_predictor()
        return self._lgd_predictor
    
    def get_real_pd(self, loan: Dict[str, Any]) -> float:
        """Get PD from trained ML model."""
        try:
            loan_id = loan.get('loan_id', 'pricing')
            metrics = {
                'loan_amnt': loan.get('loan_amount', loan.get('facility_amount', 100000)),
                'int_rate': loan.get('interest_rate', 10.0),
                'annual_inc': loan.get('annual_income', 75000),
                'dti': loan.get('debt_to_income', 20.0),
                'fico_range_low': loan.get('fico_score', 680),
            }
            result = self.pd_predictor.predict(loan_id, metrics)
            return result.breach_probability
        except Exception as e:
            logger.warning(f"PD prediction failed: {e}")
            return loan.get('pd', 0.08)
    
    def get_real_lgd(self, loan: Dict[str, Any]) -> float:
        """Get LGD from trained ML model."""
        try:
            loan_id = loan.get('loan_id', 'pricing')
            loan_data = {
                'loan_amnt': loan.get('loan_amount', loan.get('facility_amount', 100000)),
                'int_rate': loan.get('interest_rate', 10.0),
                'annual_inc': loan.get('annual_income', 75000),
                'dti': loan.get('debt_to_income', 20.0),
                'fico_range_low': loan.get('fico_score', 680),
            }
            result = self.lgd_predictor.predict(loan_id, loan_data)
            return result.lgd
        except Exception as e:
            logger.warning(f"LGD prediction failed: {e}")
            return loan.get('lgd', 0.45)
    
    def calculate_expected_loss(self, pd: float, lgd: float, ead: float) -> float:
        """Calculate Expected Loss = PD × LGD × EAD."""
        return pd * lgd * ead
    
    def calculate_economic_capital(self, ead: float, pd: float) -> float:
        """
        Calculate economic capital requirement.
        
        Simplified Basel III formula:
        EC = EAD × Capital Ratio × PD adjustment
        """
        # Risk-weight adjustment based on PD
        pd_adjustment = 1.0 + (pd * 5)  # Higher PD = higher capital
        return ead * self.capital_ratio * pd_adjustment
    
    def calculate_minimum_rate(
        self,
        ead: float,
        pd: float,
        lgd: float,
        term_years: float,
    ) -> float:
        """
        Calculate minimum interest rate to achieve target RAROC.
        
        RAROC = (Interest Income - Funding Cost - Operating Cost - EL) / EC
        
        Solving for Interest Rate:
        Rate = (RAROC × EC + Funding Cost + Operating Cost + EL) / EAD
        """
        expected_loss = self.calculate_expected_loss(pd, lgd, ead)
        economic_capital = self.calculate_economic_capital(ead, pd)
        
        # Annual costs
        annual_funding_cost = ead * self.funding_rate
        annual_operating_cost = ead * self.operating_cost_pct
        annual_expected_loss = expected_loss / term_years
        
        # Required interest income for target RAROC
        required_net_income = self.target_raroc * economic_capital + annual_expected_loss
        required_interest_income = required_net_income + annual_funding_cost + annual_operating_cost
        
        # Minimum rate
        minimum_rate = required_interest_income / ead
        
        return minimum_rate
    
    def optimize_pricing(
        self,
        loan: Dict[str, Any],
        use_real_ml: bool = True,
    ) -> PricingResult:
        """
        Calculate optimal loan pricing using RAROC.
        
        Args:
            loan: Loan data dictionary
            use_real_ml: Whether to use real ML predictions
            
        Returns:
            PricingResult with recommended pricing
        """
        loan_id = loan.get('loan_id', 'unknown')
        loan_amount = loan.get('loan_amount', loan.get('facility_amount', 100000))
        term_years = loan.get('term_years', loan.get('term', 5))
        
        # Get risk metrics
        if use_real_ml:
            pd = self.get_real_pd(loan)
            lgd = self.get_real_lgd(loan)
        else:
            pd = loan.get('pd', 0.08)
            lgd = loan.get('lgd', 0.45)
        
        # Calculate components
        expected_loss = self.calculate_expected_loss(pd, lgd, loan_amount)
        economic_capital = self.calculate_economic_capital(loan_amount, pd)
        funding_cost = loan_amount * self.funding_rate
        operating_cost = loan_amount * self.operating_cost_pct
        
        # Calculate minimum rate
        minimum_rate = self.calculate_minimum_rate(loan_amount, pd, lgd, term_years)
        
        # Add profit margin (0.5-1.5% based on risk)
        risk_margin = 0.005 + (pd * 0.1)  # Higher PD = higher margin
        recommended_rate = minimum_rate + risk_margin
        
        # Calculate actual RAROC at recommended rate
        interest_income = loan_amount * recommended_rate
        net_income = interest_income - funding_cost - operating_cost - (expected_loss / term_years)
        actual_raroc = net_income / economic_capital if economic_capital > 0 else 0
        
        # Breakdown
        risk_premium = pd * lgd * 100  # Risk premium as percentage
        funding_spread = self.funding_rate * 100
        profit_margin = risk_margin * 100
        
        return PricingResult(
            loan_id=loan_id,
            loan_amount=loan_amount,
            loan_term_years=term_years,
            pd=pd,
            lgd=lgd,
            expected_loss=round(expected_loss, 2),
            economic_capital=round(economic_capital, 2),
            funding_cost=round(funding_cost, 2),
            operating_cost=round(operating_cost, 2),
            minimum_rate=round(minimum_rate * 100, 2),  # As percentage
            recommended_rate=round(recommended_rate * 100, 2),  # As percentage
            raroc=round(actual_raroc * 100, 2),  # As percentage
            raroc_target=round(self.target_raroc * 100, 2),
            risk_premium=round(risk_premium, 2),
            funding_spread=round(funding_spread, 2),
            profit_margin=round(profit_margin, 2),
        )
    
    def price_portfolio(
        self,
        loans: list,
        use_real_ml: bool = True,
    ) -> Dict[str, Any]:
        """Price multiple loans and return summary."""
        results = [self.optimize_pricing(loan, use_real_ml) for loan in loans]
        
        avg_rate = sum(r.recommended_rate for r in results) / len(results) if results else 0
        avg_raroc = sum(r.raroc for r in results) / len(results) if results else 0
        total_el = sum(r.expected_loss for r in results)
        total_ec = sum(r.economic_capital for r in results)
        
        return {
            'success': True,
            'loan_count': len(results),
            'summary': {
                'avg_recommended_rate': round(avg_rate, 2),
                'avg_raroc': round(avg_raroc, 2),
                'total_expected_loss': round(total_el, 2),
                'total_economic_capital': round(total_ec, 2),
            },
            'loans': [r.to_dict() for r in results[:20]],
        }


# Singleton instance
_pricing_optimizer: Optional[LoanPricingOptimizer] = None


def get_pricing_optimizer() -> LoanPricingOptimizer:
    """Get or create pricing optimizer singleton."""
    global _pricing_optimizer
    if _pricing_optimizer is None:
        _pricing_optimizer = LoanPricingOptimizer()
    return _pricing_optimizer
