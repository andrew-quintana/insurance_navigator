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
        self.bucket_name = config.supabase.storage_bucket or 'raw_documents'
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

    async def upload_document(
        self,
        file_data: bytes,
        filename: str,
        user_id: str,
        document_type: str = "policy",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a document and process it for vector storage."""
        try:
            # TODO: Add duplicate document handling logic after MVP
            # - Check for existing documents by storage path or file hash
            # - Return existing document info if found
            # - Handle "Duplicate" errors from Supabase storage
            # - Consider user preferences for duplicate handling
            
            # Calculate file hash and path
            file_hash = self._calculate_file_hash(file_data)
            file_path = f"{document_type}/{user_id}/{file_hash}/{filename}"
            content_type = self._get_content_type(filename)
            
            # Upload to Supabase Storage - force upload for MVP
            try:
                # Note: upload() returns a Response object that we shouldn't await
                # The upload is complete when the method returns
                self.supabase.storage.from_(self.bucket_name).upload(
                    file_path,
                    file_data,
                    {
                        "content-type": content_type,
                        "x-upsert": "true"  # Use string "true" instead of boolean True
                    }
                )
                logger.info(f"Successfully uploaded file to storage: {file_path}")
            except Exception as e:
                logger.error(f"Storage upload failed for {file_path}: {str(e)}")
                raise RuntimeError(f"Storage upload failed: {str(e)}")
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Insert document record
                document_id = await conn.fetchval("""
                    INSERT INTO documents 
                    (user_id, original_filename, file_size, content_type, file_hash,
                     storage_path, status, document_type, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """, 
                uuid.UUID(user_id), filename, len(file_data), content_type,
                file_hash, file_path, 'processing',
                document_type, json.dumps(metadata or {}))
            
            # Extract text content for vector processing
            try:
                extracted_text = await self._extract_text_content(file_data, filename)
                
                if extracted_text:
                    # Process vectors in background
                    asyncio.create_task(
                        self._process_document_vectors(
                            str(document_id),
                            user_id,
                            extracted_text,
                            document_type
                        )
                    )
                
                # Use document service for policy basics extraction
                if document_type == 'policy':
                    from .document_service import get_document_service
                    doc_service = await get_document_service()
                    asyncio.create_task(
                        doc_service.extract_policy_basics(str(document_id), extracted_text)
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to process document {document_id}: {e}")
                # Don't fail the upload for processing errors
            
            logger.info(f"Uploaded document {filename} for user {user_id}: {file_path}")
            
            return {
                'document_id': str(document_id),
                'file_path': file_path,
                'original_filename': filename,
                'content_type': content_type,
                'file_size': len(file_data),
                'uploaded_at': datetime.utcnow().isoformat(),
                'status': 'processing',
                'policy_extraction_status': 'processing' if document_type == 'policy' else 'n/a'
            }
            
        except Exception as e:
            logger.error(f"Failed to upload document {filename} for user {user_id}: {str(e)}")
            raise RuntimeError(f"Upload failed: {str(e)}")
    
    async def _process_document_vectors(
        self,
        document_id: str,
        user_id: str,
        text: str,
        document_type: str
    ) -> None:
        """Process document text into vectors."""
        try:
            # Split into chunks
            chunks = self._chunk_text(text)
            
            # Get embedding service
            from .encryption_aware_embedding_service import get_encryption_aware_embedding_service
            embedding_service = await get_encryption_aware_embedding_service()
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                try:
                    # Generate and encrypt vector
                    vector_data = await embedding_service.process_chunk(chunk)
                    
                    # Store vector
                    pool = await get_db_pool()
                    async with pool.get_connection() as conn:
                        await conn.execute("""
                            INSERT INTO document_vectors (
                                user_id, document_record_id, document_source_type,
                                chunk_index, content_embedding, encrypted_chunk_text,
                                encrypted_chunk_metadata, encryption_key_id
                            ) VALUES (
                                $1::uuid, $2::uuid, $3::text,
                                $4::integer, $5::float[], $6::bytea,
                                $7::jsonb, $8::text
                            )
                        """,
                        uuid.UUID(user_id), uuid.UUID(document_id), document_type,
                        i, vector_data['embedding'], vector_data['encrypted_text'],
                        vector_data['encrypted_metadata'], vector_data['key_id'])
                        
                except Exception as e:
                    logger.error(f"Failed to process chunk {i} for document {document_id}: {e}")
                    continue
            
            # Update document status
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                await conn.execute("""
                    UPDATE documents 
                    SET status = 'completed',
                        updated_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(document_id))
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process vectors for document {document_id}: {error_msg}")
            # Update document status to failed and store error in metadata
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                await conn.execute("""
                    UPDATE documents 
                    SET status = 'failed',
                        metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('error_message', $2, 'error_timestamp', NOW()::text),
                        updated_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(document_id), error_msg)

    def _chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 100) -> List[str]:
        """Split text into chunks with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                # Find next sentence boundary
                next_period = text.find('.', end)
                if next_period != -1 and next_period - end < 100:
                    end = next_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
        return chunks
    
    def _calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA256 hash of file data."""
        import hashlib
        return hashlib.sha256(file_data).hexdigest()

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
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List documents for a specific policy using the new vector storage.
        
        Args:
            policy_id: Policy ID to filter by
            user_id: Optional user ID for filtering
            
        Returns:
            List of policy documents with metadata
        """
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Query the new policy_content_vectors table
                where_conditions = ["policy_id = $1", "is_active = true"]
                params = [policy_id]
                
                if user_id:
                    where_conditions.append("user_id = $2")
                    params.append(user_id)
                
                sql = f"""
                    SELECT 
                        id,
                        policy_id,
                        user_id,
                        content_text,
                        policy_metadata,
                        document_metadata,
                        created_at,
                        updated_at
                    FROM policy_content_vectors
                    WHERE {' AND '.join(where_conditions)}
                    ORDER BY created_at DESC
                """
                
                rows = await conn.fetch(sql, *params)
                
                documents = []
                for row in rows:
                    # Handle JSONB fields properly
                    policy_metadata = row['policy_metadata'] if isinstance(row['policy_metadata'], dict) else {}
                    document_metadata = row['document_metadata'] if isinstance(row['document_metadata'], dict) else {}
                    
                    documents.append({
                        'id': str(row['id']),
                        'policy_id': str(row['policy_id']),
                        'user_id': str(row['user_id']),
                        'content_text': row['content_text'],
                        'policy_metadata': policy_metadata,
                        'document_metadata': document_metadata,
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'file_path': document_metadata.get('file_path', ''),
                        'file_size': document_metadata.get('file_size', 0),
                        'file_type': document_metadata.get('file_type', 'unknown')
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Error listing policy documents: {str(e)}")
            return []

    async def get_document_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get document metadata from vector storage.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Document metadata dictionary
        """
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT document_metadata, policy_metadata
                    FROM policy_content_vectors 
                    WHERE document_metadata->>'file_path' = $1 AND is_active = true
                    LIMIT 1
                """, file_path)
                
                if row:
                    metadata = dict(row['document_metadata'])
                    metadata.update(dict(row['policy_metadata']))
                    return metadata
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting document metadata: {str(e)}")
            return {}

    async def document_exists(self, file_path: str) -> bool:
        """
        Check if a document exists in storage.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if document exists, False otherwise
            
        Note:
            TODO: Enhance duplicate detection after MVP
            - Check both storage and database
            - Consider file hash matching
            - Add user preferences for duplicate handling
        """
        try:
            # For MVP, just check if file exists in database
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                exists = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM documents 
                        WHERE storage_path = $1
                    )
                """, file_path)
                return bool(exists)
        except Exception as e:
            logger.error(f"Error checking document existence: {str(e)}")
            return False

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

    async def upload_policy_document_with_vectors(
        self,
        policy_id: str,
        file_data: bytes,
        filename: str,
        user_id: str,
        document_type: str = "policy",
        policy_metadata: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload policy document and automatically generate vectors.
        Combines file storage with vector generation.
        
        Args:
            policy_id: UUID of the policy
            file_data: Raw file data
            filename: Original filename
            user_id: ID of user uploading the file
            document_type: Type of document
            policy_metadata: Policy-specific metadata for vector storage
            metadata: Optional metadata about the document
            
        Returns:
            Dict containing upload information including vector processing status
        """
        try:
            # First, upload to storage (existing functionality)
            upload_result = await self.upload_document(
                file_data, filename, user_id, document_type, metadata
            )
            
            # Parse document content
            content_text = await self._extract_text_content(file_data, filename)
            
            if content_text and content_text.strip():
                # Generate vectors
                from db.services.encryption_aware_embedding_service import get_encryption_aware_embedding_service
                embedding_service = await get_encryption_aware_embedding_service()
                
                # Determine if this is a policy document or user document
                if document_type in ['policy', 'policy_summary', 'benefits_detail', 'claims_history']:
                    # Store as policy content vector
                    vector_id = await embedding_service.process_policy_document(
                        policy_id=policy_id,
                        user_id=user_id,
                        content_text=content_text,
                        policy_metadata=policy_metadata or {},
                        document_metadata={
                            **upload_result,
                            "document_type": document_type,
                            "processing_method": "automatic_upload",
                            "content_extracted": True
                        }
                    )
                    upload_result['vector_storage_type'] = 'policy_content'
                else:
                    # Store as user document vector
                    document_id = upload_result['document_id']
                    vector_ids = await embedding_service.process_user_document(
                        user_id=user_id,
                        document_id=str(document_id),
                        content_text=content_text,
                        document_metadata={
                            **upload_result,
                            "document_type": document_type,
                            "processing_method": "automatic_upload",
                            "content_extracted": True
                        }
                    )
                    vector_id = vector_ids[0] if vector_ids else None
                    upload_result['vector_storage_type'] = 'user_document'
                    upload_result['vector_chunk_count'] = len(vector_ids) if vector_ids else 0
                
                upload_result['vector_id'] = vector_id
                upload_result['content_processed'] = True
                logger.info(f"Successfully processed vectors for document {filename}: {vector_id}")
            else:
                upload_result['content_processed'] = False
                upload_result['vector_id'] = None
                logger.warning(f"Could not extract content from {filename} for vector processing")
            
            return upload_result
            
        except Exception as e:
            logger.error(f"Error uploading document with vectors: {str(e)}")
            # Still return upload result even if vector processing fails
            upload_result['content_processed'] = False
            upload_result['vector_error'] = str(e)
            return upload_result

    async def upload_user_document_with_vectors(
        self,
        user_id: str,
        file_data: bytes,
        filename: str,
        document_type: str = "user_document",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload user document and automatically generate chunked vectors.
        
        Args:
            user_id: ID of user uploading the file
            file_data: Raw file data
            filename: Original filename
            document_type: Type of document
            metadata: Optional metadata about the document
            
        Returns:
            Dict containing upload information and vector processing results
        """
        try:
            # Generate a document ID for this upload
            document_id = str(uuid.uuid4())
            
            # Upload using existing method
            upload_result = await self.upload_document(
                file_data, filename, user_id, document_type, metadata
            )
            
            # Parse document content
            content_text = await self._extract_text_content(file_data, filename)
            
            if content_text and content_text.strip():
                # Generate vectors
                from db.services.encryption_aware_embedding_service import get_encryption_aware_embedding_service
                embedding_service = await get_encryption_aware_embedding_service()
                
                # Store as user document vector (chunked)
                vector_ids = await embedding_service.process_user_document(
                    user_id=user_id,
                    document_id=document_id,
                    content_text=content_text,
                    document_metadata={
                        **upload_result,
                        "document_type": document_type,
                        "processing_method": "user_upload",
                        "content_extracted": True
                    }
                )
                
                upload_result['document_id'] = document_id
                upload_result['vector_ids'] = vector_ids
                upload_result['vector_chunk_count'] = len(vector_ids)
                upload_result['content_processed'] = True
                logger.info(f"Successfully processed {len(vector_ids)} chunks for document {filename}")
            else:
                upload_result['content_processed'] = False
                upload_result['vector_ids'] = []
                upload_result['vector_chunk_count'] = 0
                logger.warning(f"Could not extract content from {filename} for vector processing")
            
            return upload_result
            
        except Exception as e:
            logger.error(f"Error uploading user document with vectors: {str(e)}")
            raise

    async def search_documents_by_content(
        self,
        query: str,
        user_id: str,
        document_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents using semantic similarity.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            document_type: Optional document type filter
            limit: Maximum number of results
            
        Returns:
            List of matching documents with similarity scores
        """
        try:
            from db.services.encryption_aware_embedding_service import get_encryption_aware_embedding_service
            embedding_service = await get_encryption_aware_embedding_service()
            
            # Search both policy content and user documents
            policy_results = await embedding_service.search_policy_content(
                query=query,
                user_id=user_id,
                policy_filters={"document_type": document_type} if document_type else None,
                limit=limit // 2
            )
            
            user_doc_results = await embedding_service.search_user_documents(
                query=query,
                user_id=user_id,
                document_filters={"document_type": document_type} if document_type else None,
                limit=limit // 2
            )
            
            # Combine and sort by similarity
            all_results = []
            
            # Format policy results
            for result in policy_results:
                all_results.append({
                    **result,
                    'source_type': 'policy_content',
                    'document_info': result.get('document_metadata', {})
                })
            
            # Format user document results
            for result in user_doc_results:
                all_results.append({
                    **result,
                    'source_type': 'user_document',
                    'document_info': result.get('chunk_metadata', {})
                })
            
            # Sort by similarity score (lower is better for cosine distance)
            all_results.sort(key=lambda x: x['similarity_score'])
            
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching documents by content: {str(e)}")
            return []

    async def _extract_text_content(self, file_data: bytes, filename: str) -> str:
        """
        Extract text content from uploaded file.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        try:
            from pathlib import Path
            import tempfile
            
            logger.info(f"Starting text extraction for {filename}")
            
            # Check if we have a document parser
            try:
                # Try to import document parser from config
                logger.info("Attempting to use DocumentParser from config")
                from config.parser import DocumentParser
                parser = DocumentParser()
                
                # Save temporarily to parse
                with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix) as tmp_file:
                    tmp_file.write(file_data)
                    tmp_file.flush()
                    logger.info(f"Saved temporary file for parsing: {tmp_file.name}")
                    
                    documents = parser.parse_document(tmp_file.name)
                    content = "\n".join([doc.page_content for doc in documents])
                    logger.info(f"Successfully extracted {len(content)} characters using DocumentParser")
                    return content
                    
            except ImportError as e:
                logger.info(f"DocumentParser not available ({str(e)}), falling back to basic extraction")
                # Fallback to basic text extraction for PDFs and text files
                return await self._basic_text_extraction(file_data, filename)
                
        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {str(e)}", exc_info=True)
            return ""

    async def _basic_text_extraction(self, file_data: bytes, filename: str) -> str:
        """
        Basic text extraction fallback for common file types.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        try:
            file_extension = Path(filename).suffix.lower()
            logger.info(f"Starting basic text extraction for {filename} (type: {file_extension})")
            
            if file_extension == '.txt':
                # Plain text file
                content = file_data.decode('utf-8', errors='ignore')
                logger.info(f"Extracted {len(content)} characters from text file")
                return content
            
            elif file_extension == '.pdf':
                # Try to extract from PDF using PyPDF2 or similar
                try:
                    import PyPDF2
                    import io
                    logger.info("Using PyPDF2 for PDF extraction")
                    
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                    text_parts = []
                    
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        text_parts.append(text)
                        logger.info(f"Extracted {len(text)} characters from PDF page")
                    
                    content = "\n".join(text_parts)
                    logger.info(f"Successfully extracted {len(content)} characters from PDF")
                    return content
                    
                except ImportError:
                    logger.error("PyPDF2 not available for PDF text extraction")
                    return ""
                except Exception as e:
                    logger.error(f"PDF extraction failed: {str(e)}", exc_info=True)
                    return ""
            
            elif file_extension in ['.doc', '.docx']:
                # Try to extract from Word documents
                try:
                    import docx
                    import io
                    logger.info("Using python-docx for Word document extraction")
                    
                    doc = docx.Document(io.BytesIO(file_data))
                    text_parts = []
                    
                    for paragraph in doc.paragraphs:
                        text = paragraph.text
                        text_parts.append(text)
                        logger.info(f"Extracted {len(text)} characters from Word paragraph")
                    
                    content = "\n".join(text_parts)
                    logger.info(f"Successfully extracted {len(content)} characters from Word document")
                    return content
                    
                except ImportError:
                    logger.error("python-docx not available for Word document extraction")
                    return ""
                except Exception as e:
                    logger.error(f"Word document extraction failed: {str(e)}", exc_info=True)
                    return ""
            
            else:
                # Unsupported file type
                logger.warning(f"Text extraction not supported for file type: {file_extension}")
                return ""
                
        except Exception as e:
            logger.error(f"Error in basic text extraction: {str(e)}", exc_info=True)
            return ""


# Global storage service instance
storage_service = None

async def get_storage_service() -> StorageService:
    """Get the global storage service instance."""
    global storage_service
    if storage_service is None:
        storage_service = StorageService()
    return storage_service 