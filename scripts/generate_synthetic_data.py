#!/usr/bin/env python3
"""
Generate synthetic loan data for LoanGuard AI Platform.

Creates realistic loan portfolio data for testing and demos.
"""

import os
import sys
import uuid
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import bigquery
from common.config import settings

# Configuration
NUM_LOANS = 50
COVENANTS_PER_LOAN = (3, 6)
MEASUREMENTS_PER_COVENANT = 4

# Sample data
BORROWERS = [
    "Acme Corp", "Global Industries", "TechStart Inc", "Energy Solutions Ltd",
    "Manufacturing Plus", "Retail Group", "Healthcare Systems", "Transport Co",
    "Financial Services Inc", "Construction Holdings", "Media Corp", "Pharma Ltd",
    "Logistics Express", "Consumer Goods Co", "Industrial Materials", "Clean Energy Inc",
    "Digital Ventures", "Agricultural Holdings", "Mining Resources", "Telecom Networks",
]

INDUSTRIES = [
    "Technology", "Manufacturing", "Healthcare", "Energy", "Retail",
    "Financial Services", "Transportation", "Construction", "Media", "Pharmaceuticals",
]

LOAN_TYPES = ["Term Loan", "Revolving Credit", "Bridge Loan", "Acquisition Facility"]
CURRENCIES = ["USD", "EUR", "GBP"]

COVENANT_TYPES = [
    ("Debt/EBITDA", "financial", "<=", 4.0),
    ("Interest Coverage", "financial", ">=", 2.5),
    ("Current Ratio", "financial", ">=", 1.2),
    ("Net Worth", "financial", ">=", 50000000),
    ("CapEx Limit", "financial", "<=", 25000000),
    ("Carbon Reduction", "esg", "<=", 80000),
    ("Renewable Energy %", "esg", ">=", 40),
    ("Board Diversity %", "esg", ">=", 35),
]


