"""
Document Comparison Tool - AI-Powered Semantic Analysis
V9 Production Feature: Gemini-powered document comparison for loan documents.

Provides semantic comparison of legal documents with:
- Clause extraction and analysis
- Materiality assessment of differences
- Risk categorization and recommendations
"""

import os
import json
import difflib
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MaterialityLevel(str, Enum):
    """Materiality classification for document changes."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class ChangeCategory(str, Enum):
    """Categories of document changes."""
    FINANCIAL_TERMS = "FINANCIAL_TERMS"
    COVENANT = "COVENANT"
    DEFAULT_PROVISION = "DEFAULT_PROVISION"
    INTEREST_RATE = "INTEREST_RATE"
    COLLATERAL = "COLLATERAL"
    MATURITY = "MATURITY"
    PREPAYMENT = "PREPAYMENT"
    LEGAL_ENTITY = "LEGAL_ENTITY"
    GOVERNANCE = "GOVERNANCE"
    OTHER = "OTHER"


@dataclass
class ExtractedClause:
    """Represents an extracted clause from a document."""
    clause_type: str
    text: str
    location: Optional[str] = None
    confidence: float = 0.0


@dataclass
class MaterialChange:
    """Represents a material change between documents."""
    category: str
    original_text: str
    new_text: str
    materiality: str
    impact_description: str
    risk_score: float
    recommendation: str


@dataclass
class ComparisonResult:
    """Complete comparison result between two documents."""
    similarity_score: float
    total_changes: int
    material_changes: List[MaterialChange]
    extracted_clauses_doc1: List[ExtractedClause]
    extracted_clauses_doc2: List[ExtractedClause]
    summary: str
    risk_assessment: str
    recommendations: List[str]


class DocumentComparisonEngine:
    """
    Production-ready Document Comparison Engine using Gemini AI.
    
    Provides semantic analysis of legal documents, identifying material
    differences and assessing their risk implications.
    """
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the Document Comparison Engine.
        
        Args:
            api_key: Google AI API key. Falls back to env variable.
            model_name: Gemini model to use for analysis.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self._model = None
        
        if not self.api_key:
            logger.warning("No GOOGLE_API_KEY found. AI features will be limited.")
    
    def _get_model(self):
        """Get or initialize the Gemini model."""
        if self._model is None and self.api_key:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model
    
    def _basic_diff_analysis(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Perform basic diff analysis using difflib.
        
        This serves as a fallback when AI is unavailable and provides
        supplementary metrics for the AI analysis.
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        # Generate unified diff
        differ = difflib.unified_diff(lines1, lines2, lineterm='')
        diff_lines = list(differ)
        
        # Count changes
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        
        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, text1, text2)
        similarity = matcher.ratio()
        
        return {
            'similarity': round(similarity * 100, 2),
            'additions': additions,
            'deletions': deletions,
            'total_changes': additions + deletions,
            'diff_preview': diff_lines[:100]
        }
    
    async def extract_clauses(self, text: str) -> List[ExtractedClause]:
        """
        Extract key clauses from a legal document using Gemini AI.
        
        Args:
            text: Document text to analyze.
            
        Returns:
            List of extracted clauses with metadata.
        """
        model = self._get_model()
        
        if not model:
            logger.warning("Gemini model unavailable. Using basic extraction.")
            return self._basic_clause_extraction(text)
        
        prompt = f"""Analyze the following loan document and extract all key clauses.
For each clause, identify:
1. Type: One of [INTEREST_RATE, MATURITY, PRINCIPAL, COVENANT, DEFAULT, COLLATERAL, PREPAYMENT, FEES, GUARANTEE, REPRESENTATION, CONDITION_PRECEDENT, EVENT_OF_DEFAULT, AMENDMENT, ASSIGNMENT, GOVERNING_LAW]
2. Full text of the clause
3. Location in document (section/paragraph if identifiable)
4. Confidence score (0.0-1.0)

Return as JSON array:
[{{"clause_type": "...", "text": "...", "location": "...", "confidence": 0.95}}]

Document:
{text[:15000]}

