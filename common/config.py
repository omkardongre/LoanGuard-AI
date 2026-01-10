"""
Central configuration for LoanGuard AI Platform.

Provides port configurations, service URLs, and default parameters for all agents.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# Load .env file from project root
from dotenv import load_dotenv

# Find project root (where .env file is)
_project_root = Path(__file__).parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    # Try loading from current directory
    load_dotenv()


@dataclass
class ServiceConfig:
    """Configuration for a single service."""
    name: str
    port: int
    host: str = "127.0.0.1"

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class Settings:
    """Application settings loaded from environment variables."""

    # --- Service Port Configurations ---
    DOCUMENT_SERVICE_PORT: int = int(os.getenv("DOCUMENT_SERVICE_PORT", "8081"))
    COVENANT_SERVICE_PORT: int = int(os.getenv("COVENANT_SERVICE_PORT", "8082"))
    ESG_SERVICE_PORT: int = int(os.getenv("ESG_SERVICE_PORT", "8083"))
    ALERT_SERVICE_PORT: int = int(os.getenv("ALERT_SERVICE_PORT", "8084"))
    UI_CLIENT_PORT: int = int(os.getenv("UI_CLIENT_PORT", "8000"))

    # --- Service URL Configurations ---
    @property
    def document_service_url(self) -> str:
        return f"http://127.0.0.1:{self.DOCUMENT_SERVICE_PORT}"

    @property
    def covenant_service_url(self) -> str:
        return f"http://127.0.0.1:{self.COVENANT_SERVICE_PORT}"

    @property
    def esg_service_url(self) -> str:
        return f"http://127.0.0.1:{self.ESG_SERVICE_PORT}"

    @property
    def alert_service_url(self) -> str:
        return f"http://127.0.0.1:{self.ALERT_SERVICE_PORT}"

    @property
    def ui_client_url(self) -> str:
        return f"http://127.0.0.1:{self.UI_CLIENT_PORT}"

    # --- Google Cloud Configuration ---
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    CLOUD_PROJECT_REGION: str = os.getenv("CLOUD_PROJECT_REGION", "us-central1")

    # --- BigQuery Configuration ---
    BIGQUERY_DATASET_ID: str = os.getenv("BIGQUERY_DATASET_ID", "loanguard_data")
    BIGQUERY_LOANS_TABLE: str = os.getenv("BIGQUERY_LOANS_TABLE", "loans")
    BIGQUERY_COVENANTS_TABLE: str = os.getenv("BIGQUERY_COVENANTS_TABLE", "covenants")
    BIGQUERY_MEASUREMENTS_TABLE: str = os.getenv("BIGQUERY_MEASUREMENTS_TABLE", "covenant_measurements")
    BIGQUERY_ESG_TABLE: str = os.getenv("BIGQUERY_ESG_TABLE", "esg_kpis")
    BIGQUERY_ALERTS_TABLE: str = os.getenv("BIGQUERY_ALERTS_TABLE", "alerts")

    # --- External Services ---
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "alerts@loanguard.ai")
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    SLACK_BOT_TOKEN: Optional[str] = os.getenv("SLACK_BOT_TOKEN")

    # --- Model Configuration ---
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    BREACH_PREDICTOR_MODEL_PATH: str = os.getenv(
        "BREACH_PREDICTOR_MODEL_PATH", "models/breach_predictor.pkl"
    )
    SHAP_BASE_VALUES_PATH: str = os.getenv(
        "SHAP_BASE_VALUES_PATH", "models/shap_base_values.json"
    )

    # --- Artifact Names ---
    DOCUMENT_ARTIFACT_NAME: str = "document_extraction_results"
    COVENANT_ARTIFACT_NAME: str = "covenant_analysis_results"
    ESG_ARTIFACT_NAME: str = "esg_compliance_results"
    ALERT_ARTIFACT_NAME: str = "alert_generation_results"


settings = Settings()
