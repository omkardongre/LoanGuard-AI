"""
FRED API Integration for Real-Time Market Rates
V9 NEW - Federal Reserve Economic Data for prepayment modeling

FRED is FREE and production-level:
- Official Federal Reserve data
- Used by banks, hedge funds, research institutions
- API key available at: https://fred.stlouisfed.org/docs/api/api_key.html

Key Series for Prepayment Modeling:
- MORTGAGE30US: 30-Year Fixed Rate Mortgage Average (Weekly)
- MORTGAGE15US: 15-Year Fixed Rate Mortgage Average (Weekly)
- DGS10: 10-Year Treasury Constant Maturity Rate (Daily)
- FEDFUNDS: Federal Funds Rate (Monthly)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# FRED API settings
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Key series for prepayment modeling
FRED_SERIES = {
    "MORTGAGE30US": "30-Year Fixed Rate Mortgage Average",
    "MORTGAGE15US": "15-Year Fixed Rate Mortgage Average", 
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "FEDFUNDS": "Federal Funds Rate",
}

# Default rates (fallback if FRED unavailable)
DEFAULT_RATES = {
    "MORTGAGE30US": 6.85,  # As of Jan 2026
    "MORTGAGE15US": 6.05,
    "DGS10": 4.25,
    "FEDFUNDS": 4.50,
}


class FREDClient:
    """
    Client for Federal Reserve Economic Data (FRED) API.
    
    FREE API - Get key at: https://fred.stlouisfed.org/docs/api/api_key.html
    
    Usage:
        client = FREDClient(api_key="your_key")
        rate = client.get_current_mortgage_rate()
        spread = client.calculate_refinancing_incentive(loan_rate=7.5)
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or FRED_API_KEY
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = 3600  # 1 hour cache
    
    def _is_cache_valid(self, series_id: str) -> bool:
        """Check if cached value is still valid."""
        if series_id not in self._cache_time:
            return False
        elapsed = (datetime.now() - self._cache_time[series_id]).total_seconds()
        return elapsed < self._cache_duration
    
    def get_series_latest(self, series_id: str) -> Optional[float]:
        """
        Get the latest value for a FRED series.
        
        Args:
            series_id: FRED series ID (e.g., "MORTGAGE30US")
            
        Returns:
            Latest value as float, or None if unavailable
        """
        # Check cache first
        if self._is_cache_valid(series_id):
            return self._cache[series_id]
        
        # Return default if no API key
        if not self.api_key:
            logger.warning(f"No FRED API key, using default for {series_id}")
            return DEFAULT_RATES.get(series_id)
        
        try:
            import requests
            
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            }
            
            response = requests.get(FRED_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])
            
            if observations:
                value = float(observations[0]["value"])
                self._cache[series_id] = value
                self._cache_time[series_id] = datetime.now()
                return value
            
            return DEFAULT_RATES.get(series_id)
            
        except Exception as e:
            logger.error(f"FRED API error for {series_id}: {e}")
            return DEFAULT_RATES.get(series_id)
    
    def get_current_mortgage_rate(self, term: int = 30) -> float:
        """
        Get current mortgage rate.
        
        Args:
            term: 30 or 15 year mortgage
            
        Returns:
            Current mortgage rate as percentage
        """
        series_id = "MORTGAGE30US" if term == 30 else "MORTGAGE15US"
        rate = self.get_series_latest(series_id)
        return rate if rate else DEFAULT_RATES[series_id]
    
    def calculate_refinancing_incentive(
        self, 
        loan_rate: float, 
        term: int = 30
    ) -> Dict:
        """
        Calculate refinancing incentive (the #1 prepayment driver).
        
        Args:
            loan_rate: Original loan interest rate
            term: Loan term (30 or 15 years)
            
        Returns:
            Dict with incentive metrics
        """
        market_rate = self.get_current_mortgage_rate(term)
        spread = loan_rate - market_rate
        
        # Categorize incentive
        if spread >= 1.5:
            category = "STRONG_INCENTIVE"
            prepay_boost = 0.25  # +25% to base prepay probability
        elif spread >= 0.75:
            category = "MODERATE_INCENTIVE"
            prepay_boost = 0.15
        elif spread >= 0.25:
            category = "WEAK_INCENTIVE"
            prepay_boost = 0.05
        elif spread >= -0.25:
            category = "NO_INCENTIVE"
            prepay_boost = 0.0
        else:
            category = "DISINCENTIVE"  # Current rate HIGHER than loan
            prepay_boost = -0.10  # Reduce prepay probability
        
        return {
            "loan_rate": loan_rate,
            "market_rate": market_rate,
            "spread": round(spread, 3),
            "spread_bps": int(spread * 100),  # Basis points
            "category": category,
            "prepay_probability_adjustment": prepay_boost,
            "source": "FRED MORTGAGE30US" if term == 30 else "FRED MORTGAGE15US",
            "as_of": datetime.now().isoformat(),
        }
    
    def get_rate_scenario(
        self, 
        loan_rate: float,
        rate_changes: list = [-1.0, -0.5, 0, 0.5, 1.0]
    ) -> list:
        """
        Generate rate scenario analysis ("what-if" analysis).
        
        Args:
            loan_rate: Original loan rate
            rate_changes: List of rate changes to simulate
            
        Returns:
            List of scenario results
        """
        current_market = self.get_current_mortgage_rate()
        scenarios = []
        
        for change in rate_changes:
            scenario_rate = current_market + change
            spread = loan_rate - scenario_rate
            
            if spread >= 1.5:
                prepay_prob = "HIGH (70-85%)"
            elif spread >= 0.75:
                prepay_prob = "MODERATE (50-70%)"
            elif spread >= 0:
                prepay_prob = "LOW (30-50%)"
            else:
                prepay_prob = "VERY LOW (<30%)"
            
            scenarios.append({
                "rate_change": f"{change:+.1f}%",
                "scenario_market_rate": round(scenario_rate, 2),
                "spread": round(spread, 2),
                "prepayment_probability": prepay_prob,
            })
        
        return scenarios
    
    def get_all_rates(self) -> Dict:
        """Get all key rates for comprehensive analysis."""
        return {
            "mortgage_30y": self.get_series_latest("MORTGAGE30US"),
            "mortgage_15y": self.get_series_latest("MORTGAGE15US"),
            "treasury_10y": self.get_series_latest("DGS10"),
            "fed_funds": self.get_series_latest("FEDFUNDS"),
            "as_of": datetime.now().isoformat(),
            "source": "FRED (Federal Reserve Economic Data)",
        }


