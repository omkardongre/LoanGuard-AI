"""
Document validation tools for loan agreements.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Required sections in a standard loan agreement
REQUIRED_SECTIONS = [
    "definitions",
    "commitments",
    "conditions precedent",
    "representations and warranties",
    "affirmative covenants",
    "negative covenants",
    "financial covenants",
    "events of default",
    "agency provisions",
]

# Optional but common sections
OPTIONAL_SECTIONS = [
    "amendments and waivers",
    "assignments and participations",
    "yield protection",
    "miscellaneous",
    "schedules",
    "exhibits",
]


def validate_document_completeness(
    document_text: str,
    extracted_sections: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Validate that a loan document contains all required sections.

    Args:
        document_text: Full text of the document
        extracted_sections: Previously extracted section list

    Returns:
        Validation results with issues and completeness score
    """
    text_lower = document_text.lower()
    
    validation_result = {
        "success": True,
        "completeness_score": 0.0,
        "sections_found": [],
        "sections_missing": [],
        "issues": [],
    }

    # Check for required sections
    for section in REQUIRED_SECTIONS:
        section_patterns = [
            rf"\b{section}\b",
            rf"article\s+[ivxlcdm\d]+[:\.\s]+{section}",
            rf"section\s+\d+[:\.\s]+{section}",
        ]
        
        found = False
        for pattern in section_patterns:
            if re.search(pattern, text_lower):
                found = True
                break
        
        if found:
            validation_result["sections_found"].append(section)
        else:
            validation_result["sections_missing"].append(section)
            validation_result["issues"].append({
                "severity": "WARNING",
                "section": section,
                "message": f"Required section '{section.title()}' not found",
            })

    # Calculate completeness score
    total_required = len(REQUIRED_SECTIONS)
    found_count = len(validation_result["sections_found"])
    validation_result["completeness_score"] = round(found_count / total_required * 100, 1)

    # Add critical issues for key missing sections
    critical_sections = ["definitions", "financial covenants", "events of default"]
    for section in critical_sections:
        if section in validation_result["sections_missing"]:
            validation_result["issues"].append({
                "severity": "CRITICAL",
                "section": section,
                "message": f"Critical section '{section.title()}' is missing",
            })

    # Check for optional sections
    optional_found = []
    for section in OPTIONAL_SECTIONS:
        if section in text_lower:
            optional_found.append(section)
    
    validation_result["optional_sections_found"] = optional_found

    logger.info(
        f"Document completeness: {validation_result['completeness_score']}%, "
        f"{len(validation_result['issues'])} issues found"
    )

    return validation_result


def check_cross_references(
    document_text: str,
    extracted_sections: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Check cross-references in the document for consistency.

    Args:
        document_text: Full text of the document
        extracted_sections: Previously extracted section list

    Returns:
        Cross-reference validation results
    """
    results = {
        "success": True,
        "references_found": [],
        "broken_references": [],
        "issues": [],
    }

    # Find all cross-references
    ref_patterns = [
        r"(?:as\s+defined\s+in\s+)?[Ss]ection\s+(\d+(?:\.\d+)*)",
        r"[Aa]rticle\s+([IVXLCDM]+|\d+)",
        r"[Ss]chedule\s+([A-Z]|\d+)",
        r"[Ee]xhibit\s+([A-Z]|\d+)",
        r"(?:see|refer\s+to)\s+[\"']([^\"']+)[\"']",
    ]

    for pattern in ref_patterns:
        matches = re.finditer(pattern, document_text)
        for match in matches:
            ref_info = {
                "reference": match.group(0),
                "target": match.group(1),
                "position": match.start(),
            }
            results["references_found"].append(ref_info)

    # Validate references exist
    for ref in results["references_found"]:
        target = ref["target"]
        ref_type = ref["reference"].split()[0].lower()
        
        # Check if referenced section exists
        target_patterns = [
            rf"{ref_type}\s+{re.escape(target)}[:\.\s]",
            rf"^{target}\s+",
        ]
        
        found = False
        for pattern in target_patterns:
            if re.search(pattern, document_text, re.IGNORECASE | re.MULTILINE):
                found = True
                break
        
        if not found:
            results["broken_references"].append(ref)
            results["issues"].append({
                "severity": "WARNING",
                "reference": ref["reference"],
                "message": f"Cross-reference to '{ref['reference']}' may be broken",
            })

    logger.info(
        f"Found {len(results['references_found'])} cross-references, "
        f"{len(results['broken_references'])} potentially broken"
    )

    return results


def validate_covenant_definitions(
    covenants: List[Dict],
    document_text: str,
) -> Dict[str, Any]:
    """
    Validate that extracted covenants have complete definitions.

    Args:
        covenants: List of extracted covenant dictionaries
        document_text: Full document text

    Returns:
        Covenant validation results
    """
    results = {
        "success": True,
        "total_covenants": len(covenants),
        "valid_covenants": 0,
        "incomplete_covenants": 0,
        "issues": [],
    }

    required_fields = ["covenant_name", "covenant_type"]
    recommended_fields = ["threshold_value", "measurement_frequency"]

    for covenant in covenants:
        is_valid = True
        
        # Check required fields
        for field in required_fields:
            if not covenant.get(field):
                is_valid = False
                results["issues"].append({
                    "severity": "CRITICAL",
                    "covenant": covenant.get("covenant_name", "Unknown"),
                    "message": f"Missing required field: {field}",
                })

        # Check recommended fields for financial covenants
        if covenant.get("covenant_type") == "financial":
            for field in recommended_fields:
                if not covenant.get(field):
                    results["issues"].append({
                        "severity": "WARNING",
                        "covenant": covenant.get("covenant_name", "Unknown"),
                        "message": f"Missing recommended field for financial covenant: {field}",
                    })

        # Validate threshold value is numeric if present
        threshold = covenant.get("threshold_value")
        if threshold is not None:
            try:
                float(threshold)
            except (ValueError, TypeError):
                is_valid = False
                results["issues"].append({
                    "severity": "CRITICAL",
                    "covenant": covenant.get("covenant_name", "Unknown"),
                    "message": f"Invalid threshold value: {threshold}",
                })

        # Validate measurement frequency
        valid_frequencies = ["monthly", "quarterly", "semi-annual", "annual"]
        frequency = covenant.get("measurement_frequency", "").lower()
        if frequency and frequency not in valid_frequencies:
            results["issues"].append({
                "severity": "INFO",
                "covenant": covenant.get("covenant_name", "Unknown"),
                "message": f"Non-standard measurement frequency: {frequency}",
            })

        if is_valid:
            results["valid_covenants"] += 1
        else:
            results["incomplete_covenants"] += 1

    # Calculate validation percentage
    if results["total_covenants"] > 0:
        results["validation_percentage"] = round(
            results["valid_covenants"] / results["total_covenants"] * 100, 1
        )
    else:
        results["validation_percentage"] = 100.0

    logger.info(
        f"Covenant validation: {results['valid_covenants']}/{results['total_covenants']} valid, "
        f"{len(results['issues'])} issues found"
    )

    return results
