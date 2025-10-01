"""
Webhook handlers for external service callbacks.
"""

import json
import logging
import hmac
import hashlib
import os
import httpx
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from .database import get_database

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/llamaparse/{job_id}")
async def llamaparse_webhook(job_id: str, request: Request):
    """Handle LlamaParse webhook callbacks for document parsing completion."""
    try:
        # FM-027: Enhanced webhook logging for complete flow tracking
        logger.info(f"🔔 FM-027 WEBHOOK START: Received webhook for job: {job_id}")
        logger.info(f"🔔 FM-027 WEBHOOK HEADERS: {dict(request.headers)}")
        logger.info(f"🔔 FM-027 WEBHOOK URL: {request.url}")
        logger.info(f"🔔 FM-027 WEBHOOK METHOD: {request.method}")
        logger.info(f"🔔 FM-027 WEBHOOK CLIENT: {request.client}")
        
        # Get the raw body for signature verification
        body = await request.body()
        logger.info(f"🔔 FM-027 WEBHOOK BODY SIZE: {len(body)} bytes")
        logger.info(f"🔔 FM-027 WEBHOOK BODY PREVIEW: {body[:200] if body else 'EMPTY'}")
        
        # Get webhook secret from database
        logger.info(f"🔔 DATABASE STEP 1: Getting database connection")
        db = get_database()
        logger.info(f"🔔 DATABASE STEP 2: Database connection obtained: {db is not None}")
        
        async with db.get_connection() as conn:
            logger.info(f"🔔 DATABASE STEP 3: Database connection established")
            logger.info(f"🔔 DATABASE STEP 4: Executing job lookup query for job_id: {job_id}")
            
            job = await conn.fetchrow("""
                SELECT uj.webhook_secret, uj.document_id, uj.status, d.user_id
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.job_id = $1
            """, job_id)
            
            logger.info(f"🔔 DATABASE STEP 5: Job lookup result: {job is not None}")
            if job:
                logger.info(f"🔔 DATABASE STEP 6: Job found - document_id: {job['document_id']}, status: {job['status']}, user_id: {job['user_id']}")
            else:
                logger.error(f"🔔 DATABASE STEP 6: Job not found for job_id: {job_id}")
            
            if not job:
                logger.error(f"Webhook received for unknown job: {job_id}")
                raise HTTPException(status_code=404, detail="Job not found")
            
            webhook_secret = job["webhook_secret"]
            document_id = job["document_id"]
            current_status = job["status"]
            user_id = job["user_id"]
            
            logger.info(f"🔔 DATABASE STEP 7: Job data extracted - webhook_secret: {webhook_secret is not None}, document_id: {document_id}, current_status: {current_status}, user_id: {user_id}")
        
        # Verify webhook signature (if provided)
        logger.info(f"🔔 SIGNATURE STEP 1: Checking webhook signature")
        signature = request.headers.get("X-Webhook-Signature")
        logger.info(f"🔔 SIGNATURE STEP 2: Signature header: {signature is not None}, webhook_secret: {webhook_secret is not None}")
        
        if signature and webhook_secret:
            logger.info(f"🔔 SIGNATURE STEP 3: Verifying webhook signature")
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.error(f"🔔 SIGNATURE STEP 4: Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            else:
                logger.info(f"🔔 SIGNATURE STEP 4: Webhook signature verified successfully")
        else:
            logger.info(f"🔔 SIGNATURE STEP 3: Skipping signature verification (no signature or secret)")
        
        # Parse the webhook payload
        logger.info(f"🔔 PAYLOAD STEP 1: Parsing webhook payload")
        payload = await request.json()
        logger.info(f"🔔 PAYLOAD STEP 2: Payload parsed successfully")
        
        logger.info(
            f"🔔 PAYLOAD STEP 3: Received LlamaParse webhook for job {job_id}, document {document_id}, status {payload.get('status')}"
        )
        logger.info(f"🔔 PAYLOAD STEP 4: Webhook payload keys: {list(payload.keys())}")
        logger.info(f"🔔 PAYLOAD STEP 5: Full webhook payload: {payload}")
        logger.info(f"🔔 PAYLOAD STEP 6: Markdown content: '{payload.get('md', 'NOT_FOUND')}'")
        logger.info(f"🔔 PAYLOAD STEP 7: Text content: '{payload.get('txt', 'NOT_FOUND')}'")
        logger.info(f"🔔 PAYLOAD STEP 8: JSON content: '{payload.get('json', 'NOT_FOUND')}'")
        logger.info(f"🔔 PAYLOAD STEP 9: Parsed content: '{payload.get('parsed_content', 'NOT_FOUND')}'")
        logger.info(f"🔔 PAYLOAD STEP 10: Result: {payload.get('result', 'NOT_FOUND')}")
        
        # Handle different webhook statuses
        logger.info(f"🔔 PROCESSING STEP 1: Checking webhook status")
        webhook_status = payload.get("status")
        logger.info(f"🔔 PROCESSING STEP 2: Webhook status: {webhook_status}")
        
        # Process both 'completed' status and None status (some webhooks don't include status)
        if webhook_status == "completed" or webhook_status is None:
            logger.info(f"🔔 PROCESSING STEP 3: Processing completed webhook")
            
            # Get parsed content from webhook payload
            logger.info(f"🔔 CONTENT STEP 1: Extracting parsed content from payload")
            # LlamaParse sends content in 'result' object with 'txt', 'md', and 'json' fields
            result = payload.get("result", {})
            logger.info(f"🔔 CONTENT STEP 1.1: Result object type: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if isinstance(result, list):
                # Multi-page document - concatenate all pages
                logger.info(f"🔔 CONTENT STEP 1.2: Processing multi-page document with {len(result)} pages")
                parsed_content = "\n\n".join([
                    page.get("md", "") or page.get("txt", "") or page.get("parsed_content", "")
                    for page in result
                    if page.get("md") or page.get("txt") or page.get("parsed_content")
                ])
                logger.info(f"🔔 CONTENT STEP 1.3: Multi-page content extracted - length: {len(parsed_content)}")
            elif isinstance(result, dict):
                # Single page document
                logger.info(f"🔔 CONTENT STEP 1.2: Processing single-page document")
                parsed_content = (
                    result.get("md", "") or
                    result.get("txt", "") or
                    result.get("parsed_content", "") or
                    # Fallback to old format for backward compatibility
                    payload.get("md", "") or
                    payload.get("txt", "") or
                    payload.get("parsed_content", "")
                )
                logger.info(f"🔔 CONTENT STEP 1.3: Single-page content extracted - length: {len(parsed_content)}")
            else:
                # Fallback to old format for backward compatibility
                logger.info(f"🔔 CONTENT STEP 1.2: Using fallback format (no result object)")
                parsed_content = (
                    payload.get("md", "") or
                    payload.get("txt", "") or
                    payload.get("parsed_content", "")
                )
                logger.info(f"🔔 CONTENT STEP 1.3: Fallback content extracted - length: {len(parsed_content)}")
            
            logger.info(f"🔔 CONTENT STEP 2: Parsed content extracted - length: {len(parsed_content) if parsed_content else 0}")
            logger.info(f"🔔 CONTENT STEP 3: Parsed content preview: '{parsed_content[:200] if parsed_content else 'EMPTY'}...'")
            
            if not parsed_content:
                logger.error(f"🔔 CONTENT STEP 4: No parsed content received for document {document_id}")
                # Mark as failed if no content
                logger.info(f"🔔 CONTENT STEP 5: Updating job status to failed_parse")
                async with db.get_connection() as conn:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET status = 'failed_parse', state = 'done', 
                            last_error = $1, updated_at = now()
                        WHERE job_id = $2
                    """, json.dumps({"error": "No parsed content received from LlamaParse"}), job_id)
                logger.info(f"🔔 CONTENT STEP 6: Job status updated to failed_parse")
                return {"status": "error", "message": "No parsed content received"}
            else:
                logger.info(f"🔔 CONTENT STEP 4: Parsed content received successfully - length: {len(parsed_content)}")
            
            # Generate storage path for parsed content using standardized function
            logger.info(f"🔔 STORAGE STEP 1: Generating storage path")
            from api.upload_pipeline.utils.upload_pipeline_utils import generate_parsed_path
            parsed_path = f"storage://{generate_parsed_path(job['user_id'], document_id)}"
            logger.info(f"🔔 STORAGE STEP 2: Generated parsed_path: {parsed_path}")
            
            # Store parsed content in blob storage
            logger.info(f"🔔 STORAGE STEP 3: Starting blob storage upload for document {document_id}")
            
            # Store the parsed content in blob storage using direct HTTP request
            logger.info(f"🔔 STORAGE STEP 4: Using httpx for HTTP client")
            
            # Extract bucket and key from file path
            logger.info(f"🔔 STORAGE STEP 5: Extracting bucket and key from parsed_path")
            # Format: storage://files/user/{user_id}/parsed/{document_id}.md
            path_parts = parsed_path[10:].split("/", 1)  # Remove "storage://" prefix
            logger.info(f"🔔 STORAGE STEP 6: Path parts: {path_parts}")
            
            if len(path_parts) == 2:
                bucket, key = path_parts
                logger.info(f"🔔 STORAGE STEP 7: Extracted bucket: {bucket}, key: {key}")
            else:
                logger.error(f"🔔 STORAGE STEP 7: Invalid parsed_path format: {parsed_path}")
                raise ValueError(f"Invalid parsed_path format: {parsed_path}")
            
            logger.info(f"🔔 STORAGE STEP 8: Uploading parsed content to bucket: {bucket}, key: {key}")
            
            # Use direct HTTP request with service role key (same as upload endpoint)
            logger.info(f"🔔 STORAGE STEP 9: Getting environment variables")
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not service_role_key:
                logger.error(f"🔔 STORAGE STEP 10: SUPABASE_SERVICE_ROLE_KEY environment variable is required")
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
            else:
                logger.info(f"🔔 STORAGE STEP 10: SUPABASE_SERVICE_ROLE_KEY found")
            
            storage_url = os.getenv("SUPABASE_URL")
            if not storage_url:
                logger.error(f"🔔 STORAGE STEP 11: SUPABASE_URL environment variable is required")
                raise ValueError("SUPABASE_URL environment variable is required")
            else:
                logger.info(f"🔔 STORAGE STEP 11: SUPABASE_URL found: {storage_url}")
            
            logger.info(f"🔔 STORAGE STEP 12: Creating HTTP client and making storage request")
            async with httpx.AsyncClient() as client:
                storage_endpoint = f"{storage_url}/storage/v1/object/{bucket}/{key}"
                logger.info(f"🔔 STORAGE STEP 13: Storage endpoint: {storage_endpoint}")
                
                response = await client.put(
                    storage_endpoint,
                    content=parsed_content.encode('utf-8'),
                    headers={
                        "Content-Type": "text/markdown",
                        "Authorization": f"Bearer {service_role_key}"
                    }
                )
                
                logger.info(f"🔔 STORAGE STEP 14: Storage upload response: {response.status_code} - {response.text}")
                
                success = response.status_code in [200, 201]
                logger.info(f"🔔 STORAGE STEP 15: Storage upload success: {success}")
            
            if not success:
                logger.error(f"🔔 STORAGE STEP 16: Failed to store parsed content for document {document_id}")
                logger.info(f"🔔 STORAGE STEP 17: Updating job status to failed_parse")
                async with db.get_connection() as conn:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET status = 'failed_parse', state = 'done', 
                            last_error = $1, updated_at = now()
                        WHERE job_id = $2
                    """, json.dumps({"error": "Failed to store parsed content"}), job_id)
                logger.info(f"🔔 STORAGE STEP 18: Job status updated to failed_parse")
                return {"status": "error", "message": "Failed to store parsed content"}
            else:
                logger.info(f"🔔 STORAGE STEP 16: Storage upload successful")
            
            # Compute SHA256 hash of parsed content
            logger.info(f"🔔 DATABASE STEP 1: Computing SHA256 hash of parsed content")
            parsed_sha256 = hashlib.sha256(parsed_content.encode('utf-8')).hexdigest()
            logger.info(f"🔔 DATABASE STEP 2: SHA256 hash computed: {parsed_sha256[:16]}...")
            
            # Update database with parsed content info
            logger.info(f"🔔 DATABASE STEP 3: Updating database with parsed content info")
            async with db.get_connection() as conn:
                logger.info(f"🔔 DATABASE STEP 4: Database connection established for updates")
                
                # Update document with parsed content info
                logger.info(f"🔔 DATABASE STEP 5: Updating document record")
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET processing_status = 'parsed', parsed_path = $1, parsed_sha256 = $2, updated_at = now()
                    WHERE document_id = $3
                """, parsed_path, parsed_sha256, document_id)
                logger.info(f"🔔 DATABASE STEP 6: Document record updated successfully")
                
                # Update job status to parsed and ready for next stage
                logger.info(f"🔔 DATABASE STEP 7: Updating job status to parsed")
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'parsed', state = 'queued', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                logger.info(f"🔔 DATABASE STEP 8: Job status updated to parsed successfully")
            
            logger.info(
                f"🔔 COMPLETION: Document parsing completed and stored for job {job_id}, document {document_id}, path {parsed_path}, size {len(parsed_content)}"
            )
            
        elif payload.get("status") == "failed":
            # Handle parsing failure
            logger.info(f"🔔 ERROR STEP 1: Processing failed webhook")
            error_message = payload.get("error", "Unknown parsing error")
            logger.info(f"🔔 ERROR STEP 2: Error message: {error_message}")
            
            logger.info(f"🔔 ERROR STEP 3: Updating job status to failed_parse")
            async with db.get_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'failed_parse', state = 'done', 
                        last_error = $1, updated_at = now()
                    WHERE job_id = $2
                """, json.dumps({"error": error_message}), job_id)
            logger.info(f"🔔 ERROR STEP 4: Job status updated to failed_parse")
            
            logger.error(
                f"🔔 ERROR STEP 5: Document parsing failed for job {job_id}, document {document_id}: {error_message}"
            )
        else:
            logger.info(f"🔔 UNKNOWN STEP 1: Unknown webhook status: {webhook_status}")
        
        logger.info(f"🔔 SUCCESS: Webhook processing completed successfully")
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(
            f"🔔 EXCEPTION: Webhook processing failed for job {job_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Webhook processing failed")
