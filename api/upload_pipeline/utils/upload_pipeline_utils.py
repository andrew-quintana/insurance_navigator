"""
Utility functions for the upload pipeline.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_document_id() -> str:
    """Generate a unique document ID."""
    return str(uuid.uuid4())


def generate_storage_path(user_id: str, document_id: str, filename: str) -> str:
    """Generate a storage path for a document."""
    # Create a path like: uploads/{user_id}/{document_id}/{filename}
    return f"uploads/{user_id}/{document_id}/{filename}"


def log_event(
    event_type: str,
    user_id: str,
    document_id: str,
    job_id: str,
    stage: str,
    details: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """Log an event to the database."""
    # This is a placeholder - in a real implementation, this would log to the database
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "document_id": document_id,
        "job_id": job_id,
        "stage": stage,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {},
        "error": error
    }
    
    logger.info(f"Event logged: {log_data}")


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


def validate_file_size(bytes_len: int, max_size: int = 26214400) -> bool:
    """Validate file size (default max 25MB)."""
    return 0 < bytes_len <= max_size


def validate_mime_type(mime: str) -> bool:
    """Validate MIME type."""
    return mime == "application/pdf"
