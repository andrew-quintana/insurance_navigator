#!/usr/bin/env python3
"""
Simple worker to process queued upload jobs for local development.
This bypasses the complex worker dependencies and focuses on basic job processing.
"""

import asyncio
import asyncpg
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleWorker:
    """Simple worker to process upload jobs."""
    
    def __init__(self):
        self.running = False
        self.db_url = None
        
    async def initialize(self):
        """Initialize the worker."""
        load_dotenv('.env.development')
        self.db_url = 'postgresql://postgres:postgres@127.0.0.1:54322/postgres'
        logger.info("Simple worker initialized")
        
    async def process_jobs(self):
        """Process queued upload jobs."""
        while self.running:
            try:
                conn = await asyncpg.connect(self.db_url)
                
                # Get queued jobs
                jobs = await conn.fetch("""
                    SELECT job_id, document_id, status, state, created_at
                    FROM upload_pipeline.upload_jobs 
                    WHERE state = 'queued' AND status = 'uploaded'
                    ORDER BY created_at ASC 
                    LIMIT 5
                """)
                
                if jobs:
                    logger.info(f"Found {len(jobs)} queued jobs to process")
                    
                    for job in jobs:
                        await self.process_single_job(conn, job)
                else:
                    logger.info("No queued jobs found, waiting...")
                    await asyncio.sleep(5)
                    
                await conn.close()
                
            except Exception as e:
                logger.error(f"Error processing jobs: {e}")
                await asyncio.sleep(10)
                
    async def process_single_job(self, conn, job):
        """Process a single upload job."""
        job_id = job['job_id']
        document_id = job['document_id']
        
        try:
            logger.info(f"Processing job {job_id} for document {document_id}")
            
            # Update job state to working
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET state = 'working', updated_at = NOW()
                WHERE job_id = $1
            """, job_id)
            
            # Simulate processing (in real implementation, this would:
            # 1. Download file from storage
            # 2. Parse document
            # 3. Generate chunks
            # 4. Create embeddings
            # 5. Store in database)
            
            logger.info(f"Simulating document processing for {document_id}")
            await asyncio.sleep(2)  # Simulate processing time
            
            # Update document status
            await conn.execute("""
                UPDATE upload_pipeline.documents 
                SET processing_status = 'processed', updated_at = NOW()
                WHERE document_id = $1
            """, document_id)
            
            # Update job status to done
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET state = 'done', status = 'complete', updated_at = NOW()
                WHERE job_id = $1
            """, job_id)
            
            logger.info(f"✅ Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error processing job {job_id}: {e}")
            
            # Mark job as failed
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET state = 'deadletter', last_error = $2, updated_at = NOW()
                WHERE job_id = $1
            """, job_id, json.dumps({"error": str(e), "timestamp": datetime.utcnow().isoformat()}))
    
    async def start(self):
        """Start the worker."""
        await self.initialize()
        self.running = True
        logger.info("🚀 Simple worker started")
        await self.process_jobs()
        
    async def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info("🛑 Simple worker stopped")

async def main():
    """Main entry point."""
    worker = SimpleWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
