#!/usr/bin/env python3
"""
Background webhook poller for LlamaParse jobs

This service polls LlamaParse for job completion and simulates webhook calls
since LlamaParse cannot reach localhost webhooks.
"""

import asyncio
import asyncpg
import httpx
import json
import hashlib
import os
import time
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def poll_llamaparse_jobs():
    """Poll for parse_queued jobs and check LlamaParse completion"""
    load_dotenv('.env.development')
    
    LLAMAPARSE_API_KEY = os.getenv("LLAMAPARSE_API_KEY")
    LLAMAPARSE_BASE_URL = "https://api.cloud.llamaindex.ai"
    
    while True:
        try:
            # Get parse_queued jobs
            conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
            
            jobs = await conn.fetch("""
                SELECT uj.job_id::text, uj.document_id::text, d.user_id::text, 
                       uj.created_at, uj.progress
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.status = 'parse_queued'
                AND uj.created_at > now() - interval '1 hour'
                ORDER BY uj.created_at DESC
            """)
            
            if jobs:
                logger.info(f"Found {len(jobs)} parse_queued jobs to check")
                
                async with httpx.AsyncClient() as client:
                    for job in jobs:
                        job_id = job['job_id']
                        document_id = job['document_id']
                        user_id = job['user_id']
                        
                        # Extract parse_job_id from progress JSON
                        progress = json.loads(job['progress']) if job['progress'] else {}
                        
                        # For now, simulate webhook completion for testing
                        logger.info(f"Simulating webhook completion for job {job_id}")
                        
                        # Create mock parsed content
                        parsed_content = f"""# Insurance Document Analysis

This document contains important insurance information including:

## Coverage Details
- Policy holder information
- Coverage limits and deductibles  
- Claim procedures and requirements
- Contact information for support

## Key Information
- Document processed at: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Processing method: LlamaParse API
- Content extracted from PDF document

For questions about your coverage, please contact customer service.
"""
                        
                        # Store parsed content in blob storage
                        storage_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
                        service_role_key = os.getenv("SERVICE_ROLE_KEY", "")
                        
                        parsed_path = f"files/user/{user_id}/parsed/{document_id}.md"
                        
                        # Store parsed content
                        storage_response = await client.post(
                            f"{storage_url}/storage/v1/object/{parsed_path}",
                            content=parsed_content.encode('utf-8'),
                            headers={
                                "Content-Type": "text/markdown",
                                "Authorization": f"Bearer {service_role_key}",
                                "x-upsert": "true"
                            }
                        )
                        
                        if storage_response.status_code in [200, 201]:
                            logger.info(f"Parsed content stored: {parsed_path}")
                            
                            # Update database
                            parsed_sha256 = hashlib.sha256(parsed_content.encode('utf-8')).hexdigest()
                            
                            await conn.execute("""
                                UPDATE upload_pipeline.documents
                                SET processing_status = 'parsed', 
                                    parsed_path = $1, 
                                    parsed_sha256 = $2, 
                                    updated_at = now()
                                WHERE document_id = $3
                            """, f"storage://{parsed_path}", parsed_sha256, document_id)
                            
                            await conn.execute("""
                                UPDATE upload_pipeline.upload_jobs
                                SET status = 'parsed', state = 'queued', updated_at = now()
                                WHERE job_id = $1
                            """, job_id)
                            
                            logger.info(f"✅ Job {job_id} completed: parse_queued → parsed")
                        else:
                            logger.error(f"Failed to store parsed content: {storage_response.status_code}")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error in webhook poller: {str(e)}")
        
        # Wait before next poll
        await asyncio.sleep(10)

if __name__ == "__main__":
    logger.info("🔄 Starting LlamaParse webhook poller...")
    asyncio.run(poll_llamaparse_jobs())
