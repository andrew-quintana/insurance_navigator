"""
Job management endpoints for the upload pipeline.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Path
from fastapi.responses import JSONResponse

from models import JobStatusResponse, ErrorDetails
from auth import require_user, User
from database import get_database
from config import get_config
from utils.upload_pipeline_utils import log_event

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str = Path(..., description="Job ID to retrieve status for"),
    current_user: User = Depends(require_user)
):
    """
    Get the current status of a job.
    
    This endpoint:
    1. Validates the job ID
    2. Checks user authorization for the job
    3. Returns current stage, state, and progress information
    4. Includes error details if the job has failed
    
    Args:
        job_id: UUID of the job to check
        current_user: Authenticated user
        
    Returns:
        JobStatusResponse with current job information
        
    Raises:
        HTTPException: For not found, unauthorized, or system errors
    """
    try:
        db = get_database()
        
        # Get job information with user authorization
        job_info = await _get_job_with_authorization(job_id, current_user.user_id, db)
        if not job_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Calculate progress percentages
        progress = _calculate_job_progress(job_info["stage"])
        
        # Format error information if present
        last_error = None
        if job_info["last_error"]:
            last_error = _format_error_details(job_info["last_error"])
        
        # Calculate cost (placeholder for now)
        cost_cents = _calculate_job_cost(job_info)
        
        logger.info(
            "Job status retrieved",
            user_id=current_user.user_id,
            job_id=job_id,
            stage=job_info["stage"],
            state=job_info["state"]
        )
        
        return JobStatusResponse(
            job_id=job_id,
            stage=job_info["stage"],
            state=job_info["state"],
            retry_count=job_info["retry_count"],
            progress=progress,
            cost_cents=cost_cents,
            document_id=job_info["document_id"],
            last_error=last_error,
            updated_at=job_info["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Job status endpoint error",
            exc_info=True,
            user_id=current_user.user_id,
            job_id=job_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )


@router.get("/jobs")
async def list_user_jobs(
    current_user: User = Depends(require_user),
    limit: int = 50,
    offset: int = 0,
    state: Optional[str] = None
):
    """
    List jobs for the current user.
    
    Args:
        current_user: Authenticated user
        limit: Maximum number of jobs to return (default 50, max 100)
        offset: Number of jobs to skip (default 0)
        state: Filter by job state (optional)
        
    Returns:
        List of user's jobs with basic information
    """
    try:
        # Validate parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 50
        
        db = get_database()
        
        # Build query with filters
        query = """
            SELECT 
                uj.job_id,
                uj.stage,
                uj.state,
                uj.retry_count,
                uj.created_at,
                uj.updated_at,
                d.document_id,
                d.filename,
                d.bytes_len
            FROM upload_pipeline.upload_jobs uj
            JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
            WHERE d.user_id = $1
        """
        
        params = [current_user.user_id]
        param_count = 1
        
        if state:
            param_count += 1
            query += f" AND uj.state = ${param_count}"
            params.append(state)
        
        query += " ORDER BY uj.created_at DESC LIMIT $2 OFFSET $3"
        params.extend([limit, offset])
        
        # Execute query
        results = await db.fetch(query, *params)
        
        # Format results
        jobs = []
        for row in results:
            jobs.append({
                "job_id": str(row["job_id"]),
                "stage": row["stage"],
                "state": row["state"],
                "retry_count": row["retry_count"],
                "document_id": str(row["document_id"]),
                "filename": row["filename"],
                "bytes_len": row["bytes_len"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat()
            })
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) as total
            FROM upload_pipeline.upload_jobs uj
            JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
            WHERE d.user_id = $1
        """
        
        count_params = [current_user.user_id]
        if state:
            count_query += " AND uj.state = $2"
            count_params.append(state)
        
        count_result = await db.fetchrow(count_query, *count_params)
        total_count = count_result["total"] if count_result else 0
        
        return {
            "jobs": jobs,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        logger.error(
            "List jobs endpoint error",
            exc_info=True,
            user_id=current_user.user_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job list"
        )


async def _get_job_with_authorization(job_id: str, user_id: str, db) -> Optional[Dict[str, Any]]:
    """Get job information with user authorization check."""
    query = """
        SELECT 
            uj.job_id,
            uj.stage,
            uj.state,
            uj.retry_count,
            uj.last_error,
            uj.updated_at,
            d.document_id,
            d.filename
        FROM upload_pipeline.upload_jobs uj
        JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
        WHERE uj.job_id = $1 AND d.user_id = $2
    """
    
    result = await db.fetchrow(query, job_id, user_id)
    return dict(result) if result else None


def _calculate_job_progress(stage: str) -> Dict[str, float]:
    """
    Calculate progress percentages based on current stage.
    
    Updated stage progression:
    queued → job_validated → parsing → parsed → parse_validated → 
    chunking → chunks_buffered → chunked → embedding → 
    embeddings_buffered → embedded
    """
    stage_weights = {
        "queued": 0,
        "job_validated": 10,
        "parsing": 20,
        "parsed": 30,
        "parse_validated": 35,
        "chunking": 45,
        "chunks_buffered": 50,
        "chunked": 55,
        "embedding": 70,
        "embeddings_buffered": 75,
        "embedded": 100
    }
    
    stage_pct = stage_weights.get(stage, 0)
    total_pct = stage_pct  # For now, total progress equals stage progress
    
    return {
        "stage_pct": stage_pct,
        "total_pct": total_pct
    }


def _format_error_details(error_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format error details for API response."""
    if not error_data:
        return None
    
    # Extract error information from job payload
    error_code = error_data.get("code", "unknown_error")
    error_message = error_data.get("message", "An error occurred during processing")
    error_timestamp = error_data.get("timestamp")
    
    return {
        "code": error_code,
        "message": error_message,
        "timestamp": error_timestamp,
        "details": error_data.get("details")
    }


def _calculate_job_cost(job_info: Dict[str, Any]) -> int:
    """Calculate processing cost in cents (placeholder implementation)."""
    # This would integrate with actual cost tracking
    # For now, return 0 as placeholder
    
    # Future implementation could track:
    # - LlamaIndex parsing costs
    # - OpenAI embedding costs
    # - Storage costs
    # - Processing time costs
    
    return 0


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str = Path(..., description="Job ID to retry"),
    current_user: User = Depends(require_user)
):
    """
    Retry a failed job.
    
    This endpoint:
    1. Validates the job ID and user authorization
    2. Checks if the job is in a retryable state
    3. Resets the job to queued state for retry
    4. Logs the retry event
    
    Args:
        job_id: UUID of the job to retry
        current_user: Authenticated user
        
    Returns:
        Success message with job status
        
    Raises:
        HTTPException: For not found, unauthorized, or invalid retry state
    """
    try:
        db = get_database()
        
        # Get job information with authorization
        job_info = await _get_job_with_authorization(job_id, current_user.user_id, db)
        if not job_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if job can be retried
        if job_info["state"] not in ["retryable", "deadletter"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job in state '{job_info['state']}' cannot be retried"
            )
        
        # Reset job to queued state
        await _reset_job_for_retry(job_id, db)
        
        # Log retry event
        await log_event(
            job_id=job_id,
            document_id=job_info["document_id"],
            code="RETRY_SCHEDULED",
            type="retry",
            severity="info",
            payload={
                "user_id": str(current_user.user_id),
                "previous_state": job_info["state"],
                "retry_count": job_info["retry_count"]
            }
        )
        
        logger.info(
            "Job retry initiated",
            user_id=current_user.user_id,
            job_id=job_id,
            previous_state=job_info["state"]
        )
        
        return {
            "message": "Job queued for retry",
            "job_id": job_id,
            "new_state": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Job retry endpoint error",
            exc_info=True,
            user_id=current_user.user_id,
            job_id=job_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry job"
        )


async def _reset_job_for_retry(job_id: str, db) -> None:
    """Reset a job to queued state for retry."""
    query = """
        UPDATE upload_pipeline.upload_jobs
        SET 
            state = 'queued',
            retry_count = retry_count + 1,
            last_error = NULL,
            claimed_by = NULL,
            claimed_at = NULL,
            updated_at = NOW()
        WHERE job_id = $1
    """
    
    await db.execute(query, job_id)
