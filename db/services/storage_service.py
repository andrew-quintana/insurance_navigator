"""
Supabase Storage service for policy documents and file management.
Provides secure file upload, download, and access control with Supabase Storage.
"""

import asyncio
import os
import logging
import mimetypes
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import json

from supabase import create_client, Client
from .db_pool import get_db_pool
from ..config import config

logger = logging.getLogger(__name__)

class StorageService:
    """Handles storage operations for policy documents with Supabase Storage."""

    def __init__(self):
        """Initialize the storage service with Supabase client."""
        self.supabase_url = config.supabase.url
        self.supabase_service_key = config.supabase.service_role_key
        self.bucket_name = config.supabase.storage_bucket or 'documents'
        self.signed_url_expiry = config.supabase.signed_url_expiry or 3600
        self.max_file_size = getattr(config.supabase, 'max_file_size_mb', 10) * 1024 * 1024  # Convert MB to bytes
        
        # Initialize Supabase client
        self.supabase: Client = create_client(
            self.supabase_url,
            self.supabase_service_key
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure the storage bucket exists."""
        try:
            # Check if bucket exists, create if not
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if self.bucket_name not in bucket_names:
                logger.info(f"Creating storage bucket: {self.bucket_name}")
                self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={"public": False}  # Private bucket for security
                )
                logger.info(f"Created storage bucket: {self.bucket_name}")
            else:
                logger.info(f"Storage bucket exists: {self.bucket_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            # Don't raise - allow service to work with existing bucket

    async def upload_policy_document(
        self,
        policy_id: str,
        file_data: bytes,
        filename: str,
        user_id: str,
        document_type: str = "policy",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a policy document to Supabase Storage.
        
        Args:
            policy_id: UUID of the policy
            file_data: Raw file data
            filename: Original filename
            user_id: ID of user uploading the file
            document_type: Type of document (policy, claim, etc.)
            metadata: Optional metadata about the document
            
        Returns:
            Dict containing upload information including file path and metadata
            
        Raises:
            ValueError: If file is too large or invalid
            RuntimeError: If upload fails
        """
        try:
            # Validate file size
            if len(file_data) > self.max_file_size:
                raise ValueError(f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB")
            
            # Generate secure file path
            file_extension = Path(filename).suffix.lower()
            secure_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = f"{document_type}/{policy_id}/{secure_filename}"
            
            # Detect content type
            content_type = self._get_content_type(filename)
            
            # Upload to Supabase Storage
            upload_response = self.supabase.storage.from_(self.bucket_name).upload(
                file_path,
                file_data,
                file_options={
                    "content-type": content_type,
                    "x-upsert": "true"  # Allow overwrite
                }
            )
            
            # Check if upload was successful (Supabase returns different response format)
            if hasattr(upload_response, 'error') and upload_response.error:
                raise RuntimeError(f"Upload failed: {upload_response.error}")
            elif hasattr(upload_response, 'data') and not upload_response.data:
                raise RuntimeError("Upload failed: No data returned")
            elif isinstance(upload_response, dict) and 'error' in upload_response:
                raise RuntimeError(f"Upload failed: {upload_response['error']}")
            
            logger.info(f"File uploaded successfully to: {file_path}")
            
            # Store metadata in database
            pool = await get_db_pool()
            
            doc_metadata = {
                'original_filename': filename,
                'file_path': file_path,
                'content_type': content_type,
                'file_size': len(file_data),
                'document_type': document_type,
                'uploaded_by': user_id,
                'uploaded_at': datetime.utcnow().isoformat(),
                'policy_id': policy_id,
                **(metadata or {})
            }
            
            async with pool.get_connection() as conn:
                # Create documents table if it doesn't exist
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS policy_documents (
                        id SERIAL PRIMARY KEY,
                        policy_id TEXT NOT NULL,
                        file_path TEXT NOT NULL UNIQUE,
                        original_filename TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        document_type TEXT NOT NULL,
                        uploaded_by TEXT NOT NULL,
                        uploaded_at TIMESTAMPTZ DEFAULT NOW(),
                        metadata JSONB DEFAULT '{}'::jsonb,
                        is_active BOOLEAN DEFAULT true
                    )
                """)
                
                # Create index if not exists
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_policy_documents_policy_id 
                    ON policy_documents(policy_id)
                """)
                
                # Insert document record
                document_id = await conn.fetchval("""
                    INSERT INTO policy_documents 
                    (policy_id, file_path, original_filename, content_type, file_size, 
                     document_type, uploaded_by, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """, policy_id, file_path, filename, content_type, len(file_data),
                document_type, user_id, json.dumps(doc_metadata))
            
            logger.info(f"Uploaded document {filename} for policy {policy_id}: {file_path}")
            
            return {
                'document_id': document_id,
                'file_path': file_path,
                'original_filename': filename,
                'content_type': content_type,
                'file_size': len(file_data),
                'uploaded_at': doc_metadata['uploaded_at'],
                'metadata': doc_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload document {filename} for policy {policy_id}: {str(e)}")
            raise RuntimeError(f"Upload failed: {str(e)}")

    async def get_signed_url(
        self, 
        file_path: str, 
        expires_in: Optional[int] = None,
        download: bool = False
    ) -> str:
        """
        Get a signed URL for accessing a document.
        
        Args:
            file_path: Path to the document in storage
            expires_in: URL expiration time in seconds (default: from config)
            download: Whether URL should force download
            
        Returns:
            Signed URL string
            
        Raises:
            ValueError: If file not found
            RuntimeError: If URL generation fails
        """
        try:
            expires_in = expires_in or self.signed_url_expiry
            
            # Verify file exists in database
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                doc_exists = await conn.fetchval(
                    "SELECT 1 FROM policy_documents WHERE file_path = $1 AND is_active = true",
                    file_path
                )
                
                if not doc_exists:
                    raise ValueError(f"Document not found: {file_path}")
            
            # Generate signed URL
            signed_url_response = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in,
                options={"download": download}
            )
            
            if 'error' in signed_url_response:
                raise RuntimeError(f"Failed to generate signed URL: {signed_url_response['error']}")
            
            signed_url = signed_url_response['signedURL']
            logger.info(f"Generated signed URL for {file_path} (expires in {expires_in}s)")
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {file_path}: {str(e)}")
            raise

    async def list_policy_documents(
        self,
        policy_id: str,
        document_type: Optional[str] = None,
        user_id: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List documents for a policy with optional filtering.
        
        Args:
            policy_id: UUID of the policy
            document_type: Optional filter by document type
            user_id: Optional filter by user who uploaded
            include_inactive: Whether to include deleted/inactive documents
            
        Returns:
            List of document information
        """
        try:
            pool = await get_db_pool()
            
            # Build query with filters
            conditions = ["policy_id = $1"]
            params = [policy_id]
            param_count = 1
            
            if document_type:
                param_count += 1
                conditions.append(f"document_type = ${param_count}")
                params.append(document_type)
            
            if user_id:
                param_count += 1
                conditions.append(f"uploaded_by = ${param_count}")
                params.append(user_id)
            
            if not include_inactive:
                conditions.append("is_active = true")
            
            query = f"""
                SELECT id, policy_id, file_path, original_filename, content_type, 
                       file_size, document_type, uploaded_by, uploaded_at, metadata
                FROM policy_documents 
                WHERE {' AND '.join(conditions)}
                ORDER BY uploaded_at DESC
            """
            
            async with pool.get_connection() as conn:
                rows = await conn.fetch(query, *params)
                
                documents = []
                for row in rows:
                    doc = {
                        'id': row['id'],
                        'policy_id': row['policy_id'],
                        'file_path': row['file_path'],
                        'original_filename': row['original_filename'],
                        'content_type': row['content_type'],
                        'file_size': row['file_size'],
                        'document_type': row['document_type'],
                        'uploaded_by': row['uploaded_by'],
                        'uploaded_at': row['uploaded_at'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                    }
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Failed to list documents for policy {policy_id}: {str(e)}")
            raise RuntimeError(f"Failed to list documents: {str(e)}")

    async def get_document_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Document metadata
            
        Raises:
            ValueError: If document not found
        """
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT id, policy_id, original_filename, content_type, file_size,
                           document_type, uploaded_by, uploaded_at, metadata
                    FROM policy_documents 
                    WHERE file_path = $1 AND is_active = true
                """, file_path)
                
                if not row:
                    raise ValueError(f"Document not found: {file_path}")
                
                return {
                    'id': row['id'],
                    'policy_id': row['policy_id'],
                    'file_path': file_path,
                    'original_filename': row['original_filename'],
                    'content_type': row['content_type'],
                    'file_size': row['file_size'],
                    'document_type': row['document_type'],
                    'uploaded_by': row['uploaded_by'],
                    'uploaded_at': row['uploaded_at'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {str(e)}")
            raise

    async def delete_document(self, file_path: str, user_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a document (soft delete by default).
        
        Args:
            file_path: Path to the document
            user_id: ID of user requesting deletion
            hard_delete: Whether to permanently delete from storage
            
        Returns:
            True if deleted successfully
        """
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                if hard_delete:
                    # Delete from Supabase Storage
                    delete_response = self.supabase.storage.from_(self.bucket_name).remove([file_path])
                    
                    if 'error' in delete_response:
                        logger.error(f"Failed to delete from storage: {delete_response['error']}")
                    
                    # Delete from database
                    result = await conn.execute(
                        "DELETE FROM policy_documents WHERE file_path = $1",
                        file_path
                    )
                else:
                    # Soft delete - mark as inactive
                    result = await conn.execute("""
                        UPDATE policy_documents 
                        SET is_active = false, 
                            metadata = metadata || $2
                        WHERE file_path = $1
                    """, file_path, json.dumps({"deleted_by": user_id, "deleted_at": datetime.utcnow().isoformat()}))
                
                success = "DELETE" in result or "UPDATE" in result
                if success:
                    logger.info(f"{'Hard' if hard_delete else 'Soft'} deleted document: {file_path}")
                
                return success
                
        except Exception as e:
            logger.error(f"Failed to delete document {file_path}: {str(e)}")
            return False

    async def download_document(self, file_path: str) -> bytes:
        """
        Download document content.
        
        Args:
            file_path: Path to the document
            
        Returns:
            File content as bytes
            
        Raises:
            ValueError: If document not found
            RuntimeError: If download fails
        """
        try:
            # Verify file exists in database
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                doc_exists = await conn.fetchval(
                    "SELECT 1 FROM policy_documents WHERE file_path = $1 AND is_active = true",
                    file_path
                )
                
                if not doc_exists:
                    raise ValueError(f"Document not found: {file_path}")
            
            # Download from Supabase Storage
            download_response = self.supabase.storage.from_(self.bucket_name).download(file_path)
            
            if isinstance(download_response, dict) and 'error' in download_response:
                raise RuntimeError(f"Download failed: {download_response['error']}")
            
            logger.info(f"Downloaded document: {file_path}")
            return download_response
            
        except Exception as e:
            logger.error(f"Failed to download document {file_path}: {str(e)}")
            raise

    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension."""
        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type
        
        # Fallback for common file types
        ext = Path(filename).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.csv': 'text/csv'
        }
        
        return content_types.get(ext, 'application/octet-stream')

    async def get_file_access_permissions(self, file_path: str, user_id: str) -> Dict[str, bool]:
        """
        Check file access permissions for a user.
        
        Args:
            file_path: Path to the document
            user_id: ID of user requesting access
            
        Returns:
            Dict with permission flags (read, write, delete)
        """
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                # Get document and user info
                doc_info = await conn.fetchrow("""
                    SELECT uploaded_by, policy_id, document_type 
                    FROM policy_documents 
                    WHERE file_path = $1 AND is_active = true
                """, file_path)
                
                if not doc_info:
                    return {"read": False, "write": False, "delete": False}
                
                # Get user roles
                user_roles = await conn.fetch("""
                    SELECT r.name 
                    FROM roles r 
                    JOIN user_roles ur ON r.id = ur.role_id 
                    WHERE ur.user_id = $1::uuid
                """, user_id)
                
                role_names = [role['name'] for role in user_roles]
                
                # Permission logic
                permissions = {
                    "read": False,
                    "write": False,
                    "delete": False
                }
                
                # Owner has all permissions
                if doc_info['uploaded_by'] == user_id:
                    permissions = {"read": True, "write": True, "delete": True}
                # Admin has all permissions
                elif 'admin' in role_names:
                    permissions = {"read": True, "write": True, "delete": True}
                # Regular users can read
                elif 'user' in role_names:
                    permissions["read"] = True
                
                return permissions
                
        except Exception as e:
            logger.error(f"Failed to get permissions for {file_path}: {str(e)}")
            return {"read": False, "write": False, "delete": False}


# Global storage service instance
storage_service = None

async def get_storage_service() -> StorageService:
    """Get the global storage service instance."""
    global storage_service
    if storage_service is None:
        storage_service = StorageService()
    return storage_service 