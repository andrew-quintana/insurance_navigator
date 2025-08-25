"""
Mock Storage Service for Local Testing

This module provides a mock storage service that can handle storage:// paths
and serve test content for local development and testing.
"""

import os
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

class MockStorageManager:
    """Mock storage manager for local testing"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.storage_root = Path("mock_storage")
        self.storage_root.mkdir(exist_ok=True)
        
        # Initialize with some test content
        self._initialize_test_content()
    
    def _initialize_test_content(self):
        """Initialize mock storage with test content"""
        # Create test document content
        test_content = """# Test Insurance Document

This is a test document for validating the complete processing pipeline.

## Section 1: Introduction
This section contains introductory content that should be chunked appropriately.

## Section 2: Details  
Additional content to ensure multiple chunks are generated for embedding testing.

## Section 3: Conclusion
Final section to complete the document structure.

Processing timestamp: 2025-08-25
"""
        
        # Create the test file path
        test_file_path = self.storage_root / "documents" / "123e4567-e89b-12d3-a456-426614174000" / "25db3010-f65f-4594-b5da-401b5c1c4606.md"
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write test content
        with open(test_file_path, 'w') as f:
            f.write(test_content)
    
    def _parse_storage_path(self, path: str) -> tuple[str, str]:
        """Parse storage path to extract bucket and key"""
        # Expected format: storage://{bucket}/{user_id}/{document_id}.{ext}
        if not path.startswith("storage://"):
            raise ValueError(f"Invalid storage path format: {path}")
        
        # Remove storage:// prefix
        path_without_prefix = path[10:]
        
        # Split by first slash to get bucket
        parts = path_without_prefix.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid storage path format: {path}")
        
        bucket, key = parts
        return bucket, key
    
    async def read_blob(self, path: str) -> Optional[str]:
        """Read blob content from mock storage"""
        try:
            bucket, key = self._parse_storage_path(path)
            
            # Convert to local file path
            local_path = self.storage_root / bucket / key
            
            if not local_path.exists():
                print(f"Mock storage: File not found: {local_path}")
                return None
            
            # Read content
            with open(local_path, 'r') as f:
                content = f.read()
            
            print(f"Mock storage: Read {len(content)} bytes from {path}")
            return content
            
        except Exception as e:
            print(f"Mock storage: Failed to read blob {path}: {e}")
            return None
    
    async def write_blob(self, path: str, content: str, content_type: str = "text/plain") -> bool:
        """Write blob content to mock storage"""
        try:
            bucket, key = self._parse_storage_path(path)
            
            # Convert to local file path
            local_path = self.storage_root / bucket / key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(local_path, 'w') as f:
                f.write(content)
            
            print(f"Mock storage: Wrote {len(content)} bytes to {path}")
            return True
            
        except Exception as e:
            print(f"Mock storage: Failed to write blob {path}: {e}")
            return False
    
    async def delete_blob(self, path: str) -> bool:
        """Delete blob from mock storage"""
        try:
            bucket, key = self._parse_storage_path(path)
            
            # Convert to local file path
            local_path = self.storage_root / bucket / key
            
            if local_path.exists():
                local_path.unlink()
                print(f"Mock storage: Deleted {path}")
            
            return True
            
        except Exception as e:
            print(f"Mock storage: Failed to delete blob {path}: {e}")
            return False
    
    async def blob_exists(self, path: str) -> bool:
        """Check if blob exists in mock storage"""
        try:
            bucket, key = self._parse_storage_path(path)
            
            # Convert to local file path
            local_path = self.storage_root / bucket / key
            
            exists = local_path.exists()
            print(f"Mock storage: Blob {path} exists: {exists}")
            return exists
            
        except Exception as e:
            print(f"Mock storage: Failed to check blob existence {path}: {e}")
            return False
    
    async def get_blob_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get blob metadata from mock storage"""
        try:
            bucket, key = self._parse_storage_path(path)
            
            # Convert to local file path
            local_path = self.storage_root / bucket / key
            
            if not local_path.exists():
                return None
            
            # Get file stats
            stat = local_path.stat()
            
            metadata = {
                "size": stat.st_size,
                "content_type": "text/markdown" if path.endswith('.md') else "application/octet-stream",
                "last_modified": stat.st_mtime,
                "etag": str(stat.st_mtime)
            }
            
            print(f"Mock storage: Retrieved metadata for {path}: {metadata}")
            return metadata
            
        except Exception as e:
            print(f"Mock storage: Failed to get blob metadata {path}: {e}")
            return None
