"""
Prepayment Risk Predictor V2 - Production Level with FRED Integration
V9 NEW - XGBoost + Real-time market rate integration

KEY IMPROVEMENTS OVER V1:
1. Refinancing Incentive: loan_rate - market_rate (from FRED API)
2. Seasoning Factor: Months since origination adjustment
3. CPR/SMM Output: Bank-standard prepayment metrics
4. Scenario Analysis: What-if rate changes

Usage:
    from prepayment_predictor_v2 import get_prepayment_predictor_v2
    
    predictor = get_prepayment_predictor_v2()
    result = predictor.predict_with_market(loan_data)
"""

import os
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
import pandas as pd

from .fred_integration import (
    get_fred_client, 
    calculate_cpr_smm, 
    calculate_seasoning_factor,
    FREDClient
)
from .prepayment_predictor import PrepaymentPredictor, PrepaymentPrediction


@dataclass
class PrepaymentPredictionV2:
    """Enhanced prepayment prediction with market context."""
    # Base prediction
    base_prepay_probability: float
    adjusted_prepay_probability: float
    prepay_probability_pct: str
    will_prepay: bool
    risk_category: str
    
    # Market context
    loan_rate: float
    market_rate: float
    refinancing_spread: float
    refinancing_incentive: str
    
    # Seasoning
    months_since_origination: int
    seasoning_stage: str
    seasoning_factor: float
    
    # Bank-standard metrics
    CPR: float  # Conditional Prepayment Rate (annualized %)
    SMM: float  # Single Monthly Mortality (monthly %)
    
    # Metadata
    model_version: str
    data_source: str
    as_of: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PrepaymentPredictorV2:
    """
    Production-level prepayment predictor with FRED market integration.
    
    This is what banks actually use:
    - Real-time refinancing incentive from FRED API
    - Seasoning adjustments based on loan age
    - CPR/SMM output format for portfolio management
    """
    
    def __init__(self, models_dir: str = None):
        """Initialize V2 predictor with FRED integration."""
        # Load base V1 predictor
        self._v1_predictor = PrepaymentPredictor(models_dir)
        
        # Initialize FRED client
        self._fred_client = get_fred_client()
        
        self._version = "2.0"
    
    @property
    def is_loaded(self) -> bool:
        return self._v1_predictor.is_loaded
    
    def predict_with_market(
        self,
        loan_data: Dict,
        loan_rate: float = None,
        months_since_origination: int = None,
    ) -> PrepaymentPredictionV2:
        """
        Predict prepayment with real-time market rate adjustment.
        
        Args:
            loan_data: Dict with loan features
            loan_rate: Original loan interest rate (uses int_rate from loan_data if not provided)
            months_since_origination: Months since loan origination
            
        Returns:
            PrepaymentPredictionV2 with market-adjusted prediction
        """
        # Get base prediction from V1 model
        base_prediction = self._v1_predictor.predict(loan_data)
        base_prob = base_prediction.prepay_probability
        
        # Extract loan rate
        if loan_rate is None:
            loan_rate = float(loan_data.get('int_rate', loan_data.get('OrigInterestRate', 7.0)))
        
        # Extract term to determine 30 or 15 year
        term_str = str(loan_data.get('term', '36 months'))
        term_years = 30 if '60' in term_str else 15 if '36' in term_str else 30
        
        # Get refinancing incentive from FRED
        incentive = self._fred_client.calculate_refinancing_incentive(
            loan_rate=loan_rate,
            term=term_years
        )
        
        # Calculate months since origination if not provided
        if months_since_origination is None:
            # Try to calculate from issue_d if available
            issue_d = loan_data.get('issue_d')
            if issue_d:
                try:
                    issue_date = pd.to_datetime(issue_d, format='%b-%Y')
                    months_since_origination = int((datetime.now() - issue_date).days / 30.44)
                except:
                    months_since_origination = 24  # Default to 2 years
            else:
                months_since_origination = 24
        
        # Get seasoning factor
        seasoning = calculate_seasoning_factor(months_since_origination)
        
        # ADJUST PREDICTION based on market conditions
        # This is the production-level enhancement
        adjusted_prob = base_prob
        
        # 1. Apply refinancing incentive adjustment
        adjusted_prob += incentive['prepay_probability_adjustment']
        
        # 2. Apply seasoning factor
        adjusted_prob *= seasoning['seasoning_factor']
        
        # 3. Clamp to valid probability range
        adjusted_prob = max(0.0, min(1.0, adjusted_prob))
        
        # Calculate CPR/SMM (bank-standard metrics)
        monthly_rate = adjusted_prob / 12  # Simple approximation
        cpr_smm = calculate_cpr_smm(monthly_rate)
        
        # Categorize adjusted prediction
        if adjusted_prob >= 0.7:
            category = "HIGH_PREPAY"
        elif adjusted_prob >= 0.4:
            category = "MODERATE_PREPAY"
        else:
            category = "LOW_PREPAY"
        
        return PrepaymentPredictionV2(
            base_prepay_probability=round(base_prob, 4),
            adjusted_prepay_probability=round(adjusted_prob, 4),
            prepay_probability_pct=f"{adjusted_prob * 100:.1f}%",
            will_prepay=adjusted_prob >= 0.5,
            risk_category=category,
            loan_rate=loan_rate,
            market_rate=incentive['market_rate'],
            refinancing_spread=incentive['spread'],
            refinancing_incentive=incentive['category'],
            months_since_origination=months_since_origination,
            seasoning_stage=seasoning['stage'],
            seasoning_factor=seasoning['seasoning_factor'],
            CPR=cpr_smm['CPR'],
            SMM=cpr_smm['SMM'],
            model_version=self._version,
            data_source="Federal Reserve Live Rates + ML Analytics",
            as_of=datetime.now().isoformat(),
        )
    
    def get_scenario_analysis(
        self,
        loan_data: Dict,
        loan_rate: float = None,
        rate_changes: list = [-1.0, -0.5, 0, 0.5, 1.0],
    ) -> Dict:
        """
        What-if analysis: How would prepayment change with different market rates?
        
        This is critical for portfolio stress testing.
        """
        if loan_rate is None:
            loan_rate = float(loan_data.get('int_rate', loan_data.get('OrigInterestRate', 7.0)))
        
        current_market = self._fred_client.get_current_mortgage_rate()
        scenarios = []
        
        # Get base prediction
        base_prediction = self._v1_predictor.predict(loan_data)
        base_prob = base_prediction.prepay_probability
        
        for change in rate_changes:
            scenario_market = current_market + change
            spread = loan_rate - scenario_market
            
            # Calculate adjusted probability for scenario
            if spread >= 1.5:
                boost = 0.25
            elif spread >= 0.75:
                boost = 0.15
            elif spread >= 0.25:
                boost = 0.05
            elif spread >= -0.25:
                boost = 0.0
            else:
                boost = -0.10
            
            scenario_prob = max(0.0, min(1.0, base_prob + boost))
            
            scenarios.append({
                "rate_change": f"{change:+.1f}%",
                "market_rate": round(scenario_market, 2),
                "spread": round(spread, 2),
                "spread_bps": int(spread * 100),
                "prepay_probability": round(scenario_prob * 100, 1),
                "risk_category": "HIGH" if scenario_prob >= 0.7 else "MODERATE" if scenario_prob >= 0.4 else "LOW",
            })
        
        return {
            "loan_rate": loan_rate,
            "current_market_rate": current_market,
            "current_spread": round(loan_rate - current_market, 2),
            "base_prepay_probability": round(base_prob * 100, 1),
            "scenarios": scenarios,
            "analysis_date": datetime.now().isoformat(),
        }
    
    def explain_with_market(
        self,
        loan_data: Dict,
        top_n: int = 5
    ) -> Dict:
        """Get explanation including market factors."""
        # Get base explanation
        base_explanation = self._v1_predictor.explain(loan_data, top_n)
        
        # Get market prediction
        market_prediction = self.predict_with_market(loan_data)
        
        # Add market context
        base_explanation['market_context'] = {
            'loan_rate': market_prediction.loan_rate,
            'market_rate': market_prediction.market_rate,
            'refinancing_spread': market_prediction.refinancing_spread,
            'refinancing_incentive': market_prediction.refinancing_incentive,
            'seasoning_stage': market_prediction.seasoning_stage,
        }
        
        base_explanation['adjustment_explanation'] = (
            f"Base model predicted {market_prediction.base_prepay_probability*100:.1f}% prepayment. "
            f"Adjusted to {market_prediction.adjusted_prepay_probability*100:.1f}% based on: "
            f"{market_prediction.refinancing_incentive} refinancing incentive "
            f"(spread: {market_prediction.refinancing_spread:+.2f}%) and "
            f"{market_prediction.seasoning_stage} seasoning stage."
        )
        
        return base_explanation
    
    def get_model_info(self) -> Dict:
        """Get comprehensive model info including FRED integration."""
        base_info = self._v1_predictor.get_model_info()
        
        base_info['version'] = self._version
        base_info['enhancements'] = [
            "FRED API integration for real-time mortgage rates",
            "Refinancing incentive calculation",
            "Seasoning factor adjustment",
            "CPR/SMM bank-standard output",
            "Scenario analysis for stress testing",
        ]
        base_info['external_data'] = {
            "source": "Federal Reserve Economic Data (FRED)",
            "series": ["MORTGAGE30US", "MORTGAGE15US", "DGS10"],
            "cost": "FREE",
            "reliability": "Official Federal Reserve data",
            "update_frequency": "Weekly (Thursday)",
        }
        
        # Get current rates
        base_info['current_rates'] = self._fred_client.get_all_rates()
        
        return base_info


# Singleton instance
_prepayment_predictor_v2: Optional[PrepaymentPredictorV2] = None


def get_prepayment_predictor_v2() -> PrepaymentPredictorV2:
    """Get or create V2 prepayment predictor singleton."""
    global _prepayment_predictor_v2
    if _prepayment_predictor_v2 is None:
        _prepayment_predictor_v2 = PrepaymentPredictorV2()
    return _prepayment_predictor_v2