Respond ONLY with the JSON array, no other text."""

        try:
            response = await model.generate_content_async(prompt)
            response_text = response.text.strip()
            
            # Clean response - remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
                response_text = response_text.rsplit('```', 1)[0]
            
            clauses_data = json.loads(response_text)
            
            return [
                ExtractedClause(
                    clause_type=c.get('clause_type', 'OTHER'),
                    text=c.get('text', ''),
                    location=c.get('location'),
                    confidence=float(c.get('confidence', 0.8))
                )
                for c in clauses_data
            ]
        except Exception as e:
            logger.error(f"Clause extraction failed: {e}")
            return self._basic_clause_extraction(text)
    
    def _basic_clause_extraction(self, text: str) -> List[ExtractedClause]:
        """Fallback regex-based clause extraction."""
        import re
        
        patterns = {
            'INTEREST_RATE': r'interest rate[:\s]+(\d+\.?\d*%?)',
            'MATURITY': r'matur(?:ity|es?)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            'PRINCIPAL': r'principal[:\s]+\$?([\d,]+)',
            'COVENANT': r'covenant[s]?[\s:]+(.{0,300}?)(?:\.|$)',
            'DEFAULT': r'(?:event of )?default[:\s]+(.{0,300}?)(?:\.|$)',
        }
        
        clauses = []
        for clause_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:5]:
                clauses.append(ExtractedClause(
                    clause_type=clause_type,
                    text=match.strip() if isinstance(match, str) else str(match),
                    location=None,
                    confidence=0.6
                ))
        
        return clauses
    
    async def compare_documents(
        self,
        document1: str,
        document2: str,
        context: Optional[str] = None
    ) -> ComparisonResult:
        """
        Perform comprehensive semantic document comparison.
        
        Args:
            document1: Original document text.
            document2: New/amended document text.
            context: Optional context about the comparison (e.g., loan type).
            
        Returns:
            ComparisonResult with detailed analysis.
        """
        # Get basic diff metrics first
        basic_analysis = self._basic_diff_analysis(document1, document2)
        
        model = self._get_model()
        
        if not model:
            logger.warning("Gemini unavailable. Returning basic comparison.")
            return self._basic_comparison_result(document1, document2, basic_analysis)
        
        # Extract clauses from both documents
        clauses1 = await self.extract_clauses(document1)
        clauses2 = await self.extract_clauses(document2)
        
        # Perform semantic comparison with Gemini
        context_str = f"\nContext: {context}" if context else ""
        
        prompt = f"""Compare these two loan documents and identify material differences.
{context_str}

DOCUMENT 1 (Original):
{document1[:10000]}

DOCUMENT 2 (Amended/New):
{document2[:10000]}

Analyze the differences and return a JSON object with this structure:
{{
    "summary": "Brief executive summary of key changes",
    "risk_assessment": "Overall risk level and assessment (LOW/MEDIUM/HIGH/CRITICAL)",
    "material_changes": [
        {{
            "category": "One of: FINANCIAL_TERMS, COVENANT, DEFAULT_PROVISION, INTEREST_RATE, COLLATERAL, MATURITY, PREPAYMENT, LEGAL_ENTITY, GOVERNANCE, OTHER",
            "original_text": "Text from document 1",
            "new_text": "Changed text from document 2",
            "materiality": "CRITICAL/HIGH/MEDIUM/LOW/INFORMATIONAL",
            "impact_description": "Explanation of business impact",
            "risk_score": 0.0-1.0,
            "recommendation": "Suggested action"
        }}
    ],
    "recommendations": ["List of recommended actions based on changes"]
}}

Focus on:
1. Financial term changes (rates, amounts, dates)
2. Covenant modifications (new, removed, or altered)
3. Default provisions and triggers
4. Collateral and security changes
5. Material legal changes