def generate_loans() -> List[Dict[str, Any]]:
    """Generate synthetic loan records."""
    loans = []
    
    for i in range(NUM_LOANS):
        loan_id = f"LOAN-{str(uuid.uuid4())[:8].upper()}"
        borrower = random.choice(BORROWERS)
        
        loan = {
            "loan_id": loan_id,
            "borrower_name": borrower,
            "borrower_id": f"BOR-{str(uuid.uuid4())[:6].upper()}",
            "facility_amount": random.choice([50, 100, 150, 200, 250, 500]) * 1_000_000,
            "currency": random.choice(CURRENCIES),
            "maturity_date": (datetime.now() + timedelta(days=random.randint(365, 1825))).strftime("%Y-%m-%d"),
            "loan_type": random.choice(LOAN_TYPES),
            "syndicate_members": random.sample(
                ["Bank A", "Bank B", "Bank C", "Bank D", "Bank E"],
                k=random.randint(2, 4)
            ),
            "agent_bank": random.choice(["JPMorgan", "Citi", "BofA", "HSBC", "Barclays"]),
            "industry": random.choice(INDUSTRIES),
            "is_sll": random.random() > 0.6,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        loans.append(loan)
    
    return loans


def generate_covenants(loans: List[Dict]) -> List[Dict[str, Any]]:
    """Generate covenant definitions for each loan."""
    covenants = []
    
    for loan in loans:
        num_covenants = random.randint(*COVENANTS_PER_LOAN)
        selected_covenants = random.sample(COVENANT_TYPES, min(num_covenants, len(COVENANT_TYPES)))
        
        for cov_name, cov_type, operator, threshold in selected_covenants:
            covenant = {
                "covenant_id": f"COV-{str(uuid.uuid4())[:8].upper()}",
                "loan_id": loan["loan_id"],
                "covenant_type": cov_type,
                "covenant_name": cov_name,
                "description": f"{cov_name} covenant for {loan['borrower_name']}",
                "threshold_value": threshold * (1 + random.uniform(-0.2, 0.2)),
                "threshold_operator": operator,
                "measurement_frequency": random.choice(["quarterly", "semi-annual", "annual"]),
                "cure_period_days": random.choice([30, 45, 60]),
                "source_document": "Credit Agreement",
                "source_section": f"Section {random.randint(5, 10)}.{random.randint(1, 5)}",
                "created_at": datetime.now().isoformat(),
            }
            covenants.append(covenant)
    
    return covenants


def generate_measurements(covenants: List[Dict]) -> List[Dict[str, Any]]:
    """Generate measurement history for each covenant."""
    measurements = []
    
    for covenant in covenants:
        threshold = covenant["threshold_value"]
        operator = covenant["threshold_operator"]
        
        for i in range(MEASUREMENTS_PER_COVENANT):
            measurement_date = datetime.now() - timedelta(days=90 * (MEASUREMENTS_PER_COVENANT - i))
            
            # Generate realistic values that sometimes breach
            if operator in ["<=", "<"]:
                actual = threshold * random.uniform(0.7, 1.15)
                is_compliant = actual <= threshold
            else:
                actual = threshold * random.uniform(0.85, 1.3)
                is_compliant = actual >= threshold
            
            buffer_pct = abs(actual - threshold) / threshold if threshold != 0 else 0
            
            if not is_compliant:
                severity = "breach"
            elif buffer_pct < 0.15:
                severity = "warning"
            else:
                severity = "none"
            
            measurement = {
                "measurement_id": f"MSR-{str(uuid.uuid4())[:8].upper()}",
                "covenant_id": covenant["covenant_id"],
                "loan_id": covenant["loan_id"],
                "measurement_date": measurement_date.strftime("%Y-%m-%d"),
                "actual_value": round(actual, 2),
                "is_compliant": is_compliant,
                "breach_severity": severity,
                "buffer_percentage": round(buffer_pct, 4),
                "predicted_breach_probability": round(random.uniform(0.05, 0.85), 4),
                "shap_explanation": None,
                "created_at": datetime.now().isoformat(),
            }
            measurements.append(measurement)
    
    return measurements


def generate_esg_kpis(loans: List[Dict]) -> List[Dict[str, Any]]:
    """Generate ESG KPIs for SLL loans."""
    kpis = []
    
    esg_definitions = [
        ("Carbon Emissions", "environmental", 100000, 70000, "tCO2e"),
        ("Renewable Energy", "environmental", 20, 50, "%"),
        ("Board Diversity", "social", 25, 40, "%"),
        ("Water Usage", "environmental", 500000, 350000, "m3"),
        ("Safety Incidents", "social", 10, 3, "count"),
    ]
    
    for loan in loans:
        if not loan.get("is_sll", False):
            continue
        
        for kpi_name, kpi_type, baseline, target, unit in random.sample(esg_definitions, k=random.randint(2, 4)):
            progress = random.uniform(0.3, 1.1)
            if baseline > target:
                current = baseline - (baseline - target) * progress
            else:
                current = baseline + (target - baseline) * progress
            
            kpi = {
                "kpi_id": f"KPI-{str(uuid.uuid4())[:8].upper()}",
                "loan_id": loan["loan_id"],
                "kpi_name": kpi_name,
                "kpi_type": kpi_type,
                "baseline_value": baseline,
                "target_value": target,
                "current_value": round(current, 2),
                "unit": unit,
                "target_date": (datetime.now() + timedelta(days=random.randint(180, 730))).strftime("%Y-%m-%d"),
                "measurement_date": datetime.now().strftime("%Y-%m-%d"),
                "verification_status": random.choice(["verified", "pending", "unverified"]),
                "verifier": random.choice(["Deloitte", "KPMG", "EY", None]),
                "greenwashing_risk_score": round(random.uniform(0.1, 0.7), 2),
                "margin_adjustment_bps": random.choice([2.5, 5.0, 7.5, 10.0]),
                "created_at": datetime.now().isoformat(),
            }
            kpis.append(kpi)
    
    return kpis


def upload_to_bigquery(data: List[Dict], table_name: str, client: bigquery.Client) -> None:
    """Upload data to BigQuery table."""
    table_id = f"{client.project}.{settings.BIGQUERY_DATASET_ID}.{table_name}"
    
    errors = client.insert_rows_json(table_id, data)
    if errors:
        print(f"❌ Errors inserting into {table_name}: {errors[:3]}")
    else:
        print(f"✅ Inserted {len(data)} rows into {table_name}")


def main():
    """Main entry point."""
    print("🔧 Generating synthetic data for LoanGuard AI...")
    print("")
    
    project_id = settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT not set")
        sys.exit(1)
    
    client = bigquery.Client(project=project_id)
    
    print(f"📊 Generating {NUM_LOANS} loans...")
    loans = generate_loans()
    
    print("📝 Generating covenants...")
    covenants = generate_covenants(loans)
    
    print("📈 Generating measurements...")
    measurements = generate_measurements(covenants)
    
    print("🌿 Generating ESG KPIs...")
    esg_kpis = generate_esg_kpis(loans)
    
    print("")
    print("📤 Uploading to BigQuery...")
    
    upload_to_bigquery(loans, "loans", client)
    upload_to_bigquery(covenants, "covenants", client)
    upload_to_bigquery(measurements, "covenant_measurements", client)
    upload_to_bigquery(esg_kpis, "esg_kpis", client)
    
    print("")
    print("✅ Synthetic data generation complete!")
    print(f"   • Loans: {len(loans)}")
    print(f"   • Covenants: {len(covenants)}")
    print(f"   • Measurements: {len(measurements)}")
    print(f"   • ESG KPIs: {len(esg_kpis)}")


if __name__ == "__main__":
    main()
