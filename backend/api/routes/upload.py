"""
Enhanced upload endpoint for document ingestion pipeline with service router integration.

This endpoint integrates with the Phase 1 service router and cost tracking infrastructure
to provide real service integration capabilities while maintaining backward compatibility.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4, UUID

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from backend.shared.schemas.jobs import UploadRequest, UploadResponse, JobStatusResponse
from backend.shared.external.service_router import ServiceRouter
from backend.shared.monitoring.cost_tracker import CostTracker
from backend.shared.config.enhanced_config import EnhancedConfig, ServiceMode
from backend.shared.storage.storage_manager import StorageManager
from backend.shared.db.connection import DatabaseManager
from backend.shared.logging import StructuredLogger
from backend.shared.exceptions import (
    ServiceUnavailableError, CostLimitExceededError, 
    ValidationError, ConfigurationError
)

logger = StructuredLogger(__name__)

router = APIRouter()

# Global instances (would be dependency injected in production)
_service_router: Optional[ServiceRouter] = None
_cost_tracker: Optional[CostTracker] = None
_config: Optional[EnhancedConfig] = None
_storage_manager: Optional[StorageManager] = None
_db_manager: Optional[DatabaseManager] = None

def get_service_router() -> ServiceRouter:
    """Get or create service router instance"""
    global _service_router
    if _service_router is None:
        config = get_enhanced_config()
        _service_router = ServiceRouter(config.get_service_router_config())
    return _service_router

def get_cost_tracker() -> CostTracker:
    """Get or create cost tracker instance"""
    global _cost_tracker
    if _cost_tracker is None:
        config = get_enhanced_config()
        _cost_tracker = CostTracker(config.cost_control)
    return _cost_tracker

def get_enhanced_config() -> EnhancedConfig:
    """Get or create enhanced configuration instance"""
    global _config
    if _config is None:
        _config = EnhancedConfig()
    return _config

def get_storage_manager() -> StorageManager:
    """Get or create storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        config = get_enhanced_config()
        storage_config = {
            "storage_url": config.storage.url,
            "anon_key": config.storage.anon_key,
            "service_role_key": config.storage.service_role_key,
            "timeout": 60
        }
        _storage_manager = StorageManager(storage_config)
    return _storage_manager

