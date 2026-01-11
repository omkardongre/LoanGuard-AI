"""
SLLB Portfolio Manager Agent - Manage eligible SLL portfolios for SLLB issuance.

Production-level implementation based on ICMA Guidelines for SLL Financing Bonds (June 2024).
Implements 4 SLLBG core components.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import json

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class SLLBPortfolioManager:
    """
    Manage SLLB (Sustainability-Linked Loans financing Bonds) portfolios.
    
    Based on ICMA SLLBG 4 Components:
    1. Use of Proceeds - Allocate bond proceeds to eligible SLLs
    2. Process for SLL Evaluation & Selection - Eligibility governance
    3. Management of Proceeds - Track proceeds allocation
    4. Reporting - Annual SLLB reporting
    
    Reference: research4_sllb_guidelines.md
    """
    
    # SLLB Approaches
    APPROACH_FRAMEWORK = "APPROACH_1_FRAMEWORK"
    APPROACH_INDIVIDUAL = "APPROACH_2_INDIVIDUAL"
    
    # Eligibility statuses
    ELIGIBILITY_STATUSES = ["ELIGIBLE", "PENDING", "DISQUALIFIED", "REQUALIFIED"]
    
    def __init__(self):
        """Initialize SLLB Portfolio Manager."""
        self.bq = BigQueryClient()
    
    def create_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new SLLB portfolio.
        
        Args:
            portfolio_data: Portfolio configuration
            
        Returns:
            Created portfolio details
        """
        try:
            portfolio_id = f"SLLB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.sllb_portfolios`
                (portfolio_id, bond_isin, bond_name, issuer_name, issue_date, 
                 maturity_date, bond_amount, currency, single_sustainability_objective,
                 approach, total_eligible_slls, total_sll_value, allocated_amount,
                 unallocated_amount, created_at)
                VALUES (
                    '{portfolio_id}',
                    '{portfolio_data.get("bond_isin", "")}',
                    '{portfolio_data.get("bond_name", "")}',
                    '{portfolio_data.get("issuer_name", "")}',
                    DATE('{portfolio_data.get("issue_date", date.today())}'),
                    DATE('{portfolio_data.get("maturity_date", date.today())}'),
                    {portfolio_data.get("bond_amount", 0)},
                    '{portfolio_data.get("currency", "USD")}',
                    '{portfolio_data.get("sustainability_objective", "")}',
                    '{portfolio_data.get("approach", self.APPROACH_FRAMEWORK)}',
                    0,
                    0,
                    0,
                    {portfolio_data.get("bond_amount", 0)},
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "message": "SLLB portfolio created",
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Portfolio creation error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio(self, portfolio_id: str) -> Dict[str, Any]:
        """Get SLLB portfolio details."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sllb_portfolios`
                WHERE portfolio_id = '{portfolio_id}'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": False, "error": f"Portfolio {portfolio_id} not found"}
            
            portfolio = results[0]
            
            # Get eligible SLLs
            slls = self._get_eligible_slls(portfolio_id)
            
            return {
                "success": True,
                "portfolio": {
                    "portfolio_id": portfolio.get("portfolio_id"),
                    "bond_isin": portfolio.get("bond_isin"),
                    "bond_name": portfolio.get("bond_name"),
                    "issuer_name": portfolio.get("issuer_name"),
                    "bond_amount": portfolio.get("bond_amount"),
                    "currency": portfolio.get("currency"),
                    "sustainability_objective": portfolio.get("single_sustainability_objective"),
                    "approach": portfolio.get("approach"),
                    "total_eligible_slls": len(slls),
                    "total_sll_value": sum(s.get("loan_amount", 0) for s in slls),
                    "allocated_amount": sum(s.get("allocated_to_bond", 0) for s in slls),
                    "unallocated_amount": portfolio.get("unallocated_amount", 0),
                },
                "eligible_slls": slls,
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Portfolio retrieval error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_eligible_slls(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get eligible SLLs for a portfolio."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sllb_eligible_slls`
                WHERE portfolio_id = '{portfolio_id}'
                  AND eligibility_status = 'ELIGIBLE'
            """
            return self.bq.execute_query(query) or []
        except Exception:
            return []
    
    def add_sll_to_portfolio(
        self, 
        portfolio_id: str, 
        loan_id: str,
        sll_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add an SLL to the SLLB portfolio.
        
        Args:
            portfolio_id: SLLB portfolio ID
            loan_id: SLL loan ID
            sll_data: SLL details
            
        Returns:
            Add result
        """
        try:
            eligibility_id = f"ELIG-{loan_id}-{datetime.now().strftime('%Y%m%d')}"
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.sllb_eligible_slls`
                (eligibility_id, portfolio_id, loan_id, borrower_sector, borrower_geography,
                 loan_amount, allocated_to_bond, vintage_year, eligibility_status,
                 eligibility_date, kpi_type, spt_description, spt_progress, spt_achieved,
                 sllp_aligned, external_review_status, created_at)
                VALUES (
                    '{eligibility_id}',
                    '{portfolio_id}',
                    '{loan_id}',
                    '{sll_data.get("borrower_sector", "")}',
                    '{sll_data.get("borrower_geography", "")}',
                    {sll_data.get("loan_amount", 0)},
                    {sll_data.get("allocated_to_bond", 0)},
                    {sll_data.get("vintage_year", date.today().year)},
                    'ELIGIBLE',
                    CURRENT_DATE(),
                    '{sll_data.get("kpi_type", "")}',
                    '{sll_data.get("spt_description", "")}',
                    {sll_data.get("spt_progress", 0)},
                    {str(sll_data.get("spt_achieved", False)).upper()},
                    {str(sll_data.get("sllp_aligned", True)).upper()},
                    '{sll_data.get("external_review_status", "PENDING")}',
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            # Update portfolio totals
            self._update_portfolio_totals(portfolio_id)
            
            return {
                "success": True,
                "eligibility_id": eligibility_id,
                "message": f"SLL {loan_id} added to portfolio {portfolio_id}",
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Add SLL error: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_portfolio_totals(self, portfolio_id: str) -> None:
        """Update portfolio aggregate totals."""
        try:
            query = f"""
                UPDATE `{self.bq.project_id}.{self.bq.dataset_id}.sllb_portfolios`
                SET 
                    total_eligible_slls = (
                        SELECT COUNT(*) FROM `{self.bq.project_id}.{self.bq.dataset_id}.sllb_eligible_slls`
                        WHERE portfolio_id = '{portfolio_id}' AND eligibility_status = 'ELIGIBLE'
                    ),
                    total_sll_value = (
                        SELECT COALESCE(SUM(loan_amount), 0) FROM `{self.bq.project_id}.{self.bq.dataset_id}.sllb_eligible_slls`
                        WHERE portfolio_id = '{portfolio_id}' AND eligibility_status = 'ELIGIBLE'
                    ),
                    allocated_amount = (
                        SELECT COALESCE(SUM(allocated_to_bond), 0) FROM `{self.bq.project_id}.{self.bq.dataset_id}.sllb_eligible_slls`
                        WHERE portfolio_id = '{portfolio_id}' AND eligibility_status = 'ELIGIBLE'
                    ),
                    updated_at = CURRENT_TIMESTAMP()
                WHERE portfolio_id = '{portfolio_id}'
            """
            self.bq.execute_query(query)
        except Exception as e:
            logger.error(f"Portfolio update error: {e}")
    
    def disqualify_sll(
        self, 
        portfolio_id: str, 
        loan_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Disqualify an SLL from the portfolio.
        
        Args:
            portfolio_id: SLLB portfolio ID
            loan_id: SLL loan ID
            reason: Disqualification reason
            
        Returns:
            Disqualification result
        """
        try:
            query = f"""
                UPDATE `{self.bq.project_id}.{self.bq.dataset_id}.sllb_eligible_slls`
                SET 
                    eligibility_status = 'DISQUALIFIED',
                    disqualification_date = CURRENT_DATE(),
                    disqualification_reason = '{reason}'
                WHERE portfolio_id = '{portfolio_id}' AND loan_id = '{loan_id}'
            """
            
            self.bq.execute_query(query)
            self._update_portfolio_totals(portfolio_id)
            
            return {
                "success": True,
                "message": f"SLL {loan_id} disqualified from portfolio {portfolio_id}",
                "reason": reason,
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Disqualification error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get aggregate SLLB portfolio summary."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_portfolios,
                    SUM(bond_amount) as total_bond_value,
                    SUM(total_eligible_slls) as total_slls,
                    SUM(allocated_amount) as total_allocated,
                    SUM(unallocated_amount) as total_unallocated
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sllb_portfolios`
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "total_portfolios": 0, "source": "BigQuery"}
            
            row = results[0]
            
            return {
                "success": True,
                "total_portfolios": row.get("total_portfolios", 0),
                "total_bond_value": row.get("total_bond_value", 0),
                "total_slls": row.get("total_slls", 0),
                "total_allocated": row.get("total_allocated", 0),
                "total_unallocated": row.get("total_unallocated", 0),
                "allocation_rate": round(
                    (row.get("total_allocated", 0) or 0) / 
                    (row.get("total_bond_value", 1) or 1) * 100, 1
                ),
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Portfolio summary error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_sector_breakdown(self, portfolio_id: str) -> Dict[str, Any]:
        """Get sector breakdown for a portfolio."""
        try:
            query = f"""
                SELECT 
                    borrower_sector,
                    COUNT(*) as count,
                    SUM(loan_amount) as total_value,
                    SUM(allocated_to_bond) as allocated
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sllb_eligible_slls`
                WHERE portfolio_id = '{portfolio_id}' AND eligibility_status = 'ELIGIBLE'
                GROUP BY borrower_sector
            """
            
            results = self.bq.execute_query(query) or []
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "sector_breakdown": [
                    {
                        "sector": r.get("borrower_sector", "Unknown"),
                        "count": r.get("count", 0),
                        "total_value": r.get("total_value", 0),
                        "allocated": r.get("allocated", 0),
                    }
                    for r in results
                ],
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Sector breakdown error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_sllb_manager: Optional[SLLBPortfolioManager] = None


def get_sllb_manager() -> SLLBPortfolioManager:
    """Get or create SLLB Portfolio Manager singleton."""
    global _sllb_manager
    if _sllb_manager is None:
        _sllb_manager = SLLBPortfolioManager()
    return _sllb_manager


# Convenience functions
def create_sllb_portfolio(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new SLLB portfolio."""
    return get_sllb_manager().create_portfolio(portfolio_data)


def get_sllb_portfolio(portfolio_id: str) -> Dict[str, Any]:
    """Get SLLB portfolio details."""
    return get_sllb_manager().get_portfolio(portfolio_id)


def add_sll_to_sllb(portfolio_id: str, loan_id: str, sll_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add SLL to SLLB portfolio."""
    return get_sllb_manager().add_sll_to_portfolio(portfolio_id, loan_id, sll_data)


def disqualify_sllb_sll(portfolio_id: str, loan_id: str, reason: str) -> Dict[str, Any]:
    """Disqualify SLL from portfolio."""
    return get_sllb_manager().disqualify_sll(portfolio_id, loan_id, reason)


def get_sllb_summary() -> Dict[str, Any]:
    """Get SLLB portfolio summary."""
    return get_sllb_manager().get_portfolio_summary()
