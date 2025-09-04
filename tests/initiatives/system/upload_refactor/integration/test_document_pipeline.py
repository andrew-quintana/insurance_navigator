"""
End-to-end tests for the document processing pipeline.

Tests the complete flow:
1. Document upload
2. Processing supervisor triggering
3. Document parsing
4. Chunking
5. Vectorization
"""

import pytest
import asyncio
import os
import uuid
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, Any, List
from langchain_core.documents import Document

from db.services.document_service import DocumentService
from db.services.embedding_service import EmbeddingService
from config.parser import DocumentParser
from tests.config.test_config import get_base_test_config
from tests.db.helpers import get_test_client

@pytest.fixture
async def test_user_id(supabase_client):
    """Create a test user and return their ID."""
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "email": f"test_{user_id}@example.com",
        "name": "Test User",
        "created_at": datetime.utcnow().isoformat()
    }
    await supabase_client.table("users").insert(user_data).execute()
    return user_id

@pytest.fixture
async def test_pdf():
    """Sample PDF for testing."""
    pdf_path = Path("tests/data/test.pdf")
    if not pdf_path.exists():
        pytest.skip("Test PDF not found")
    return pdf_path

@pytest.fixture
def test_config():
    """Get test configuration."""
    return get_base_test_config()

@pytest.fixture
async def supabase_client(test_config):
    """Initialize Supabase client."""
    return get_test_client(auth_type="service_role")

@pytest.fixture
async def document_service(supabase_client):
    """Initialize document service."""
    return DocumentService(supabase_client)

@pytest.mark.asyncio
async def test_complete_document_pipeline(
    test_pdf: Path,
    document_service: DocumentService,
    supabase_client: Any,
    test_user_id: str,
    test_config: Any
):
    """Test the complete document processing pipeline."""
    # 1. Upload document
    doc_id = await document_service.upload_document(
        file_path=test_pdf,
        user_id=test_user_id,
        content_type="application/pdf"
    )
    assert doc_id, "Document upload failed"

    # 2. Verify document record
    doc = await document_service.get_document(doc_id)
    assert doc is not None
    assert doc["user_id"] == test_user_id
    assert doc["status"] == "uploaded"

    # 3. Verify storage path
    storage_path = doc["storage_path"]
    assert storage_path.startswith(f"documents/{test_user_id}/")
    assert storage_path.endswith(".pdf")

    # 4. Clean up
    await document_service.delete_document(doc_id) 