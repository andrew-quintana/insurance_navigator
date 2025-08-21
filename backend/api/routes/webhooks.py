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

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, ValidationError

from backend.shared.external.service_router import ServiceRouter
from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.schemas.webhooks import LlamaParseWebhookRequest, LlamaParseWebhookResponse
from backend.shared.exceptions import WebhookError, ValidationError as SharedValidationError
from backend.shared.config.enhanced_config import get_config

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
    llamaparse_service: RealLlamaParseService = Depends(get_llamaparse_service)
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
            await _handle_parsed_status(webhook_request, service_router, correlation_id)
        elif webhook_request.status == "failed":
            await _handle_failed_status(webhook_request, service_router, correlation_id)
        else:
            logger.info(f"Unhandled webhook status: {webhook_request.status}")
        
        # Return success response
        return LlamaParseWebhookResponse(
            status="success",
            message="Webhook processed successfully",
            correlation_id=correlation_id,
            timestamp=datetime.utcnow().isoformat()
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
    correlation_id: str
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
            if artifact.get("type") == "markdown":
                markdown_artifact = artifact
                break
        
        if not markdown_artifact:
            logger.warning(f"No markdown artifact found for {correlation_id}")
            return
        
        # Update job status to parsed
        # This would integrate with the existing job state management from 003
        # For now, we'll log the successful parsing
        logger.info(
            f"Successfully processed parsed content",
            extra={
                "correlation_id": correlation_id,
                "content_length": len(markdown_artifact.get("content", "")),
                "content_sha256": markdown_artifact.get("sha256"),
                "bytes": markdown_artifact.get("bytes")
            }
        )
        
        # TODO: Integrate with 003 job state management
        # - Update job status to 'parsed'
        # - Store parsed content path
        # - Trigger next processing stage
        
    except Exception as e:
        logger.error(f"Error handling parsed status for {correlation_id}: {e}")
        raise

async def _handle_failed_status(
    webhook_request: LlamaParseWebhookRequest,
    service_router: ServiceRouter,
    correlation_id: str
):
    """Handle parsing failure."""
    try:
        logger.warning(
            f"Processing parse failure",
            extra={
                "correlation_id": correlation_id,
                "parse_job_id": webhook_request.parse_job_id,
                "error": webhook_request.meta.get("error")
            }
        )
        
        # TODO: Integrate with 003 job state management
        # - Update job status to 'failed_parse'
        # - Store error details
        # - Implement retry logic if appropriate
        
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
