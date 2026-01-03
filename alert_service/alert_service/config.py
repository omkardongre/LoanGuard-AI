"""
Configuration for Alert Service.
"""

import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Email configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "alerts@loanguard.ai")

# Slack configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")

# Alert thresholds
ALERT_SEVERITY_CRITICAL = "CRITICAL"
ALERT_SEVERITY_HIGH = "HIGH"
ALERT_SEVERITY_MEDIUM = "MEDIUM"
ALERT_SEVERITY_LOW = "LOW"