def calculate_cpr_smm(monthly_prepay_rate: float) -> Dict:
    """
    Convert prepayment probability to industry-standard CPR/SMM.
    
    CPR = Conditional Prepayment Rate (annualized)
    SMM = Single Monthly Mortality (monthly rate)
    
    Formula: CPR = 1 - (1 - SMM)^12
    """
    smm = monthly_prepay_rate
    cpr = 1 - (1 - smm) ** 12
    
    return {
        "SMM": round(smm * 100, 4),  # As percentage
        "SMM_description": "Single Monthly Mortality - Monthly prepayment rate",
        "CPR": round(cpr * 100, 2),  # As percentage
        "CPR_description": "Conditional Prepayment Rate - Annualized prepayment rate",
        "PSA_equivalent": round(cpr * 100 / 6, 1),  # PSA assumes 6% CPR at 30 months
    }


def calculate_seasoning_factor(months_since_origination: int) -> Dict:
    """
    Calculate seasoning factor for prepayment modeling.
    
    Seasoning effect: Prepayment rates typically increase as loans age,
    peak around 30-60 months, then plateau or decline (burnout).
    """
    # PSA standard seasoning curve
    if months_since_origination <= 30:
        # Linear ramp-up in first 30 months
        factor = months_since_origination / 30.0
    else:
        # Plateau after 30 months with slight decline
        factor = max(0.8, 1.0 - (months_since_origination - 30) * 0.002)
    
    # Burnout effect for older loans (5+ years)
    if months_since_origination > 60:
        burnout_factor = 0.95 ** ((months_since_origination - 60) / 12)
        factor *= burnout_factor
    
    return {
        "months_since_origination": months_since_origination,
        "seasoning_factor": round(factor, 3),
        "stage": "RAMP_UP" if months_since_origination <= 30 else "MATURE" if months_since_origination <= 60 else "BURNOUT",
        "description": "Multiplier applied to base prepayment probability",
    }


# Singleton FRED client
_fred_client: Optional[FREDClient] = None


def get_fred_client() -> FREDClient:
    """Get or create FRED client singleton."""
    global _fred_client
    if _fred_client is None:
        _fred_client = FREDClient()
    return _fred_client


# Service info for documentation
SERVICE_INFO = {
    "name": "FRED API Integration",
    "provider": "Federal Reserve Bank of St. Louis",
    "cost": "FREE",
    "registration": "https://fred.stlouisfed.org/docs/api/api_key.html",
    "production_level": True,
    "used_by": ["Banks", "Hedge Funds", "Research Institutions", "Government Agencies"],
    "update_frequency": {
        "MORTGAGE30US": "Weekly (Thursday)",
        "DGS10": "Daily",
        "FEDFUNDS": "Monthly",
    },
    "data_quality": "Official Federal Reserve data - highest reliability",
}
