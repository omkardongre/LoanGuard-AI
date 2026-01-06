"""
Portfolio Concentration Radar Tools.

Production-level tools for analyzing portfolio concentration risk
across sectors, geographies, borrowers, and loan types.

Key metrics:
- HHI (Herfindahl-Hirschman Index) for concentration measurement
- Exposure percentages per dimension
- Regulatory threshold alerts (>25% single exposure)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConcentrationRisk(Enum):
    """Concentration risk levels based on HHI."""
    LOW = "LOW"           # HHI < 1000
    MODERATE = "MODERATE" # HHI 1000-1800
    HIGH = "HIGH"         # HHI 1800-2500
    VERY_HIGH = "VERY_HIGH"  # HHI > 2500


class RegulatoryAlert(Enum):
    """Regulatory alert types for concentration."""
    SINGLE_BORROWER = "SINGLE_BORROWER_LIMIT"  # >25% to one borrower
    SECTOR_CONCENTRATION = "SECTOR_CONCENTRATION"  # >25% to one sector
    GEOGRAPHIC_CONCENTRATION = "GEOGRAPHIC_CONCENTRATION"  # >30% to one region
    TOP_10_CONCENTRATION = "TOP_10_CONCENTRATION"  # >60% in top 10 exposures


@dataclass
class ExposureItem:
    """Single exposure item in concentration analysis."""
    name: str
    exposure_amount: float
    exposure_pct: float
    loan_count: int


@dataclass
class ConcentrationResult:
    """Result of concentration analysis for one dimension."""
    dimension: str  # sector, geography, borrower, loan_type
    total_exposure: float
    item_count: int
    hhi: float
    hhi_risk_level: ConcentrationRisk
    top_exposures: List[ExposureItem]
    alerts: List[Dict[str, Any]]


@dataclass
class PortfolioConcentrationRadar:
    """Complete portfolio concentration analysis."""
    success: bool
    as_of_date: str
    total_portfolio_value: float
    total_loans: int
    sector_concentration: Optional[ConcentrationResult]
    geography_concentration: Optional[ConcentrationResult]
    borrower_concentration: Optional[ConcentrationResult]
    loan_type_concentration: Optional[ConcentrationResult]
    overall_hhi: float
    overall_risk_level: ConcentrationRisk
    regulatory_alerts: List[Dict[str, Any]]
    recommendations: List[str]


def calculate_hhi(exposures: List[float], total: float) -> float:
    """
    Calculate Herfindahl-Hirschman Index (HHI).
    
    HHI = sum of squared market shares (each share as 0-100)
    
    Interpretation:
    - < 1000: Low concentration (competitive)
    - 1000-1800: Moderate concentration
    - 1800-2500: High concentration
    - > 2500: Very high concentration
    
    Args:
        exposures: List of exposure amounts
        total: Total portfolio value
        
    Returns:
        HHI value (0-10000 scale)
    """
    if total <= 0 or not exposures:
        return 0
    
    shares = [(exp / total * 100) for exp in exposures]
    hhi = sum(share ** 2 for share in shares)
    
    return round(hhi, 2)


def determine_hhi_risk(hhi: float) -> ConcentrationRisk:
    """Determine risk level from HHI value."""
    if hhi < 1000:
        return ConcentrationRisk.LOW
    elif hhi < 1800:
        return ConcentrationRisk.MODERATE
    elif hhi < 2500:
        return ConcentrationRisk.HIGH
    else:
        return ConcentrationRisk.VERY_HIGH


def calculate_dimension_concentration(
    loans: List[Dict[str, Any]],
    dimension_field: str,
    dimension_name: str,
    single_limit_pct: float = 25.0,
) -> ConcentrationResult:
    """
    Calculate concentration for a single dimension (sector, geography, etc.).
    
    Args:
        loans: List of loan dictionaries
        dimension_field: Field name to group by
        dimension_name: Human-readable dimension name
        single_limit_pct: Regulatory limit for single exposure (default 25%)
        
    Returns:
        ConcentrationResult with HHI and alerts
    """
    if not loans:
        return ConcentrationResult(
            dimension=dimension_name,
            total_exposure=0,
            item_count=0,
            hhi=0,
            hhi_risk_level=ConcentrationRisk.LOW,
            top_exposures=[],
            alerts=[],
        )
    
    # Group exposures by dimension
    exposure_by_dimension: Dict[str, Dict[str, Any]] = {}
    total_exposure = 0
    
    for loan in loans:
        dimension_value = loan.get(dimension_field, "Unknown") or "Unknown"
        amount = float(loan.get("facility_amount", 0) or 0)
        
        if dimension_value not in exposure_by_dimension:
            exposure_by_dimension[dimension_value] = {
                "amount": 0,
                "count": 0,
            }
        
        exposure_by_dimension[dimension_value]["amount"] += amount
        exposure_by_dimension[dimension_value]["count"] += 1
        total_exposure += amount
    
    # Calculate percentages and build exposure list
    exposures: List[ExposureItem] = []
    exposure_amounts: List[float] = []
    alerts: List[Dict[str, Any]] = []
    
    for name, data in exposure_by_dimension.items():
        pct = (data["amount"] / total_exposure * 100) if total_exposure > 0 else 0
        
        exposures.append(ExposureItem(
            name=name,
            exposure_amount=data["amount"],
            exposure_pct=round(pct, 2),
            loan_count=data["count"],
        ))
        exposure_amounts.append(data["amount"])
        
        # Check for regulatory alerts
        if pct > single_limit_pct:
            alerts.append({
                "type": f"{dimension_name.upper()}_CONCENTRATION",
                "entity": name,
                "exposure_pct": round(pct, 2),
                "limit_pct": single_limit_pct,
                "excess_pct": round(pct - single_limit_pct, 2),
                "message": f"{name} exceeds {single_limit_pct}% limit with {pct:.1f}% exposure",
            })
    
    # Sort by exposure amount descending
    exposures.sort(key=lambda x: x.exposure_amount, reverse=True)
    
    # Calculate HHI
    hhi = calculate_hhi(exposure_amounts, total_exposure)
    risk_level = determine_hhi_risk(hhi)
    
    return ConcentrationResult(
        dimension=dimension_name,
        total_exposure=total_exposure,
        item_count=len(exposure_by_dimension),
        hhi=hhi,
        hhi_risk_level=risk_level,
        top_exposures=exposures[:10],  # Top 10
        alerts=alerts,
    )


def get_portfolio_concentration(
    loan_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get comprehensive portfolio concentration analysis.
    
    This is the main entry point for the Portfolio Concentration Radar.
    
    Args:
        loan_id: Optional - if provided, analyze concentration impact of this loan
        
    Returns:
        Dictionary with complete concentration analysis
    """
    try:
        from common.bigquery_client import BigQueryClient
        from datetime import datetime
        
        client = BigQueryClient()
        loans = client.get_all_loans(limit=1000)
        
        if not loans:
            return {
                "success": False,
                "error": "No loans found in portfolio",
            }
        
        # Calculate concentration by different dimensions
        # Using available fields from loans table
        
        # 1. Borrower Concentration (single name risk)
        borrower_conc = calculate_dimension_concentration(
            loans,
            dimension_field="borrower_name",
            dimension_name="Borrower",
            single_limit_pct=25.0,  # Regulatory: 25% single name limit
        )
        
        # 2. Loan Type Concentration (proxy for sector)
        loan_type_conc = calculate_dimension_concentration(
            loans,
            dimension_field="loan_type",
            dimension_name="Loan Type",
            single_limit_pct=30.0,
        )
        
        # 3. Status Concentration (active vs at-risk)
        status_conc = calculate_dimension_concentration(
            loans,
            dimension_field="status",
            dimension_name="Status",
            single_limit_pct=50.0,
        )
        
        # 4. Currency Concentration
        currency_conc = calculate_dimension_concentration(
            loans,
            dimension_field="currency",
            dimension_name="Currency",
            single_limit_pct=80.0,
        )
        
        # Aggregate alerts
        all_alerts = (
            borrower_conc.alerts +
            loan_type_conc.alerts +
            status_conc.alerts +
            currency_conc.alerts
        )
        
        # Calculate overall HHI (using borrower concentration as primary)
        overall_hhi = borrower_conc.hhi
        overall_risk = borrower_conc.hhi_risk_level
        
        # Generate recommendations
        recommendations = []
        
        if borrower_conc.hhi > 1800:
            recommendations.append(
                "Consider diversifying borrower base - HHI indicates high concentration"
            )
        
        if len(borrower_conc.alerts) > 0:
            recommendations.append(
                f"Review {len(borrower_conc.alerts)} borrower(s) exceeding single-name exposure limits"
            )
        
        if loan_type_conc.hhi > 2500:
            recommendations.append(
                "Loan type concentration is very high - consider sector diversification"
            )
        
        # Check top 5 concentration (should not exceed 50%)
        top_5_pct = sum(e.exposure_pct for e in borrower_conc.top_exposures[:5])
        if top_5_pct > 50:
            recommendations.append(
                f"Top 5 borrowers represent {top_5_pct:.1f}% of portfolio - consider rebalancing"
            )
        
        # Build result
        total_portfolio = sum(float(l.get("facility_amount", 0) or 0) for l in loans)
        
        result = {
            "success": True,
            "as_of_date": datetime.now().isoformat(),
            "total_portfolio_value": total_portfolio,
            "total_loans": len(loans),
            "overall_hhi": overall_hhi,
            "overall_risk_level": overall_risk.value,
            "concentrations": {
                "borrower": {
                    "dimension": "Borrower (Single Name Risk)",
                    "hhi": borrower_conc.hhi,
                    "risk_level": borrower_conc.hhi_risk_level.value,
                    "unique_count": borrower_conc.item_count,
                    "top_exposures": [asdict(e) for e in borrower_conc.top_exposures[:5]],
                    "alerts": borrower_conc.alerts,
                },
                "loan_type": {
                    "dimension": "Loan Type (Sector Proxy)",
                    "hhi": loan_type_conc.hhi,
                    "risk_level": loan_type_conc.hhi_risk_level.value,
                    "unique_count": loan_type_conc.item_count,
                    "top_exposures": [asdict(e) for e in loan_type_conc.top_exposures[:5]],
                    "alerts": loan_type_conc.alerts,
                },
                "status": {
                    "dimension": "Loan Status",
                    "hhi": status_conc.hhi,
                    "risk_level": status_conc.hhi_risk_level.value,
                    "unique_count": status_conc.item_count,
                    "top_exposures": [asdict(e) for e in status_conc.top_exposures[:5]],
                    "alerts": status_conc.alerts,
                },
                "currency": {
                    "dimension": "Currency Exposure",
                    "hhi": currency_conc.hhi,
                    "risk_level": currency_conc.hhi_risk_level.value,
                    "unique_count": currency_conc.item_count,
                    "top_exposures": [asdict(e) for e in currency_conc.top_exposures[:5]],
                    "alerts": currency_conc.alerts,
                },
            },
            "regulatory_alerts": all_alerts,
            "alert_count": len(all_alerts),
            "recommendations": recommendations,
        }
        
        return result
        
    except Exception as e:
        logger.exception("Error calculating portfolio concentration")
        return {
            "success": False,
            "error": str(e),
        }


