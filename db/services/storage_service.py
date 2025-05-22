"""Storage service for policy documents."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from supabase import create_client, Client
from ..config import config
import os
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """Handles storage operations for policy documents."""

    def __init__(self, db_session):
        """Initialize the storage service.
        
        Args:
            db_session: Database session for storage operations
        """
        self.db = db_session
        self.base_path = "policies"
        self.supabase: Client = create_client(
            config.supabase.url,
            config.supabase.service_role_key
        )
        self.bucket_name = 'documents'
        self.signed_url_expiry = config.supabase.signed_url_expiry

    async def upload_policy_document(
        self,
        policy_id: uuid.UUID,
        file_data: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a policy document.
        
        Args:
            policy_id: UUID of the policy
            file_data: Raw file data
            filename: Original filename
            metadata: Optional metadata about the document
            
        Returns:
            Dict containing upload information
        """
        try:
            path = f"{self.base_path}/{policy_id}/raw/{filename}"
            
            # Store file metadata
            doc_metadata = {
                'filename': filename,
                'size': len(file_data),
                'uploaded_at': datetime.utcnow().isoformat(),
                'content_type': self._get_content_type(filename),
                **(metadata or {})
            }
            
            # In a real implementation, this would use cloud storage
            # For now, we'll just simulate storage
            await self.db.policy_documents.insert_one({
                'policy_id': str(policy_id),
                'path': path,
                'metadata': doc_metadata
            })
            
            logger.info(f"Uploaded document for policy {policy_id}: {path}")
            
            return {
                'path': path,
                'metadata': doc_metadata
            }
        except Exception as e:
            logger.error(f"Failed to upload document for policy {policy_id}: {str(e)}")
            raise RuntimeError(f"Upload failed: {str(e)}")

    async def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a signed URL for accessing a document.
        
        Args:
            path: Path to the document
            expires_in: URL expiration time in seconds
            
        Returns:
            Signed URL string
        """
        # In a real implementation, this would generate a signed URL
        # For now, we'll just return a dummy URL
        return f"https://storage.example.com/{path}?token=dummy"

    async def list_policy_documents(
        self,
        policy_id: uuid.UUID,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List documents for a policy.
        
        Args:
            policy_id: UUID of the policy
            document_type: Optional filter by document type
            
        Returns:
            List of document information
        """
        query = {'policy_id': str(policy_id)}
        if document_type:
            query['metadata.document_type'] = document_type
            
        documents = await self.db.policy_documents.find(query).to_list(None)
        return documents

    async def get_document_metadata(self, path: str) -> Dict[str, Any]:
        """Get metadata for a document.
        
        Args:
            path: Path to the document
            
        Returns:
            Document metadata
        """
        doc = await self.db.policy_documents.find_one({'path': path})
        if not doc:
            raise ValueError(f"Document not found: {path}")
        return doc['metadata']

    async def delete_document(self, path: str) -> bool:
        """Delete a document.
        
        Args:
            path: Path to the document
            
        Returns:
            True if deleted successfully
        """
        result = await self.db.policy_documents.delete_one({'path': path})
        return result.deleted_count > 0

    async def move_document(self, old_path: str, new_path: str) -> bool:
        """Move/rename a document.
        
        Args:
            old_path: Current path
            new_path: New path
            
        Returns:
            True if moved successfully
        """
        result = await self.db.policy_documents.update_one(
            {'path': old_path},
            {'$set': {'path': new_path}}
        )
        return result.modified_count > 0

    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension."""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        return content_types.get(ext, 'application/octet-stream')

    async def create_processed_version(
        self,
        policy_id: uuid.UUID,
        file_data: bytes,
        file_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a processed version of a policy document.
        Stores in policies/{policy_id}/processed/ directory.
        """
        path = f"policies/{policy_id}/processed/{file_name}"
        
        # Upload processed file
        response = await self.supabase.storage \
            .from_(self.bucket_name) \
            .upload(path, file_data)
        
        # Update metadata
        metadata_path = f"metadata/{policy_id}.json"
        current_metadata = await self.get_document_metadata(path)
        
        current_metadata['processed_version'] = {
            'path': path,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        await self.supabase.storage \
            .from_(self.bucket_name) \
            .upload(metadata_path, current_metadata)
        
        return {
            'path': path,
            'metadata': current_metadata
        } 