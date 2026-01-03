"""
LexNLP-based legal document extraction tools.

Reference: lexpredict-lexnlp patterns for legal entity extraction.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_money_amounts(text: str) -> List[Dict[str, Any]]:
    """
    Extract monetary amounts from legal text.
    
    Based on LexNLP money extraction patterns.
    
    Args:
        text: Document text
        
    Returns:
        List of extracted money amounts
    """
    amounts = []
    
    # Currency patterns
    patterns = [
        # $X,XXX,XXX.XX or USD X,XXX,XXX.XX
        r'(?:USD?\s*|US\s*\$\s*|\$\s*)([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)\s*(?:million|billion|thousand|M|B|K)?',
        # EUR patterns
        r'(?:EUR?\s*|€\s*)([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)\s*(?:million|billion|thousand|M|B|K)?',
        # GBP patterns
        r'(?:GBP\s*|£\s*)([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)\s*(?:million|billion|thousand|M|B|K)?',
    ]
    
    currency_map = {
        '$': 'USD', 'USD': 'USD', 'US$': 'USD',
        '€': 'EUR', 'EUR': 'EUR',
        '£': 'GBP', 'GBP': 'GBP',
    }
    
    multipliers = {
        'million': 1_000_000, 'M': 1_000_000,
        'billion': 1_000_000_000, 'B': 1_000_000_000,
        'thousand': 1_000, 'K': 1_000,
    }
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                
                # Check for multiplier
                full_match = match.group(0).upper()
                for mult_key, mult_val in multipliers.items():
                    if mult_key.upper() in full_match:
                        amount *= mult_val
                        break
                
                # Determine currency
                currency = 'USD'  # default
                for symbol, curr in currency_map.items():
                    if symbol in match.group(0):
                        currency = curr
                        break
                
                amounts.append({
                    "amount": amount,
                    "currency": currency,
                    "text": match.group(0).strip(),
                    "start": match.start(),
                    "end": match.end(),
                })
            except ValueError:
                continue
    
    return amounts


def extract_dates(text: str) -> List[Dict[str, Any]]:
    """
    Extract dates from legal text.
    
    Based on LexNLP date extraction patterns.
    
    Args:
        text: Document text
        
    Returns:
        List of extracted dates
    """
    dates = []
    
    # Date patterns
    patterns = [
        # Month DD, YYYY
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
        # DD Month YYYY
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        # MM/DD/YYYY or MM-DD-YYYY
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        # YYYY-MM-DD (ISO)
        r'(\d{4})-(\d{2})-(\d{2})',
    ]
    
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
    }
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                groups = match.groups()
                
                if len(groups) == 3:
                    # Try to parse based on pattern
                    if groups[0].lower() in month_map:
                        # Month DD, YYYY
                        month = month_map[groups[0].lower()]
                        day = int(groups[1])
                        year = int(groups[2])
                    elif groups[1].lower() in month_map:
                        # DD Month YYYY
                        day = int(groups[0])
                        month = month_map[groups[1].lower()]
                        year = int(groups[2])
                    elif len(groups[0]) == 4:
                        # YYYY-MM-DD
                        year = int(groups[0])
                        month = int(groups[1])
                        day = int(groups[2])
                    else:
                        # MM/DD/YYYY
                        month = int(groups[0])
                        day = int(groups[1])
                        year = int(groups[2])
                    
                    date_obj = datetime(year, month, day)
                    dates.append({
                        "date": date_obj.strftime("%Y-%m-%d"),
                        "text": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                    })
            except (ValueError, IndexError):
                continue
    
    return dates


def extract_percentages(text: str) -> List[Dict[str, Any]]:
    """
    Extract percentage values from text.
    
    Args:
        text: Document text
        
    Returns:
        List of extracted percentages
    """
    percentages = []
    
    # Percentage patterns
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:%|percent|per\s*cent)',
        r'(\d+(?:\.\d+)?)\s*basis\s*points?',
        r'(\d+(?:\.\d+)?)\s*bps',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                value = float(match.group(1))
                
                # Check if basis points
                full_match = match.group(0).lower()
                is_bps = 'basis' in full_match or 'bps' in full_match
                
                percentages.append({
                    "value": value,
                    "unit": "bps" if is_bps else "percent",
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                })
            except ValueError:
                continue
    
    return percentages


def extract_definitions(text: str) -> List[Dict[str, Any]]:
    """
    Extract defined terms from legal text.
    
    Based on LexNLP definitions extraction.
    
    Args:
        text: Document text
        
    Returns:
        List of defined terms
    """
    definitions = []
    
    # Definition patterns common in legal documents
    patterns = [
        # "Term" means/shall mean
        r'"([^"]+)"\s+(?:means?|shall\s+mean|is\s+defined\s+as)',
        # (the "Term")
        r'\((?:the\s+)?"([^"]+)"\)',
        # as defined herein
        r'"([^"]+)"\s+(?:as\s+defined\s+(?:herein|above|below))',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            term = match.group(1).strip()
            if len(term) > 2 and len(term) < 100:  # Reasonable term length
                definitions.append({
                    "term": term,
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                })
    
    return definitions


def extract_parties(text: str) -> List[Dict[str, Any]]:
    """
    Extract party names from legal documents.
    
    Args:
        text: Document text
        
    Returns:
        List of party information
    """
    parties = []
    
    # Party patterns
    patterns = [
        # COMPANY NAME, a [state] corporation ("Role")
        r'([A-Z][A-Za-z\s&.,]+(?:Inc\.|LLC|L\.L\.C\.|Corp\.|Corporation|Limited|Ltd\.?|LLP|L\.P\.))\s*,?\s*(?:a|an)\s+([A-Za-z\s]+)\s+(?:corporation|company|limited\s+liability\s+company)',
        # ("Borrower"), ("Lender"), ("Agent")
        r'\("?(Borrower|Lender|Agent|Administrative\s+Agent|Collateral\s+Agent|Guarantor|Issuer)"?\)',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            if len(match.groups()) >= 1:
                parties.append({
                    "name": match.group(1).strip(),
                    "role": match.group(2).strip() if len(match.groups()) > 1 else None,
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                })
    
    return parties


def extract_covenant_clauses(text: str) -> List[Dict[str, Any]]:
    """
    Extract covenant clauses from loan documents.
    
    Args:
        text: Document text
        
    Returns:
        List of covenant clauses
    """
    covenants = []
    
    # Covenant section patterns
    section_patterns = [
        r'Section\s+(\d+(?:\.\d+)*)\s*[.:]?\s*(Financial\s+Covenants?|Affirmative\s+Covenants?|Negative\s+Covenants?|Reporting\s+Covenants?)',
        r'(?:ARTICLE|Article)\s+([IVXLCDM]+|\d+)\s*[.:]?\s*(Financial\s+Covenants?|Affirmative\s+Covenants?|Negative\s+Covenants?)',
    ]
    
    # Specific covenant patterns
    covenant_patterns = [
        # Financial ratios
        (r'(?:Consolidated\s+)?(?:Total\s+)?Debt[\s-]+to[\s-]+EBITDA|Leverage\s+Ratio', 'financial', 'Debt/EBITDA'),
        (r'Interest\s+Coverage\s+Ratio|Fixed\s+Charge\s+Coverage', 'financial', 'Interest Coverage'),
        (r'Current\s+Ratio', 'financial', 'Current Ratio'),
        (r'(?:Minimum\s+)?(?:Consolidated\s+)?(?:Tangible\s+)?Net\s+Worth', 'financial', 'Net Worth'),
        (r'(?:Maximum\s+)?Capital\s+Expenditures?|CapEx', 'financial', 'CapEx Limit'),
        # ESG covenants
        (r'(?:Carbon|CO2|Greenhouse\s+Gas)\s+(?:Emissions?|Reduction)', 'esg', 'Carbon Emissions'),
        (r'Renewable\s+Energy|Clean\s+Energy', 'esg', 'Renewable Energy'),
        (r'(?:Board|Gender|Workforce)\s+Diversity', 'esg', 'Diversity'),
        (r'Sustainability[\s-]+(?:Linked|Performance)', 'esg', 'Sustainability Target'),
    ]
    
    for pattern, cov_type, cov_name in covenant_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Try to find the threshold near this match
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end]
            
            # Look for threshold values
            threshold_match = re.search(
                r'(?:not\s+(?:to\s+)?exceed|shall\s+not\s+be\s+(?:less|greater)\s+than|≤|≥|<=|>=|<|>)\s*(\d+(?:\.\d+)?)',
                context, re.IGNORECASE
            )
            
            threshold = None
            operator = None
            if threshold_match:
                threshold = float(threshold_match.group(1))
                if 'exceed' in threshold_match.group(0).lower() or '<' in threshold_match.group(0):
                    operator = '<='
                else:
                    operator = '>='
            
            covenants.append({
                "name": cov_name,
                "type": cov_type,
                "threshold": threshold,
                "operator": operator,
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })
    
    return covenants


def analyze_document(text: str) -> Dict[str, Any]:
    """
    Perform comprehensive legal document analysis.
    
    Args:
        text: Full document text
        
    Returns:
        Complete analysis results
    """
    logger.info("Starting LexNLP document analysis")
    
    results = {
        "money_amounts": extract_money_amounts(text),
        "dates": extract_dates(text),
        "percentages": extract_percentages(text),
        "definitions": extract_definitions(text),
        "parties": extract_parties(text),
        "covenants": extract_covenant_clauses(text),
    }
    
    # Summary statistics
    results["summary"] = {
        "total_money_amounts": len(results["money_amounts"]),
        "total_dates": len(results["dates"]),
        "total_percentages": len(results["percentages"]),
        "total_definitions": len(results["definitions"]),
        "total_parties": len(results["parties"]),
        "total_covenants": len(results["covenants"]),
        "financial_covenants": sum(1 for c in results["covenants"] if c["type"] == "financial"),
        "esg_covenants": sum(1 for c in results["covenants"] if c["type"] == "esg"),
    }
    
    logger.info(f"LexNLP analysis complete: {results['summary']}")
    
    return results
