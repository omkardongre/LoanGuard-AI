"""
Production-level Covenant Text Parser for LoanGuard V10.

Parses loan agreement text to extract structured covenant data:
- Covenant type (debt_to_ebitda, interest_coverage, etc.)
- Threshold value (numeric)
- Threshold operator (min/max)
- Measurement frequency (quarterly/annually/monthly)

This is a fallback for when Affinda AI returns empty/unknown covenants.

Architecture: V10 alignment
Source: Research on NLP/regex for credit agreements (2024-2025)
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ParsedCovenant:
    """Structured covenant extracted from text."""
    covenant_type: str  # e.g., "debt_to_ebitda", "interest_coverage"
    covenant_name: str  # Human-readable name
    threshold_value: float  # Numeric threshold
    threshold_operator: str  # "min" or "max"
    measurement_frequency: str  # "quarterly", "annually", "monthly"
    raw_text: str  # Original text snippet
    confidence: float  # 0.0 to 1.0


# Covenant patterns with regex and metadata
# Each entry: (type, display_name, pattern, operator, frequency)
# NOTE: Patterns prioritize "CURRENT THRESHOLD" lines for accurate extraction
COVENANT_PATTERNS = [
    # Leverage / Debt Ratios - Look for "CURRENT THRESHOLD" or explicit ratio statements
    (
        "debt_to_ebitda",
        "Debt to EBITDA",
        r"(?:debt\s*(?:to|/)\s*ebitda|leverage\s+ratio|total\s+(?:leverage|debt))"
        r".*?(?:current\s+threshold|threshold|shall\s+not\s+(?:exceed|permit)|maximum|≤).*?"
        r"(\d+\.?\d*)\s*(?:x|to\s*1(?:\.00)?|:1|times)",
        "max",
        "quarterly"
    ),
    (
        "interest_coverage",
        "Interest Coverage Ratio",
        r"(?:interest\s+coverage\s+ratio|icr)"
        r".*?(?:current\s+threshold|threshold|shall\s+maintain|minimum|≥|not\s+less\s+than).*?"
        r"(\d+\.?\d*)\s*(?:x|to\s*1(?:\.00)?|:1|times)",
        "min",
        "quarterly"
    ),
    (
        "fixed_charge_coverage",
        "Fixed Charge Coverage Ratio",
        r"(?:fixed\s+charge\s+coverage\s+ratio|fccr)"
        r".*?(?:current\s+threshold|threshold|minimum|≥|not\s+less\s+than).*?"
        r"(\d+\.?\d*)\s*(?:x|to\s*1(?:\.00)?|:1|times)",
        "min",
        "quarterly"
    ),
    (
        "dscr",
        "Debt Service Coverage Ratio",
        r"(?:debt\s+service\s+coverage\s+ratio|dscr)"
        r".*?(?:current\s+threshold|threshold|minimum|≥|not\s+less\s+than).*?"
        r"(\d+\.?\d*)\s*(?:x|to\s*1(?:\.00)?|:1|times)",
        "min",
        "quarterly"
    ),
    (
        "current_ratio",
        "Current Ratio",
        r"(?:current\s+ratio)"
        r".*?(?:current\s+threshold|threshold|minimum|≥|not\s+less\s+than).*?"
        r"(\d+\.?\d*)\s*(?:x|to\s*1(?:\.00)?|:1|times)",
        "min",
        "quarterly"
    ),
    # Capital and Liquidity - Look for amounts with USD/$
    (
        "capex_limit",
        "Capital Expenditure Limit",
        r"(?:capital\s+expenditure|capex)"
        r".*?(?:current\s+threshold|threshold|shall\s+not\s+(?:exceed|make)|maximum|≤).*?"
        r"(?:USD\s*|\\$)?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:million|m|M)?",
        "max",
        "annually"
    ),
    (
        "minimum_liquidity",
        "Minimum Liquidity",
        r"(?:minimum\s+liquidity|liquidity|unrestricted\s+cash|cash\s+and\s+cash\s+equivalents)"
        r".*?(?:current\s+threshold|threshold|minimum|≥|not\s+less\s+than|at\s+least).*?"
        r"(?:USD\s*|\\$)?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:million|m|M)?",
        "min",
        "monthly"
    ),
    (
        "tangible_net_worth",
        "Tangible Net Worth",
        r"(?:tangible\s+net\s+worth|tnw)"
        r".*?(?:current\s+threshold|threshold|minimum|≥|not\s+less\s+than).*?"
        r"(?:USD\s*|\\$)?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:million|m|M)?",
        "min",
        "annually"
    ),
    # ESG / Sustainability Covenants
    (
        "ghg_emissions",
        "GHG Emissions Reduction",
        r"(?:ghg|greenhouse\s+gas|carbon|scope\s+[12]|emissions?\s+reduction)"
        r".*?(\d+\.?\d*)\s*(?:%|percent)",
        "min",
        "annually"
    ),
    (
        "renewable_energy",
        "Renewable Energy Target",
        r"(?:renewable\s+(?:energy\s+)?(?:capacity|target|generation))"
        r".*?(\d[\d,]*(?:\.\d+)?)\s*(?:mw|MW|gw|GW|percent|%)?",
        "min",
        "annually"
    ),
]


class CovenantParser:
    """
    Production-level covenant text parser.
    
    Uses regex patterns to extract structured covenant data from
    credit agreement text. Designed as a fallback when Affinda AI
    cannot extract structured covenants.
    """
    
    def __init__(self):
        self.patterns = COVENANT_PATTERNS
        logger.info("CovenantParser initialized with %d patterns", len(self.patterns))
    
    def extract_covenants(self, text: str) -> List[ParsedCovenant]:
        """
        Extract all covenants from document text.
        
        Args:
            text: Full document text (raw_text from Affinda)
            
        Returns:
            List of ParsedCovenant objects with structured data
        """
        if not text:
            logger.warning("Empty text provided to covenant parser")
            return []
        
        # Normalize text for better matching
        normalized_text = self._normalize_text(text)
        
        covenants = []
        seen_types = set()  # Avoid duplicates
        
        for cov_type, name, pattern, operator, frequency in self.patterns:
            matches = self._find_covenant(normalized_text, pattern, cov_type)
            
            for match_text, value in matches:
                if cov_type in seen_types:
                    continue  # Skip duplicates
                
                # Parse numeric value
                parsed_value = self._parse_numeric_value(value, cov_type)
                
                if parsed_value > 0:
                    covenant = ParsedCovenant(
                        covenant_type=cov_type,
                        covenant_name=name,
                        threshold_value=parsed_value,
                        threshold_operator=operator,
                        measurement_frequency=frequency,
                        raw_text=match_text[:200],  # Limit length
                        confidence=0.85,  # Regex-based confidence
                    )
                    covenants.append(covenant)
                    seen_types.add(cov_type)
                    logger.info(f"Extracted covenant: {name} = {parsed_value} ({operator})")
        
        logger.info(f"Total covenants extracted by parser: {len(covenants)}")
        return covenants
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for pattern matching."""
        # Convert to lowercase for matching
        text = text.lower()
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Normalize common symbols
        text = text.replace('≤', '<=').replace('≥', '>=')
        text = text.replace('—', '-').replace('–', '-')
        return text
    
    def _find_covenant(
        self, 
        text: str, 
        pattern: str, 
        cov_type: str
    ) -> List[Tuple[str, str]]:
        """
        Find covenant matches in text.
        
        Returns list of (matched_text, value) tuples.
        """
        try:
            matches = []
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                full_match = match.group(0)
                value = match.group(1) if match.lastindex >= 1 else None
                if value:
                    matches.append((full_match, value))
            return matches
        except re.error as e:
            logger.error(f"Regex error for {cov_type}: {e}")
            return []
    
    def _parse_numeric_value(self, value_str: str, cov_type: str) -> float:
        """
        Parse numeric value from string.
        
        Handles:
        - Plain numbers: "4.0", "3.50"
        - Comma-separated: "50,000,000"
        - With suffixes: "50M", "25 million"
        """
        try:
            # Remove commas
            value_str = value_str.replace(',', '')
            
            # Extract numeric part
            numeric_match = re.search(r'(\d+\.?\d*)', value_str)
            if not numeric_match:
                return 0.0
            
            value = float(numeric_match.group(1))
            
            # Check for million/billion suffix in monetary covenants
            if cov_type in ('capex_limit', 'minimum_liquidity', 'tangible_net_worth'):
                # If value is small, assume it's in millions
                if value < 1000:
                    value = value * 1_000_000
            
            return value
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse value '{value_str}': {e}")
            return 0.0
    
    def to_affinda_format(
        self, 
        covenants: List[ParsedCovenant]
    ) -> List["ExtractedCovenant"]:
        """
        Convert parsed covenants to Affinda ExtractedCovenant format.
        
        This allows seamless integration with existing Affinda flow.
        """
        from common.affinda_client import ExtractedCovenant
        
        return [
            ExtractedCovenant(
                covenant_type=c.covenant_type,
                covenant_name=c.covenant_name,  # Human-readable name
                threshold_value=str(c.threshold_value),
                measurement_frequency=c.measurement_frequency.capitalize(),
                raw_text=c.raw_text,
                confidence=c.confidence,
            )
            for c in covenants
        ]


