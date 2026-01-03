"""
Covenant parsing tools for extracting covenant definitions from loan documents.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Common financial covenant patterns
FINANCIAL_COVENANT_PATTERNS = {
    "debt_to_ebitda": [
        r"(?:total\s+)?debt[/-]to[/-]ebitda",
        r"leverage\s+ratio",
        r"net\s+debt[/-]ebitda",
    ],
    "interest_coverage": [
        r"interest\s+coverage\s+ratio",
        r"ebitda[/-]to[/-]interest",
        r"fixed\s+charge\s+coverage",
    ],
    "current_ratio": [
        r"current\s+ratio",
        r"current\s+assets[/-]to[/-]current\s+liabilities",
    ],
    "net_worth": [
        r"minimum\s+(?:tangible\s+)?net\s+worth",
        r"shareholders['']?\s+equity",
    ],
    "capex": [
        r"capital\s+expenditure",
        r"capex\s+limit",
        r"maximum\s+capital\s+expenditure",
    ],
}

# ESG/Sustainability covenant patterns
ESG_COVENANT_PATTERNS = {
    "carbon_reduction": [
        r"carbon\s+(?:emission|dioxide|reduction)",
        r"ghg\s+(?:emission|reduction)",
        r"scope\s+[123]\s+emission",
    ],
    "renewable_energy": [
        r"renewable\s+energy",
        r"clean\s+energy\s+(?:percentage|ratio)",
    ],
    "board_diversity": [
        r"board\s+diversity",
        r"gender\s+(?:diversity|representation)",
        r"(?:female|women)\s+(?:board\s+)?representation",
    ],
    "sustainability_rating": [
        r"esg\s+rating",
        r"sustainability\s+(?:score|rating)",
        r"msci\s+esg",
        r"sustainalytics",
    ],
    "green_investment": [
        r"green\s+(?:investment|project|asset)",
        r"sustainable\s+(?:investment|finance)",
    ],
}


def extract_financial_covenants(
    document_text: str,
    include_context: bool = True,
) -> Dict[str, Any]:
    """
    Extract financial covenants from document text.

    Args:
        document_text: Full text of the loan document
        include_context: Whether to include surrounding context

    Returns:
        Dictionary with extracted financial covenants
    """
    covenants = []
    text_lower = document_text.lower()

    for covenant_type, patterns in FINANCIAL_COVENANT_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                covenant_info = _extract_covenant_details(
                    document_text,
                    match,
                    covenant_type,
                    "financial",
                    include_context,
                )
                if covenant_info and not _is_duplicate(covenants, covenant_info):
                    covenants.append(covenant_info)

    logger.info(f"Extracted {len(covenants)} financial covenants")
    
    return {
        "success": True,
        "covenant_type": "financial",
        "count": len(covenants),
        "covenants": covenants,
    }


def extract_esg_covenants(
    document_text: str,
    include_context: bool = True,
) -> Dict[str, Any]:
    """
    Extract ESG/Sustainability covenants from document text.

    Args:
        document_text: Full text of the loan document
        include_context: Whether to include surrounding context

    Returns:
        Dictionary with extracted ESG covenants
    """
    covenants = []
    text_lower = document_text.lower()

    for covenant_type, patterns in ESG_COVENANT_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                covenant_info = _extract_covenant_details(
                    document_text,
                    match,
                    covenant_type,
                    "esg",
                    include_context,
                )
                if covenant_info and not _is_duplicate(covenants, covenant_info):
                    covenants.append(covenant_info)

    logger.info(f"Extracted {len(covenants)} ESG covenants")
    
    return {
        "success": True,
        "covenant_type": "esg",
        "count": len(covenants),
        "covenants": covenants,
    }


def classify_covenant_type(covenant_text: str) -> Dict[str, Any]:
    """
    Classify a covenant based on its text.

    Args:
        covenant_text: Text of the covenant clause

    Returns:
        Classification result with type and confidence
    """
    text_lower = covenant_text.lower()
    
    classifications = []

    # Check financial patterns
    for covenant_type, patterns in FINANCIAL_COVENANT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                classifications.append({
                    "type": covenant_type,
                    "category": "financial",
                    "confidence": 0.85,
                })
                break

    # Check ESG patterns
    for covenant_type, patterns in ESG_COVENANT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                classifications.append({
                    "type": covenant_type,
                    "category": "esg",
                    "confidence": 0.85,
                })
                break

    # Check for affirmative covenants
    affirmative_keywords = [
        "shall maintain", "shall provide", "shall deliver",
        "shall notify", "shall permit", "shall preserve",
    ]
    for keyword in affirmative_keywords:
        if keyword in text_lower:
            classifications.append({
                "type": "affirmative",
                "category": "operational",
                "confidence": 0.75,
            })
            break

    # Check for negative covenants
    negative_keywords = [
        "shall not", "will not", "may not", "prohibited from",
        "restriction on", "limitation on",
    ]
    for keyword in negative_keywords:
        if keyword in text_lower:
            classifications.append({
                "type": "negative",
                "category": "restrictive",
                "confidence": 0.75,
            })
            break

    if not classifications:
        classifications.append({
            "type": "unknown",
            "category": "other",
            "confidence": 0.5,
        })

    # Return highest confidence classification
    classifications.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "success": True,
        "primary_classification": classifications[0],
        "all_classifications": classifications,
    }


def _extract_covenant_details(
    full_text: str,
    match: re.Match,
    covenant_type: str,
    category: str,
    include_context: bool,
) -> Optional[Dict[str, Any]]:
    """Extract detailed covenant information from a regex match."""
    try:
        start_pos = match.start()
        end_pos = match.end()
        
        # Get surrounding context (sentence or paragraph)
        context_start = max(0, start_pos - 200)
        context_end = min(len(full_text), end_pos + 300)
        
        # Find sentence boundaries
        context = full_text[context_start:context_end]
        
        # Try to extract threshold value
        threshold_info = _extract_threshold(full_text[start_pos:context_end])
        
        # Try to extract measurement frequency
        frequency = _extract_frequency(context)
        
        covenant_info = {
            "covenant_name": covenant_type.replace("_", " ").title(),
            "covenant_type": category,
            "matched_text": match.group(0),
            "position": start_pos,
        }
        
        if include_context:
            covenant_info["context"] = context.strip()
        
        if threshold_info:
            covenant_info.update(threshold_info)
        
        if frequency:
            covenant_info["measurement_frequency"] = frequency
        
        return covenant_info
        
    except Exception as e:
        logger.error(f"Error extracting covenant details: {e}")
        return None


def _extract_threshold(text: str) -> Optional[Dict[str, Any]]:
    """Extract threshold value and operator from covenant text."""
    # Patterns for numeric thresholds
    threshold_patterns = [
        r"(?:not\s+)?(?:greater|less)\s+than\s+(\d+(?:\.\d+)?)",
        r"(?:not\s+)?(?:exceed|below)\s+(\d+(?:\.\d+)?)",
        r"(?:at\s+least|minimum\s+of)\s+(\d+(?:\.\d+)?)",
        r"(?:no\s+more\s+than|maximum\s+of)\s+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?::|to)\s*1",  # Ratio format
        r"(\d+(?:\.\d+)?)\s*[x×X]",  # Multiplier format
        r"(\d+(?:\.\d+)?)\s*%",  # Percentage
    ]
    
    for pattern in threshold_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            
            # Determine operator
            operator = "="
            full_match = match.group(0).lower()
            if "greater" in full_match or "exceed" in full_match or "at least" in full_match:
                operator = ">="
            elif "less" in full_match or "below" in full_match or "no more" in full_match:
                operator = "<="
            
            return {
                "threshold_value": value,
                "threshold_operator": operator,
                "threshold_text": match.group(0),
            }
    
    return None


def _extract_frequency(text: str) -> Optional[str]:
    """Extract measurement frequency from covenant text."""
    frequency_patterns = {
        "quarterly": r"quarter(?:ly)?|every\s+(?:three|3)\s+months",
        "semi-annual": r"semi[- ]?annual|every\s+(?:six|6)\s+months|twice\s+(?:a|per)\s+year",
        "annual": r"annual(?:ly)?|every\s+(?:twelve|12)\s+months|once\s+(?:a|per)\s+year",
        "monthly": r"month(?:ly)?|every\s+month",
    }
    
    text_lower = text.lower()
    for frequency, pattern in frequency_patterns.items():
        if re.search(pattern, text_lower):
            return frequency
    
    return None


def _is_duplicate(
    existing_covenants: List[Dict],
    new_covenant: Dict,
) -> bool:
    """Check if a covenant is a duplicate."""
    for existing in existing_covenants:
        # Check if same type and similar position
        if existing["covenant_name"] == new_covenant["covenant_name"]:
            pos_diff = abs(existing["position"] - new_covenant["position"])
            if pos_diff < 100:  # Within 100 characters
                return True
    return False
