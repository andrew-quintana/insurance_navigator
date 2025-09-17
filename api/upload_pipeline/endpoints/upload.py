"""
Upload endpoint for document ingestion pipeline.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from fastapi.responses import JSONResponse

from ..models import UploadRequest, UploadResponse, JobPayloadJobValidated
from ..auth import require_user, User
from ..database import get_database
from ..config import get_config
from ..utils.upload_pipeline_utils import generate_document_id, log_event, generate_storage_path
from ..utils.document_duplication import (
    find_existing_document_by_content_hash,
    check_user_has_document,
    duplicate_document_for_user
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: UploadRequest,
    # current_user: User = Depends(require_user)  # Temporarily disabled for testing
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
        
        # Mock user for testing (temporarily disabled authentication)
        from uuid import uuid4
        current_user = type('MockUser', (), {'user_id': str(uuid4())})()
        
        # Check concurrent job limits
        await _check_concurrent_job_limits(current_user.user_id, db)
        
        # Phase 3: Multi-User Data Integrity - Check for duplicates
        # First check if this user already has this document
        user_existing_document = await check_user_has_document(
            str(current_user.user_id),
            request.sha256,
            db
        )
        
        if user_existing_document:
            # User already has this document - return existing document
            logger.info(
                f"User duplicate document detected - user_id: {current_user.user_id}, file_sha256: {request.sha256}, existing_document_id: {user_existing_document['document_id']}"
            )
            
            # Log duplicate event
            log_event(
                event_type="UPLOAD_USER_DEDUP_HIT",
                user_id=str(current_user.user_id),
                document_id=user_existing_document["document_id"],
                job_id=None,
                stage="duplicate_detection",
                details={
                    "file_sha256": request.sha256,
                    "filename": request.filename,
                    "duplicate_type": "user_existing"
                }
            )
            
            # Return existing document response
            return UploadResponse(
                job_id=user_existing_document["job_id"],
                document_id=user_existing_document["document_id"],
                signed_url=user_existing_document["signed_url"],
                upload_expires_at=user_existing_document["upload_expires_at"]
            )
        
        # Check if any other user has uploaded this document content
        cross_user_existing_document = await find_existing_document_by_content_hash(
            request.sha256,
            db
        )
        
        if cross_user_existing_document:
            # Another user has this document - duplicate it for this user
            logger.info(
                f"Cross-user duplicate detected - creating duplicate for user: {current_user.user_id}, "
                f"source_document_id: {cross_user_existing_document['document_id']}, "
                f"source_user_id: {cross_user_existing_document['user_id']}"
            )
            
            try:
                # Duplicate the document for this user
                duplicated_document = await duplicate_document_for_user(
                    source_document_id=cross_user_existing_document["document_id"],
                    target_user_id=str(current_user.user_id),
                    target_filename=request.filename,
                    db_connection=db
                )
                
                # Log duplication event
                log_event(
                    event_type="UPLOAD_CROSS_USER_DEDUP",
                    user_id=str(current_user.user_id),
                    document_id=duplicated_document["document_id"],
                    job_id=None,
                    stage="duplicate_detection",
                    details={
                        "file_sha256": request.sha256,
                        "filename": request.filename,
                        "duplicate_type": "cross_user_duplicated",
                        "source_document_id": cross_user_existing_document["document_id"],
                        "source_user_id": cross_user_existing_document["user_id"]
                    }
                )
                
                # Generate signed URL for the duplicated document
                signed_url = await _generate_signed_url(duplicated_document["raw_path"], config.signed_url_ttl_seconds)
                upload_expires_at = datetime.utcnow() + timedelta(seconds=config.signed_url_ttl_seconds)
                
                logger.info(
                    f"Document successfully duplicated - new_document_id: {duplicated_document['document_id']}, "
                    f"user: {current_user.user_id}, source: {cross_user_existing_document['document_id']}"
                )
                
                return UploadResponse(
                    job_id=None,  # No new job needed since document is already processed
                    document_id=duplicated_document["document_id"],
                    signed_url=signed_url,
                    upload_expires_at=upload_expires_at
                )
                
            except Exception as e:
                logger.error(f"Failed to duplicate document for user {current_user.user_id}: {str(e)}")
                # Fall through to create new document if duplication fails
                pass
        
        # Generate new document ID using deterministic approach
        document_id = generate_document_id(str(current_user.user_id), request.sha256)
        
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
        
        # Generate proper signed URL for file upload
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
    """
    Check if document with same hash already exists for user.
    
    This function is now deprecated in favor of the new Phase 3 approach
    using check_user_has_document and find_existing_document_by_content_hash.
    Kept for backward compatibility.
    """
    # Use the new Phase 3 function
    result = await check_user_has_document(user_id, file_sha256, db)
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
            job_id, document_id, status, state, progress, 
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
        "uploaded",  # Start in uploaded state
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
            job_id, document_id, status, state, progress, 
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
        "uploaded",  # Start in uploaded state per updated stage progression
        "queued",
        json.dumps(payload_dict)  # Convert to JSON string for database storage
    )


async def _generate_signed_url(storage_path: str, ttl_seconds: int) -> str:
    """Generate a signed URL for file upload. For development, return a direct upload URL."""
    config = get_config()
    
    # For development, use direct upload URL with service role key
    if config.storage_environment == "development":
        # Return a URL that the frontend can use with proper authentication
        return f"http://127.0.0.1:54321/storage/v1/object/files/{storage_path[6:] if storage_path.startswith('files/') else storage_path}"
    
    # For production, use proper Supabase signed URL generation
    try:
        from config.database import get_supabase_service_client
        supabase = await get_supabase_service_client()
        
        # Handle new path format: files/user/{userId}/raw/{datetime}_{hash}.{ext}
        if storage_path.startswith("files/user/"):
            key = storage_path[6:]  # Remove "files/" prefix
            bucket = "files"
            
            # Generate signed URL using Supabase client
            response = supabase.storage.from_(bucket).create_signed_upload_url(key)
            
            if response.get('error'):
                raise ValueError(f"Failed to generate signed URL: {response['error']}")
            
            return response['signed_url']
        
        # Handle legacy storage:// format
        elif storage_path.startswith("storage://"):
            path_parts = storage_path[10:].split("/", 1)
            if len(path_parts) == 2:
                bucket, key = path_parts
                response = supabase.storage.from_(bucket).create_signed_upload_url(key)
                
                if response.get('error'):
                    raise ValueError(f"Failed to generate signed URL: {response['error']}")
                
                return response['signed_url']
        
        raise ValueError(f"Invalid storage path format: {storage_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate signed URL for {storage_path}: {str(e)}")
        raise


@router.post("/upload-file/{job_id}")
async def upload_file_to_storage(
    job_id: str,
    file: UploadFile = File(...)
):
    """Handle direct file upload to storage for development."""
    from config.database import get_supabase_service_client
    
    try:
        # Get the job to find the storage path
        db = get_database()
        async with db.get_connection() as conn:
            job = await conn.fetchrow(
                "SELECT document_id, status FROM upload_pipeline.upload_jobs WHERE job_id = $1",
                job_id
            )
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Get document info
            doc = await conn.fetchrow(
                "SELECT raw_path FROM upload_pipeline.documents WHERE document_id = $1",
                job["document_id"]
            )
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            raw_path = doc["raw_path"]
        
        # Upload file to Supabase storage using service role
        supabase = await get_supabase_service_client()
        
        # Extract bucket and key from raw_path
        if raw_path.startswith("files/user/"):
            key = raw_path[6:]  # Remove "files/" prefix
            bucket = "files"
        else:
            raise ValueError(f"Invalid raw_path format: {raw_path}")
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase storage
        response = supabase.storage.from_(bucket).upload(
            key,
            file_content,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )
        
        if response.get('error'):
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to upload file to storage: {response['error']}"
            )
        
        # Update job status to indicate file is uploaded
        async with db.get_connection() as conn:
            await conn.execute(
                "UPDATE upload_pipeline.upload_jobs SET status = 'uploaded', state = 'queued' WHERE job_id = $1",
                job_id
            )
        
        logger.info(f"File uploaded successfully to {raw_path} for job {job_id}")
        
        return {"message": "File uploaded successfully", "path": raw_path}
        
    except Exception as e:
        logger.error(f"File upload failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/test-endpoint")
async def test_endpoint():
    """Test endpoint to verify router is working."""
    return {"message": "Router is working", "status": "ok"}

@router.post("/upload-test")
async def upload_test(request: UploadRequest):
    """Test upload endpoint without authentication."""
    try:
        config = get_config()
        db = get_database()
        
        # Mock user for testing
        from uuid import uuid4
        current_user = type('MockUser', (), {'user_id': str(uuid4())})()
        
        # Generate new document ID using deterministic approach
        document_id = generate_document_id(str(current_user.user_id), request.sha256)
        
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
        
        # Generate proper signed URL for file upload
        signed_url = await _generate_signed_url(raw_path, config.signed_url_ttl_seconds)
        upload_expires_at = datetime.utcnow() + timedelta(seconds=config.signed_url_ttl_seconds)
        
        logger.info(f"Test upload successful - document_id: {document_id}, job_id: {job_id}")
        
        return UploadResponse(
            job_id=job_id,
            document_id=document_id,
            signed_url=signed_url,
            upload_expires_at=upload_expires_at
        )
        
    except Exception as e:
        logger.error(f"Test upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test upload failed: {str(e)}"
        )

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
