"""
Entity extraction tools for loan documents.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_parties(document_text: str) -> Dict[str, Any]:
    """
    Extract party information from a loan document.

    Args:
        document_text: Full text of the loan document

    Returns:
        Dictionary with extracted party information
    """
    parties = {
        "borrowers": [],
        "lenders": [],
        "agents": [],
        "guarantors": [],
    }

    # Common patterns for party identification
    borrower_patterns = [
        r"(?:the\s+)?[\"']?borrower[\"']?\s+(?:means|refers\s+to|is)\s+([^,\.\n]+)",
        r"([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corporation|Corp|Company|Co)\.?)\s*(?:,\s*)?(?:as\s+)?(?:the\s+)?[\"']?borrower",
        r"borrower[:\s]+([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corporation|Corp|Company|Co)\.?)",
    ]

    lender_patterns = [
        r"(?:the\s+)?[\"']?lender[s]?[\"']?\s+(?:means|refers\s+to|is)\s+([^,\.\n]+)",
        r"([A-Z][A-Za-z\s&]+(?:Bank|N\.A\.|NA|Financial|Capital))\s*(?:,\s*)?(?:as\s+)?(?:the\s+)?[\"']?(?:lender|agent)",
    ]

    agent_patterns = [
        r"(?:administrative|facility|collateral)\s+agent[:\s]+([A-Z][A-Za-z\s&]+(?:Bank|N\.A\.|NA))",
        r"([A-Z][A-Za-z\s&]+(?:Bank|N\.A\.|NA))\s*,?\s*as\s+(?:administrative|facility|collateral)\s+agent",
    ]

    guarantor_patterns = [
        r"(?:the\s+)?[\"']?guarantor[s]?[\"']?\s+(?:means|refers\s+to|is)\s+([^,\.\n]+)",
        r"([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corporation|Corp|Company|Co)\.?)\s*(?:,\s*)?(?:as\s+)?(?:the\s+)?[\"']?guarantor",
    ]

    # Extract each party type
    for pattern in borrower_patterns:
        matches = re.findall(pattern, document_text, re.IGNORECASE)
        for match in matches:
            clean_name = _clean_party_name(match)
            if clean_name and clean_name not in parties["borrowers"]:
                parties["borrowers"].append(clean_name)

    for pattern in lender_patterns:
        matches = re.findall(pattern, document_text, re.IGNORECASE)
        for match in matches:
            clean_name = _clean_party_name(match)
            if clean_name and clean_name not in parties["lenders"]:
                parties["lenders"].append(clean_name)

    for pattern in agent_patterns:
        matches = re.findall(pattern, document_text, re.IGNORECASE)
        for match in matches:
            clean_name = _clean_party_name(match)
            if clean_name and clean_name not in parties["agents"]:
                parties["agents"].append(clean_name)

    for pattern in guarantor_patterns:
        matches = re.findall(pattern, document_text, re.IGNORECASE)
        for match in matches:
            clean_name = _clean_party_name(match)
            if clean_name and clean_name not in parties["guarantors"]:
                parties["guarantors"].append(clean_name)

    total_parties = sum(len(v) for v in parties.values())
    logger.info(f"Extracted {total_parties} parties from document")

    return {
        "success": True,
        "parties": parties,
        "total_count": total_parties,
    }


def extract_financial_terms(document_text: str) -> Dict[str, Any]:
    """
    Extract financial terms from a loan document.

    Args:
        document_text: Full text of the loan document

    Returns:
        Dictionary with extracted financial terms
    """
    terms = {
        "facility_amount": None,
        "currency": None,
        "interest_rate": None,
        "margin": None,
        "commitment_fee": None,
        "maturity_date": None,
        "facility_type": None,
    }

    # Currency and amount patterns
    amount_patterns = [
        r"(?:aggregate\s+)?(?:principal\s+)?(?:commitment|facility)\s+(?:amount|of)\s+(?:up\s+to\s+)?(?:USD|EUR|GBP|£|\$|€)\s*([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B)?",
        r"(?:USD|EUR|GBP|£|\$|€)\s*([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B)?\s*(?:credit\s+)?(?:facility|loan|commitment)",
        r"([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B)?\s*(?:USD|EUR|GBP|Dollars|Euros|Pounds)",
    ]

    currency_patterns = [
        r"(USD|EUR|GBP|US\s+Dollars?|Euros?|British\s+Pounds?|Sterling)",
        r"(£|\$|€)",
    ]

    interest_patterns = [
        r"(?:interest\s+rate|applicable\s+rate)[:\s]+([A-Z]+\s*\+?\s*[\d\.]+%?)",
        r"(LIBOR|SOFR|EURIBOR|Base\s+Rate)\s*\+\s*([\d\.]+)\s*%?",
        r"margin\s+(?:of\s+)?([\d\.]+)\s*%",
    ]

    # Extract amounts
    for pattern in amount_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
                # Convert to standard units
                full_match = match.group(0).lower()
                if "billion" in full_match or "b" in full_match:
                    amount *= 1_000_000_000
                elif "million" in full_match or "m" in full_match:
                    amount *= 1_000_000
                terms["facility_amount"] = amount
                break
            except ValueError:
                continue

    # Extract currency
    for pattern in currency_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            currency = match.group(1)
            currency_map = {
                "$": "USD", "usd": "USD", "us dollars": "USD", "dollars": "USD",
                "€": "EUR", "eur": "EUR", "euros": "EUR", "euro": "EUR",
                "£": "GBP", "gbp": "GBP", "pounds": "GBP", "sterling": "GBP",
            }
            terms["currency"] = currency_map.get(currency.lower(), currency.upper())
            break

    # Extract interest rate / margin
    for pattern in interest_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            if match.lastindex >= 2:
                terms["interest_rate"] = f"{match.group(1)} + {match.group(2)}%"
                terms["margin"] = float(match.group(2))
            else:
                terms["interest_rate"] = match.group(1)
            break

    # Extract facility type
    facility_types = [
        "revolving credit", "term loan", "bridge loan", "acquisition facility",
        "working capital", "letter of credit", "swing line",
    ]
    for ftype in facility_types:
        if ftype in document_text.lower():
            terms["facility_type"] = ftype.title()
            break

    logger.info(f"Extracted financial terms: {terms}")

    return {
        "success": True,
        "terms": terms,
    }


def extract_key_dates(document_text: str) -> Dict[str, Any]:
    """
    Extract key dates from a loan document.

    Args:
        document_text: Full text of the loan document

    Returns:
        Dictionary with extracted dates
    """
    dates = {
        "signing_date": None,
        "effective_date": None,
        "maturity_date": None,
        "first_payment_date": None,
        "reporting_dates": [],
    }

    # Date patterns
    date_patterns = [
        r"(\d{1,2})\s+(?:of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
        r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})",
        r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})",
    ]

    # Context patterns for date types
    date_contexts = {
        "signing_date": [r"(?:dated|executed|signed)\s+(?:as\s+of\s+)?", r"this\s+agreement\s+(?:is\s+)?dated"],
        "effective_date": [r"effective\s+(?:as\s+of\s+)?(?:date)?", r"(?:becomes|became)\s+effective\s+(?:on)?"],
        "maturity_date": [r"maturity\s+date", r"(?:final|termination)\s+date", r"expires?\s+(?:on)?"],
    }

    text_lower = document_text.lower()

    for date_type, context_patterns in date_contexts.items():
        for ctx_pattern in context_patterns:
            ctx_match = re.search(ctx_pattern, text_lower)
            if ctx_match:
                # Look for date near the context
                search_start = ctx_match.end()
                search_text = document_text[search_start:search_start + 100]
                
                for date_pattern in date_patterns:
                    date_match = re.search(date_pattern, search_text, re.IGNORECASE)
                    if date_match:
                        date_str = _parse_date_match(date_match)
                        if date_str:
                            dates[date_type] = date_str
                            break
                
                if dates[date_type]:
                    break

    # Extract reporting dates
    reporting_patterns = [
        r"(?:quarterly|annual)\s+(?:financial\s+)?(?:statements?|reports?)\s+(?:due|delivered|within)\s+(\d+)\s+days",
        r"within\s+(\d+)\s+days\s+(?:after|of)\s+(?:each|the)\s+(?:fiscal|quarter)",
    ]
    
    for pattern in reporting_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            dates["reporting_dates"].append(f"Within {match} days")

    logger.info(f"Extracted dates: {dates}")

    return {
        "success": True,
        "dates": dates,
    }


def _clean_party_name(name: str) -> Optional[str]:
    """Clean and normalize party name."""
    if not name:
        return None
    
    # Remove extra whitespace
    name = " ".join(name.split())
    
    # Remove common prefixes/suffixes
    remove_patterns = [
        r"^the\s+", r"^a\s+", r"^an\s+",
        r"\s*\(.*\)\s*$",
    ]
    
    for pattern in remove_patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    
    name = name.strip()
    
    # Validate minimum length and contains letters
    if len(name) < 3 or not re.search(r"[A-Za-z]", name):
        return None
    
    return name


def _parse_date_match(match: re.Match) -> Optional[str]:
    """Parse a date match into ISO format."""
    try:
        groups = match.groups()
        
        # Try different format combinations
        month_names = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        }
        
        if len(groups) == 3:
            # Check if any group is a month name
            for i, g in enumerate(groups):
                if g.lower() in month_names:
                    month = month_names[g.lower()]
                    if i == 0:  # Month Day Year
                        day = int(groups[1])
                        year = int(groups[2])
                    else:  # Day Month Year
                        day = int(groups[0])
                        year = int(groups[2])
                    
                    return datetime(year, month, day).strftime("%Y-%m-%d")
            
            # Numeric date
            g0, g1, g2 = [int(g) for g in groups]
            if g0 > 1900:  # YYYY-MM-DD
                return datetime(g0, g1, g2).strftime("%Y-%m-%d")
            elif g2 > 1900:  # MM-DD-YYYY or DD-MM-YYYY
                if g0 > 12:  # DD-MM-YYYY
                    return datetime(g2, g1, g0).strftime("%Y-%m-%d")
                else:  # MM-DD-YYYY
                    return datetime(g2, g0, g1).strftime("%Y-%m-%d")
        
        return None
        
    except (ValueError, TypeError):
        return None
