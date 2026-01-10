"""
Configuration for Document Service.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Model configuration
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("TOP_P", "0.95"))
TOP_K = int(os.getenv("TOP_K", "40"))

# Google Cloud configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("CLOUD_PROJECT_REGION", "us-central1")

# Document AI configuration
DOCUMENT_AI_PROCESSOR_ID = os.getenv("DOCUMENT_AI_PROCESSOR_ID", "")
DOCUMENT_AI_PROCESSOR_VERSION = os.getenv("DOCUMENT_AI_PROCESSOR_VERSION", "pretrained-ocr-v2.0-2023-06-02")

# BigQuery configuration
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET_ID", "loanguard_data")
BIGQUERY_DOCUMENTS_TABLE = os.getenv("BIGQUERY_DOCUMENTS_TABLE", "documents")
BIGQUERY_COVENANTS_TABLE = os.getenv("BIGQUERY_COVENANTS_TABLE", "covenants")
