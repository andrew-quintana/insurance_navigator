"""
Webhook handlers for external service callbacks.
"""

import json
import logging
import hmac
import hashlib
import os
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from core import get_database
from backend.shared.storage import StorageManager

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
        logger.info(f"Full webhook payload: {payload}")
        logger.info(f"Markdown content: '{payload.get('md', 'NOT_FOUND')}'")
        logger.info(f"Text content: '{payload.get('txt', 'NOT_FOUND')}'")
        logger.info(f"JSON content: '{payload.get('json', 'NOT_FOUND')}'")
        logger.info(f"Parsed content: '{payload.get('parsed_content', 'NOT_FOUND')}'")
        logger.info(f"Result: {payload.get('result', 'NOT_FOUND')}")
        
        # Handle different webhook statuses
        # Process both 'completed' status and None status (some webhooks don't include status)
        if payload.get("status") == "completed" or payload.get("status") is None:
            # Get parsed content from webhook payload
            # LlamaParse sends content in 'txt', 'md', and 'json' fields
            parsed_content = (
                payload.get("md", "") or  # Markdown format (preferred)
                payload.get("txt", "") or  # Raw text format
                payload.get("json", "") or  # JSON format (might contain content)
                payload.get("parsed_content", "") or  # Fallback to old format
                payload.get("result", {}).get("markdown", "")  # Another fallback
            )
            
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
            # Format: storage://files/user/{user_id}/parsed/{document_id}.md
            parsed_path = f"storage://files/user/{job['user_id']}/parsed/{document_id}.md"
            
            # Store parsed content in blob storage
            logger.info(f"Parsed content received, storing in blob storage for document {document_id}")
            
            # Store the parsed content in blob storage using direct HTTP request
            import httpx
            
            # Extract bucket and key from parsed_path
            # Format: storage://files/user/{user_id}/parsed/{document_id}.md
            path_parts = parsed_path[10:].split("/", 1)  # Remove "storage://" prefix
            if len(path_parts) == 2:
                bucket, key = path_parts
            else:
                raise ValueError(f"Invalid parsed_path format: {parsed_path}")
            
            logger.info(f"Uploading parsed content to bucket: {bucket}, key: {key}")
            
            # Use direct HTTP request with service role key (same as upload endpoint)
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not service_role_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
            
            storage_url = os.getenv("SUPABASE_URL")
            if not storage_url:
                raise ValueError("SUPABASE_URL environment variable is required")
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{storage_url}/storage/v1/object/{bucket}/{key}",
                    content=parsed_content.encode('utf-8'),
                    headers={
                        "Content-Type": "text/markdown",
                        "Authorization": f"Bearer {service_role_key}"
                    }
                )
                
                logger.info(f"Storage upload response: {response.status_code} - {response.text}")
                
                success = response.status_code in [200, 201]
            
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
            
            async with db.get_connection() as conn:
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