def calculate_marginal_concentration_impact(
    loan_amount: float,
    borrower_name: str,
    loan_type: str,
) -> Dict[str, Any]:
    """
    Calculate the marginal impact of a new loan on portfolio concentration.
    
    Useful for credit officers evaluating a new loan application.
    
    Args:
        loan_amount: Proposed loan amount
        borrower_name: Borrower name
        loan_type: Type of loan
        
    Returns:
        Dictionary with before/after concentration metrics
    """
    try:
        # Get current concentration
        current = get_portfolio_concentration()
        
        if not current.get("success"):
            return {"success": False, "error": "Could not get current concentration"}
        
        current_portfolio = current.get("total_portfolio_value", 0)
        new_portfolio = current_portfolio + loan_amount
        
        # Calculate new borrower exposure
        borrower_conc = current.get("concentrations", {}).get("borrower", {})
        top_exposures = borrower_conc.get("top_exposures", [])
        
        # Find if borrower already exists
        existing_exposure = 0
        for exp in top_exposures:
            if exp.get("name") == borrower_name:
                existing_exposure = exp.get("exposure_amount", 0)
                break
        
        new_borrower_exposure = existing_exposure + loan_amount
        new_borrower_pct = (new_borrower_exposure / new_portfolio * 100) if new_portfolio > 0 else 0
        
        # Check if this would trigger alerts
        would_breach_limit = new_borrower_pct > 25.0
        
        return {
            "success": True,
            "proposed_loan": {
                "amount": loan_amount,
                "borrower": borrower_name,
                "loan_type": loan_type,
            },
            "current_portfolio_value": current_portfolio,
            "new_portfolio_value": new_portfolio,
            "borrower_analysis": {
                "current_exposure": existing_exposure,
                "new_exposure": new_borrower_exposure,
                "current_pct": (existing_exposure / current_portfolio * 100) if current_portfolio > 0 else 0,
                "new_pct": new_borrower_pct,
                "would_breach_limit": would_breach_limit,
                "limit_pct": 25.0,
            },
            "recommendation": (
                "DECLINE - Would exceed single-name concentration limit"
                if would_breach_limit
                else "ACCEPTABLE - Within concentration limits"
            ),
        }
        
    except Exception as e:
        logger.exception("Error calculating marginal impact")
        return {"success": False, "error": str(e)}


# Export functions
__all__ = [
    "calculate_hhi",
    "determine_hhi_risk",
    "calculate_dimension_concentration",
    "get_portfolio_concentration",
    "calculate_marginal_concentration_impact",
    "ConcentrationRisk",
    "RegulatoryAlert",
    "ExposureItem",
    "ConcentrationResult",
]
