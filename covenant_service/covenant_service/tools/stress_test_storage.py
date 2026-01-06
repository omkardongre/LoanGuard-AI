"""
BigQuery Storage for Stress Test Results.
V9 - Store and retrieve stress test history for compliance.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


# BigQuery table schema for stress test results
STRESS_TEST_RESULTS_SCHEMA = [
    {"name": "result_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "run_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "scenario_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "scenario_name", "type": "STRING", "mode": "REQUIRED"},
    {"name": "scenario_type", "type": "STRING", "mode": "NULLABLE"},
    {"name": "loan_count", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "total_ead", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "base_ecl_total", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "stressed_ecl_total", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "ecl_increase_pct", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "pd_multiplier", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "lgd_multiplier", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "avg_base_pd", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "avg_stressed_pd", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "avg_base_lgd", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "macro_mortgage_rate", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "macro_treasury_10y", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "macro_fed_funds", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "production_level", "type": "BOOLEAN", "mode": "REQUIRED"},
    {"name": "loan_results_json", "type": "STRING", "mode": "NULLABLE"},
    {"name": "sector_impacts_json", "type": "STRING", "mode": "NULLABLE"},
]


class StressTestStorage:
    """Storage service for stress test results in BigQuery."""
    
    TABLE_NAME = "stress_test_results"
    
    def __init__(self):
        self._client = None
        self._dataset = None
        self._project = None
        self._table_created = False
    
    @property
    def client(self):
        """Lazy load BigQuery client."""
        if self._client is None:
            from common.bigquery_client import get_bigquery_client
            bq = get_bigquery_client()
            self._client = bq.client
            self._dataset = bq.dataset
            self._project = bq.project
        return self._client
    
    def _ensure_table_exists(self):
        """Create table if it doesn't exist."""
        if self._table_created:
            return
        
        try:
            from google.cloud import bigquery
            
            table_id = f"{self._project}.{self._dataset}.{self.TABLE_NAME}"
            
            # Check if table exists
            try:
                self.client.get_table(table_id)
                self._table_created = True
                return
            except Exception:
                pass  # Table doesn't exist
            
            # Create table
            schema = [
                bigquery.SchemaField(
                    field["name"],
                    field["type"],
                    mode=field.get("mode", "NULLABLE")
                )
                for field in STRESS_TEST_RESULTS_SCHEMA
            ]
            
            table = bigquery.Table(table_id, schema=schema)
            table.description = "Stress test results for Basel III/IFRS 9 compliance"
            
            self.client.create_table(table)
            logger.info(f"Created table {table_id}")
            self._table_created = True
            
        except Exception as e:
            logger.warning(f"Could not create table: {e}")
    
    def save_result(self, result: Dict[str, Any]) -> str:
        """
        Save stress test result to BigQuery.
        
        Args:
            result: Stress test result dictionary
            
        Returns:
            Result ID
        """
        self._ensure_table_exists()
        
        # Generate result ID
        result_id = f"st_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{result.get('scenario', {}).get('id', 'unknown')}"
        
        try:
            # Prepare row
            row = {
                "result_id": result_id,
                "run_timestamp": result.get("run_timestamp", datetime.utcnow().isoformat()),
                "scenario_id": result.get("scenario", {}).get("id", ""),
                "scenario_name": result.get("scenario", {}).get("name", ""),
                "scenario_type": result.get("scenario", {}).get("type", ""),
                "loan_count": result.get("portfolio_summary", {}).get("loan_count", 0),
                "total_ead": result.get("portfolio_summary", {}).get("total_ead", 0),
                "base_ecl_total": result.get("ecl_summary", {}).get("base_ecl_total", 0),
                "stressed_ecl_total": result.get("ecl_summary", {}).get("stressed_ecl_total", 0),
                "ecl_increase_pct": result.get("ecl_summary", {}).get("ecl_increase_pct", 0),
                "pd_multiplier": result.get("scenario", {}).get("pd_multiplier"),
                "lgd_multiplier": result.get("scenario", {}).get("lgd_multiplier"),
                "avg_base_pd": result.get("ml_predictions", {}).get("avg_base_pd"),
                "avg_stressed_pd": result.get("ml_predictions", {}).get("avg_stressed_pd"),
                "avg_base_lgd": result.get("ml_predictions", {}).get("avg_base_lgd"),
                "macro_mortgage_rate": result.get("macro_conditions", {}).get("mortgage_rate_30y"),
                "macro_treasury_10y": result.get("macro_conditions", {}).get("treasury_10y"),
                "macro_fed_funds": result.get("macro_conditions", {}).get("fed_funds_rate"),
                "production_level": result.get("production_level", False),
                "loan_results_json": json.dumps(result.get("loan_results", [])[:50]),
                "sector_impacts_json": json.dumps(result.get("sector_impacts", {})),
            }
            
            # Insert row
            table_id = f"{self._project}.{self._dataset}.{self.TABLE_NAME}"
            errors = self.client.insert_rows_json(table_id, [row])
            
            if errors:
                logger.error(f"Failed to insert row: {errors}")
                return ""
            
            logger.info(f"Saved stress test result: {result_id}")
            return result_id
            
        except Exception as e:
            logger.error(f"Failed to save stress test result: {e}")
            return ""
    
    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific stress test result by ID."""
        try:
            query = f"""
                SELECT *
                FROM `{self._project}.{self._dataset}.{self.TABLE_NAME}`
                WHERE result_id = @result_id
            """
            
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("result_id", "STRING", result_id)
                ]
            )
            
            result = self.client.query(query, job_config=job_config)
            rows = list(result)
            
            if not rows:
                return None
            
            row = dict(rows[0])
            
            # Parse JSON fields
            if row.get("loan_results_json"):
                row["loan_results"] = json.loads(row["loan_results_json"])
            if row.get("sector_impacts_json"):
                row["sector_impacts"] = json.loads(row["sector_impacts_json"])
            
            return row
            
        except Exception as e:
            logger.error(f"Failed to get stress test result: {e}")
            return None
    
    def get_history(
        self,
        limit: int = 50,
        scenario_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get stress test history.
        
        Args:
            limit: Maximum number of results
            scenario_id: Filter by scenario (optional)
        """
        try:
            where_clause = ""
            if scenario_id:
                where_clause = f"WHERE scenario_id = '{scenario_id}'"
            
            query = f"""
                SELECT 
                    result_id,
                    run_timestamp,
                    scenario_id,
                    scenario_name,
                    scenario_type,
                    loan_count,
                    total_ead,
                    base_ecl_total,
                    stressed_ecl_total,
                    ecl_increase_pct,
                    production_level
                FROM `{self._project}.{self._dataset}.{self.TABLE_NAME}`
                {where_clause}
                ORDER BY run_timestamp DESC
                LIMIT {limit}
            """
            
            result = self.client.query(query)
            return [dict(row) for row in result]
            
        except Exception as e:
            logger.error(f"Failed to get stress test history: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics for stress tests."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_runs,
                    COUNT(DISTINCT scenario_id) as scenarios_used,
                    AVG(ecl_increase_pct) as avg_ecl_increase,
                    MAX(ecl_increase_pct) as max_ecl_increase,
                    MIN(run_timestamp) as first_run,
                    MAX(run_timestamp) as last_run
                FROM `{self._project}.{self._dataset}.{self.TABLE_NAME}`
            """
            
            result = self.client.query(query)
            rows = list(result)
            
            if not rows:
                return {}
            
            return dict(rows[0])
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Singleton instance
_stress_test_storage: Optional[StressTestStorage] = None


def get_stress_test_storage() -> StressTestStorage:
    """Get or create StressTestStorage singleton."""
    global _stress_test_storage
    if _stress_test_storage is None:
        _stress_test_storage = StressTestStorage()
    return _stress_test_storage
