"""
Webhook handlers for external service callbacks.

This module provides secure webhook handling for LlamaParse and other external services,
including HMAC signature verification and job state management integration.
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, ValidationError

from backend.shared.external.service_router import ServiceRouter
from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.schemas.webhooks import LlamaParseWebhookRequest, LlamaParseWebhookResponse
from backend.shared.exceptions import WebhookError, ValidationError as SharedValidationError
from backend.shared.config.enhanced_config import get_config
from backend.shared.db.connection import DatabaseManager
from backend.shared.storage.storage_manager import StorageManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get service router
async def get_service_router() -> ServiceRouter:
    """Get service router instance."""
    config = get_config()
    return ServiceRouter(mode=config.service_mode)

# Dependency to get LlamaParse service
async def get_llamaparse_service() -> RealLlamaParseService:
    """Get LlamaParse service instance."""
    config = get_config()
    return RealLlamaParseService(
        api_key=config.llamaparse.api_key,
        base_url=config.llamaparse.base_url,
        webhook_secret=config.llamaparse.webhook_secret
    )

# Dependency to get database manager
async def get_db_manager() -> DatabaseManager:
    """Get database manager instance."""
    config = get_config()
    db_manager = DatabaseManager(config.database_url)
    await db_manager.initialize()
    return db_manager

# Dependency to get storage manager
async def get_storage_manager() -> StorageManager:
    """Get storage manager instance."""
    config = get_config()
    return StorageManager(
        url=config.supabase.url,
        anon_key=config.supabase.anon_key,
        service_role_key=config.supabase.service_role_key
    )

def verify_webhook_signature(
    payload: bytes, 
    signature: str, 
    secret: str
) -> bool:
    """
    Verify webhook HMAC signature for security.
    
    Args:
        payload: Raw webhook payload
        signature: Webhook signature header
        secret: Webhook secret for verification
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return False

