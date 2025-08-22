"""
Upload endpoint for document ingestion pipeline.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from models import UploadRequest, UploadResponse, JobPayloadJobValidated
from auth import require_user, User
from database import get_database
from config import get_config
from utils.upload_pipeline_utils import generate_document_id, log_event, generate_storage_path

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: UploadRequest,
    current_user: User = Depends(require_user())
):
    """
    Upload a new document for processing.
    
    This endpoint:
    1. Validates the upload request
    2. Checks for duplicate documents
    3. Creates a new document record
    4. Initializes a job in the queue
    5. Returns a signed URL for file upload
    
    Args:
        request: Upload request with file metadata
        current_user: Authenticated user
        
    Returns:
        UploadResponse with job ID, document ID, and signed URL
        
    Raises:
        HTTPException: For validation errors, duplicates, or system errors
    """
    try:
        config = get_config()
        db = get_database()
        
        # Check concurrent job limits
        await _check_concurrent_job_limits(current_user.user_id, db)
        
        # Check for duplicate document
        existing_document = await _check_duplicate_document(
            current_user.user_id, 
            request.sha256, 
            db
        )
        
        if existing_document:
            # Return existing document information
            logger.info(
                f"Duplicate document detected - user_id: {current_user.user_id}, file_sha256: {request.sha256}, existing_document_id: {existing_document['document_id']}"
            )
            
            # Log duplicate event
            log_event(
                event_type="UPLOAD_DEDUP_HIT",
                user_id=str(current_user.user_id),
                document_id=existing_document["document_id"],
                job_id=None,
                stage="duplicate_detection",
                details={
                    "file_sha256": request.sha256,
                    "filename": request.filename
                }
            )
            
            # Return existing document response
            return UploadResponse(
                job_id=existing_document["job_id"],
                document_id=existing_document["document_id"],
                signed_url=existing_document["signed_url"],
                upload_expires_at=existing_document["upload_expires_at"]
            )
        
        # Generate new document ID
        document_id = generate_document_id()
        
        # Generate storage path
        raw_path = generate_storage_path(
            str(current_user.user_id),
            str(document_id),
            request.filename
        )
        
        # Create document record
        await _create_document_record(
            document_id=document_id,
            user_id=current_user.user_id,
            filename=request.filename,
            mime=request.mime,
            bytes_len=request.bytes_len,
            file_sha256=request.sha256,
            raw_path=raw_path,
            db=db
        )
        
        # Create upload job
        job_id = uuid4()
        await _create_upload_job(
            job_id=job_id,
            document_id=document_id,
            user_id=current_user.user_id,
            request=request,
            raw_path=raw_path,
            db=db
        )
        
        # Generate signed URL for upload
        signed_url = await _generate_signed_url(raw_path, config.signed_url_ttl_seconds)
        upload_expires_at = datetime.utcnow() + timedelta(seconds=config.signed_url_ttl_seconds)
        
        # Log upload accepted event
        log_event(
            event_type="UPLOAD_ACCEPTED",
            user_id=str(current_user.user_id),
            document_id=document_id,
            job_id=job_id,
            stage="upload_initiated",
            details={
                "filename": request.filename,
                "bytes_len": request.bytes_len,
                "file_sha256": request.sha256,
                "raw_path": raw_path
            }
        )
        
        logger.info(
            f"Document upload initiated - user_id: {current_user.user_id}, document_id: {document_id}, job_id: {job_id}, filename: {request.filename}"
        )
        
        return UploadResponse(
            job_id=job_id,
            document_id=document_id,
            signed_url=signed_url,
            upload_expires_at=upload_expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Upload endpoint error - user_id: {current_user.user_id}, filename: {request.filename}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process upload request"
        )


async def _check_concurrent_job_limits(user_id: str, db) -> None:
    """Check if user has exceeded concurrent job limits."""
    config = get_config()
    
    # Count active jobs for user
    query = """
        SELECT COUNT(*) as job_count
        FROM upload_pipeline.upload_jobs uj
        JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
        WHERE d.user_id = $1 
        AND uj.state IN ('queued', 'working', 'retryable')
    """
    
    result = await db.fetchrow(query, user_id)
    active_jobs = result["job_count"] if result else 0
    
    if active_jobs >= config.max_concurrent_jobs_per_user:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum concurrent jobs ({config.max_concurrent_jobs_per_user}) exceeded"
        )


async def _check_duplicate_document(user_id: str, file_sha256: str, db) -> Optional[dict]:
    """Check if document with same hash already exists for user."""
    query = """
        SELECT d.document_id, d.filename, d.raw_path
        FROM upload_pipeline.documents d
        WHERE d.user_id = $1 AND d.file_sha256 = $2
        ORDER BY d.created_at DESC
        LIMIT 1
    """
    
    result = await db.fetchrow(query, user_id, file_sha256)
    if not result:
        return None
    
    # Check if there's an active job for this document
    job_query = """
        SELECT job_id, stage, state
        FROM upload_pipeline.upload_jobs
        WHERE document_id = $1 
        AND state IN ('queued', 'working', 'retryable')
        ORDER BY created_at DESC
        LIMIT 1
    """
    
    job_result = await db.fetchrow(job_query, result["document_id"])
    
    # If no active job exists, create a new one for the duplicate
    if not job_result:
        from uuid import uuid4
        new_job_id = str(uuid4())
        
        # Create a new job for the duplicate document
        await _create_upload_job_for_duplicate(
            job_id=new_job_id,
            document_id=result["document_id"],
            user_id=user_id,
            raw_path=result["raw_path"],
            db=db
        )
        job_id = new_job_id
    else:
        job_id = job_result["job_id"]
    
    # Generate signed URL for existing file
    config = get_config()
    signed_url = await _generate_signed_url(result["raw_path"], config.signed_url_ttl_seconds)
    upload_expires_at = datetime.utcnow() + timedelta(seconds=config.signed_url_ttl_seconds)
    
    return {
        "document_id": result["document_id"],
        "job_id": job_id,
        "signed_url": signed_url,
        "upload_expires_at": upload_expires_at
    }


async def _create_document_record(
    document_id: str,
    user_id: str,
    filename: str,
    mime: str,
    bytes_len: int,
    file_sha256: str,
    raw_path: str,
    db
) -> None:
    """Create a new document record in the database."""
    query = """
        INSERT INTO upload_pipeline.documents (
            document_id, user_id, filename, mime, bytes_len, 
            file_sha256, raw_path, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
    """
    
    await db.execute(
        query,
        document_id,
        user_id,
        filename,
        mime,
        bytes_len,
        file_sha256,
        raw_path
    )


async def _create_upload_job_for_duplicate(
    job_id: str,
    document_id: str,
    user_id: str,
    raw_path: str,
    db
) -> None:
    """Create a new upload job for a duplicate document."""
    # Create job payload for duplicate
    payload = JobPayloadJobValidated(
        user_id=user_id,
        document_id=document_id,
        file_sha256="",  # Will be filled from existing document
        bytes_len=0,     # Will be filled from existing document
        mime="application/pdf",  # Default for existing documents
        storage_path=raw_path
    )
    
    query = """
        INSERT INTO upload_pipeline.upload_jobs (
            job_id, document_id, stage, state, payload, 
            created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
    """
    
    # Convert UUIDs to strings for JSON serialization
    payload_dict = payload.dict()
    payload_dict["user_id"] = str(payload_dict["user_id"])
    payload_dict["document_id"] = str(payload_dict["document_id"])
    
    await db.execute(
        query,
        job_id,
        document_id,
        "queued",  # Start in queued state
        "queued",
        json.dumps(payload_dict)  # Convert to JSON string for database storage
    )


async def _create_upload_job(
    job_id: str,
    document_id: str,
    user_id: str,
    request: UploadRequest,
    raw_path: str,
    db
) -> None:
    """Create a new upload job in the queue."""
    # Create job payload
    payload = JobPayloadJobValidated(
        user_id=user_id,
        document_id=document_id,
        file_sha256=request.sha256,
        bytes_len=request.bytes_len,
        mime=request.mime,
        storage_path=raw_path
    )
    
    query = """
        INSERT INTO upload_pipeline.upload_jobs (
            job_id, document_id, stage, state, payload, 
            created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
    """
    
    # Convert UUIDs to strings for JSON serialization
    payload_dict = payload.dict()
    payload_dict["user_id"] = str(payload_dict["user_id"])
    payload_dict["document_id"] = str(payload_dict["document_id"])
    
    await db.execute(
        query,
        job_id,
        document_id,
        "queued",  # Start in queued state per updated stage progression
        "queued",
        json.dumps(payload_dict)  # Convert to JSON string for database storage
    )


async def _generate_signed_url(storage_path: str, ttl_seconds: int) -> str:
    """Generate a signed URL for file upload."""
    # This would integrate with Supabase Storage
    # For now, return a placeholder URL
    # TODO: Implement actual Supabase signed URL generation
    
    # Handle new path format: files/user/{userId}/raw/{datetime}_{hash}.{ext}
    if storage_path.startswith("files/user/"):
        # For Supabase storage, we need to extract the key part
        # The format is: files/user/{userId}/raw/{datetime}_{hash}.{ext}
        # We'll use the full path as the key
        key = storage_path
        
        # Placeholder signed URL generation for Supabase Storage
        # In production, this would call Supabase Storage API
        return f"https://storage.supabase.co/files/{key}?signed=true&ttl={ttl_seconds}"
    
    # Handle legacy storage:// format
    elif storage_path.startswith("storage://"):
        path_parts = storage_path[10:].split("/", 1)  # Remove "storage://" and split
        if len(path_parts) == 2:
            bucket, key = path_parts
            # Placeholder signed URL generation
            # In production, this would call Supabase Storage API
            return f"https://storage.supabase.co/{bucket}/{key}?signed=true&ttl={ttl_seconds}"
    
    # Fallback for invalid storage paths
    raise ValueError(f"Invalid storage path format: {storage_path}")


@router.get("/upload/limits")
async def get_upload_limits():
    """Get upload limits and constraints."""
    config = get_config()
    
    return {
        "max_file_size_bytes": config.max_file_size_bytes,
        "max_pages": config.max_pages,
        "max_concurrent_jobs_per_user": config.max_concurrent_jobs_per_user,
        "max_uploads_per_day_per_user": config.max_uploads_per_day_per_user,
        "supported_mime_types": ["application/pdf"],
        "signed_url_ttl_seconds": config.signed_url_ttl_seconds
    }
