"""
ESG Materiality Data - Sector-Based Material ESG Issues.

TNFD/GRI aligned mappings for determining material ESG issues by sector.
Used for ESG-as-Financial-Risk assessment per EBA 2026 regulations.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ESGPillar(Enum):
    """ESG pillar categories."""
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"


class RiskSeverity(Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MaterialIssue:
    """A material ESG issue for a sector."""
    issue_id: str
    name: str
    pillar: ESGPillar
    description: str
    risk_weight: float  # 0.0 - 1.0
    regulatory_reference: str  # TNFD, GRI, SASB etc.


@dataclass
class SectorMateriality:
    """Material ESG issues for a specific sector."""
    sector_id: str
    sector_name: str
    material_issues: List[MaterialIssue]
    transition_risk_exposure: float  # 0.0 - 1.0
    physical_risk_exposure: float    # 0.0 - 1.0


# Sector-based material ESG issues (TNFD/GRI aligned)
SECTOR_MATERIALITY_MAP: Dict[str, SectorMateriality] = {
    # Energy Sector - High transition risk
    "energy": SectorMateriality(
        sector_id="energy",
        sector_name="Energy (Oil & Gas)",
        transition_risk_exposure=0.95,
        physical_risk_exposure=0.60,
        material_issues=[
            MaterialIssue(
                issue_id="ghg_emissions",
                name="GHG Emissions (Scope 1, 2, 3)",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Direct and indirect greenhouse gas emissions from operations",
                risk_weight=0.95,
                regulatory_reference="TNFD, GRI 11"
            ),
            MaterialIssue(
                issue_id="climate_transition",
                name="Climate Transition Planning",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Net-zero transition strategy and decarbonization pathway",
                risk_weight=0.90,
                regulatory_reference="TCFD, TNFD"
            ),
            MaterialIssue(
                issue_id="stranded_assets",
                name="Stranded Asset Risk",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Risk of assets losing value due to energy transition",
                risk_weight=0.85,
                regulatory_reference="NGFS"
            ),
            MaterialIssue(
                issue_id="worker_safety",
                name="Occupational Health & Safety",
                pillar=ESGPillar.SOCIAL,
                description="Worker safety in hazardous operations",
                risk_weight=0.70,
                regulatory_reference="GRI 403"
            ),
        ]
    ),
    
    # Real Estate Sector - High physical risk
    "real_estate": SectorMateriality(
        sector_id="real_estate",
        sector_name="Real Estate & Construction",
        transition_risk_exposure=0.60,
        physical_risk_exposure=0.85,
        material_issues=[
            MaterialIssue(
                issue_id="building_emissions",
                name="Building Energy Efficiency",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Energy consumption and emissions from buildings",
                risk_weight=0.80,
                regulatory_reference="TNFD"
            ),
            MaterialIssue(
                issue_id="flood_risk",
                name="Physical Climate Risk (Flooding)",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Exposure to flood risk from sea level rise and extreme weather",
                risk_weight=0.85,
                regulatory_reference="NGFS"
            ),
            MaterialIssue(
                issue_id="green_buildings",
                name="Green Building Certification",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="LEED, BREEAM, or equivalent certification status",
                risk_weight=0.65,
                regulatory_reference="GRI"
            ),
        ]
    ),
    
    # Technology Sector - Lower transition risk
    "technology": SectorMateriality(
        sector_id="technology",
        sector_name="Technology & Software",
        transition_risk_exposure=0.30,
        physical_risk_exposure=0.20,
        material_issues=[
            MaterialIssue(
                issue_id="data_privacy",
                name="Data Privacy & Security",
                pillar=ESGPillar.GOVERNANCE,
                description="Protection of customer and employee data",
                risk_weight=0.85,
                regulatory_reference="GRI 418"
            ),
            MaterialIssue(
                issue_id="energy_consumption",
                name="Data Center Energy",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Energy consumption of data centers and cloud operations",
                risk_weight=0.60,
                regulatory_reference="TNFD"
            ),
            MaterialIssue(
                issue_id="supply_chain",
                name="Supply Chain Labor Practices",
                pillar=ESGPillar.SOCIAL,
                description="Labor conditions in hardware manufacturing supply chain",
                risk_weight=0.70,
                regulatory_reference="GRI 414"
            ),
        ]
    ),
    
    # Healthcare Sector
    "healthcare": SectorMateriality(
        sector_id="healthcare",
        sector_name="Healthcare & Pharmaceuticals",
        transition_risk_exposure=0.35,
        physical_risk_exposure=0.40,
        material_issues=[
            MaterialIssue(
                issue_id="product_safety",
                name="Product Safety & Quality",
                pillar=ESGPillar.SOCIAL,
                description="Drug safety, clinical trial ethics, product recalls",
                risk_weight=0.90,
                regulatory_reference="GRI 416"
            ),
            MaterialIssue(
                issue_id="access_to_medicine",
                name="Access to Medicine",
                pillar=ESGPillar.SOCIAL,
                description="Affordable access to essential medicines globally",
                risk_weight=0.75,
                regulatory_reference="SASB"
            ),
            MaterialIssue(
                issue_id="waste_management",
                name="Hazardous Waste Management",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Pharmaceutical and medical waste disposal",
                risk_weight=0.65,
                regulatory_reference="GRI 306"
            ),
        ]
    ),
    
    # Manufacturing Sector
    "manufacturing": SectorMateriality(
        sector_id="manufacturing",
        sector_name="Manufacturing & Industrial",
        transition_risk_exposure=0.70,
        physical_risk_exposure=0.55,
        material_issues=[
            MaterialIssue(
                issue_id="industrial_emissions",
                name="Industrial Emissions",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Air, water, and soil pollution from manufacturing",
                risk_weight=0.85,
                regulatory_reference="GRI 305"
            ),
            MaterialIssue(
                issue_id="resource_efficiency",
                name="Resource Efficiency",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Raw material usage and circular economy practices",
                risk_weight=0.70,
                regulatory_reference="TNFD"
            ),
            MaterialIssue(
                issue_id="worker_safety",
                name="Occupational Health & Safety",
                pillar=ESGPillar.SOCIAL,
                description="Factory worker health and safety conditions",
                risk_weight=0.75,
                regulatory_reference="GRI 403"
            ),
        ]
    ),
    
    # Financial Services
    "financial_services": SectorMateriality(
        sector_id="financial_services",
        sector_name="Financial Services & Banking",
        transition_risk_exposure=0.55,  # Indirect via portfolio
        physical_risk_exposure=0.40,
        material_issues=[
            MaterialIssue(
                issue_id="financed_emissions",
                name="Financed Emissions (Scope 3)",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="GHG emissions from lending and investment portfolio",
                risk_weight=0.85,
                regulatory_reference="PCAF"
            ),
            MaterialIssue(
                issue_id="sustainable_finance",
                name="Sustainable Finance Products",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Green loans, sustainability-linked loans, ESG funds",
                risk_weight=0.70,
                regulatory_reference="EU Taxonomy"
            ),
            MaterialIssue(
                issue_id="aml_compliance",
                name="Anti-Money Laundering",
                pillar=ESGPillar.GOVERNANCE,
                description="AML/KYC compliance and financial crime prevention",
                risk_weight=0.90,
                regulatory_reference="FATF"
            ),
        ]
    ),
    
    # Retail Sector
    "retail": SectorMateriality(
        sector_id="retail",
        sector_name="Retail & Consumer Goods",
        transition_risk_exposure=0.45,
        physical_risk_exposure=0.50,
        material_issues=[
            MaterialIssue(
                issue_id="supply_chain_sustainability",
                name="Sustainable Supply Chain",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Environmental impact of global supply chains",
                risk_weight=0.80,
                regulatory_reference="GRI 308"
            ),
            MaterialIssue(
                issue_id="labor_practices",
                name="Supply Chain Labor Practices",
                pillar=ESGPillar.SOCIAL,
                description="Fair labor conditions in manufacturing",
                risk_weight=0.75,
                regulatory_reference="GRI 414"
            ),
            MaterialIssue(
                issue_id="packaging_waste",
                name="Packaging & Plastic Waste",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Single-use plastics and packaging sustainability",
                risk_weight=0.65,
                regulatory_reference="TNFD"
            ),
        ]
    ),
    
    # Agriculture Sector
    "agriculture": SectorMateriality(
        sector_id="agriculture",
        sector_name="Agriculture & Food",
        transition_risk_exposure=0.50,
        physical_risk_exposure=0.90,  # High physical risk
        material_issues=[
            MaterialIssue(
                issue_id="land_use",
                name="Land Use & Biodiversity",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Deforestation, land degradation, biodiversity loss",
                risk_weight=0.90,
                regulatory_reference="TNFD, GRI 13"
            ),
            MaterialIssue(
                issue_id="water_management",
                name="Water Management",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Water scarcity, irrigation, water quality",
                risk_weight=0.85,
                regulatory_reference="GRI 303"
            ),
            MaterialIssue(
                issue_id="climate_resilience",
                name="Climate Resilience",
                pillar=ESGPillar.ENVIRONMENTAL,
                description="Crop vulnerability to extreme weather and temperature changes",
                risk_weight=0.85,
                regulatory_reference="NGFS"
            ),
        ]
    ),
}


def get_sector_materiality(sector: str) -> SectorMateriality | None:
    """
    Get material ESG issues for a sector.
    
    Args:
        sector: Sector identifier (lowercase, underscored)
        
    Returns:
        SectorMateriality object or None if sector not found
    """
    # Normalize sector name
    sector_key = sector.lower().replace(" ", "_").replace("-", "_")
    
    # Try direct match
    if sector_key in SECTOR_MATERIALITY_MAP:
        return SECTOR_MATERIALITY_MAP[sector_key]
    
    # Try partial match
    for key, value in SECTOR_MATERIALITY_MAP.items():
        if key in sector_key or sector_key in key:
            return value
    
    # Default to manufacturing if unknown
    return SECTOR_MATERIALITY_MAP.get("manufacturing")


def get_all_sectors() -> List[str]:
    """Get list of all supported sectors."""
    return list(SECTOR_MATERIALITY_MAP.keys())


def calculate_sector_esg_risk_score(sector: str) -> Dict[str, Any]:
    """
    Calculate composite ESG risk score for a sector.
    
    Returns:
        Dict with composite score and breakdown
    """
    materiality = get_sector_materiality(sector)
    if not materiality:
        return {"error": f"Unknown sector: {sector}"}
    
    # Calculate pillar scores
    env_issues = [i for i in materiality.material_issues if i.pillar == ESGPillar.ENVIRONMENTAL]
    soc_issues = [i for i in materiality.material_issues if i.pillar == ESGPillar.SOCIAL]
    gov_issues = [i for i in materiality.material_issues if i.pillar == ESGPillar.GOVERNANCE]
    
    env_score = sum(i.risk_weight for i in env_issues) / len(env_issues) if env_issues else 0
    soc_score = sum(i.risk_weight for i in soc_issues) / len(soc_issues) if soc_issues else 0
    gov_score = sum(i.risk_weight for i in gov_issues) / len(gov_issues) if gov_issues else 0
    
    # Composite with weighting (40% E, 30% S, 30% G)
    composite = (env_score * 0.4) + (soc_score * 0.3) + (gov_score * 0.3)
    
    return {
        "sector": materiality.sector_name,
        "composite_risk_score": round(composite, 3),
        "environmental_score": round(env_score, 3),
        "social_score": round(soc_score, 3),
        "governance_score": round(gov_score, 3),
        "transition_risk_exposure": materiality.transition_risk_exposure,
        "physical_risk_exposure": materiality.physical_risk_exposure,
        "material_issues_count": len(materiality.material_issues),
    }


# Climate scenario impacts (NGFS aligned)
CLIMATE_SCENARIO_IMPACTS = {
    "net_zero_2050": {
        "name": "Net Zero 2050 (Orderly)",
        "transition_risk_multiplier": 1.2,
        "physical_risk_multiplier": 1.0,
        "description": "Orderly transition with stringent climate policies"
    },
    "delayed_transition": {
        "name": "Delayed Transition (Disorderly)",
        "transition_risk_multiplier": 1.8,
        "physical_risk_multiplier": 1.2,
        "description": "Late, disorderly transition with sudden policy changes"
    },
    "current_policies": {
        "name": "Current Policies (Hot House)",
        "transition_risk_multiplier": 1.0,
        "physical_risk_multiplier": 2.0,
        "description": "No additional policies, high physical risk"
    },
    "fragmented_world": {
        "name": "Fragmented World",
        "transition_risk_multiplier": 1.5,
        "physical_risk_multiplier": 1.5,
        "description": "Uneven global response to climate change"
    }
}


def get_climate_scenario_impact(
    sector: str, 
    scenario_id: str
) -> Dict[str, Any]:
    """
    Get climate scenario impact for a sector.
    
    Args:
        sector: Sector identifier
        scenario_id: Climate scenario ID from CLIMATE_SCENARIO_IMPACTS
        
    Returns:
        Dict with adjusted risk exposure under scenario
    """
    materiality = get_sector_materiality(sector)
    scenario = CLIMATE_SCENARIO_IMPACTS.get(scenario_id)
    
    if not materiality or not scenario:
        return {"error": "Invalid sector or scenario"}
    
    adjusted_transition = min(1.0, materiality.transition_risk_exposure * scenario["transition_risk_multiplier"])
    adjusted_physical = min(1.0, materiality.physical_risk_exposure * scenario["physical_risk_multiplier"])
    
    # Combined climate risk (weighted average)
    combined_climate_risk = (adjusted_transition * 0.5) + (adjusted_physical * 0.5)
    
    return {
        "sector": materiality.sector_name,
        "scenario": scenario["name"],
        "scenario_description": scenario["description"],
        "base_transition_risk": materiality.transition_risk_exposure,
        "base_physical_risk": materiality.physical_risk_exposure,
        "adjusted_transition_risk": round(adjusted_transition, 3),
        "adjusted_physical_risk": round(adjusted_physical, 3),
        "combined_climate_risk": round(combined_climate_risk, 3),
    }