def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance"""
    global _db_manager
    if _db_manager is None:
        config = get_enhanced_config()
        _db_manager = DatabaseManager(config.database.url)
    return _db_manager

# Mock user dependency for development (replace with real auth in production)
async def require_user():
    """Mock user dependency for development"""
    class MockUser:
        def __init__(self):
            self.user_id = UUID("12345678-1234-5678-1234-567812345678")
            self.email = "test@example.com"
    return MockUser()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: UploadRequest,
    current_user = Depends(require_user)
):
    """
    Enhanced upload endpoint with service router integration.
    
    This endpoint:
    1. Validates the upload request with real service requirements
    2. Checks service availability and cost limits
    3. Creates a new document record with service tracking
    4. Initializes a job with service mode awareness
    5. Triggers the processing pipeline with service router
    6. Returns a signed URL for file upload
    
    Args:
        request: Upload request with file metadata
        current_user: Authenticated user (mock for development)
        
    Returns:
        UploadResponse with job ID, document ID, and signed URL
        
    Raises:
        HTTPException: For validation errors, cost limits, or service unavailability
    """
    try:
        # Generate correlation ID for tracking
        correlation_id = uuid4()
        
        logger.info(
            "Upload request received",
            correlation_id=str(correlation_id),
            user_id=str(current_user.user_id),
            filename=request.filename,
            file_size=request.bytes_len
        )
        
        # Get service infrastructure
        service_router = get_service_router()
        cost_tracker = get_cost_tracker()
        config = get_enhanced_config()
        
        # Validate service availability and cost limits
        await _validate_service_availability(service_router, correlation_id)
        await _validate_cost_limits(request, cost_tracker, correlation_id)
        
        # Check concurrent job limits
        await _check_concurrent_job_limits(current_user.user_id, correlation_id)
        
        # Check for duplicate document
        existing_document = await _check_duplicate_document(
            current_user.user_id, 
            request.sha256, 
            correlation_id
        )
        
        if existing_document:
            logger.info(
                "Duplicate document detected",
                correlation_id=str(correlation_id),
                user_id=str(current_user.user_id),
                file_sha256=request.sha256,
                existing_document_id=str(existing_document["document_id"])
            )
            
            return UploadResponse(
                job_id=existing_document["job_id"],
                document_id=existing_document["document_id"],
                signed_url=existing_document["signed_url"],
                upload_expires_at=existing_document["upload_expires_at"]
            )
        
        # Generate new document ID
        document_id = _generate_document_id(str(current_user.user_id), request.sha256)
        
        # Generate storage path
        raw_path = _generate_storage_path(
            config.storage.raw_bucket,
            str(current_user.user_id),
            str(document_id),
            "pdf"
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
            correlation_id=correlation_id
        )
        
        # Create enhanced upload job with service tracking
        job_id = uuid4()
        await _create_enhanced_upload_job(
            job_id=job_id,
            document_id=document_id,
            user_id=current_user.user_id,
            request=request,
            raw_path=raw_path,
            service_router=service_router,
            correlation_id=correlation_id
        )
        
        # Generate signed URL for upload
        storage_manager = get_storage_manager()
        signed_url = await storage_manager._get_signed_url(
            config.storage.raw_bucket,
            f"{current_user.user_id}/{document_id}.pdf",
            "POST"
        )
        upload_expires_at = datetime.utcnow() + timedelta(seconds=config.storage.signed_url_ttl_seconds)
        
        # Log upload accepted event
        await _log_upload_event(
            job_id=job_id,
            document_id=document_id,
            correlation_id=correlation_id,
            event_type="UPLOAD_ACCEPTED",
            payload={
                "user_id": str(current_user.user_id),
                "filename": request.filename,
                "bytes_len": request.bytes_len,
                "file_sha256": request.sha256,
                "raw_path": raw_path,
                "service_mode": config.service_mode.value
            }
        )
        
        logger.info(
            "Document upload initiated successfully",
            correlation_id=str(correlation_id),
            user_id=str(current_user.user_id),
            document_id=str(document_id),
            job_id=str(job_id),
            filename=request.filename,
            service_mode=config.service_mode.value
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
            "Upload endpoint error",
            exc_info=True,
            correlation_id=str(correlation_id) if 'correlation_id' in locals() else None,
            user_id=str(current_user.user_id) if current_user else None,
            filename=request.filename if request else None
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process upload request"
        )

async def _validate_service_availability(
    service_router: ServiceRouter, 
    correlation_id: UUID
) -> Dict[str, Any]:
    """Validate service availability before job creation"""
    
    try:
        # Check service health
        health_status = await service_router.get_health_status()
        
        # Validate required services are available
        required_services = ['llamaparse', 'openai']
        for service in required_services:
            if not health_status.get(service, {}).get('healthy', False):
                logger.warning(
                    f"Service {service} unhealthy, will use fallback",
                    correlation_id=str(correlation_id),
                    service=service,
                    health_status=health_status.get(service, {})
                )
        
        logger.info(
            "Service availability validation completed",
            correlation_id=str(correlation_id),
            health_status=health_status
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            "Service availability validation failed",
            correlation_id=str(correlation_id),
            error=str(e)
        )
        raise ServiceUnavailableError(f"Failed to validate service availability: {e}")

async def _validate_cost_limits(
    request: UploadRequest, 
    cost_tracker: CostTracker,
    correlation_id: UUID
) -> None:
    """Validate cost limits before job creation"""
    
    try:
        # Estimate processing costs
        estimated_cost = await _estimate_processing_cost(request)
        
        # Check daily and hourly limits
        if not await cost_tracker.check_daily_limit(estimated_cost):
            logger.warning(
                "Daily cost limit exceeded",
                correlation_id=str(correlation_id),
                estimated_cost=estimated_cost
            )
            raise CostLimitExceededError("Daily cost limit exceeded")
        
        if not await cost_tracker.check_hourly_limit(estimated_cost):
            logger.warning(
                "Hourly cost limit exceeded",
                correlation_id=str(correlation_id),
                estimated_cost=estimated_cost
            )
            raise CostLimitExceededError("Hourly cost limit exceeded")
        
        logger.info(
            "Cost validation passed",
            correlation_id=str(correlation_id),
            estimated_cost=estimated_cost
        )
        
    except CostLimitExceededError:
        raise
    except Exception as e:
        logger.error(
            "Cost validation failed",
            correlation_id=str(correlation_id),
            error=str(e)
        )
        raise ValidationError(f"Failed to validate cost limits: {e}")

async def _estimate_processing_cost(request: UploadRequest) -> float:
    """Estimate processing cost for the upload request"""
    
    # Base cost estimation based on file size
    # This is a simplified estimation - in production, this would be more sophisticated
    
    # LlamaParse costs: $0.003 per page (estimated 1 page per 50KB)
    estimated_pages = max(1, request.bytes_len // (50 * 1024))
    llamaparse_cost = estimated_pages * 0.003
    
    # OpenAI costs: $0.00002 per 1K tokens (estimated 1 token per 4 characters)
    estimated_tokens = max(100, request.bytes_len // 4)
    openai_cost = (estimated_tokens / 1000) * 0.00002
    
    total_cost = llamaparse_cost + openai_cost
    
    logger.debug(
        "Cost estimation completed",
        file_size=request.bytes_len,
        estimated_pages=estimated_pages,
        estimated_tokens=estimated_tokens,
        llamaparse_cost=llamaparse_cost,
        openai_cost=openai_cost,
        total_cost=total_cost
    )
    
    return total_cost

async def _check_concurrent_job_limits(user_id: str, correlation_id: UUID) -> None:
    """Check if user has exceeded concurrent job limits"""
    
    try:
        config = get_enhanced_config()
        db_manager = get_db_manager()
        
        # Count active jobs for user
        query = """
            SELECT COUNT(*) as job_count
            FROM upload_pipeline.upload_jobs uj
            JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
            WHERE d.user_id = $1 
            AND uj.status IN ('uploaded', 'parse_queued', 'parsed', 'parse_validated', 
                             'chunking', 'chunks_stored', 'embedding_queued', 
                             'embedding_in_progress')
        """
        
        async with db_manager.transaction() as tx:
            result = await tx.fetchrow(query, user_id)
            active_jobs = result["job_count"] if result else 0
        
        if active_jobs >= config.upload.max_concurrent_jobs_per_user:
            logger.warning(
                "Concurrent job limit exceeded",
                correlation_id=str(correlation_id),
                user_id=user_id,
                active_jobs=active_jobs,
                limit=config.upload.max_concurrent_jobs_per_user
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum concurrent jobs ({config.upload.max_concurrent_jobs_per_user}) exceeded"
            )
        
        logger.debug(
            "Concurrent job limit check passed",
            correlation_id=str(correlation_id),
            user_id=user_id,
            active_jobs=active_jobs,
            limit=config.upload.max_concurrent_jobs_per_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Concurrent job limit check failed",
            correlation_id=str(correlation_id),
            user_id=user_id,
            error=str(e)
        )
        raise ValidationError(f"Failed to check concurrent job limits: {e}")

async def _check_duplicate_document(
    user_id: str, 
    file_sha256: str, 
    correlation_id: UUID
) -> Optional[Dict[str, Any]]:
    """Check if document with same hash already exists for user"""
    
    try:
        db_manager = get_db_manager()
        config = get_enhanced_config()
        
        query = """
            SELECT d.document_id, d.filename, d.raw_path
            FROM upload_pipeline.documents d
            WHERE d.user_id = $1 AND d.file_sha256 = $2
            ORDER BY d.created_at DESC
            LIMIT 1
        """
        
        async with db_manager.transaction() as tx:
            result = await tx.fetchrow(query, user_id, file_sha256)
        
        if not result:
            return None
        
        # Check if there's an active job for this document
        job_query = """
            SELECT job_id, status
            FROM upload_pipeline.upload_jobs
            WHERE document_id = $1 
            AND status IN ('uploaded', 'parse_queued', 'parsed', 'parse_validated', 
                          'chunking', 'chunks_stored', 'embedding_queued', 
                          'embedding_in_progress')
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        async with db_manager.transaction() as tx:
            job_result = await tx.fetchrow(job_query, result["document_id"])
        
        # Generate signed URL for existing file
        storage_manager = get_storage_manager()
        signed_url = await storage_manager._get_signed_url(
            config.storage.raw_bucket,
            result["raw_path"].split("/", 1)[1] if "/" in result["raw_path"] else result["raw_path"],
            "POST"
        )
        upload_expires_at = datetime.utcnow() + timedelta(seconds=config.storage.signed_url_ttl_seconds)
        
        logger.info(
            "Duplicate document found",
            correlation_id=str(correlation_id),
            user_id=user_id,
            file_sha256=file_sha256,
            existing_document_id=str(result["document_id"])
        )
        
        return {
            "document_id": result["document_id"],
            "job_id": job_result["job_id"] if job_result else None,
            "signed_url": signed_url,
            "upload_expires_at": upload_expires_at
        }
        
    except Exception as e:
        logger.error(
            "Duplicate document check failed",
            correlation_id=str(correlation_id),
            user_id=user_id,
            file_sha256=file_sha256,
            error=str(e)
        )
        raise ValidationError(f"Failed to check for duplicate document: {e}")

