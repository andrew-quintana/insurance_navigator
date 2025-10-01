"""
Document duplication utilities for Phase 3: Multi-User Data Integrity.

This module implements the document row duplication system that allows multiple users
to upload the same document content while maintaining separate user-scoped document
entries and preserving existing processing data.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


async def duplicate_document_for_user(
    source_document_id: str,
    target_user_id: str,
    target_filename: str,
    db_connection
) -> Dict[str, Any]:
    """
    Duplicate an existing document for a new user.
    
    This function creates a new document row for the target user with the same
    processing data as the source document, while preserving all document_chunks
    relationships through proper document_id references.
    
    Args:
        source_document_id: UUID of the source document to duplicate
        target_user_id: UUID of the user who will own the new document
        target_filename: Filename for the new document (may differ from source)
        db_connection: Database connection for executing queries
        
    Returns:
        Dictionary containing the new document information:
        - document_id: UUID of the newly created document
        - filename: Name of the new document
        - raw_path: Storage path for the raw document
        - parsed_path: Storage path for the parsed document (if exists)
        - processing_status: Current processing status
        - created_at: Timestamp when the document was created
        
    Raises:
        ValueError: If source document doesn't exist or target user is invalid
        RuntimeError: If document duplication fails
    """
    try:
        # First, verify the source document exists and get its data
        source_query = """
            SELECT 
                document_id, user_id, filename, mime, bytes_len, file_sha256,
                parsed_sha256, raw_path, parsed_path, processing_status,
                created_at, updated_at
            FROM upload_pipeline.documents 
            WHERE document_id = $1
        """
        
        source_doc = await db_connection.fetchrow(source_query, source_document_id)
        if not source_doc:
            raise ValueError(f"Source document {source_document_id} not found")
        
        # Generate new document ID for the target user
        # Use deterministic UUID generation based on target user and content hash
        from ..utils.upload_pipeline_utils import generate_document_id
        new_document_id = generate_document_id(str(target_user_id), source_doc['file_sha256'])
        
        # Generate new storage paths for the target user using standardized functions
        from ..utils.upload_pipeline_utils import generate_storage_path, generate_parsed_path
        new_raw_path = generate_storage_path(
            str(target_user_id),
            str(new_document_id),
            target_filename
        )
        
        # Generate parsed path if source has one using standardized function
        new_parsed_path = None
        if source_doc['parsed_path']:
            new_parsed_path = generate_parsed_path(str(target_user_id), str(new_document_id))
        
        # Create new document record with same processing data but new user
        insert_query = """
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, file_sha256,
                parsed_sha256, raw_path, parsed_path, processing_status,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            RETURNING document_id, filename, raw_path, parsed_path, processing_status, created_at
        """
        
        now = datetime.utcnow()
        new_doc = await db_connection.fetchrow(
            insert_query,
            new_document_id,           # $1: new document_id
            target_user_id,            # $2: target user_id
            target_filename,           # $3: new filename
            source_doc['mime'],        # $4: same mime type
            source_doc['bytes_len'],   # $5: same file size
            source_doc['file_sha256'], # $6: same content hash
            source_doc['parsed_sha256'], # $7: same parsed hash
            new_raw_path,              # $8: new raw path
            new_parsed_path,           # $9: new parsed path
            source_doc['processing_status'], # $10: same processing status
            now,                       # $11: new created_at
            now                        # $12: new updated_at
        )
        
        # Copy all document chunks from source to new document
        await _copy_document_chunks(
            source_document_id, 
            new_document_id, 
            target_user_id, 
            db_connection
        )
        
        logger.info(
            f"Document duplicated successfully - "
            f"source: {source_document_id}, target: {new_document_id}, "
            f"user: {target_user_id}"
        )
        
        return {
            "document_id": new_doc["document_id"],
            "filename": new_doc["filename"],
            "raw_path": new_doc["raw_path"],
            "parsed_path": new_doc["parsed_path"],
            "processing_status": new_doc["processing_status"],
            "created_at": new_doc["created_at"]
        }
        
    except Exception as e:
        logger.error(f"Failed to duplicate document {source_document_id} for user {target_user_id}: {str(e)}")
        raise RuntimeError(f"Document duplication failed: {str(e)}")


async def _copy_document_chunks(
    source_document_id: str,
    target_document_id: str,
    target_user_id: str,
    db_connection
) -> int:
    """
    Copy all document chunks from source document to target document.
    
    This preserves the document_chunks relationships by creating new chunk records
    that reference the new document_id while maintaining all processing data.
    
    Args:
        source_document_id: UUID of the source document
        target_document_id: UUID of the target document
        target_user_id: UUID of the target user
        db_connection: Database connection for executing queries
        
    Returns:
        Number of chunks copied
        
    Raises:
        RuntimeError: If chunk copying fails
    """
    try:
        # Get all chunks from source document
        source_chunks_query = """
            SELECT 
                chunker_name, chunker_version, chunk_ord, text, chunk_sha,
                embed_model, embed_version, vector_dim, embedding,
                embed_updated_at, created_at, updated_at
            FROM upload_pipeline.document_chunks
            WHERE document_id = $1
            ORDER BY chunk_ord
        """
        
        source_chunks = await db_connection.fetch(source_chunks_query, source_document_id)
        
        if not source_chunks:
            logger.warning(f"No chunks found for source document {source_document_id}")
            return 0
        
        # Copy each chunk to the new document
        chunks_copied = 0
        now = datetime.utcnow()
        
        for chunk in source_chunks:
            # Generate new chunk ID
            new_chunk_id = str(uuid.uuid4())
            
            # Insert new chunk record
            insert_chunk_query = """
                INSERT INTO upload_pipeline.document_chunks (
                    chunk_id, document_id, chunker_name, chunker_version, chunk_ord,
                    text, chunk_sha, embed_model, embed_version, vector_dim, embedding,
                    embed_updated_at, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
            """
            
            await db_connection.execute(
                insert_chunk_query,
                new_chunk_id,                    # $1: new chunk_id
                target_document_id,              # $2: target document_id
                chunk['chunker_name'],           # $3: same chunker_name
                chunk['chunker_version'],        # $4: same chunker_version
                chunk['chunk_ord'],              # $5: same chunk_ord
                chunk['text'],                   # $6: same text
                chunk['chunk_sha'],              # $7: same chunk_sha
                chunk['embed_model'],            # $8: same embed_model
                chunk['embed_version'],          # $9: same embed_version
                chunk['vector_dim'],             # $10: same vector_dim
                chunk['embedding'],              # $11: same embedding vector
                chunk['embed_updated_at'],       # $12: same embed_updated_at
                now,                             # $13: new created_at
                now                              # $14: new updated_at
            )
            
            chunks_copied += 1
        
        logger.info(
            f"Copied {chunks_copied} chunks from document {source_document_id} "
            f"to document {target_document_id}"
        )
        
        return chunks_copied
        
    except Exception as e:
        logger.error(f"Failed to copy chunks from {source_document_id} to {target_document_id}: {str(e)}")
        raise RuntimeError(f"Chunk copying failed: {str(e)}")


async def find_existing_document_by_content_hash(
    content_hash: str,
    db_connection
) -> Optional[Dict[str, Any]]:
    """
    Find an existing document by content hash across all users.
    
    This function searches for documents with the same content hash regardless
    of which user uploaded them, enabling cross-user duplicate detection.
    
    Args:
        content_hash: SHA256 hash of the document content
        db_connection: Database connection for executing queries
        
    Returns:
        Dictionary containing the first matching document information, or None if not found
    """
    try:
        query = """
            SELECT 
                document_id, user_id, filename, mime, bytes_len, file_sha256,
                parsed_sha256, raw_path, parsed_path, processing_status,
                created_at, updated_at
            FROM upload_pipeline.documents 
            WHERE file_sha256 = $1
            ORDER BY created_at ASC
            LIMIT 1
        """
        
        result = await db_connection.fetchrow(query, content_hash)
        
        if result:
            logger.info(f"Found existing document {result['document_id']} with content hash {content_hash}")
            return dict(result)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to search for document with content hash {content_hash}: {str(e)}")
        return None


async def check_user_has_document(
    user_id: str,
    content_hash: str,
    db_connection
) -> Optional[Dict[str, Any]]:
    """
    Check if a user already has a document with the given content hash.
    
    This function provides user-scoped duplicate detection to prevent
    the same user from uploading the same document multiple times.
    
    Args:
        user_id: UUID of the user
        content_hash: SHA256 hash of the document content
        db_connection: Database connection for executing queries
        
    Returns:
        Dictionary containing the user's existing document information, or None if not found
    """
    try:
        query = """
            SELECT 
                document_id, user_id, filename, mime, bytes_len, file_sha256,
                parsed_sha256, raw_path, parsed_path, processing_status,
                created_at, updated_at
            FROM upload_pipeline.documents 
            WHERE user_id = $1 AND file_sha256 = $2
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        result = await db_connection.fetchrow(query, user_id, content_hash)
        
        if result:
            logger.info(f"User {user_id} already has document {result['document_id']} with content hash {content_hash}")
            return dict(result)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to check user {user_id} for document with content hash {content_hash}: {str(e)}")
        return None

