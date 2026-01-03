"""
Configuration for Covenant Service.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Model configuration
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))

# Google Cloud configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("CLOUD_PROJECT_REGION", "us-central1")

# BigQuery configuration
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET_ID", "loanguard_data")
BIGQUERY_COVENANTS_TABLE = os.getenv("BIGQUERY_COVENANTS_TABLE", "covenants")
BIGQUERY_MEASUREMENTS_TABLE = os.getenv("BIGQUERY_MEASUREMENTS_TABLE", "covenant_measurements")

# ML Model configuration
BREACH_MODEL_PATH = os.getenv("BREACH_PREDICTOR_MODEL_PATH", "models/breach_predictor.pkl")
SHAP_BASE_VALUES_PATH = os.getenv("SHAP_BASE_VALUES_PATH", "models/shap_base_values.json")

# Compliance thresholds
DEFAULT_WARNING_THRESHOLD = 0.15  # 15% buffer before breach
DEFAULT_PREDICTION_HORIZON_DAYS = 90
