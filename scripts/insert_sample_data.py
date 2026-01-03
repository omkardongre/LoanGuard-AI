"""
Insert Sample Data into BigQuery for LoanGuard AI Demo.

This script creates realistic sample data for:
- 50 loans (mix of healthy, warning, and breach states)
- 150 covenants (3 per loan)
- 600 measurements (4 quarters per covenant)
- 50 ESG KPIs
- Sample alerts
- Sample ESG claims (for greenwashing detection)

Run: python scripts/insert_sample_data.py
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "loanguard-ai-hackathon")
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "loanguard_data")

# Sample data generators
COMPANY_NAMES = [
    "Acme Corporation", "TechFlow Industries", "GreenEnergy Solutions",
    "Metro Manufacturing", "Pacific Logistics", "Alpine Resources",
    "Coastal Shipping", "Summit Healthcare", "Valley Agritech",
    "Horizon Retail", "Pinnacle Construction", "Atlas Mining",
    "Quantum Computing", "Sterling Pharma", "Omega Aerospace",
    "Delta Automotive", "Phoenix Materials", "Zenith Telecom",
    "Titan Heavy Industries", "Nebula Software", "Crimson Foods",
    "Azure Hospitality", "Golden Financial", "Silver Media",
    "Bronze Trading", "Platinum Energy", "Diamond Tech",
    "Ruby Logistics", "Sapphire Health", "Emerald Agri",
    "Topaz Manufacturing", "Opal Services", "Jade Electronics",
    "Pearl Retail", "Amber Construction", "Coral Maritime",
    "Onyx Mining", "Garnet Pharma", "Quartz Telecom",
    "Citrine Foods", "Peridot Software", "Aquamarine Transport",
    "Turquoise Energy", "Lapis Tech", "Malachite Industries",
    "Obsidian Holdings", "Jasper Capital", "Moonstone Media",
    "Sunstone Retail", "Starlight Ventures"
]

INDUSTRIES = [
    "Technology", "Manufacturing", "Healthcare", "Energy", "Retail",
    "Transportation", "Financial Services", "Real Estate", "Agriculture",
    "Construction", "Mining", "Pharmaceuticals", "Telecommunications"
]

LOAN_TYPES = ["Term Loan", "Revolving Credit", "Bridge Loan", "Syndicated Loan"]
BANKS = ["JPMorgan Chase", "Bank of America", "Citibank", "Wells Fargo", "Goldman Sachs"]


def generate_loan_id() -> str:
    """Generate unique loan ID."""
    return f"LOAN-{uuid.uuid4().hex[:8].upper()}"


def generate_covenant_id() -> str:
    """Generate unique covenant ID."""
    return f"COV-{uuid.uuid4().hex[:8].upper()}"


def generate_loans(count: int = 50) -> List[Dict[str, Any]]:
    """Generate sample loan records."""
    loans = []
    statuses = ["GREEN"] * 35 + ["AMBER"] * 10 + ["RED"] * 5  # 70% green, 20% amber, 10% red
    random.shuffle(statuses)
    
    for i in range(count):
        loan_id = generate_loan_id()
        is_sll = random.random() < 0.3  # 30% are sustainability-linked
        
        loans.append({
            "loan_id": loan_id,
            "borrower_name": COMPANY_NAMES[i % len(COMPANY_NAMES)],
            "borrower_industry": random.choice(INDUSTRIES),
            "facility_amount": random.randint(10, 500) * 1_000_000,
            "currency": "USD",
            "maturity_date": (datetime.now() + timedelta(days=random.randint(365, 1825))).strftime("%Y-%m-%d"),
            "loan_type": random.choice(LOAN_TYPES),
            "is_sll": is_sll,
            "agent_bank": random.choice(BANKS),
            "status": statuses[i],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })
    
    return loans


def generate_covenants(loans: List[Dict]) -> List[Dict[str, Any]]:
    """Generate covenant definitions for each loan."""
    covenant_types = [
        {"name": "Debt/EBITDA", "type": "debt_to_ebitda", "threshold": 4.0, "threshold_type": "max"},
        {"name": "Interest Coverage", "type": "interest_coverage", "threshold": 2.5, "threshold_type": "min"},
        {"name": "Current Ratio", "type": "current_ratio", "threshold": 1.2, "threshold_type": "min"},
        {"name": "Net Worth", "type": "net_worth", "threshold": 50_000_000, "threshold_type": "min"},
        {"name": "Fixed Charge Coverage", "type": "fixed_charge_coverage", "threshold": 1.25, "threshold_type": "min"},
    ]
    
    covenants = []
    
    for loan in loans:
        # Each loan gets 3 random covenants
        selected = random.sample(covenant_types, 3)
        
        for cov_type in selected:
            # Vary thresholds slightly
            threshold = cov_type["threshold"] * random.uniform(0.9, 1.1)
            
            covenants.append({
                "covenant_id": generate_covenant_id(),
                "loan_id": loan["loan_id"],
                "covenant_name": cov_type["name"],
                "covenant_type": cov_type["type"],
                "threshold": round(threshold, 2),
                "threshold_type": cov_type["threshold_type"],
                "frequency": "quarterly",
                "grace_period_days": 30,
                "cure_period_days": 30,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            })
    
    return covenants


def generate_measurements(covenants: List[Dict], loans: List[Dict]) -> List[Dict[str, Any]]:
    """Generate historical measurements for each covenant."""
    measurements = []
    
    # Create loan status lookup
    loan_status = {loan["loan_id"]: loan["status"] for loan in loans}
    
    for covenant in covenants:
        loan_id = covenant["loan_id"]
        status = loan_status.get(loan_id, "GREEN")
        threshold = covenant["threshold"]
        is_max = covenant["threshold_type"] == "max"
        
        # Generate 4 quarters of history
        for q in range(4):
            period_date = datetime.now() - timedelta(days=90 * (3 - q))
            
            # Generate realistic values based on loan status
            if status == "GREEN":
                # Healthy - good buffer from threshold
                if is_max:
                    actual = threshold * random.uniform(0.7, 0.9)
                else:
                    actual = threshold * random.uniform(1.2, 1.5)
                meas_status = "GREEN"
                buffer = abs(threshold - actual) / threshold * 100
                
            elif status == "AMBER":
                # Warning - close to threshold
                if is_max:
                    actual = threshold * random.uniform(0.85, 0.98)
                else:
                    actual = threshold * random.uniform(1.02, 1.15)
                meas_status = "AMBER"
                buffer = abs(threshold - actual) / threshold * 100
                
            else:  # RED
                # Breach - exceeded threshold
                if is_max:
                    actual = threshold * random.uniform(1.02, 1.2)
                else:
                    actual = threshold * random.uniform(0.8, 0.98)
                meas_status = "RED"
                buffer = -abs(threshold - actual) / threshold * 100
            
            measurements.append({
                "measurement_id": f"MEAS-{uuid.uuid4().hex[:8].upper()}",
                "covenant_id": covenant["covenant_id"],
                "loan_id": loan_id,
                "period_date": period_date.strftime("%Y-%m-%d"),
                "actual_value": round(actual, 2),
                "threshold": threshold,
                "status": meas_status,
                "buffer_percent": round(buffer, 2),
                "created_at": datetime.now().isoformat(),
            })
    
    return measurements


def generate_esg_kpis(loans: List[Dict]) -> List[Dict[str, Any]]:
    """Generate ESG KPIs for SLL loans."""
    kpi_types = [
        {"name": "Carbon Emissions (tCO2e)", "category": "environmental", "reduction": True},
        {"name": "Renewable Energy %", "category": "environmental", "reduction": False},
        {"name": "Water Usage (m³)", "category": "environmental", "reduction": True},
        {"name": "Waste Recycled %", "category": "environmental", "reduction": False},
        {"name": "Gender Diversity %", "category": "social", "reduction": False},
        {"name": "Lost Time Injury Rate", "category": "social", "reduction": True},
    ]
    
    kpis = []
    
    for loan in loans:
        if not loan.get("is_sll"):
            continue
        
        # Each SLL loan gets 2-3 KPIs
        selected = random.sample(kpi_types, random.randint(2, 3))
        
        for kpi_type in selected:
            if kpi_type["reduction"]:
                baseline = random.uniform(10000, 100000)
                target = baseline * random.uniform(0.5, 0.8)
                current = baseline * random.uniform(0.6, 0.95)
            else:
                baseline = random.uniform(10, 40)
                target = random.uniform(50, 80)
                current = random.uniform(baseline, target * 1.1)
            
            kpis.append({
                "kpi_id": f"KPI-{uuid.uuid4().hex[:8].upper()}",
                "loan_id": loan["loan_id"],
                "kpi_name": kpi_type["name"],
                "kpi_category": kpi_type["category"],
                "baseline_value": round(baseline, 2),
                "target_value": round(target, 2),
                "current_value": round(current, 2),
                "target_date": (datetime.now() + timedelta(days=random.randint(180, 730))).strftime("%Y-%m-%d"),
                "measurement_date": datetime.now().strftime("%Y-%m-%d"),
                "verification_status": random.choice(["VERIFIED", "PENDING", "PENDING"]),
                "verifier": random.choice(["EY", "Deloitte", "KPMG", None, None]),
                "created_at": datetime.now().isoformat(),
            })
    
    return kpis


def generate_esg_claims(loans: List[Dict]) -> List[Dict[str, Any]]:
    """Generate ESG claims for greenwashing detection demo."""
    claim_templates = [
        {"text": "Carbon neutral by 2030", "category": "emissions", "risk": "MEDIUM"},
        {"text": "100% renewable energy by 2028", "category": "energy", "risk": "LOW"},
        {"text": "Net zero emissions across all operations", "category": "emissions", "risk": "HIGH"},
        {"text": "Sustainable supply chain practices", "category": "supply_chain", "risk": "MEDIUM"},
        {"text": "Zero waste to landfill by 2025", "category": "waste", "risk": "MEDIUM"},
        {"text": "Climate-positive company", "category": "emissions", "risk": "HIGH"},
        {"text": "Eco-friendly manufacturing processes", "category": "operations", "risk": "MEDIUM"},
        {"text": "Science-based emissions targets certified by SBTi", "category": "emissions", "risk": "LOW"},
        {"text": "Water neutral operations", "category": "water", "risk": "HIGH"},
        {"text": "Committed to biodiversity protection", "category": "biodiversity", "risk": "MEDIUM"},
    ]
    
    claims = []
    
    for loan in loans:
        if not loan.get("is_sll"):
            continue
        
        # Each SLL loan has 1-3 ESG claims
        num_claims = random.randint(1, 3)
        selected = random.sample(claim_templates, num_claims)
        
        for claim in selected:
            risk = claim["risk"]
            if risk == "HIGH":
                score = random.uniform(0.2, 0.4)
                verdict = random.choice(["QUESTIONABLE", "UNVERIFIED", "CONTRADICTED"])
            elif risk == "MEDIUM":
                score = random.uniform(0.4, 0.7)
                verdict = random.choice(["QUESTIONABLE", "VERIFIED"])
            else:
                score = random.uniform(0.7, 0.95)
                verdict = "VERIFIED"
            
            claims.append({
                "claim_id": f"CLM-{uuid.uuid4().hex[:8].upper()}",
                "loan_id": loan["loan_id"],
                "borrower_name": loan["borrower_name"],
                "claim_text": claim["text"],
                "claim_category": claim["category"],
                "source_document": "Annual Sustainability Report 2024",
                "verification_score": round(score, 2),
                "verdict": verdict,
                "risk_level": risk,
                "contradictions_found": random.randint(0, 3) if risk == "HIGH" else 0,
                "analysis_date": datetime.now().isoformat(),
            })
    
    return claims


def generate_alerts(loans: List[Dict]) -> List[Dict[str, Any]]:
    """Generate sample alerts."""
    alerts = []
    
    for loan in loans:
        if loan["status"] == "AMBER":
            alerts.append({
                "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
                "loan_id": loan["loan_id"],
                "alert_type": "covenant_warning",
                "severity": "MEDIUM",
                "title": "Covenant Approaching Threshold",
                "message": f"{loan['borrower_name']}: Interest Coverage approaching threshold (buffer < 10%)",
                "is_acknowledged": False,
                "acknowledged_by": None,
                "acknowledged_at": None,
                "created_at": datetime.now().isoformat(),
            })
        
        elif loan["status"] == "RED":
            alerts.append({
                "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
                "loan_id": loan["loan_id"],
                "alert_type": "covenant_breach",
                "severity": "HIGH",
                "title": "Covenant Breach Detected",
                "message": f"{loan['borrower_name']}: Debt/EBITDA covenant breached. Cure period: 30 days.",
                "is_acknowledged": False,
                "acknowledged_by": None,
                "acknowledged_at": None,
                "created_at": datetime.now().isoformat(),
            })
    
    # Add some greenwashing alerts
    alerts.append({
        "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
        "loan_id": loans[0]["loan_id"] if loans else "LOAN-DEMO",
        "alert_type": "greenwashing_risk",
        "severity": "HIGH",
        "title": "Greenwashing Risk Detected",
        "message": "ESG claim 'Carbon neutral by 2030' contradicted by external news source",
        "is_acknowledged": False,
        "acknowledged_by": None,
        "acknowledged_at": None,
        "created_at": datetime.now().isoformat(),
    })
    
    return alerts


def insert_to_bigquery(client: bigquery.Client, table_name: str, rows: List[Dict]) -> int:
    """Insert rows into BigQuery table."""
    if not rows:
        print(f"  No rows to insert into {table_name}")
        return 0
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    errors = client.insert_rows_json(table_id, rows)
    
    if errors:
        print(f"  Errors inserting into {table_name}: {errors[:3]}")
        return 0
    
    print(f"  ✅ Inserted {len(rows)} rows into {table_name}")
    return len(rows)


def main():
    """Main function to generate and insert all sample data."""
    print("=" * 60)
    print("LoanGuard AI - Sample Data Generator")
    print("=" * 60)
    
    # Initialize BigQuery client
    print(f"\n📡 Connecting to BigQuery project: {PROJECT_ID}")
    client = bigquery.Client(project=PROJECT_ID)
    
    # Generate all data
    print("\n📝 Generating sample data...")
    
    loans = generate_loans(50)
    print(f"  Generated {len(loans)} loans")
    
    covenants = generate_covenants(loans)
    print(f"  Generated {len(covenants)} covenants")
    
    measurements = generate_measurements(covenants, loans)
    print(f"  Generated {len(measurements)} measurements")
    
    esg_kpis = generate_esg_kpis(loans)
    print(f"  Generated {len(esg_kpis)} ESG KPIs")
    
    esg_claims = generate_esg_claims(loans)
    print(f"  Generated {len(esg_claims)} ESG claims")
    
    alerts = generate_alerts(loans)
    print(f"  Generated {len(alerts)} alerts")
    
    # Insert data
    print("\n💾 Inserting data into BigQuery...")
    
    insert_to_bigquery(client, "loans", loans)
    insert_to_bigquery(client, "covenants", covenants)
    insert_to_bigquery(client, "covenant_measurements", measurements)
    insert_to_bigquery(client, "esg_kpis", esg_kpis)
    insert_to_bigquery(client, "esg_claims", esg_claims)
    insert_to_bigquery(client, "alerts", alerts)
    
    print("\n" + "=" * 60)
    print("✅ Sample data generation complete!")
    print("=" * 60)
    
    # Summary
    print("\nData Summary:")
    print(f"  - Loans: {len(loans)} (35 GREEN, 10 AMBER, 5 RED)")
    print(f"  - Covenants: {len(covenants)}")
    print(f"  - Measurements: {len(measurements)}")
    print(f"  - ESG KPIs: {len(esg_kpis)}")
    print(f"  - ESG Claims: {len(esg_claims)}")
    print(f"  - Alerts: {len(alerts)}")


if __name__ == "__main__":
    main()