Return ONLY valid JSON, no other text."""

        try:
            response = await model.generate_content_async(prompt)
            response_text = response.text.strip()
            
            # Clean markdown formatting
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
                response_text = response_text.rsplit('```', 1)[0]
            
            analysis = json.loads(response_text)
            
            material_changes = [
                MaterialChange(
                    category=mc.get('category', 'OTHER'),
                    original_text=mc.get('original_text', ''),
                    new_text=mc.get('new_text', ''),
                    materiality=mc.get('materiality', 'MEDIUM'),
                    impact_description=mc.get('impact_description', ''),
                    risk_score=float(mc.get('risk_score', 0.5)),
                    recommendation=mc.get('recommendation', '')
                )
                for mc in analysis.get('material_changes', [])
            ]
            
            return ComparisonResult(
                similarity_score=basic_analysis['similarity'],
                total_changes=basic_analysis['total_changes'],
                material_changes=material_changes,
                extracted_clauses_doc1=clauses1,
                extracted_clauses_doc2=clauses2,
                summary=analysis.get('summary', ''),
                risk_assessment=analysis.get('risk_assessment', 'UNKNOWN'),
                recommendations=analysis.get('recommendations', [])
            )
            
        except Exception as e:
            logger.error(f"Semantic comparison failed: {e}")
            return self._basic_comparison_result(document1, document2, basic_analysis)
    
    def _basic_comparison_result(
        self,
        doc1: str,
        doc2: str,
        basic_analysis: Dict[str, Any]
    ) -> ComparisonResult:
        """Generate basic comparison result as fallback."""
        clauses1 = self._basic_clause_extraction(doc1)
        clauses2 = self._basic_clause_extraction(doc2)
        
        # Detect material changes using keywords
        material_keywords = [
            'default', 'covenant', 'interest rate', 'principal',
            'maturity', 'collateral', 'waiver', 'amendment'
        ]
        
        material_changes = []
        for line in basic_analysis.get('diff_preview', []):
            line_lower = line.lower()
            for keyword in material_keywords:
                if keyword in line_lower:
                    material_changes.append(MaterialChange(
                        category='OTHER',
                        original_text=line if line.startswith('-') else '',
                        new_text=line if line.startswith('+') else '',
                        materiality='MEDIUM',
                        impact_description=f'Change detected involving: {keyword}',
                        risk_score=0.5,
                        recommendation='Review this change with legal counsel'
                    ))
                    break
        
        return ComparisonResult(
            similarity_score=basic_analysis['similarity'],
            total_changes=basic_analysis['total_changes'],
            material_changes=material_changes[:20],
            extracted_clauses_doc1=clauses1,
            extracted_clauses_doc2=clauses2,
            summary=f"Documents are {basic_analysis['similarity']}% similar with {basic_analysis['total_changes']} line changes.",
            risk_assessment='REVIEW_REQUIRED',
            recommendations=[
                'Enable Gemini API for detailed semantic analysis',
                'Manual review recommended for detected changes'
            ]
        )
    
    def to_dict(self, result: ComparisonResult) -> Dict[str, Any]:
        """Convert ComparisonResult to dictionary for JSON serialization."""
        return {
            'similarity_score': result.similarity_score,
            'total_changes': result.total_changes,
            'material_changes': [asdict(mc) for mc in result.material_changes],
            'extracted_clauses_doc1': [asdict(c) for c in result.extracted_clauses_doc1],
            'extracted_clauses_doc2': [asdict(c) for c in result.extracted_clauses_doc2],
            'summary': result.summary,
            'risk_assessment': result.risk_assessment,
            'recommendations': result.recommendations
        }


# Singleton instance
_engine_instance: Optional[DocumentComparisonEngine] = None


def get_document_comparison_engine() -> DocumentComparisonEngine:
    """Get singleton DocumentComparisonEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DocumentComparisonEngine()
    return _engine_instance


# ADK Tool Functions for Agent Integration
async def compare_documents_tool(
    document1: str,
    document2: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    ADK Tool: Compare two documents and identify material differences.
    
    Args:
        document1: Original document text
        document2: New/amended document text  
        context: Optional context about the loan type
        
    Returns:
        Dictionary with comparison results including material changes,
        risk assessment, and recommendations.
    """
    engine = get_document_comparison_engine()
    result = await engine.compare_documents(document1, document2, context)
    return engine.to_dict(result)


async def extract_clauses_tool(document: str) -> Dict[str, Any]:
    """
    ADK Tool: Extract key clauses from a loan document.
    
    Args:
        document: Document text to analyze
        
    Returns:
        Dictionary with extracted clauses and their metadata.
    """
    engine = get_document_comparison_engine()
    clauses = await engine.extract_clauses(document)
    return {
        'clauses': [asdict(c) for c in clauses],
        'total_extracted': len(clauses)
    }