async def _create_document_record(
    document_id: str,
    user_id: str,
    filename: str,
    mime: str,
    bytes_len: int,
    file_sha256: str,
    raw_path: str,
    correlation_id: UUID
) -> None:
    """Create a new document record in the database"""
    
    try:
        db_manager = get_db_manager()
        
        query = """
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """
        
        async with db_manager.transaction() as tx:
            await tx.execute(
                query,
                document_id,
                user_id,
                filename,
                mime,
                bytes_len,
                file_sha256,
                raw_path
            )
        
        logger.info(
            "Document record created",
            correlation_id=str(correlation_id),
            document_id=document_id,
            user_id=user_id,
            filename=filename
        )
        
    except Exception as e:
        logger.error(
            "Failed to create document record",
            correlation_id=str(correlation_id),
            document_id=document_id,
            user_id=user_id,
            error=str(e)
        )
        raise ValidationError(f"Failed to create document record: {e}")

async def _create_enhanced_upload_job(
    job_id: str,
    document_id: str,
    user_id: str,
    request: UploadRequest,
    raw_path: str,
    service_router: ServiceRouter,
    correlation_id: UUID
) -> None:
    """Create a new enhanced upload job with service tracking"""
    
    try:
        config = get_enhanced_config()
        db_manager = get_db_manager()
        
        # Get service router configuration
        service_router_config = service_router.get_config()
        
        # Get service health status
        health_status = await service_router.get_health_status()
        
        # Create enhanced job payload
        job_payload = {
            "user_id": str(user_id),
            "document_id": str(document_id),
            "file_sha256": request.sha256,
            "bytes_len": request.bytes_len,
            "mime": request.mime,
            "storage_path": raw_path,
            "service_mode": config.service_mode.value,
            "correlation_id": str(correlation_id),
            "service_router_config": service_router_config,
            "service_health_status": health_status,
            "cost_tracking_enabled": True,
            "processing_priority": 0
        }
        
        query = """
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, user_id, status, raw_path, 
                chunks_version, embed_model, embed_version, progress, 
                retry_count, correlation_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
        """
        
        async with db_manager.transaction() as tx:
            await tx.execute(
                query,
                job_id,
                document_id,
                user_id,
                "uploaded",  # Start in uploaded status per 003 state machine
                raw_path,
                "markdown-simple@1",  # Default chunking version
                "text-embedding-3-small",  # Default embedding model
                "1",  # Default embedding version
                job_payload,  # Store enhanced payload in progress field
                0,  # retry_count
                correlation_id
            )
        
        logger.info(
            "Enhanced upload job created",
            correlation_id=str(correlation_id),
            job_id=job_id,
            document_id=document_id,
            user_id=user_id,
            service_mode=config.service_mode.value
        )
        
    except Exception as e:
        logger.error(
            "Failed to create enhanced upload job",
            correlation_id=str(correlation_id),
            job_id=job_id,
            document_id=document_id,
            error=str(e)
        )
        raise ValidationError(f"Failed to create upload job: {e}")

