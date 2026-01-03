"""
BigQuery client utilities for LoanGuard AI Platform.

Provides reusable functions for interacting with BigQuery across all services.
"""

import logging
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from common.config import settings

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Client wrapper for BigQuery operations."""

    def __init__(self, project_id: Optional[str] = None, dataset_id: Optional[str] = None):
        self.project_id = project_id or settings.GOOGLE_CLOUD_PROJECT
        self.dataset_id = dataset_id or settings.BIGQUERY_DATASET_ID
        self._client: Optional[bigquery.Client] = None

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            self._client = bigquery.Client(project=self.project_id)
        return self._client

    def get_full_table_id(self, table_name: str) -> str:
        """Get fully qualified table ID."""
        return f"{self.project_id}.{self.dataset_id}.{table_name}"

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            self.client.get_table(self.get_full_table_id(table_name))
            return True
        except NotFound:
            return False

    def execute_query(
        self, query: str, params: Optional[List[bigquery.ScalarQueryParameter]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dicts."""
        job_config = bigquery.QueryJobConfig()
        if params:
            job_config.query_parameters = params

        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def insert_rows(self, table_name: str, rows: List[Dict[str, Any]]) -> List[Dict]:
        """Insert rows into a table."""
        table_id = self.get_full_table_id(table_name)
        errors = self.client.insert_rows_json(table_id, rows)
        if errors:
            logger.error(f"Insert errors: {errors}")
        return errors

    def get_loans(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve loans from the loans table."""
        query = f"""
            SELECT *
            FROM `{self.get_full_table_id(settings.BIGQUERY_LOANS_TABLE)}`
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        return self.execute_query(query)

    def get_loan_by_id(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific loan by ID."""
        query = f"""
            SELECT *
            FROM `{self.get_full_table_id(settings.BIGQUERY_LOANS_TABLE)}`
            WHERE loan_id = @loan_id
        """
        params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
        results = self.execute_query(query, params)
        return results[0] if results else None

    def get_covenants_by_loan(self, loan_id: str) -> List[Dict[str, Any]]:
        """Retrieve all covenants for a loan."""
        query = f"""
            SELECT *
            FROM `{self.get_full_table_id(settings.BIGQUERY_COVENANTS_TABLE)}`
            WHERE loan_id = @loan_id
        """
        params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
        return self.execute_query(query, params)

    def get_latest_measurements(self, covenant_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve latest measurements for a covenant."""
        query = f"""
            SELECT *
            FROM `{self.get_full_table_id(settings.BIGQUERY_MEASUREMENTS_TABLE)}`
            WHERE covenant_id = @covenant_id
            ORDER BY measurement_date DESC
            LIMIT {limit}
        """
        params = [bigquery.ScalarQueryParameter("covenant_id", "STRING", covenant_id)]
        return self.execute_query(query, params)

    def get_esg_kpis_by_loan(self, loan_id: str) -> List[Dict[str, Any]]:
        """Retrieve ESG KPIs for a loan."""
        query = f"""
            SELECT *
            FROM `{self.get_full_table_id(settings.BIGQUERY_ESG_TABLE)}`
            WHERE loan_id = @loan_id
        """
        params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
        return self.execute_query(query, params)

    def get_pending_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve unacknowledged alerts."""
        query = f"""
            SELECT *
            FROM `{self.get_full_table_id(settings.BIGQUERY_ALERTS_TABLE)}`
            WHERE acknowledged = FALSE
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        return self.execute_query(query)

    def get_compliance_summary(self, loan_id: str) -> Dict[str, Any]:
        """Get compliance summary for a loan."""
        query = f"""
            SELECT
                l.loan_id,
                l.borrower_name,
                l.facility_amount,
                COUNT(c.covenant_id) as total_covenants,
                COUNTIF(cm.is_compliant = TRUE) as compliant_count,
                COUNTIF(cm.is_compliant = FALSE) as breach_count,
                AVG(cm.predicted_breach_probability) as avg_breach_probability
            FROM `{self.get_full_table_id(settings.BIGQUERY_LOANS_TABLE)}` l
            LEFT JOIN `{self.get_full_table_id(settings.BIGQUERY_COVENANTS_TABLE)}` c
                ON l.loan_id = c.loan_id
            LEFT JOIN `{self.get_full_table_id(settings.BIGQUERY_MEASUREMENTS_TABLE)}` cm
                ON c.covenant_id = cm.covenant_id
            WHERE l.loan_id = @loan_id
            GROUP BY l.loan_id, l.borrower_name, l.facility_amount
        """
        params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
        results = self.execute_query(query, params)
        return results[0] if results else {}


# Singleton instance
bq_client = BigQueryClient()
