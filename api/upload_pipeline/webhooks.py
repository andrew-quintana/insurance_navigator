"""
Webhook handlers for external service callbacks.
"""

import json
import logging
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from .database import get_database

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/llamaparse/{job_id}")
async def llamaparse_webhook(job_id: str, request: Request):
    """Handle LlamaParse webhook callbacks for document parsing completion."""
    try:
        # Get the raw body for signature verification
        body = await request.body()
        
        # Get webhook secret from database
        db = get_database()
        async with db.get_db_connection() as conn:
            job = await conn.fetchrow("""
                SELECT webhook_secret, document_id, status
                FROM upload_pipeline.upload_jobs
                WHERE job_id = $1
            """, job_id)
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            webhook_secret = job["webhook_secret"]
            document_id = job["document_id"]
            current_status = job["status"]
        
        # Verify webhook signature (if provided)
        signature = request.headers.get("X-Webhook-Signature")
        if signature and webhook_secret:
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse the webhook payload
        payload = await request.json()
        
        logger.info(
            "Received LlamaParse webhook",
            job_id=job_id,
            document_id=document_id,
            status=payload.get("status")
        )
        
        # Handle different webhook statuses
        if payload.get("status") == "completed":
            # Update document with parsed content
            parsed_content = payload.get("result", {}).get("markdown", "")
            parsed_path = f"parsed/{document_id}.md"
            
            # Store parsed content in storage (mock for now)
            # In production, this would upload to Supabase storage
            logger.info(f"Storing parsed content for document {document_id}")
            
            # Update document record
            async with db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET parsed_path = $1, parsed_sha256 = $2, updated_at = now()
                    WHERE document_id = $3
                """, parsed_path, "parsed_sha256_hash", document_id)
                
                # Advance job to parsed status
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'parsed', state = 'queued', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
            
            logger.info(
                "Document parsing completed",
                job_id=job_id,
                document_id=document_id
            )
            
        elif payload.get("status") == "failed":
            # Handle parsing failure
            error_message = payload.get("error", "Unknown parsing error")
            
            async with db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'failed_parse', state = 'done', 
                        last_error = $1, updated_at = now()
                    WHERE job_id = $2
                """, json.dumps({"error": error_message}), job_id)
            
            logger.error(
                "Document parsing failed",
                job_id=job_id,
                document_id=document_id,
                error=error_message
            )
        
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(
            "Webhook processing failed",
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Webhook processing failed")
