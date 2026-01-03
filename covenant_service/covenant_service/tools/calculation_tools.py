"""
Financial ratio calculation tools for covenant testing.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def calculate_debt_to_ebitda(
    total_debt: float,
    ebitda: float,
    adjustments: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Calculate Debt-to-EBITDA ratio.

    Args:
        total_debt: Total debt amount
        ebitda: EBITDA for the period
        adjustments: Optional adjustments (e.g., cash netting)

    Returns:
        Calculation result with ratio value
    """
    try:
        adjusted_debt = total_debt
        adjusted_ebitda = ebitda

        # Apply adjustments if provided
        if adjustments:
            if "cash_netting" in adjustments:
                adjusted_debt -= adjustments["cash_netting"]
            if "ebitda_addbacks" in adjustments:
                adjusted_ebitda += adjustments["ebitda_addbacks"]
            if "one_time_expenses" in adjustments:
                adjusted_ebitda += adjustments["one_time_expenses"]

        if adjusted_ebitda <= 0:
            return {
                "success": False,
                "error": "EBITDA must be positive for ratio calculation",
                "ebitda": adjusted_ebitda,
            }

        ratio = adjusted_debt / adjusted_ebitda

        return {
            "success": True,
            "ratio_name": "Debt/EBITDA",
            "ratio_value": round(ratio, 2),
            "components": {
                "total_debt": total_debt,
                "adjusted_debt": adjusted_debt,
                "ebitda": ebitda,
                "adjusted_ebitda": adjusted_ebitda,
            },
            "formula": f"{adjusted_debt:,.0f} / {adjusted_ebitda:,.0f} = {ratio:.2f}x",
        }
    except Exception as e:
        logger.error(f"Debt/EBITDA calculation error: {e}")
        return {"success": False, "error": str(e)}


def calculate_interest_coverage(
    ebitda: float,
    interest_expense: float,
    adjustments: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Calculate Interest Coverage Ratio (ICR).

    Args:
        ebitda: EBITDA for the period
        interest_expense: Total interest expense
        adjustments: Optional adjustments

    Returns:
        Calculation result with ratio value
    """
    try:
        adjusted_ebitda = ebitda
        adjusted_interest = interest_expense

        if adjustments:
            if "ebitda_addbacks" in adjustments:
                adjusted_ebitda += adjustments["ebitda_addbacks"]
            if "capitalized_interest" in adjustments:
                adjusted_interest += adjustments["capitalized_interest"]

        if adjusted_interest <= 0:
            return {
                "success": True,
                "ratio_name": "Interest Coverage",
                "ratio_value": float("inf"),
                "note": "No interest expense - ratio is infinite",
            }

        ratio = adjusted_ebitda / adjusted_interest

        return {
            "success": True,
            "ratio_name": "Interest Coverage",
            "ratio_value": round(ratio, 2),
            "components": {
                "ebitda": ebitda,
                "adjusted_ebitda": adjusted_ebitda,
                "interest_expense": interest_expense,
                "adjusted_interest": adjusted_interest,
            },
            "formula": f"{adjusted_ebitda:,.0f} / {adjusted_interest:,.0f} = {ratio:.2f}x",
        }
    except Exception as e:
        logger.error(f"Interest coverage calculation error: {e}")
        return {"success": False, "error": str(e)}


def calculate_current_ratio(
    current_assets: float,
    current_liabilities: float,
) -> Dict[str, Any]:
    """
    Calculate Current Ratio.

    Args:
        current_assets: Total current assets
        current_liabilities: Total current liabilities

    Returns:
        Calculation result with ratio value
    """
    try:
        if current_liabilities <= 0:
            return {
                "success": False,
                "error": "Current liabilities must be positive",
            }

        ratio = current_assets / current_liabilities

        return {
            "success": True,
            "ratio_name": "Current Ratio",
            "ratio_value": round(ratio, 2),
            "components": {
                "current_assets": current_assets,
                "current_liabilities": current_liabilities,
            },
            "formula": f"{current_assets:,.0f} / {current_liabilities:,.0f} = {ratio:.2f}",
        }
    except Exception as e:
        logger.error(f"Current ratio calculation error: {e}")
        return {"success": False, "error": str(e)}


def calculate_net_worth(
    total_assets: float,
    total_liabilities: float,
    exclude_intangibles: bool = False,
    intangible_assets: float = 0,
) -> Dict[str, Any]:
    """
    Calculate Net Worth (or Tangible Net Worth).

    Args:
        total_assets: Total assets
        total_liabilities: Total liabilities
        exclude_intangibles: Whether to calculate tangible net worth
        intangible_assets: Value of intangible assets to exclude

    Returns:
        Calculation result with net worth value
    """
    try:
        adjusted_assets = total_assets
        if exclude_intangibles:
            adjusted_assets -= intangible_assets

        net_worth = adjusted_assets - total_liabilities

        ratio_name = "Tangible Net Worth" if exclude_intangibles else "Net Worth"

        return {
            "success": True,
            "ratio_name": ratio_name,
            "ratio_value": round(net_worth, 2),
            "components": {
                "total_assets": total_assets,
                "adjusted_assets": adjusted_assets,
                "total_liabilities": total_liabilities,
                "intangibles_excluded": intangible_assets if exclude_intangibles else 0,
            },
            "formula": f"{adjusted_assets:,.0f} - {total_liabilities:,.0f} = {net_worth:,.0f}",
        }
    except Exception as e:
        logger.error(f"Net worth calculation error: {e}")
        return {"success": False, "error": str(e)}


def calculate_fixed_charge_coverage(
    ebitda: float,
    capex: float,
    interest_expense: float,
    principal_payments: float,
    lease_payments: float = 0,
) -> Dict[str, Any]:
    """
    Calculate Fixed Charge Coverage Ratio.

    Args:
        ebitda: EBITDA for the period
        capex: Capital expenditures
        interest_expense: Interest expense
        principal_payments: Scheduled principal payments
        lease_payments: Operating lease payments

    Returns:
        Calculation result with ratio value
    """
    try:
        # Numerator: EBITDA - CapEx
        numerator = ebitda - capex

        # Denominator: Interest + Principal + Lease payments
        denominator = interest_expense + principal_payments + lease_payments

        if denominator <= 0:
            return {
                "success": True,
                "ratio_name": "Fixed Charge Coverage",
                "ratio_value": float("inf"),
                "note": "No fixed charges - ratio is infinite",
            }

        ratio = numerator / denominator

        return {
            "success": True,
            "ratio_name": "Fixed Charge Coverage",
            "ratio_value": round(ratio, 2),
            "components": {
                "ebitda": ebitda,
                "capex": capex,
                "numerator": numerator,
                "interest_expense": interest_expense,
                "principal_payments": principal_payments,
                "lease_payments": lease_payments,
                "denominator": denominator,
            },
            "formula": f"({ebitda:,.0f} - {capex:,.0f}) / ({interest_expense:,.0f} + {principal_payments:,.0f} + {lease_payments:,.0f}) = {ratio:.2f}x",
        }
    except Exception as e:
        logger.error(f"Fixed charge coverage calculation error: {e}")
        return {"success": False, "error": str(e)}
