"""
Common utilities and configurations for LoanGuard AI Platform.
"""

from common.config import settings
from common.bigquery_client import get_bigquery_client, BigQueryClient
from common.gcs_storage import get_storage, GCSStorage

__all__ = [
    "settings",
    "get_bigquery_client",
    "BigQueryClient",
    "get_storage",
    "GCSStorage",
]
