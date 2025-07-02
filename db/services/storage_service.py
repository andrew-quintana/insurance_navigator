"""
Storage service module for managing file storage operations with HIPAA compliance.
"""
from typing import Optional, Dict, Any, BinaryIO
from fastapi import Depends, HTTPException, status
from supabase import Client as SupabaseClient
import logging
import os
from datetime import datetime
from cryptography.fernet import Fernet
from config.database import get_supabase_client as get_base_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageService:
    """Service for managing file storage operations with HIPAA compliance."""

    def __init__(self, supabase_client: SupabaseClient):
        """Initialize the storage service."""
        self.supabase = supabase_client
        self.storage = supabase_client.storage
        self.audit_table = "audit_logs"
        self.encryption_key = os.getenv("DOCUMENT_ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("Document encryption key not configured")
        self.fernet = Fernet(self.encryption_key.encode())

    async def upload_file(self, bucket: str, file_path: str, file: BinaryIO, user_id: str) -> Optional[Dict[str, Any]]:
        """Upload an encrypted file to storage."""
        try:
            logger.info(f"Uploading encrypted file to {bucket}/{file_path}")
            
            # Read and encrypt file content
            file_content = file.read()
            encrypted_content = self.fernet.encrypt(file_content)
            
            # Upload encrypted file
            response = await self.storage.from_(bucket).upload(
                file_path,
                encrypted_content,
                file_options={
                    'content-type': 'application/octet-stream',
                    'x-upsert': 'true',
                    'x-encrypted': 'true'
                }
            )
            
            if response.error:
                logger.error(f"Error uploading file: {response.error}")
                return None
            
            # Create audit log entry
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "file_upload",
                "details": {
                    "bucket": bucket,
                    "file_path": file_path,
                    "timestamp": datetime.utcnow().isoformat(),
                    "encrypted": True
                },
                "success": True
            }).execute()
                
            return response.data
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None

    async def get_file_url(self, bucket: str, file_path: str, user_id: str) -> Optional[str]:
        """Get signed URL for an encrypted file."""
        try:
            logger.info(f"Getting signed URL for {bucket}/{file_path}")
            
            # Create signed URL with short expiration
            url = await self.storage.from_(bucket).create_signed_url(
                file_path,
                60,  # 60 seconds expiration
                {
                    'transform': {
                        'encryption': 'required'
                    }
                }
            )
            
            if not url:
                logger.error(f"No URL found for {bucket}/{file_path}")
                return None
            
            # Create audit log entry
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "file_access",
                "details": {
                    "bucket": bucket,
                    "file_path": file_path,
                    "timestamp": datetime.utcnow().isoformat(),
                    "access_type": "signed_url"
                },
                "success": True
            }).execute()
                
            return url
            
        except Exception as e:
            logger.error(f"Error getting file URL: {str(e)}")
            return None

    async def download_file(self, bucket: str, file_path: str, user_id: str) -> Optional[bytes]:
        """Download and decrypt a file."""
        try:
            logger.info(f"Downloading file from {bucket}/{file_path}")
            
            # Download encrypted file
            response = await self.storage.from_(bucket).download(file_path)
            
            if not response:
                logger.error(f"No file found at {bucket}/{file_path}")
                return None
            
            # Decrypt file content
            decrypted_content = self.fernet.decrypt(response)
            
            # Create audit log entry
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "file_download",
                "details": {
                    "bucket": bucket,
                    "file_path": file_path,
                    "timestamp": datetime.utcnow().isoformat(),
                    "decrypted": True
                },
                "success": True
            }).execute()
            
            return decrypted_content
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None

    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete a file from storage."""
        try:
            logger.info(f"Deleting file {bucket}/{file_path}")
            response = await self.storage.from_(bucket).remove([file_path])
            
            if response.error:
                logger.error(f"Error deleting file: {response.error}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False

async def get_storage_service() -> StorageService:
    """Get configured storage service instance."""
    try:
        client = await get_base_client()
        return StorageService(client)
    except Exception as e:
        logger.error(f"Error creating storage service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 