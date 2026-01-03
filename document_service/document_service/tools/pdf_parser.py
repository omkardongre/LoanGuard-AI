"""
PDF parsing tools for loan documents.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_pdf_document(
    file_path: str,
    extract_tables: bool = True,
    extract_metadata: bool = True,
) -> Dict[str, Any]:
    """
    Parse a PDF document and extract text content.

    Args:
        file_path: Path to the PDF file
        extract_tables: Whether to extract tables
        extract_metadata: Whether to extract document metadata

    Returns:
        Dictionary containing parsed content with sections
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("pypdf not installed. Install with: pip install pypdf")
        return {"error": "pypdf not installed", "success": False}

    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}", "success": False}

        reader = PdfReader(str(path))
        
        result = {
            "success": True,
            "file_path": file_path,
            "page_count": len(reader.pages),
            "metadata": {},
            "sections": [],
            "full_text": "",
        }

        # Extract metadata
        if extract_metadata and reader.metadata:
            result["metadata"] = {
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
                "creation_date": str(reader.metadata.get("/CreationDate", "")),
            }

        # Extract text from all pages
        full_text_parts = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            full_text_parts.append(page_text)

        full_text = "\n".join(full_text_parts)
        result["full_text"] = full_text

        # Identify sections based on common loan document patterns
        result["sections"] = _identify_sections(full_text)

        logger.info(
            f"Parsed PDF: {path.name}, {result['page_count']} pages, "
            f"{len(result['sections'])} sections identified"
        )

        return result

    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
        return {"error": str(e), "success": False}


def _identify_sections(text: str) -> List[Dict[str, Any]]:
    """
    Identify document sections based on common loan agreement patterns.
    """
    sections = []
    
    # Common section patterns in loan agreements
    section_patterns = [
        r"ARTICLE\s+([IVXLCDM]+|\d+)[:\.\s]+([^\n]+)",
        r"SECTION\s+(\d+(?:\.\d+)?)[:\.\s]+([^\n]+)",
        r"(\d+(?:\.\d+)?)\s+([A-Z][A-Z\s]+)(?=\n)",
        r"^([A-Z][A-Z\s]{3,50})$",
    ]

    for pattern in section_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            section_info = {
                "number": match.group(1).strip() if match.lastindex >= 1 else "",
                "title": match.group(2).strip() if match.lastindex >= 2 else match.group(1).strip(),
                "start_position": match.start(),
                "match_text": match.group(0)[:100],
            }
            
            # Avoid duplicates
            if not any(s["start_position"] == section_info["start_position"] for s in sections):
                sections.append(section_info)

    # Sort by position in document
    sections.sort(key=lambda x: x["start_position"])
    
    return sections


def extract_text_from_pages(
    file_path: str,
    start_page: int = 0,
    end_page: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Extract text from specific pages of a PDF.

    Args:
        file_path: Path to the PDF file
        start_page: Starting page (0-indexed)
        end_page: Ending page (exclusive), None for all remaining

    Returns:
        Dictionary with extracted text
    """
    try:
        from pypdf import PdfReader
        
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        
        if end_page is None:
            end_page = total_pages
        
        end_page = min(end_page, total_pages)
        start_page = max(0, start_page)
        
        text_parts = []
        for i in range(start_page, end_page):
            page_text = reader.pages[i].extract_text() or ""
            text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
        
        return {
            "success": True,
            "pages_extracted": end_page - start_page,
            "text": "\n\n".join(text_parts),
        }
        
    except Exception as e:
        logger.error(f"Page extraction error: {e}")
        return {"error": str(e), "success": False}
