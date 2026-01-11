"""
SLL KPI Extractor Agent - Extract ESG KPIs from loan documents.

Production-level implementation for Sustainability-Linked Loan monitoring.
Uses Affinda for document parsing and Gemini for KPI extraction.
"""

import logging
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

import google.generativeai as genai
from common.config import settings
from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


@dataclass
class ExtractedSLLKPI:
    """Structured SLL KPI data extracted from documents."""
    kpi_type: str  # GHG, Water, Waste, Energy, Biodiversity, Social
    kpi_name: str
    baseline_value: Optional[float]
    target_value: Optional[float]
    unit: str
    target_year: Optional[int]
    measurement_frequency: str  # Annual, Semi-annual, Quarterly
    verification_required: bool
    raw_text: str


class SLLKPIExtractor:
    """
    Extract SLL KPIs from loan documents using Gemini AI.
    
    Follows LMA SLLP (Sustainability-Linked Loan Principles) guidelines:
    - Core Components: Selection of KPIs, SPT Calibration, Loan Characteristics,
      Reporting, Verification
    """
    
    # LMA-defined KPI categories
    KPI_CATEGORIES = [
        "GHG Emissions (Scope 1, 2, 3)",
        "Energy Efficiency",
        "Renewable Energy",
        "Water Consumption",
        "Waste Management",
        "Biodiversity",
        "Board Diversity",
        "Employee Safety (LTIR)",
        "ESG Ratings",
        "Sustainable Products",
        "Supply Chain ESG",
    ]
    
    EXTRACTION_PROMPT = """You are an expert in analyzing Sustainability-Linked Loan (SLL) documents.
    
Extract ALL Key Performance Indicators (KPIs) and Sustainability Performance Targets (SPTs) from this document.

For each KPI/SPT found, provide:
1. kpi_type: One of [GHG, Energy, Water, Waste, Biodiversity, Social, Governance, Sustainable_Products]
2. kpi_name: Descriptive name (e.g., "Scope 1 & 2 GHG Emissions Reduction")
3. baseline_value: The starting/reference value (numeric only, no units)
4. target_value: The target to achieve (numeric only, no units)
5. unit: Measurement unit (e.g., "tCO2e", "%", "MWh", "ML")
6. target_year: Year by which target should be achieved (e.g., 2030)
7. measurement_frequency: How often measured [Annual, Semi-annual, Quarterly]
8. verification_required: true/false - whether third-party verification is required
9. raw_text: The exact text from the document describing this KPI

Return as JSON array. If no KPIs found, return empty array [].

Example output:
[
  {{
    "kpi_type": "GHG",
    "kpi_name": "Scope 1 & 2 GHG Emissions Reduction",
    "baseline_value": 100000,
    "target_value": 70000,
    "unit": "tCO2e",
    "target_year": 2030,
    "measurement_frequency": "Annual",
    "verification_required": true,
    "raw_text": "The Borrower shall reduce Scope 1 and 2 emissions from 100,000 tCO2e to 70,000 tCO2e by 2030"
  }}
]

DOCUMENT TEXT:
{document_text}

Extract all KPIs and SPTs as JSON array:"""

    def __init__(self):
        """Initialize the SLL KPI Extractor."""
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.bq = BigQueryClient()
        
    def extract_kpis_from_text(self, document_text: str) -> List[ExtractedSLLKPI]:
        """
        Extract KPIs from document text using Gemini.
        
        Args:
            document_text: Raw text from loan document
            
        Returns:
            List of extracted KPIs
        """
        import re
        
        try:
            prompt = self.EXTRACTION_PROMPT.format(document_text=document_text[:50000])
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.info(f"Gemini response length: {len(response_text)}")
            
            # Multiple strategies to extract JSON array
            kpis_data = None
            
            # Strategy 1: Try markdown code block extraction FIRST (most common format)
            if "```json" in response_text:
                try:
                    json_block = response_text.split("```json")[1].split("```")[0].strip()
                    kpis_data = json.loads(json_block)
                    logger.info("Parsed JSON from ```json code block")
                except (IndexError, json.JSONDecodeError) as e:
                    logger.debug(f"Failed ```json extraction: {e}")
            
            if kpis_data is None and "```" in response_text:
                try:
                    json_block = response_text.split("```")[1].split("```")[0].strip()
                    kpis_data = json.loads(json_block)
                    logger.info("Parsed JSON from ``` code block")
                except (IndexError, json.JSONDecodeError) as e:
                    logger.debug(f"Failed ``` extraction: {e}")
            
            # Strategy 2: Try full response as JSON
            if kpis_data is None:
                try:
                    kpis_data = json.loads(response_text)
                    logger.info("Parsed entire response as JSON")
                except json.JSONDecodeError:
                    pass
            
            # Strategy 3: Find JSON array with bracket matching
            if kpis_data is None:
                # Find the [ and match to final ]
                start_idx = response_text.find('[')
                if start_idx >= 0:
                    # Find matching closing bracket
                    bracket_count = 0
                    end_idx = start_idx
                    for i, char in enumerate(response_text[start_idx:], start=start_idx):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_idx = i
                                break
                    if end_idx > start_idx:
                        try:
                            json_str = response_text[start_idx:end_idx + 1]
                            kpis_data = json.loads(json_str)
                            logger.info("Parsed JSON using bracket matching")
                        except json.JSONDecodeError as e:
                            logger.debug(f"Bracket matching failed: {e}")
            
            # Strategy 4: Empty array check
            if kpis_data is None:
                if "[]" in response_text:
                    kpis_data = []
                    logger.info("Found empty array")
            
            if kpis_data is None:
                logger.warning(f"Could not parse JSON from response: {response_text[:500]}")
                return []
            
            if not isinstance(kpis_data, list):
                logger.warning(f"Response is not a list: {type(kpis_data)}")
                return []
            
            # Convert to dataclass objects
            kpis = []
            for kpi in kpis_data:
                if not isinstance(kpi, dict):
                    continue
                extracted = ExtractedSLLKPI(
                    kpi_type=kpi.get("kpi_type", "Unknown"),
                    kpi_name=kpi.get("kpi_name", ""),
                    baseline_value=kpi.get("baseline_value"),
                    target_value=kpi.get("target_value"),
                    unit=kpi.get("unit", ""),
                    target_year=kpi.get("target_year"),
                    measurement_frequency=kpi.get("measurement_frequency", "Annual"),
                    verification_required=kpi.get("verification_required", True),
                    raw_text=kpi.get("raw_text", ""),
                )
                kpis.append(extracted)
            
            logger.info(f"Extracted {len(kpis)} KPIs from document")
            return kpis
            
        except Exception as e:
            logger.error(f"KPI extraction error: {e}")
            return []
    
    def save_kpis_to_bigquery(
        self, 
        loan_id: str, 
        kpis: List[ExtractedSLLKPI],
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save extracted KPIs to BigQuery.
        
        Args:
            loan_id: Loan identifier
            kpis: List of extracted KPIs
            document_id: Optional source document ID
            
        Returns:
            Result with saved KPI IDs
        """
        try:
            saved_ids = []
            
            for kpi in kpis:
                kpi_id = f"{loan_id}_{kpi.kpi_type.lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                insert_query = f"""
                    INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.sll_kpis`
                    (kpi_id, loan_id, kpi_type, kpi_name, baseline_value, target_value, 
                     unit, target_year, measurement_frequency, verification_required,
                     raw_text, source_document_id, created_at)
                    VALUES (
                        '{kpi_id}',
                        '{loan_id}',
                        '{kpi.kpi_type}',
                        '{kpi.kpi_name.replace("'", "''")}',
                        {kpi.baseline_value if kpi.baseline_value else 'NULL'},
                        {kpi.target_value if kpi.target_value else 'NULL'},
                        '{kpi.unit}',
                        {kpi.target_year if kpi.target_year else 'NULL'},
                        '{kpi.measurement_frequency}',
                        {str(kpi.verification_required).upper()},
                        '{kpi.raw_text[:500].replace("'", "''")}',
                        {f"'{document_id}'" if document_id else 'NULL'},
                        CURRENT_TIMESTAMP()
                    )
                """
                
                self.bq.execute_query(insert_query)
                saved_ids.append(kpi_id)
            
            return {
                "success": True,
                "loan_id": loan_id,
                "kpis_saved": len(saved_ids),
                "kpi_ids": saved_ids,
            }
            
        except Exception as e:
            logger.error(f"Failed to save KPIs to BigQuery: {e}")
            return {"success": False, "error": str(e)}
    
    def get_loan_sll_kpis(self, loan_id: str) -> Dict[str, Any]:
        """
        Get all SLL KPIs for a loan from BigQuery.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            Dictionary with loan KPI data
        """
        try:
            query = f"""
                SELECT 
                    kpi_id,
                    kpi_type,
                    kpi_name,
                    baseline_value,
                    target_value,
                    unit,
                    target_year,
                    measurement_frequency,
                    verification_required,
                    current_value,
                    achievement_probability,
                    last_measurement_date,
                    verification_status,
                    created_at
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sll_kpis`
                WHERE loan_id = '{loan_id}'
                ORDER BY created_at DESC
            """
            
            results = self.bq.execute_query(query)
            
            return {
                "success": True,
                "loan_id": loan_id,
                "kpi_count": len(results),
                "kpis": results,
            }
            
        except Exception as e:
            logger.error(f"Failed to get loan SLL KPIs: {e}")
            return {"success": False, "error": str(e), "kpis": []}


# Singleton instance
_sll_kpi_extractor: Optional[SLLKPIExtractor] = None


def get_sll_kpi_extractor() -> SLLKPIExtractor:
    """Get or create SLL KPI extractor singleton."""
    global _sll_kpi_extractor
    if _sll_kpi_extractor is None:
        _sll_kpi_extractor = SLLKPIExtractor()
    return _sll_kpi_extractor


def extract_sll_kpis_from_document(
    loan_id: str,
    document_text: str,
    document_id: Optional[str] = None,
    save_to_db: bool = True,
) -> Dict[str, Any]:
    """
    Extract SLL KPIs from document and optionally save to BigQuery.
    
    Args:
        loan_id: Loan identifier
        document_text: Raw document text
        document_id: Optional source document ID
        save_to_db: Whether to save to BigQuery
        
    Returns:
        Extraction result with KPIs
    """
    extractor = get_sll_kpi_extractor()
    
    # Extract KPIs
    kpis = extractor.extract_kpis_from_text(document_text)
    
    # Convert to dict for response
    kpis_dict = [
        {
            "kpi_type": kpi.kpi_type,
            "kpi_name": kpi.kpi_name,
            "baseline_value": kpi.baseline_value,
            "target_value": kpi.target_value,
            "unit": kpi.unit,
            "target_year": kpi.target_year,
            "measurement_frequency": kpi.measurement_frequency,
            "verification_required": kpi.verification_required,
            "raw_text": kpi.raw_text,
        }
        for kpi in kpis
    ]
    
    result = {
        "success": True,
        "loan_id": loan_id,
        "kpis_extracted": len(kpis),
        "kpis": kpis_dict,
        "source": "SLL KPI Extractor (Gemini)",
    }
    
    # Save to BigQuery if requested
    if save_to_db and kpis:
        save_result = extractor.save_kpis_to_bigquery(loan_id, kpis, document_id)
        result["saved_to_db"] = save_result.get("success", False)
        result["kpi_ids"] = save_result.get("kpi_ids", [])
    
    return result


def get_loan_sll_kpis(loan_id: str) -> Dict[str, Any]:
    """Get all SLL KPIs for a loan."""
    extractor = get_sll_kpi_extractor()
    return extractor.get_loan_sll_kpis(loan_id)
