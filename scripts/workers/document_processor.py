import asyncio
import logging
import sys
import os
from typing import Dict, Any
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db.services.queue_service import QueueService
from db.services.llamaparse_service import LlamaParseService
from db.services.vector_service import VectorService
from db.services.storage_service import StorageService
from db.services.document_processing_service import DocumentProcessingService

logger = logging.getLogger(__name__)

class DocumentProcessorWorker:
    def __init__(self):
        self.services = None
        self.running = False
        
    async def initialize_services(self):
        """Initialize all required services."""
        from config import config
        from db.db_pool import get_db_pool
        
        pool = await get_db_pool()
        
        self.services = {
            "storage": StorageService(),
            "queue": QueueService(pool),
            "llamaparse": LlamaParseService(
                api_key=config.get("LLAMAPARSE_API_KEY")
            ),
            "vector": VectorService(
                api_key=config.get("OPENAI_API_KEY"),
                pool=pool
            )
        }
        
        self.services["document_processing"] = DocumentProcessingService(
            storage_service=self.services["storage"],
            queue_service=self.services["queue"],
            llamaparse_service=self.services["llamaparse"],
            vector_service=self.services["vector"]
        )
        
    async def process_job(self, job_id: str, job_type: str, payload: Dict[str, Any]):
        """Process a single job."""
        try:
            if job_type == "llamaparse":
                # Process document with LlamaParse
                result = await self.services["llamaparse"].parse_document(
                    file_data=payload["file_data"],
                    filename=payload["filename"],
                    content_type=payload["content_type"]
                )
                
                await self.services["queue"].complete_job(job_id, result=result)
                
            elif job_type == "vector_generation":
                # Generate vectors for text chunks
                embeddings = await self.services["vector"].generate_embeddings(
                    texts=payload["chunks"],
                    metadata={"document_id": payload["document_id"]}
                )
                
                # Store vectors in database
                vector_ids = await self.services["vector"].store_embeddings(
                    document_id=payload["document_id"],
                    embeddings=embeddings,
                    user_id=payload["user_id"]
                )
                
                await self.services["queue"].complete_job(
                    job_id,
                    result={"vectors": vector_ids}
                )
                
            else:
                logger.error(f"Unknown job type: {job_type}")
                await self.services["queue"].complete_job(
                    job_id,
                    error=f"Unknown job type: {job_type}"
                )
                
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            await self.services["queue"].complete_job(
                job_id,
                error=str(e)
            )
            
    async def poll_jobs(self):
        """Poll for new jobs and process them."""
        while self.running:
            try:
                # Get pending jobs
                pool = await get_db_pool()
                async with pool.get_connection() as conn:
                    jobs = await conn.fetch("""
                        SELECT id, job_type, payload
                        FROM processing_jobs
                        WHERE status = 'pending'
                        ORDER BY created_at ASC
                        LIMIT 10
                    """)
                    
                    for job in jobs:
                        # Update job status to processing
                        await conn.execute("""
                            UPDATE processing_jobs
                            SET status = 'processing',
                                updated_at = NOW()
                            WHERE id = $1
                        """, job["id"])
                        
                        # Process job
                        await self.process_job(
                            job["id"],
                            job["job_type"],
                            json.loads(job["payload"])
                        )
                        
                # Small delay between polling
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error polling jobs: {str(e)}")
                await asyncio.sleep(5)  # Longer delay on error
                
    async def start(self):
        """Start the worker."""
        await self.initialize_services()
        self.running = True
        await self.poll_jobs()
        
    async def stop(self):
        """Stop the worker."""
        self.running = False
        
async def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start worker
    worker = DocumentProcessorWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        await worker.stop()
        
if __name__ == "__main__":
    asyncio.run(main()) 