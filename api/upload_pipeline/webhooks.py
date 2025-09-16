"""
Webhook handlers for external service callbacks.
"""

import json
import logging
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from core import get_database

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/llamaparse/{job_id}")
async def llamaparse_webhook(job_id: str, request: Request):
    """Handle LlamaParse webhook callbacks for document parsing completion."""
    try:
        logger.info(f"Received webhook for job: {job_id}")
        # Get the raw body for signature verification
        body = await request.body()
        
        # Get webhook secret from database
        db = await get_database()
        async with db.get_connection() as conn:
            job = await conn.fetchrow("""
                SELECT uj.webhook_secret, uj.document_id, uj.status, d.user_id
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.job_id = $1
            """, job_id)
            
            if not job:
                logger.error(f"Webhook received for unknown job: {job_id}")
                raise HTTPException(status_code=404, detail="Job not found")
            
            webhook_secret = job["webhook_secret"]
            document_id = job["document_id"]
            current_status = job["status"]
            user_id = job["user_id"]
        
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
            f"Received LlamaParse webhook for job {job_id}, document {document_id}, status {payload.get('status')}"
        )
        logger.info(f"Webhook payload keys: {list(payload.keys())}")
        logger.info(f"Parsed content from payload: '{payload.get('parsed_content', 'NOT_FOUND')}'")
        logger.info(f"Result from payload: {payload.get('result', 'NOT_FOUND')}")
        
        # Handle different webhook statuses
        if payload.get("status") == "completed":
            # Get parsed content from webhook payload
            # Try both formats: direct parsed_content or nested result.markdown
            parsed_content = payload.get("parsed_content", "") or payload.get("result", {}).get("markdown", "")
            
            if not parsed_content:
                logger.error(f"No parsed content received for document {document_id}")
                # Mark as failed if no content
                async with db.get_connection() as conn:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET status = 'failed_parse', state = 'done', 
                            last_error = $1, updated_at = now()
                        WHERE job_id = $2
                    """, json.dumps({"error": "No parsed content received from LlamaParse"}), job_id)
                return {"status": "error", "message": "No parsed content received"}
            
            # Generate storage path for parsed content
            parsed_path = f"files/user/{job['user_id']}/parsed/{document_id}.md"
            
            # Store parsed content in blob storage
            logger.info(f"Parsed content received, storing in blob storage for document {document_id}")
            
            # Store the parsed content in blob storage
            storage_config = {
                "storage_url": "http://localhost:54321",
                "anon_key": "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
                "service_role_key": "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nk0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
            }
            storage = StorageManager(storage_config)
            
            # Store the parsed content
            success = await storage.write_blob(parsed_path, parsed_content, "text/markdown")
            
            if not success:
                logger.error(f"Failed to store parsed content for document {document_id}")
                async with db.get_connection() as conn:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET status = 'failed_parse', state = 'done', 
                            last_error = $1, updated_at = now()
                        WHERE job_id = $2
                    """, json.dumps({"error": "Failed to store parsed content"}), job_id)
                return {"status": "error", "message": "Failed to store parsed content"}
            
            # Compute SHA256 hash of parsed content
            import hashlib
            parsed_sha256 = hashlib.sha256(parsed_content.encode('utf-8')).hexdigest()
            
            # Update database with parsed content info
            async with db.get_connection() as conn:
                # Update document with parsed content info
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET processing_status = 'parsed', parsed_path = $1, parsed_sha256 = $2, updated_at = now()
                    WHERE document_id = $3
                """, parsed_path, parsed_sha256, document_id)
                
                # Update job status to parsed and ready for next stage
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'parsed', state = 'queued', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
            
            logger.info(
                f"Document parsing completed and stored for job {job_id}, document {document_id}, path {parsed_path}, size {len(parsed_content)}"
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
                f"Document parsing failed for job {job_id}, document {document_id}: {error_message}"
            )
        
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(
            f"Webhook processing failed for job {job_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Webhook processing failed")
