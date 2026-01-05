#!/usr/bin/env python3
"""
Create BigQuery tables for LoanGuard AI Platform.
"""

import os
import sys
from google.cloud import bigquery
from google.cloud.exceptions import Conflict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import settings


def create_dataset(client: bigquery.Client, dataset_id: str) -> None:
    """Create dataset if it doesn't exist."""
    dataset_ref = f"{client.project}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    
    try:
        client.create_dataset(dataset)
        print(f"✅ Created dataset: {dataset_id}")
    except Conflict:
        print(f"ℹ️  Dataset already exists: {dataset_id}")


def create_tables(client: bigquery.Client, dataset_id: str) -> None:
    """Create all required tables."""
    
    tables = {
        "loans": [
            bigquery.SchemaField("loan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("borrower_name", "STRING"),
            bigquery.SchemaField("borrower_id", "STRING"),
            bigquery.SchemaField("facility_amount", "FLOAT64"),
            bigquery.SchemaField("currency", "STRING"),
            bigquery.SchemaField("maturity_date", "DATE"),
            bigquery.SchemaField("loan_type", "STRING"),
            bigquery.SchemaField("syndicate_members", "STRING", mode="REPEATED"),
            bigquery.SchemaField("agent_bank", "STRING"),
            bigquery.SchemaField("industry", "STRING"),
            bigquery.SchemaField("is_sll", "BOOL"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ],
        "covenants": [
            bigquery.SchemaField("covenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("loan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("covenant_type", "STRING"),
            bigquery.SchemaField("covenant_name", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("threshold_value", "FLOAT64"),
            bigquery.SchemaField("threshold_operator", "STRING"),
            bigquery.SchemaField("measurement_frequency", "STRING"),
            bigquery.SchemaField("cure_period_days", "INT64"),
            bigquery.SchemaField("source_document", "STRING"),
            bigquery.SchemaField("source_section", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
        "covenant_measurements": [
            bigquery.SchemaField("measurement_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("covenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("loan_id", "STRING"),
            bigquery.SchemaField("measurement_date", "DATE"),
            bigquery.SchemaField("actual_value", "FLOAT64"),
            bigquery.SchemaField("is_compliant", "BOOL"),
            bigquery.SchemaField("breach_severity", "STRING"),
            bigquery.SchemaField("buffer_percentage", "FLOAT64"),
            bigquery.SchemaField("predicted_breach_probability", "FLOAT64"),
            bigquery.SchemaField("shap_explanation", "JSON"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
        "esg_kpis": [
            bigquery.SchemaField("kpi_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("loan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("kpi_name", "STRING"),
            bigquery.SchemaField("kpi_type", "STRING"),
            bigquery.SchemaField("baseline_value", "FLOAT64"),
            bigquery.SchemaField("target_value", "FLOAT64"),
            bigquery.SchemaField("current_value", "FLOAT64"),
            bigquery.SchemaField("unit", "STRING"),
            bigquery.SchemaField("target_date", "DATE"),
            bigquery.SchemaField("measurement_date", "DATE"),
            bigquery.SchemaField("verification_status", "STRING"),
            bigquery.SchemaField("verifier", "STRING"),
            bigquery.SchemaField("greenwashing_risk_score", "FLOAT64"),
            bigquery.SchemaField("margin_adjustment_bps", "FLOAT64"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
        "alerts": [
            bigquery.SchemaField("alert_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("loan_id", "STRING"),
            bigquery.SchemaField("alert_type", "STRING"),
            bigquery.SchemaField("severity", "STRING"),
            bigquery.SchemaField("message", "STRING"),
            bigquery.SchemaField("details", "JSON"),
            bigquery.SchemaField("recommended_action", "STRING"),
            bigquery.SchemaField("response_deadline", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("acknowledged", "BOOL"),
            bigquery.SchemaField("acknowledged_by", "STRING"),
            bigquery.SchemaField("acknowledged_at", "TIMESTAMP"),
        ],
        "documents": [
            bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("loan_id", "STRING"),
            bigquery.SchemaField("document_type", "STRING"),
            bigquery.SchemaField("file_name", "STRING"),
            bigquery.SchemaField("file_path", "STRING"),
            bigquery.SchemaField("page_count", "INT64"),
            bigquery.SchemaField("extracted_text", "STRING"),
            bigquery.SchemaField("sections", "JSON"),
            bigquery.SchemaField("upload_date", "TIMESTAMP"),
            bigquery.SchemaField("processed_at", "TIMESTAMP"),
            bigquery.SchemaField("status", "STRING"),
        ],
        # V8 New Table (Affinda Integration)
        "document_extractions": [
            bigquery.SchemaField("extraction_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("loan_id", "STRING"),
            bigquery.SchemaField("document_filename", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("extraction_source", "STRING"),
            bigquery.SchemaField("extraction_confidence", "FLOAT64"),
            bigquery.SchemaField("borrower_name", "STRING"),
            bigquery.SchemaField("lender_name", "STRING"),
            bigquery.SchemaField("loan_amount", "FLOAT64"),
            bigquery.SchemaField("currency", "STRING"),
            bigquery.SchemaField("maturity_date", "DATE"),
            bigquery.SchemaField("interest_rate", "STRING"),
            bigquery.SchemaField("covenants_json", "JSON"),
            bigquery.SchemaField("raw_text", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
    }

    for table_name, schema in tables.items():
        table_ref = f"{client.project}.{dataset_id}.{table_name}"
        table = bigquery.Table(table_ref, schema=schema)
        
        try:
            client.create_table(table)
            print(f"✅ Created table: {table_name}")
        except Conflict:
            print(f"ℹ️  Table already exists: {table_name}")


def main():
    """Main entry point."""
    print("🔧 Creating BigQuery tables for LoanGuard AI...")
    print("")
    
    project_id = settings.GOOGLE_CLOUD_PROJECT
    dataset_id = settings.BIGQUERY_DATASET_ID
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT not set")
        sys.exit(1)
    
    print(f"📋 Project: {project_id}")
    print(f"📊 Dataset: {dataset_id}")
    print("")
    
    client = bigquery.Client(project=project_id)
    
    create_dataset(client, dataset_id)
    create_tables(client, dataset_id)
    
    print("")
    print("✅ BigQuery setup complete!")


if __name__ == "__main__":
    main()
