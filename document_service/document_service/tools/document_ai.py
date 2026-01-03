"""
Google Document AI integration for advanced document processing.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from document_service.document_service.config import (
    PROJECT_ID,
    LOCATION,
    DOCUMENT_AI_PROCESSOR_ID,
)

logger = logging.getLogger(__name__)


def process_with_document_ai(
    file_path: str,
    processor_type: str = "FORM_PARSER_PROCESSOR",
) -> Dict[str, Any]:
    """
    Process a document using Google Document AI.

    Args:
        file_path: Path to the document file
        processor_type: Type of Document AI processor to use

    Returns:
        Dictionary containing processed document data
    """
    if not PROJECT_ID or not DOCUMENT_AI_PROCESSOR_ID:
        logger.warning("Document AI not configured, falling back to basic parsing")
        return {
            "success": False,
            "error": "Document AI not configured",
            "fallback": True,
        }

    try:
        from google.cloud import documentai_v1 as documentai
    except ImportError:
        logger.error("google-cloud-documentai not installed")
        return {"error": "google-cloud-documentai not installed", "success": False}

    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}", "success": False}

        # Read the file
        with open(path, "rb") as f:
            content = f.read()

        # Determine MIME type
        mime_type = _get_mime_type(path.suffix)

        # Create Document AI client
        client = documentai.DocumentProcessorServiceClient()

        # Build processor name
        processor_name = (
            f"projects/{PROJECT_ID}/locations/{LOCATION}"
            f"/processors/{DOCUMENT_AI_PROCESSOR_ID}"
        )

        # Create request
        raw_document = documentai.RawDocument(content=content, mime_type=mime_type)
        request = documentai.ProcessRequest(
            name=processor_name,
            raw_document=raw_document,
        )

        # Process document
        result = client.process_document(request=request)
        document = result.document

        # Extract structured data
        extracted_data = {
            "success": True,
            "text": document.text,
            "pages": [],
            "entities": [],
            "tables": [],
        }

        # Process pages
        for page in document.pages:
            page_info = {
                "page_number": page.page_number,
                "width": page.dimension.width if page.dimension else 0,
                "height": page.dimension.height if page.dimension else 0,
                "paragraphs": [],
                "tables": [],
            }

            # Extract paragraphs
            for paragraph in page.paragraphs:
                para_text = _get_text_from_layout(paragraph.layout, document.text)
                if para_text.strip():
                    page_info["paragraphs"].append(para_text)

            # Extract tables
            for table in page.tables:
                table_data = _extract_table(table, document.text)
                if table_data:
                    page_info["tables"].append(table_data)
                    extracted_data["tables"].append(table_data)

            extracted_data["pages"].append(page_info)

        # Extract entities if available
        for entity in document.entities:
            entity_info = {
                "type": entity.type_,
                "mention_text": entity.mention_text,
                "confidence": entity.confidence,
            }
            extracted_data["entities"].append(entity_info)

        logger.info(
            f"Document AI processed: {len(extracted_data['pages'])} pages, "
            f"{len(extracted_data['entities'])} entities, "
            f"{len(extracted_data['tables'])} tables"
        )

        return extracted_data

    except Exception as e:
        logger.error(f"Document AI processing error: {e}")
        return {"error": str(e), "success": False}


def _get_mime_type(suffix: str) -> str:
    """Get MIME type from file extension."""
    mime_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    return mime_types.get(suffix.lower(), "application/pdf")


def _get_text_from_layout(layout, full_text: str) -> str:
    """Extract text from a Document AI layout element."""
    if not layout.text_anchor or not layout.text_anchor.text_segments:
        return ""
    
    text_parts = []
    for segment in layout.text_anchor.text_segments:
        start = int(segment.start_index) if segment.start_index else 0
        end = int(segment.end_index) if segment.end_index else len(full_text)
        text_parts.append(full_text[start:end])
    
    return "".join(text_parts)


def _extract_table(table, full_text: str) -> Optional[Dict[str, Any]]:
    """Extract table data from Document AI table object."""
    try:
        rows = []
        
        for row in table.body_rows:
            cells = []
            for cell in row.cells:
                cell_text = _get_text_from_layout(cell.layout, full_text)
                cells.append(cell_text.strip())
            rows.append(cells)

        header_row = []
        if table.header_rows:
            for cell in table.header_rows[0].cells:
                cell_text = _get_text_from_layout(cell.layout, full_text)
                header_row.append(cell_text.strip())

        return {
            "headers": header_row,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(header_row) if header_row else (len(rows[0]) if rows else 0),
        }
        
    except Exception as e:
        logger.error(f"Table extraction error: {e}")
        return None
