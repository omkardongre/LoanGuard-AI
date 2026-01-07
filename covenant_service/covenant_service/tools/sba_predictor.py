"""
SBA Commercial Loan Default Predictor.
V9 - Predict defaults for Small Business Administration loans.

SBA loans differ from consumer loans:
- Larger amounts ($50K - $5M+)
- Business-level metrics (employees, business age, NAICS industry)
- SBA guarantee percentage
- Different risk factors
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SBAPrediction:
    """SBA loan default prediction result."""
    loan_id: str
    default_probability: float
    risk_level: str
    confidence: float
    
    # Key risk factors
    top_factors: List[Dict[str, Any]]
    
    # Loan details
    loan_amount: float
    sba_guarantee_pct: float
    industry: str
    business_age_years: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# SBA-specific risk adjustments by industry (NAICS-based)
INDUSTRY_RISK_FACTORS = {
    'restaurants': 1.4,  # Higher failure rate
    'retail': 1.3,
    'construction': 1.2,
    'hospitality': 1.35,
    'healthcare': 0.8,
    'professional_services': 0.85,
    'technology': 1.1,
    'manufacturing': 0.9,
    'transportation': 1.15,
    'wholesale': 0.95,
    'agriculture': 1.25,
    'real_estate': 1.0,
    'default': 1.0,
}


class SBALoanPredictor:
    """
    SBA loan default predictor using business-level features.
    
    Uses a combination of:
    1. Base credit risk from consumer model (adapted)
    2. Business-specific risk factors
    3. SBA program adjustments
    """
    
    def __init__(self):
        self._base_predictor = None
        self._model_loaded = False
    
    @property
    def base_predictor(self):
        """Lazy load the base breach predictor."""
        if self._base_predictor is None:
            from covenant_service.covenant_service.tools.ml_tools import get_predictor
            self._base_predictor = get_predictor()
        return self._base_predictor
    
    def _calculate_base_pd(self, loan: Dict[str, Any]) -> float:
        """Get base PD from consumer model, adapted for business."""
        try:
            # Map business metrics to consumer equivalent
            metrics = {
                'loan_amnt': loan.get('loan_amount', 100000),
                'int_rate': loan.get('interest_rate', 8.0),
                'annual_inc': loan.get('business_revenue', loan.get('annual_revenue', 500000)),
                'dti': loan.get('debt_service_coverage', 30),  # DSC as proxy
                'fico_range_low': loan.get('owner_credit_score', 680),
            }
            result = self.base_predictor.predict(loan.get('loan_id', 'sba'), metrics)
            return result.breach_probability
        except Exception as e:
            logger.warning(f"Base PD calculation failed: {e}")
            return 0.10  # Default 10% baseline
    
    def _adjust_for_sba_guarantee(self, base_pd: float, guarantee_pct: float) -> float:
        """
        Adjust PD based on SBA guarantee percentage.
        
        Higher guarantee = More rigorous SBA review = Lower risk
        But also = Riskier loans get higher guarantees
        
        Net effect: slight reduction for moderate guarantees
        """
        if guarantee_pct >= 85:
            # High guarantee often = higher risk borrower
            return base_pd * 1.1
        elif guarantee_pct >= 75:
            return base_pd * 0.95
        elif guarantee_pct >= 50:
            return base_pd * 0.90
        else:
            # Low guarantee = SBA thinks low risk
            return base_pd * 0.85
    
    def _adjust_for_business_age(self, pd: float, business_age_years: float) -> float:
        """
        Adjust PD based on business age.
        
        < 2 years: Very high risk
        2-5 years: Elevated risk
        5-10 years: Moderate risk
        10+ years: Lower risk
        """
        if business_age_years < 2:
            return pd * 1.5
        elif business_age_years < 5:
            return pd * 1.2
        elif business_age_years < 10:
            return pd * 1.0
        else:
            return pd * 0.8
    
    def _adjust_for_industry(self, pd: float, industry: str) -> float:
        """Apply industry-specific risk adjustment."""
        industry_key = industry.lower().replace(' ', '_')
        factor = INDUSTRY_RISK_FACTORS.get(industry_key, INDUSTRY_RISK_FACTORS['default'])
        return pd * factor
    
    def _adjust_for_employee_count(self, pd: float, employees: int) -> float:
        """
        Adjust for business size.
        
        Very small (< 5): Higher risk
        Small (5-20): Moderate
        Medium (20-100): Lower
        Large (100+): Stable
        """
        if employees < 5:
            return pd * 1.2
        elif employees < 20:
            return pd * 1.0
        elif employees < 100:
            return pd * 0.9
        else:
            return pd * 0.8
    
    def _get_risk_factors(
        self,
        loan: Dict[str, Any],
        adjustments: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Get top contributing risk factors."""
        factors = []
        
        for factor_name, impact in sorted(adjustments.items(), key=lambda x: abs(x[1] - 1.0), reverse=True):
            direction = "increases" if impact > 1.0 else "decreases"
            magnitude = abs(impact - 1.0) * 100
            
            factors.append({
                'factor': factor_name,
                'impact': round(magnitude, 1),
                'direction': direction,
                'value': loan.get(factor_name.split('_')[0], 'N/A'),
            })
        
        return factors[:5]
    
    def predict(self, loan: Dict[str, Any]) -> SBAPrediction:
        """
        Predict default probability for an SBA loan.
        
        Args:
            loan: Dictionary with loan and business details
            
        Returns:
            SBAPrediction with default probability and risk factors
        """
        loan_id = loan.get('loan_id', 'sba_loan')
        loan_amount = loan.get('loan_amount', 100000)
        sba_guarantee_pct = loan.get('sba_guarantee_pct', 75)
        industry = loan.get('industry', 'default')
        business_age_years = loan.get('business_age_years', 5)
        employees = loan.get('employees', 10)
        
        # Calculate base PD
        base_pd = self._calculate_base_pd(loan)
        
        # Apply adjustments
        adjustments = {}
        
        # SBA guarantee adjustment
        pd = self._adjust_for_sba_guarantee(base_pd, sba_guarantee_pct)
        adjustments['sba_guarantee'] = pd / base_pd
        
        # Business age adjustment
        prev_pd = pd
        pd = self._adjust_for_business_age(pd, business_age_years)
        adjustments['business_age'] = pd / prev_pd if prev_pd > 0 else 1.0
        
        # Industry adjustment
        prev_pd = pd
        pd = self._adjust_for_industry(pd, industry)
        adjustments['industry_risk'] = pd / prev_pd if prev_pd > 0 else 1.0
        
        # Employee count adjustment
        prev_pd = pd
        pd = self._adjust_for_employee_count(pd, employees)
        adjustments['business_size'] = pd / prev_pd if prev_pd > 0 else 1.0
        
        # Cap probability
        final_pd = min(max(pd, 0.01), 0.95)
        
        # Determine risk level
        if final_pd < 0.05:
            risk_level = "LOW"
        elif final_pd < 0.15:
            risk_level = "MEDIUM"
        elif final_pd < 0.30:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        # Calculate confidence based on data quality
        confidence = 0.85  # Base confidence
        if loan.get('owner_credit_score'):
            confidence += 0.05
        if loan.get('business_revenue'):
            confidence += 0.05
        if loan.get('debt_service_coverage'):
            confidence += 0.05
        
        return SBAPrediction(
            loan_id=loan_id,
            default_probability=round(final_pd, 4),
            risk_level=risk_level,
            confidence=round(min(confidence, 0.99), 2),
            top_factors=self._get_risk_factors(loan, adjustments),
            loan_amount=loan_amount,
            sba_guarantee_pct=sba_guarantee_pct,
            industry=industry,
            business_age_years=business_age_years,
        )
    
    def predict_batch(self, loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict for multiple SBA loans."""
        results = [self.predict(loan) for loan in loans]
        
        # Summary statistics
        avg_pd = sum(r.default_probability for r in results) / len(results) if results else 0
        risk_distribution = {
            'LOW': sum(1 for r in results if r.risk_level == 'LOW'),
            'MEDIUM': sum(1 for r in results if r.risk_level == 'MEDIUM'),
            'HIGH': sum(1 for r in results if r.risk_level == 'HIGH'),
            'CRITICAL': sum(1 for r in results if r.risk_level == 'CRITICAL'),
        }
        
        return {
            'success': True,
            'loan_count': len(results),
            'summary': {
                'avg_default_probability': round(avg_pd, 4),
                'risk_distribution': risk_distribution,
            },
            'predictions': [r.to_dict() for r in results[:20]],
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'model_name': 'SBA Commercial Loan Predictor',
            'version': 'v1.0',
            'base_model': 'LightGBM (Lending Club adapted)',
            'adjustment_factors': list(INDUSTRY_RISK_FACTORS.keys()),
            'features_used': [
                'loan_amount',
                'sba_guarantee_pct',
                'industry',
                'business_age_years',
                'employees',
                'owner_credit_score',
                'business_revenue',
                'debt_service_coverage',
            ],
        }


# Singleton instance
_sba_predictor: Optional[SBALoanPredictor] = None


def get_sba_predictor() -> SBALoanPredictor:
    """Get or create SBA predictor singleton."""
    global _sba_predictor
    if _sba_predictor is None:
        _sba_predictor = SBALoanPredictor()
    return _sba_predictor