async def _log_upload_event(
    job_id: str,
    document_id: str,
    correlation_id: UUID,
    event_type: str,
    payload: Dict[str, Any]
) -> None:
    """Log upload event for monitoring and debugging"""
    
    try:
        db_manager = get_db_manager()
        
        query = """
            INSERT INTO upload_pipeline.events (
                event_id, job_id, document_id, type, severity, code, 
                payload, correlation_id, ts
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        """
        
        event_id = uuid4()
        
        async with db_manager.transaction() as tx:
            await tx.execute(
                query,
                event_id,
                job_id,
                document_id,
                "stage_started",  # Event type
                "info",  # Severity
                event_type,  # Event code
                payload,  # Event payload
                correlation_id
            )
        
        logger.debug(
            "Upload event logged",
            correlation_id=str(correlation_id),
            event_id=str(event_id),
            event_type=event_type
        )
        
    except Exception as e:
        logger.warning(
            "Failed to log upload event",
            correlation_id=str(correlation_id),
            event_type=event_type,
            error=str(e)
        )
        # Don't fail the upload if logging fails

def _generate_document_id(user_id: str, file_sha256: str) -> str:
    """Generate deterministic document ID"""
    # Use UUIDv5 with user_id and file hash for deterministic generation
    from uuid import uuid5, UUID
    
    # Create namespace from user_id
    namespace = UUID("6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42")
    canonical_string = f"{user_id}:{file_sha256}"
    return str(uuid5(namespace, canonical_string.lower()))