@router.post("/llamaparse", response_model=LlamaParseWebhookResponse)
async def llamaparse_webhook(
    request: Request,
    service_router: ServiceRouter = Depends(get_service_router),
    llamaparse_service: RealLlamaParseService = Depends(get_llamaparse_service),
    db_manager: DatabaseManager = Depends(get_db_manager),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """
    Handle LlamaParse webhook callbacks.
    
    This endpoint receives parsing completion notifications from LlamaParse
    and updates the corresponding job state in the system.
    """
    try:
        # Get raw payload for signature verification
        raw_payload = await request.body()
        
        # Extract signature header
        signature = request.headers.get("X-Webhook-Signature")
        if not signature:
            logger.warning("Missing webhook signature header")
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        
        # Verify webhook signature
        config = get_config()
        if not verify_webhook_signature(
            raw_payload, 
            signature, 
            config.llamaparse.webhook_secret
        ):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse webhook payload
        try:
            webhook_data = json.loads(raw_payload)
            webhook_request = LlamaParseWebhookRequest(**webhook_data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        
        # Extract correlation ID for tracking
        correlation_id = webhook_request.correlation_id
        if not correlation_id:
            logger.warning("Missing correlation ID in webhook")
            raise HTTPException(status_code=400, detail="Missing correlation ID")
        
        logger.info(
            f"Processing LlamaParse webhook",
            extra={
                "correlation_id": correlation_id,
                "parse_job_id": webhook_request.parse_job_id,
                "status": webhook_request.status
            }
        )
        
        # Process webhook based on status
        if webhook_request.status == "parsed":
            await _handle_parsed_status(webhook_request, service_router, correlation_id, db_manager, storage_manager)
        elif webhook_request.status == "failed":
            await _handle_failed_status(webhook_request, service_router, correlation_id, db_manager)
        else:
            logger.info(f"Unhandled webhook status: {webhook_request.status}")
        
        # Return success response
        return LlamaParseWebhookResponse(
            success=True,
            message="Webhook processed successfully",
            job_id=webhook_request.job_id,
            document_id=webhook_request.document_id,
            processed_at=datetime.utcnow()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def _handle_parsed_status(
    webhook_request: LlamaParseWebhookRequest,
    service_router: ServiceRouter,
    correlation_id: str,
    db_manager: DatabaseManager,
    storage_manager: StorageManager
):
    """Handle successful parsing completion."""
    try:
        logger.info(
            f"Processing successful parse completion",
            extra={
                "correlation_id": correlation_id,
                "parse_job_id": webhook_request.parse_job_id,
                "artifact_count": len(webhook_request.artifacts)
            }
        )
        
        # Extract parsed content from artifacts
        if not webhook_request.artifacts:
            logger.warning(f"No artifacts found in parsed webhook for {correlation_id}")
            return
        
        # Find markdown artifact
        markdown_artifact = None
        for artifact in webhook_request.artifacts:
            if artifact.type == "markdown":
                markdown_artifact = artifact
                break
        
        if not markdown_artifact:
            logger.warning(f"No markdown artifact found for {correlation_id}")
            return
        
        # Store parsed content to storage
        parsed_path = f"storage://parsed/{webhook_request.document_id}/{webhook_request.job_id}.md"
        content_stored = await storage_manager.write_blob(
            parsed_path, 
            markdown_artifact.content, 
            "text/markdown"
        )
        
        if not content_stored:
            raise Exception(f"Failed to store parsed content for {correlation_id}")
        
        # Update job status to parsed with database transaction
        async with db_manager.get_db_connection() as conn:
            # Update job status and parsed content path
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'parsed', 
                    parsed_path = $1, 
                    parsed_sha256 = $2,
                    updated_at = now()
                WHERE job_id = $3
            """, parsed_path, markdown_artifact.sha256, webhook_request.job_id)
            
            # Log the state transition event
            event_id = uuid4()
            await conn.execute("""
                INSERT INTO upload_pipeline.events (
                    event_id, job_id, document_id, type, severity, code, 
                    payload, correlation_id, ts
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            """, 
                str(event_id),
                webhook_request.job_id,
                webhook_request.document_id,
                "stage_done",  # Event type
                "info",  # Severity
                "parse_completed",  # Event code
                json.dumps({
                    "parsed_path": parsed_path,
                    "content_sha256": markdown_artifact.sha256,
                    "content_length": len(markdown_artifact.content),
                    "bytes": markdown_artifact.bytes,
                    "parser_name": webhook_request.meta.parser_name,
                    "parser_version": webhook_request.meta.parser_version
                }),  # Event payload
                correlation_id
            )
        
        logger.info(
            f"Successfully processed parsed content",
            extra={
                "correlation_id": correlation_id,
                "content_length": len(markdown_artifact.content),
                "content_sha256": markdown_artifact.sha256,
                "bytes": markdown_artifact.bytes,
                "parsed_path": parsed_path
            }
        )
        
        # TODO: Trigger next processing stage (parse validation)
        # This would typically involve queuing the job for the next worker stage
        # For now, we'll log that the job is ready for the next stage
        logger.info(
            f"Job ready for next processing stage",
            extra={
                "correlation_id": correlation_id,
                "job_id": str(webhook_request.job_id),
                "next_stage": "parse_validated"
            }
        )
        
    except Exception as e:
        logger.error(f"Error handling parsed status for {correlation_id}: {e}")
        raise

async def _handle_failed_status(
    webhook_request: LlamaParseWebhookRequest,
    service_router: ServiceRouter,
    correlation_id: str,
    db_manager: DatabaseManager
):
    """Handle parsing failure."""
    try:
        logger.warning(
            f"Processing parse failure",
            extra={
                "correlation_id": correlation_id,
                "parse_job_id": webhook_request.parse_job_id,
                "error": webhook_request.meta.get("error") if hasattr(webhook_request.meta, 'get') else str(webhook_request.meta)
            }
        )
        
        # Update job status to failed_parse with database transaction
        async with db_manager.get_db_connection() as conn:
            # Update job status to failed
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'failed_parse', 
                    last_error = $1,
                    updated_at = now()
                WHERE job_id = $3
            """, json.dumps({
                "error": "LlamaParse parsing failed",
                "parser_name": webhook_request.meta.parser_name,
                "parser_version": webhook_request.meta.parser_version,
                "failed_at": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id
            }), webhook_request.job_id)
            
            # Log the failure event
            event_id = uuid4()
            await conn.execute("""
                INSERT INTO upload_pipeline.events (
                    event_id, job_id, document_id, type, severity, code, 
                    payload, correlation_id, ts
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            """, 
                str(event_id),
                webhook_request.job_id,
                webhook_request.document_id,
                "error",  # Event type
                "error",  # Severity
                "parse_failed",  # Event code
                json.dumps({
                    "error": "LlamaParse parsing failed",
                    "parser_name": webhook_request.meta.parser_name,
                    "parser_version": webhook_request.meta.parser_version,
                    "correlation_id": correlation_id
                }),  # Event payload
                correlation_id
            )
        
        logger.info(
            f"Job marked as failed_parse",
            extra={
                "correlation_id": correlation_id,
                "job_id": str(webhook_request.job_id),
                "status": "failed_parse"
            }
        )
        
        # TODO: Implement retry logic if appropriate
        # This would involve checking retry count and potentially requeuing
        # For now, we'll log that the job has failed and needs manual intervention
        logger.warning(
            f"Job failed parsing - manual intervention may be required",
            extra={
                "correlation_id": correlation_id,
                "job_id": str(webhook_request.job_id)
            }
        )
        
    except Exception as e:
        logger.error(f"Error handling failed status for {correlation_id}: {e}")
        raise

@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints."""
    return {
        "status": "healthy",
        "service": "webhook-handler",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "llamaparse": "/webhooks/llamaparse"
        }
    }