def extract_covenants_from_text(text: str) -> List[ParsedCovenant]:
    """
    Convenience function for covenant extraction.
    
    Args:
        text: Document text to parse
        
    Returns:
        List of ParsedCovenant objects
    """
    parser = CovenantParser()
    return parser.extract_covenants(text)


# CLI test support
if __name__ == "__main__":
    import sys
    
    # Test with sample text
    sample_text = """
    ARTICLE VI - FINANCIAL COVENANTS
    
    Section 6.1 - Maximum Total Leverage Ratio (Debt/EBITDA)
    The Borrower shall not permit the ratio of Total Debt to Consolidated EBITDA 
    to exceed 4.00x at the end of each fiscal quarter.
    
    Section 6.2 - Minimum Interest Coverage Ratio
    The Borrower shall maintain an Interest Coverage Ratio of not less than 2.50x
    at the end of each fiscal quarter.
    
    Section 6.3 - Minimum Fixed Charge Coverage Ratio
    The Borrower shall maintain a Fixed Charge Coverage Ratio of not less than 1.25x.
    
    Section 6.4 - Maximum Annual Capital Expenditures
    The Borrower shall not make Capital Expenditures exceeding USD 50,000,000 annually.
    
    Section 6.5 - Minimum Liquidity
    The Borrower shall maintain unrestricted cash of at least $25,000,000.
    """
    
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            sample_text = f.read()
    
    print("=" * 60)
    print("COVENANT PARSER TEST")
    print("=" * 60)
    
    parser = CovenantParser()
    covenants = parser.extract_covenants(sample_text)
    
    print(f"\nExtracted {len(covenants)} covenants:\n")
    
    for i, cov in enumerate(covenants, 1):
        print(f"{i}. {cov.covenant_name}")
        print(f"   Type: {cov.covenant_type}")
        print(f"   Threshold: {cov.threshold_value} ({cov.threshold_operator})")
        print(f"   Frequency: {cov.measurement_frequency}")
        print(f"   Confidence: {cov.confidence:.0%}")
        print()
