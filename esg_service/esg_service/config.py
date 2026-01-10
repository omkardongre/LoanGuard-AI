"""
Configuration for ESG Service.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Model configuration
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Google Cloud configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# BigQuery configuration
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET_ID", "loanguard_data")
BIGQUERY_ESG_TABLE = os.getenv("BIGQUERY_ESG_TABLE", "esg_kpis")

# ESG Thresholds
GREENWASHING_RISK_THRESHOLD = 0.6  # Score above this triggers warning
SPT_ACHIEVEMENT_BUFFER = 0.05  # 5% buffer for SPT achievement