def _generate_storage_path(bucket: str, user_id: str, document_id: str, extension: str) -> str:
    """Generate storage path for document"""
    return f"storage://{bucket}/{user_id}/{document_id}.{extension}"

@router.get("/upload/limits")
async def get_upload_limits():
    """Get upload limits and constraints"""
    
    try:
        config = get_enhanced_config()
        
        return {
            "max_file_size_bytes": config.upload.max_file_size_bytes,
            "max_pages": config.upload.max_pages,
            "max_concurrent_jobs_per_user": config.upload.max_concurrent_jobs_per_user,
            "max_uploads_per_day_per_user": config.upload.max_uploads_per_day_per_user,
            "supported_mime_types": ["application/pdf"],
            "signed_url_ttl_seconds": config.storage.signed_url_ttl_seconds,
            "service_mode": config.service_mode.value,
            "cost_limits": {
                "daily_limit_usd": config.cost_control.daily_cost_limit_usd,
                "hourly_limit_usd": config.cost_control.hourly_cost_limit_usd
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get upload limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upload limits"
        )

@router.get("/upload/health")
async def get_upload_health():
    """Get upload service health status"""
    
    try:
        service_router = get_service_router()
        cost_tracker = get_cost_tracker()
        config = get_enhanced_config()
        
        # Get service health status
        service_health = await service_router.get_health_status()
        
        # Get cost tracking status
        cost_status = await cost_tracker.get_status()
        
        return {
            "status": "healthy",
            "service": "upload",
            "timestamp": datetime.utcnow().isoformat(),
            "service_mode": config.service_mode.value,
            "service_health": service_health,
            "cost_tracking": cost_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get upload health: {e}")
        return {
            "status": "unhealthy",
            "service": "upload",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
