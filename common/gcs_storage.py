"""
Google Cloud Storage utilities for document and asset storage.

Based on EcoLafaek S3/GCS storage patterns.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, BinaryIO
import base64

logger = logging.getLogger(__name__)

# Configuration
GCS_BUCKET = os.getenv("GCS_STORAGE_BUCKET", "loanguard-storage")
GCS_REGION = os.getenv("GCS_REGION", "us-central1")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Storage paths
DOCUMENTS_PATH = "documents"
CHARTS_PATH = "charts"
REPORTS_PATH = "reports"
MODELS_PATH = "models"


class GCSStorage:
    """
    Google Cloud Storage client for LoanGuard assets.
    """
    
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or GCS_BUCKET
        self._client = None
        self._bucket = None
    
    @property
    def client(self):
        """Lazy initialization of GCS client."""
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client(project=PROJECT_ID)
                self._bucket = self._client.bucket(self.bucket_name)
                logger.info(f"GCS client initialized for bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"GCS client initialization failed: {e}")
                self._client = False
        return self._client
    
    @property
    def available(self) -> bool:
        """Check if GCS is available."""
        return self.client is not None and self.client is not False
    
    def upload_document(
        self,
        loan_id: str,
        file_data: bytes,
        filename: str,
        content_type: str = "application/pdf",
    ) -> Dict[str, Any]:
        """
        Upload a loan document to GCS.
        
        Args:
            loan_id: Loan identifier
            file_data: File bytes
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Upload result with URL
        """
        document_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        gcs_path = f"{DOCUMENTS_PATH}/{loan_id}/{document_id}/{filename}"
        
        if not self.available:
            logger.warning("GCS not available, returning mock response")
            return {
                "success": False,
                "document_id": document_id,
                "error": "GCS not configured",
                "mock": True,
            }
        
        try:
            blob = self._bucket.blob(gcs_path)
            blob.upload_from_string(file_data, content_type=content_type)
            
            url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            logger.info(f"Document uploaded: {document_id} -> {gcs_path}")
            
            return {
                "success": True,
                "document_id": document_id,
                "loan_id": loan_id,
                "filename": filename,
                "gcs_path": gcs_path,
                "url": url,
                "size_bytes": len(file_data),
                "uploaded_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_chart(
        self,
        chart_data: bytes,
        chart_type: str = "png",
        loan_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a chart image to GCS.
        
        Args:
            chart_data: Image bytes
            chart_type: Image format (png, jpg, html)
            loan_id: Optional loan identifier
            
        Returns:
            Upload result with URL
        """
        chart_id = f"chart_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y%m%d")
        
        if loan_id:
            gcs_path = f"{CHARTS_PATH}/{loan_id}/{timestamp}/{chart_id}.{chart_type}"
        else:
            gcs_path = f"{CHARTS_PATH}/general/{timestamp}/{chart_id}.{chart_type}"
        
        content_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "html": "text/html",
            "svg": "image/svg+xml",
        }
        content_type = content_types.get(chart_type, "application/octet-stream")
        
        if not self.available:
            return {
                "success": False,
                "chart_id": chart_id,
                "error": "GCS not configured",
                "mock": True,
            }
        
        try:
            blob = self._bucket.blob(gcs_path)
            blob.upload_from_string(chart_data, content_type=content_type)
            
            url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            return {
                "success": True,
                "chart_id": chart_id,
                "gcs_path": gcs_path,
                "url": url,
                "format": chart_type,
            }
        except Exception as e:
            logger.error(f"Chart upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_report(
        self,
        loan_id: str,
        report_data: bytes,
        report_type: str = "compliance",
        format: str = "pdf",
    ) -> Dict[str, Any]:
        """
        Upload a generated report to GCS.
        
        Args:
            loan_id: Loan identifier
            report_data: Report bytes
            report_type: Type of report
            format: File format
            
        Returns:
            Upload result with URL
        """
        report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.{format}"
        gcs_path = f"{REPORTS_PATH}/{loan_id}/{report_id}/{filename}"
        
        content_types = {
            "pdf": "application/pdf",
            "html": "text/html",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "json": "application/json",
        }
        content_type = content_types.get(format, "application/octet-stream")
        
        if not self.available:
            return {
                "success": False,
                "report_id": report_id,
                "error": "GCS not configured",
                "mock": True,
            }
        
        try:
            blob = self._bucket.blob(gcs_path)
            blob.upload_from_string(report_data, content_type=content_type)
            
            url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            return {
                "success": True,
                "report_id": report_id,
                "loan_id": loan_id,
                "report_type": report_type,
                "gcs_path": gcs_path,
                "url": url,
                "generated_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Report upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    def download_document(self, gcs_path: str) -> Optional[bytes]:
        """
        Download a document from GCS.
        
        Args:
            gcs_path: GCS path to document
            
        Returns:
            Document bytes or None
        """
        if not self.available:
            return None
        
        try:
            blob = self._bucket.blob(gcs_path)
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"Document download failed: {e}")
            return None
    
    def list_documents(self, loan_id: str) -> list:
        """
        List all documents for a loan.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            List of document metadata
        """
        if not self.available:
            return []
        
        try:
            prefix = f"{DOCUMENTS_PATH}/{loan_id}/"
            blobs = self._bucket.list_blobs(prefix=prefix)
            
            documents = []
            for blob in blobs:
                documents.append({
                    "name": blob.name,
                    "size": blob.size,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "url": f"https://storage.googleapis.com/{self.bucket_name}/{blob.name}",
                })
            
            return documents
        except Exception as e:
            logger.error(f"List documents failed: {e}")
            return []
    
    def delete_document(self, gcs_path: str) -> bool:
        """
        Delete a document from GCS.
        
        Args:
            gcs_path: GCS path to document
            
        Returns:
            Success status
        """
        if not self.available:
            return False
        
        try:
            blob = self._bucket.blob(gcs_path)
            blob.delete()
            logger.info(f"Document deleted: {gcs_path}")
            return True
        except Exception as e:
            logger.error(f"Document delete failed: {e}")
            return False


# Global storage instance
_storage: Optional[GCSStorage] = None


def get_storage() -> GCSStorage:
    """Get or create the global storage instance."""
    global _storage
    if _storage is None:
        _storage = GCSStorage()
    return _storage
