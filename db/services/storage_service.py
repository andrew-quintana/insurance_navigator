from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from supabase import create_client, Client
from ..config import config

class StorageService:
    def __init__(self):
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
        file_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a policy document to the storage bucket.
        Organizes files in the policies/{policy_id}/raw/ directory.
        """
        path = f"policies/{policy_id}/raw/{file_name}"
        
        # Upload file
        response = await self.supabase.storage \
            .from_(self.bucket_name) \
            .upload(path, file_data)
        
        # Store metadata
        metadata_path = f"metadata/{policy_id}.json"
        metadata_data = {
            'policy_id': str(policy_id),
            'file_name': file_name,
            'uploaded_at': datetime.now().isoformat(),
            'path': path,
            'type': 'policy',
            'metadata': metadata or {}
        }
        
        await self.supabase.storage \
            .from_(self.bucket_name) \
            .upload(metadata_path, metadata_data)
        
        return {
            'path': path,
            'metadata_path': metadata_path,
            'metadata': metadata_data
        }

    async def get_signed_url(
        self,
        path: str,
        expiry_seconds: Optional[int] = None
    ) -> str:
        """
        Generate a signed URL for accessing a document.
        """
        expiry = expiry_seconds or self.signed_url_expiry
        
        response = await self.supabase.storage \
            .from_(self.bucket_name) \
            .create_signed_url(path, expiry)
        
        return response['signedURL']

    async def list_policy_documents(
        self,
        policy_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        List all documents associated with a policy.
        """
        response = await self.supabase.storage \
            .from_(self.bucket_name) \
            .list(f"policies/{policy_id}")
        
        return response

    async def get_document_metadata(
        self,
        document_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Retrieve metadata for a document.
        """
        path = f"metadata/{document_id}.json"
        
        response = await self.supabase.storage \
            .from_(self.bucket_name) \
            .download(path)
        
        return response

    async def delete_document(
        self,
        path: str,
        delete_metadata: bool = True
    ) -> None:
        """
        Delete a document and optionally its metadata.
        """
        # Delete the document
        await self.supabase.storage \
            .from_(self.bucket_name) \
            .remove([path])
        
        # Delete metadata if requested
        if delete_metadata:
            metadata_path = f"metadata/{path.split('/')[-2]}.json"
            await self.supabase.storage \
                .from_(self.bucket_name) \
                .remove([metadata_path])

    async def move_document(
        self,
        source_path: str,
        destination_path: str,
        update_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Move a document to a new location and update its metadata.
        """
        # Copy to new location
        await self.supabase.storage \
            .from_(self.bucket_name) \
            .copy(source_path, destination_path)
        
        # Delete from old location
        await self.delete_document(source_path, delete_metadata=False)
        
        # Update metadata if requested
        if update_metadata:
            metadata_path = f"metadata/{source_path.split('/')[-2]}.json"
            metadata = await self.get_document_metadata(uuid.UUID(source_path.split('/')[-2]))
            metadata['path'] = destination_path
            metadata['updated_at'] = datetime.now().isoformat()
            
            await self.supabase.storage \
                .from_(self.bucket_name) \
                .upload(metadata_path, metadata)
        
        return {
            'new_path': destination_path,
            'metadata_updated': update_metadata
        }

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
        current_metadata = await self.get_document_metadata(policy_id)
        
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