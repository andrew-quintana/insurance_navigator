"""
Document Helper for Phase 3 Testing

Provides utilities for creating and uploading test documents.
"""

import asyncio
import httpx
import logging
from typing import Dict, Any, Optional
import hashlib
import time

logger = logging.getLogger(__name__)

def create_test_document(filename: str = "test_document.pdf", content: str = "Test content") -> Dict[str, Any]:
    """Create a test document with realistic metadata."""
    content_bytes = content.encode('utf-8')
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    
    return {
        "filename": filename,
        "content": content,
        "bytes_len": len(content_bytes),
        "mime": "application/pdf" if filename.endswith('.pdf') else "text/plain",
        "sha256": content_hash,
        "ocr": False
    }

async def upload_test_document(
    document_data: Dict[str, Any], 
    auth_token: str, 
    base_url: str = "http://localhost:8000"
) -> Optional[Dict[str, Any]]:
    """Upload a test document using the upload pipeline."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            upload_payload = {
                "filename": document_data["filename"],
                "bytes_len": document_data["bytes_len"],
                "mime": document_data["mime"],
                "sha256": document_data["sha256"],
                "ocr": document_data.get("ocr", False)
            }
            
            response = await client.post(
                f"{base_url}/api/v2/upload",
                json=upload_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        return None

async def check_document_status(
    document_id: str, 
    auth_token: str, 
    base_url: str = "http://localhost:8000"
) -> Optional[Dict[str, Any]]:
    """Check the status of an uploaded document."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            response = await client.get(
                f"{base_url}/documents/{document_id}/status",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Document status check failed: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Document status check failed: {e}")
        return None
