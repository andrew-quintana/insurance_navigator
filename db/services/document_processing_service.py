from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
import hashlib
from concurrent.futures import ThreadPoolExecutor

from .storage_service import StorageService
from .queue_service import QueueService
from .llamaparse_service import LlamaParseService
from .vector_service import VectorService

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    def __init__(
        self,
        storage_service: StorageService,
        queue_service: QueueService,
        llamaparse_service: LlamaParseService,
        vector_service: VectorService
    ):
        self.storage = storage_service
        self.queue = queue_service
        self.llamaparse = llamaparse_service
        self.vector = vector_service
        
        # Processing configuration
        self.chunk_size = 1500
        self.chunk_overlap = 100
        self.max_concurrent_chunks = 25
        self.batch_size = 5
        
    async def process_document(
        self,
        document_id: str,
        file_data: bytes,
        filename: str,
        content_type: str,
        user_id: str,
        document_type: str = "user_document",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the entire pipeline:
        1. Upload to storage
        2. Parse with LlamaParse
        3. Chunk text
        4. Generate vectors
        5. Store in database
        """
        try:
            # 1. Upload to storage
            storage_path = f"{user_id}/{document_id}/{filename}"
            await self.storage.upload_document(
                file_data=file_data,
                filename=filename,
                user_id=user_id,
                document_type=document_type,
                metadata=metadata
            )
            
            # 2. Queue LlamaParse processing
            parse_job = await self.queue.enqueue_job(
                "llamaparse",
                {
                    "document_id": document_id,
                    "storage_path": storage_path,
                    "content_type": content_type
                }
            )
            
            # 3. Wait for parsing (with timeout)
            parse_result = await self.queue.wait_for_job(parse_job.id, timeout=60)
            if not parse_result or not parse_result.get("text"):
                raise Exception("Document parsing failed or timed out")
                
            text_content = parse_result["text"]
            
            # 4. Chunk text
            chunks = self._chunk_text(text_content)
            
            # 5. Process chunks in batches
            processed_chunks = []
            failed_chunks = 0
            
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                
                # Queue vector generation for batch
                vector_job = await self.queue.enqueue_job(
                    "vector_generation",
                    {
                        "document_id": document_id,
                        "chunks": batch,
                        "batch_index": i // self.batch_size
                    }
                )
                
                # Wait for vectors (with timeout)
                vector_result = await self.queue.wait_for_job(vector_job.id, timeout=30)
                if vector_result and vector_result.get("vectors"):
                    processed_chunks.extend(vector_result["vectors"])
                else:
                    failed_chunks += len(batch)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # 6. Return processing results
            return {
                "success": True,
                "document_id": document_id,
                "storage_path": storage_path,
                "chunks_processed": len(processed_chunks),
                "chunks_failed": failed_chunks,
                "total_chunks": len(chunks),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
                "status": "failed"
            }
            
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                # Find next sentence boundary
                next_period = text.find('.', end)
                if next_period != -1 and next_period - end < 100:
                    end = next_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            
        return chunks 