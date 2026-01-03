"""
Covenant Cure Calculator - V6 P2 Feature

Calculates remediation options when breach is imminent or detected.
Shows HOW to cure a breach, not just that it exists.

This is a UNIQUE feature - provides actionable remediation steps.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CureMethod(Enum):
    """Available cure methods."""
    EQUITY_CURE = "EQUITY_CURE"
    DEBT_PAYDOWN = "DEBT_PAYDOWN"
    ASSET_SALE = "ASSET_SALE"
    OPERATIONAL_IMPROVEMENT = "OPERATIONAL_IMPROVEMENT"
    WAIVER_REQUEST = "WAIVER_REQUEST"
    AMENDMENT_REQUEST = "AMENDMENT_REQUEST"


class Feasibility(Enum):
    """Feasibility assessment."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Standard cure periods by covenant type (days)
CURE_PERIODS = {
    "debt_to_ebitda": 30,
    "leverage_ratio": 30,
    "interest_coverage": 30,
    "fixed_charge_coverage": 30,
    "current_ratio": 15,
    "quick_ratio": 15,
    "debt_service_coverage": 30,
    "net_debt_to_ebitda": 30,
    "senior_debt_to_ebitda": 30,
}


def calculate_cure_options(
    loan_id: str,
    covenant_type: str,
    current_value: float,
    threshold: float,
    loan_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate cure options for a covenant breach or near-breach.
    
    Args:
        loan_id: Loan identifier
        covenant_type: Type of covenant (e.g., "debt_to_ebitda")
        current_value: Current metric value
        threshold: Covenant threshold
        loan_details: Optional loan details for more accurate calculations
    
    Returns:
        Cure options with amounts and feasibility
    """
    try:
        # Calculate breach amount
        breach_amount = abs(current_value - threshold)
        is_breached = _is_covenant_breached(covenant_type, current_value, threshold)
        
        # Get cure period
        cure_period_days = CURE_PERIODS.get(covenant_type, 30)
        
        # Get loan details or use defaults
        loan_details = loan_details or {}
        total_debt = loan_details.get("total_debt", 100_000_000)  # Default $100M
        ebitda = loan_details.get("ebitda", 25_000_000)  # Default $25M
        
        # Calculate cure options based on covenant type
        options = []
        
        if covenant_type in ["debt_to_ebitda", "leverage_ratio", "net_debt_to_ebitda"]:
            options = _calculate_leverage_cures(
                current_value=current_value,
                threshold=threshold,
                total_debt=total_debt,
                ebitda=ebitda,
            )
        elif covenant_type in ["interest_coverage", "fixed_charge_coverage", "debt_service_coverage"]:
            options = _calculate_coverage_cures(
                current_value=current_value,
                threshold=threshold,
                total_debt=total_debt,
                ebitda=ebitda,
            )
        elif covenant_type in ["current_ratio", "quick_ratio"]:
            options = _calculate_liquidity_cures(
                current_value=current_value,
                threshold=threshold,
                loan_details=loan_details,
            )
        else:
            # Generic cure options
            options = _calculate_generic_cures(
                current_value=current_value,
                threshold=threshold,
                covenant_type=covenant_type,
            )
        
        # Always add waiver option
        options.append({
            "method": CureMethod.WAIVER_REQUEST.value,
            "amount": 0,
            "description": "Request temporary waiver from lender",
            "feasibility": Feasibility.MEDIUM.value,
            "timeline_days": 14,
            "requirements": [
                "Formal waiver request letter",
                "Updated financial projections",
                "Remediation plan",
                "Potential waiver fee (typically 25-50 bps)",
            ],
            "pros": ["No immediate cash outflow", "Preserves liquidity"],
            "cons": ["May affect relationship", "Future covenant tightening possible"],
        })
        
        # Sort by feasibility
        feasibility_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        options.sort(key=lambda x: feasibility_order.get(x["feasibility"], 99))
        
        return {
            "success": True,
            "loan_id": loan_id,
            "covenant_type": covenant_type,
            "current_value": round(current_value, 4),
            "threshold": threshold,
            "breach_amount": round(breach_amount, 4),
            "is_breached": is_breached,
            "cure_deadline_days": cure_period_days,
            "options": options,
            "options_count": len(options),
            "recommended": options[0] if options else None,
            "summary": _generate_cure_summary(is_breached, options),
        }
        
    except Exception as e:
        logger.error(f"Cure calculation error: {e}")
        return {"success": False, "error": str(e)}


def _calculate_leverage_cures(
    current_value: float,
    threshold: float,
    total_debt: float,
    ebitda: float,
) -> List[Dict[str, Any]]:
    """Calculate cure options for leverage covenants."""
    options = []
    
    # Current: Debt/EBITDA = current_value
    # Target: Debt/EBITDA <= threshold
    # Required EBITDA at current debt: total_debt / threshold
    # Required debt at current EBITDA: ebitda * threshold
    
    required_debt = ebitda * threshold
    debt_reduction_needed = total_debt - required_debt
    
    if debt_reduction_needed > 0:
        # Option 1: Debt paydown
        options.append({
            "method": CureMethod.DEBT_PAYDOWN.value,
            "amount": round(debt_reduction_needed, 0),
            "description": f"Pay down ${debt_reduction_needed:,.0f} in debt to achieve {threshold}x leverage",
            "feasibility": _assess_feasibility(debt_reduction_needed, total_debt * 0.1),
            "timeline_days": 30,
            "requirements": [
                "Available cash or credit facility",
                "Lender consent for prepayment",
            ],
            "impact": f"Reduces Debt/EBITDA from {current_value:.2f}x to {threshold:.2f}x",
            "pros": ["Permanent fix", "Improves credit profile"],
            "cons": ["Requires significant cash", "May have prepayment penalties"],
        })
    
    # Option 2: Equity cure
    # Equity injection that converts to EBITDA credit or reduces debt
    equity_multiplier = 1.5  # Standard equity cure multiplier
    equity_cure_amount = debt_reduction_needed * equity_multiplier
    
    options.append({
        "method": CureMethod.EQUITY_CURE.value,
        "amount": round(equity_cure_amount, 0),
        "description": f"Inject ${equity_cure_amount:,.0f} equity (sponsor contribution)",
        "feasibility": Feasibility.MEDIUM.value,
        "timeline_days": 15,
        "requirements": [
            "Sponsor commitment letter",
            "Equity cure provisions in credit agreement",
            "Funds in escrow within cure period",
        ],
        "impact": f"Cures breach through EBITDA add-back or debt reduction",
        "pros": ["Common cure mechanism", "Preserves lender relationship"],
        "cons": ["Dilutes equity", "May have caps on frequency"],
    })
    
    # Option 3: Asset sale
    asset_sale_amount = debt_reduction_needed * 1.2  # 20% premium for execution risk
    options.append({
        "method": CureMethod.ASSET_SALE.value,
        "amount": round(asset_sale_amount, 0),
        "description": f"Sell non-core assets worth ${asset_sale_amount:,.0f}",
        "feasibility": Feasibility.LOW.value,
        "timeline_days": 90,
        "requirements": [
            "Identify non-core assets",
            "Market valuation",
            "Buyer identification",
            "Lender consent for proceeds application",
        ],
        "impact": f"Net proceeds applied to debt reduction",
        "pros": ["No dilution", "Focuses business"],
        "cons": ["Time-consuming", "May sell at discount", "Fire sale risk"],
    })
    
    return options


def _calculate_coverage_cures(
    current_value: float,
    threshold: float,
    total_debt: float,
    ebitda: float,
) -> List[Dict[str, Any]]:
    """Calculate cure options for coverage covenants."""
    options = []
    
    # For coverage ratios, need to increase EBITDA or reduce interest
    coverage_gap = threshold - current_value
    
    # Estimate interest expense
    assumed_rate = 0.08  # 8% interest rate
    interest_expense = total_debt * assumed_rate
    
    # Required EBITDA increase
    ebitda_increase_needed = coverage_gap * interest_expense
    
    # Option 1: Operational improvement
    options.append({
        "method": CureMethod.OPERATIONAL_IMPROVEMENT.value,
        "amount": round(ebitda_increase_needed, 0),
        "description": f"Improve EBITDA by ${ebitda_increase_needed:,.0f} through cost reduction or revenue growth",
        "feasibility": Feasibility.MEDIUM.value,
        "timeline_days": 90,
        "requirements": [
            "Detailed operational improvement plan",
            "Cost reduction initiatives",
            "Revenue enhancement actions",
        ],
        "impact": f"Increases coverage ratio from {current_value:.2f}x to {threshold:.2f}x",
        "pros": ["Sustainable improvement", "No capital required"],
        "cons": ["Takes time to realize", "Execution risk"],
    })
    
    # Option 2: Interest rate reduction
    options.append({
        "method": CureMethod.AMENDMENT_REQUEST.value,
        "amount": 0,
        "description": "Request covenant amendment to lower threshold or extend cure period",
        "feasibility": Feasibility.MEDIUM.value,
        "timeline_days": 30,
        "requirements": [
            "Amendment request with supporting projections",
            "Amendment fee (typically 25-50 bps)",
            "Commitment to enhanced reporting",
        ],
        "impact": "Provides additional headroom without immediate cure",
        "pros": ["Buys time", "May be more achievable"],
        "cons": ["Amendment fee", "May include covenant tightening elsewhere"],
    })
    
    return options


def _calculate_liquidity_cures(
    current_value: float,
    threshold: float,
    loan_details: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Calculate cure options for liquidity covenants."""
    options = []
    
    current_assets = loan_details.get("current_assets", 50_000_000)
    current_liabilities = loan_details.get("current_liabilities", 40_000_000)
    
    # Required current assets at current liabilities
    required_current_assets = threshold * current_liabilities
    asset_increase_needed = required_current_assets - current_assets
    
    if asset_increase_needed > 0:
        # Option 1: Cash injection
        options.append({
            "method": CureMethod.EQUITY_CURE.value,
            "amount": round(asset_increase_needed, 0),
            "description": f"Inject ${asset_increase_needed:,.0f} cash to improve current ratio",
            "feasibility": Feasibility.MEDIUM.value,
            "timeline_days": 15,
            "requirements": [
                "Available sponsor capital",
                "Equity cure provisions",
            ],
            "impact": f"Increases current ratio from {current_value:.2f}x to {threshold:.2f}x",
            "pros": ["Quick fix", "Improves liquidity"],
            "cons": ["Requires capital injection"],
        })
        
        # Option 2: Liability reduction
        liability_reduction = current_assets / threshold - current_liabilities
        if liability_reduction < 0:
            liability_reduction = abs(liability_reduction)
            options.append({
                "method": CureMethod.DEBT_PAYDOWN.value,
                "amount": round(liability_reduction, 0),
                "description": f"Pay down ${liability_reduction:,.0f} in current liabilities",
                "feasibility": Feasibility.MEDIUM.value,
                "timeline_days": 30,
                "requirements": [
                    "Available cash",
                    "Vendor/lender agreements for early payment",
                ],
                "impact": f"Reduces denominator to achieve target ratio",
                "pros": ["Reduces leverage", "Improves working capital"],
                "cons": ["Uses cash reserves"],
            })
    
    return options


def _calculate_generic_cures(
    current_value: float,
    threshold: float,
    covenant_type: str,
) -> List[Dict[str, Any]]:
    """Calculate generic cure options when specific type not recognized."""
    return [
        {
            "method": CureMethod.AMENDMENT_REQUEST.value,
            "amount": 0,
            "description": f"Request amendment to {covenant_type} covenant",
            "feasibility": Feasibility.MEDIUM.value,
            "timeline_days": 30,
            "requirements": [
                "Amendment request",
                "Supporting financial projections",
                "Amendment fee",
            ],
            "pros": ["Addresses specific covenant"],
            "cons": ["Fee required", "May have conditions"],
        },
    ]


def _is_covenant_breached(
    covenant_type: str,
    current_value: float,
    threshold: float,
) -> bool:
    """Determine if covenant is breached based on type."""
    # Max covenants: value should be <= threshold
    max_covenants = [
        "debt_to_ebitda", "leverage_ratio", "net_debt_to_ebitda",
        "senior_debt_to_ebitda",
    ]
    
    # Min covenants: value should be >= threshold
    min_covenants = [
        "interest_coverage", "fixed_charge_coverage", "debt_service_coverage",
        "current_ratio", "quick_ratio",
    ]
    
    if covenant_type in max_covenants:
        return current_value > threshold
    elif covenant_type in min_covenants:
        return current_value < threshold
    else:
        # Default to max covenant logic
        return current_value > threshold


def _assess_feasibility(
    required_amount: float,
    benchmark: float,
) -> str:
    """Assess feasibility based on required amount vs benchmark."""
    ratio = required_amount / benchmark if benchmark > 0 else float('inf')
    
    if ratio <= 0.5:
        return Feasibility.HIGH.value
    elif ratio <= 1.5:
        return Feasibility.MEDIUM.value
    else:
        return Feasibility.LOW.value


def _generate_cure_summary(
    is_breached: bool,
    options: List[Dict[str, Any]],
) -> str:
    """Generate human-readable cure summary."""
    if not options:
        return "No cure options available. Contact lender directly."
    
    status = "BREACHED" if is_breached else "AT RISK"
    recommended = options[0]
    
    if recommended["method"] == CureMethod.WAIVER_REQUEST.value:
        return f"Covenant {status}. Recommended: Request waiver while exploring other options."
    
    return f"Covenant {status}. Recommended: {recommended['description']}. Estimated amount: ${recommended.get('amount', 0):,.0f}"


# Tool function for ADK agent
def get_cure_options(
    loan_id: str,
    covenant_type: str,
    current_value: float,
    threshold: float,
    total_debt: Optional[float] = None,
    ebitda: Optional[float] = None,
) -> Dict[str, Any]:
    """
    ADK Tool: Calculate cure options for a covenant.
    
    Args:
        loan_id: Loan identifier
        covenant_type: Type of covenant
        current_value: Current metric value
        threshold: Covenant threshold
        total_debt: Total debt amount (optional)
        ebitda: EBITDA amount (optional)
    
    Returns:
        Cure options with recommendations
    """
    loan_details = {}
    if total_debt:
        loan_details["total_debt"] = total_debt
    if ebitda:
        loan_details["ebitda"] = ebitda
    
    return calculate_cure_options(
        loan_id=loan_id,
        covenant_type=covenant_type,
        current_value=current_value,
        threshold=threshold,
        loan_details=loan_details if loan_details else None,
    )
