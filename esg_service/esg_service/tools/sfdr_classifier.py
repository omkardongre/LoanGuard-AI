"""
SFDR 2.0 Classifier - Classify financial products under new SFDR categories.

Production-level implementation based on EU SFDR 2.0 (November 2025 proposal).
Implements 3 new product categories replacing Article 8/9.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class SFDR2Classifier:
    """
    Classify financial products under SFDR 2.0 categories.
    
    Based on EU SFDR 2.0 (November 2025 Proposal):
    - Article 7: Transition - Products investing in credible transition
    - Article 8: ESG Basics - Products integrating ESG beyond risk
    - Article 9: Sustainable - Products with high sustainability standards
    
    70% threshold for positive contribution in Transition/Sustainable.
    15% Taxonomy alignment = automatic 70% threshold meeting.
    
    Reference: research5_lma_linkedin_insights.md, SFDR 2.0 proposal
    """
    
    # New SFDR 2.0 Categories
    CATEGORIES = {
        "ARTICLE_7_TRANSITION": {
            "name": "Transition",
            "description": "Products investing in credible transition pathways",
            "threshold": 70,
            "color": "amber",
        },
        "ARTICLE_8_ESG_BASICS": {
            "name": "ESG Basics",
            "description": "Products integrating ESG beyond risk management",
            "threshold": 70,
            "color": "light_green",
        },
        "ARTICLE_9_SUSTAINABLE": {
            "name": "Sustainable",
            "description": "Products with high sustainability standards",
            "threshold": 70,
            "color": "dark_green",
        },
        "UNCATEGORIZED": {
            "name": "Uncategorized",
            "description": "Products not meeting any sustainability category",
            "threshold": 0,
            "color": "grey",
        },
    }
    
    # Old to new mapping
    LEGACY_MAPPING = {
        "ARTICLE_6": "UNCATEGORIZED",
        "ARTICLE_8": "ARTICLE_8_ESG_BASICS",
        "ARTICLE_8_PLUS": "ARTICLE_7_TRANSITION",
        "ARTICLE_9": "ARTICLE_9_SUSTAINABLE",
    }
    
    # Taxonomy alignment bonus
    TAXONOMY_ALIGNMENT_BONUS_THRESHOLD = 15  # 15% taxonomy = meets 70%
    
    def __init__(self):
        """Initialize SFDR 2.0 Classifier."""
        self.bq = BigQueryClient()
    
    def classify_product(self, product_id: str) -> Dict[str, Any]:
        """
        Classify a financial product under SFDR 2.0.
        
        Args:
            product_id: Product identifier
            
        Returns:
            SFDR 2.0 classification
        """
        try:
            # Get product data
            product_data = self._get_product_data(product_id)
            
            if not product_data:
                return {"success": False, "error": f"Product {product_id} not found"}
            
            # Get current classification
            current = product_data.get("current_classification", "ARTICLE_6")
            
            # Calculate component scores
            transition_score = self._calculate_transition_score(product_data)
            sustainable_score = self._calculate_sustainable_score(product_data)
            esg_basics_score = self._calculate_esg_basics_score(product_data)
            taxonomy_aligned = product_data.get("taxonomy_aligned_pct", 0) or 0
            
            # Apply taxonomy bonus
            if taxonomy_aligned >= self.TAXONOMY_ALIGNMENT_BONUS_THRESHOLD:
                transition_score = max(transition_score, 70)
                sustainable_score = max(sustainable_score, 70)
            
            # Determine new classification
            if sustainable_score >= 70:
                new_classification = "ARTICLE_9_SUSTAINABLE"
            elif transition_score >= 70:
                new_classification = "ARTICLE_7_TRANSITION"
            elif esg_basics_score >= 70:
                new_classification = "ARTICLE_8_ESG_BASICS"
            else:
                new_classification = "UNCATEGORIZED"
            
            # Check exclusion compliance
            exclusions_met = self._check_exclusions(product_data, new_classification)
            
            if not exclusions_met and new_classification != "UNCATEGORIZED":
                new_classification = "UNCATEGORIZED"
            
            return {
                "success": True,
                "product_id": product_id,
                "product_name": product_data.get("product_name", ""),
                "current_classification": current,
                "new_classification": new_classification,
                "category_details": self.CATEGORIES[new_classification],
                "component_scores": {
                    "transition": round(transition_score, 1),
                    "sustainable": round(sustainable_score, 1),
                    "esg_basics": round(esg_basics_score, 1),
                },
                "taxonomy_aligned_pct": taxonomy_aligned,
                "exclusion_compliance": exclusions_met,
                "requires_change": current != self._map_legacy_to_new(current) or 
                                   self._map_legacy_to_new(current) != new_classification,
                "classification_date": str(date.today()),
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"SFDR classification error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_product_data(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product data from BigQuery."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sfdr_classifications`
                WHERE product_id = '{product_id}'
                ORDER BY created_at DESC
                LIMIT 1
            """
            results = self.bq.execute_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def _calculate_transition_score(self, data: Dict[str, Any]) -> float:
        """Calculate transition category score."""
        score = data.get("transition_threshold_pct", 0) or 0
        
        # Check for transition plan alignment
        if data.get("has_transition_plan"):
            score = max(score, 70)
        
        # Check Climate Transition Benchmark alignment
        if data.get("ctb_aligned"):
            score = max(score, 70)
        
        return min(score, 100)
    
    def _calculate_sustainable_score(self, data: Dict[str, Any]) -> float:
        """Calculate sustainable category score."""
        score = data.get("sustainable_threshold_pct", 0) or 0
        
        # Paris-aligned benchmark
        if data.get("pab_aligned"):
            score = max(score, 70)
        
        # Taxonomy alignment bonus
        taxonomy = data.get("taxonomy_aligned_pct", 0) or 0
        if taxonomy >= 15:
            score = max(score, 70)
        
        return min(score, 100)
    
    def _calculate_esg_basics_score(self, data: Dict[str, Any]) -> float:
        """Calculate ESG basics category score."""
        score = data.get("esg_basics_pct", 0) or 0
        
        # ESG integration beyond risk
        if data.get("esg_integration"):
            score = max(score, 50)
        
        # PAI consideration
        if data.get("pai_disclosed"):
            score += 20
        
        return min(score, 100)
    
    def _check_exclusions(self, data: Dict[str, Any], category: str) -> bool:
        """Check mandatory exclusions for category."""
        # SFDR 2.0 has mandatory exclusions per category
        if category == "ARTICLE_9_SUSTAINABLE":
            # Strictest exclusions
            return data.get("exclusion_compliance", False)
        elif category == "ARTICLE_7_TRANSITION":
            # Transition-specific exclusions
            return data.get("exclusion_compliance", False)
        elif category == "ARTICLE_8_ESG_BASICS":
            # Basic ESG exclusions
            return data.get("exclusion_compliance", False)
        
        return True
    
    def _map_legacy_to_new(self, legacy: str) -> str:
        """Map legacy SFDR classification to new."""
        return self.LEGACY_MAPPING.get(legacy, "UNCATEGORIZED")
    
    def save_classification(
        self, 
        product_id: str,
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save SFDR 2.0 classification to BigQuery."""
        try:
            classification_id = f"SFDR-{product_id}-{datetime.now().strftime('%Y%m%d')}"
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.sfdr_classifications`
                (classification_id, product_id, product_name, current_classification,
                 new_classification, transition_threshold_pct, sustainable_threshold_pct,
                 esg_basics_pct, taxonomy_aligned_pct, exclusion_compliance,
                 classification_date, created_at)
                VALUES (
                    '{classification_id}',
                    '{product_id}',
                    '{classification.get("product_name", "")}',
                    '{classification.get("current_classification", "")}',
                    '{classification.get("new_classification", "")}',
                    {classification.get("component_scores", {}).get("transition", 0)},
                    {classification.get("component_scores", {}).get("sustainable", 0)},
                    {classification.get("component_scores", {}).get("esg_basics", 0)},
                    {classification.get("taxonomy_aligned_pct", 0)},
                    {str(classification.get("exclusion_compliance", False)).upper()},
                    CURRENT_DATE(),
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "classification_id": classification_id,
                "message": "SFDR 2.0 classification saved",
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Classification save error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio_classification_summary(self) -> Dict[str, Any]:
        """Get portfolio-level SFDR 2.0 classification summary."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_products,
                    COUNTIF(new_classification = 'ARTICLE_9_SUSTAINABLE') as sustainable,
                    COUNTIF(new_classification = 'ARTICLE_7_TRANSITION') as transition,
                    COUNTIF(new_classification = 'ARTICLE_8_ESG_BASICS') as esg_basics,
                    COUNTIF(new_classification = 'UNCATEGORIZED') as uncategorized,
                    AVG(taxonomy_aligned_pct) as avg_taxonomy_alignment
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sfdr_classifications`
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "total_products": 0, "source": "BigQuery"}
            
            row = results[0]
            total = row.get("total_products", 0) or 0
            
            return {
                "success": True,
                "total_products": total,
                "by_category": {
                    "ARTICLE_9_SUSTAINABLE": row.get("sustainable", 0),
                    "ARTICLE_7_TRANSITION": row.get("transition", 0),
                    "ARTICLE_8_ESG_BASICS": row.get("esg_basics", 0),
                    "UNCATEGORIZED": row.get("uncategorized", 0),
                },
                "avg_taxonomy_alignment": round(row.get("avg_taxonomy_alignment", 0) or 0, 1),
                "compliance_note": "SFDR 2.0 expected effective ~2028",
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Classification summary error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_migration_analysis(self) -> Dict[str, Any]:
        """Analyze migration from old to new SFDR categories."""
        try:
            query = f"""
                SELECT 
                    current_classification,
                    new_classification,
                    COUNT(*) as count
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sfdr_classifications`
                GROUP BY current_classification, new_classification
            """
            
            results = self.bq.execute_query(query) or []
            
            migrations = []
            for row in results:
                migrations.append({
                    "from": row.get("current_classification"),
                    "to": row.get("new_classification"),
                    "count": row.get("count", 0),
                })
            
            return {
                "success": True,
                "migrations": migrations,
                "note": "Shows how products would migrate under SFDR 2.0",
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Migration analysis error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_sfdr_classifier: Optional[SFDR2Classifier] = None


def get_sfdr_classifier() -> SFDR2Classifier:
    """Get or create SFDR 2.0 Classifier singleton."""
    global _sfdr_classifier
    if _sfdr_classifier is None:
        _sfdr_classifier = SFDR2Classifier()
    return _sfdr_classifier


# Convenience functions
def classify_sfdr_product(product_id: str) -> Dict[str, Any]:
    """Classify product under SFDR 2.0."""
    return get_sfdr_classifier().classify_product(product_id)


def get_sfdr_portfolio_summary() -> Dict[str, Any]:
    """Get portfolio SFDR 2.0 summary."""
    return get_sfdr_classifier().get_portfolio_classification_summary()


def get_sfdr_migration_analysis() -> Dict[str, Any]:
    """Analyze SFDR migration."""
    return get_sfdr_classifier().get_migration_analysis()
