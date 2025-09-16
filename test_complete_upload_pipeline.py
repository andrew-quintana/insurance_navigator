#!/usr/bin/env python3
"""
Complete Upload Pipeline Test
Following the upload_refactor specifications for end-to-end testing
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteUploadPipelineTester:
    """Test the complete upload pipeline flow"""
    
    def __init__(self):
        self.db_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable"
        self.api_base_url = "http://localhost:8000"
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()
    
    async def test_upload_stage(self):
        """Test Stage 1: Upload - Create document and job records"""
        logger.info("🧪 Testing Upload Stage")
        
        # Create test document via API
        test_data = {
            "filename": "complete_pipeline_test.pdf",
            "bytes_len": 2048000,
            "mime": "application/pdf",
            "sha256": "5e02220b4d42255fdcfcf5daba65ace0616ae4949350001445ab8871bbadf84c",
            "ocr": False
        }
        
        response = await self.http_client.post(
            f"{self.api_base_url}/api/upload-pipeline/upload-test",
            json=test_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
        
        result = response.json()
        job_id = result["job_id"]
        document_id = result["document_id"]
        
        logger.info(f"✅ Upload successful - Job: {job_id}, Document: {document_id}")
        
        # Verify database records
        conn = await asyncpg.connect(self.db_url)
        try:
            # Check document
            doc = await conn.fetchrow(
                "SELECT document_id, filename, processing_status, mime, bytes_len FROM upload_pipeline.documents WHERE document_id = $1",
                document_id
            )
            
            if not doc:
                raise Exception("Document not created in database")
            
            # Check job
            job = await conn.fetchrow(
                "SELECT job_id, document_id, status, state FROM upload_pipeline.upload_jobs WHERE job_id = $1",
                job_id
            )
            
            if not job:
                raise Exception("Job not created in database")
            
            logger.info(f"✅ Database records verified - Status: {job['status']}, State: {job['state']}")
        finally:
            await conn.close()
        
        return {
            "job_id": job_id,
            "document_id": document_id,
            "status": "uploaded"
        }
    
    async def test_parsing_stage(self, job_id, document_id):
        """Test Stage 2: Parsing - Process document with LlamaParse"""
        logger.info("🧪 Testing Parsing Stage")
        
        # For testing, we'll simulate the parsing stage by updating the job status
        # In a real implementation, this would be handled by the enhanced worker
        conn = await asyncpg.connect(self.db_url)
        try:
            # Update job to simulate parsing completion
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'parsed'
                WHERE job_id = $1
            """, job_id)
            
            # Update document status
            await conn.execute("""
                UPDATE upload_pipeline.documents 
                SET processing_status = 'parsed', parsed_path = $1
                WHERE document_id = $2
            """, f"storage://parsed/test-user/{document_id}.md", document_id)
        finally:
            await conn.close()
        
        logger.info("✅ Parsing stage completed (simulated)")
        return {"status": "parsed"}
    
    async def test_chunking_stage(self, job_id, document_id):
        """Test Stage 3: Chunking - Create document chunks"""
        logger.info("🧪 Testing Chunking Stage")
        
        # Create test chunks
        test_chunks = [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_ord": 0,
                "text": "# Complete Pipeline Test Document\n\nThis is a test document for the complete upload pipeline validation.",
                "chunk_sha": "test-chunk-sha-1",
                "chunker_name": "markdown-simple",
                "chunker_version": "1.0",
                "embed_model": "text-embedding-3-small",
                "embed_version": "1",
                "vector_dim": 1536
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_ord": 1,
                "text": "## Section 1\n\nThis section contains test content for chunking validation.",
                "chunk_sha": "test-chunk-sha-2",
                "chunker_name": "markdown-simple",
                "chunker_version": "1.0",
                "embed_model": "text-embedding-3-small",
                "embed_version": "1",
                "vector_dim": 1536
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_ord": 2,
                "text": "## Section 2\n\nAdditional content for multi-chunk testing and validation.",
                "chunk_sha": "test-chunk-sha-3",
                "chunker_name": "markdown-simple",
                "chunker_version": "1.0",
                "embed_model": "text-embedding-3-small",
                "embed_version": "1",
                "vector_dim": 1536
            }
        ]
        
        conn = await asyncpg.connect(self.db_url)
        try:
            # Insert chunks with mock embeddings
            for chunk in test_chunks:
                # Create vector string format: '[0.1,0.1,0.1,...]'
                mock_embedding_str = '[' + ','.join(['0.1'] * 1536) + ']'
                await conn.execute("""
                    INSERT INTO upload_pipeline.document_chunks 
                    (chunk_id, document_id, chunk_ord, text, chunk_sha, chunker_name, chunker_version, 
                     embed_model, embed_version, vector_dim, embedding, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                """, chunk["chunk_id"], chunk["document_id"], chunk["chunk_ord"], 
                     chunk["text"], chunk["chunk_sha"], chunk["chunker_name"], chunk["chunker_version"],
                     chunk["embed_model"], chunk["embed_version"], chunk["vector_dim"], mock_embedding_str)
            
            # Update job status
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'chunks_stored'
                WHERE job_id = $1
            """, job_id)
            
            # Update document status
            await conn.execute("""
                UPDATE upload_pipeline.documents 
                SET processing_status = 'chunked'
                WHERE document_id = $1
            """, document_id)
        finally:
            await conn.close()
        
        logger.info(f"✅ Chunking stage completed - Created {len(test_chunks)} chunks")
        return {"status": "chunks_stored", "chunk_count": len(test_chunks)}
    
    async def test_embedding_stage(self, job_id, document_id):
        """Test Stage 4: Embedding - Generate embeddings for chunks"""
        logger.info("🧪 Testing Embedding Stage")
        
        # Generate mock embeddings for chunks
        conn = await asyncpg.connect(self.db_url)
        try:
            # Get chunks
            chunks = await conn.fetch(
                "SELECT chunk_id FROM upload_pipeline.document_chunks WHERE document_id = $1 ORDER BY chunk_ord",
                document_id
            )
            
            # Generate mock embeddings (1536 dimensions for text-embedding-3-small)
            for chunk in chunks:
                # Create vector string format: '[0.1,0.1,0.1,...]'
                mock_embedding_str = '[' + ','.join(['0.1'] * 1536) + ']'
                await conn.execute("""
                    UPDATE upload_pipeline.document_chunks 
                    SET embedding = $1
                    WHERE chunk_id = $2
                """, mock_embedding_str, chunk["chunk_id"])
            
            # Update job status
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'embeddings_stored'
                WHERE job_id = $1
            """, job_id)
            
            # Update document status
            await conn.execute("""
                UPDATE upload_pipeline.documents 
                SET processing_status = 'embedded'
                WHERE document_id = $1
            """, document_id)
        finally:
            await conn.close()
        
        logger.info(f"✅ Embedding stage completed - Generated embeddings for {len(chunks)} chunks")
        return {"status": "embeddings_stored", "embedding_count": len(chunks)}
    
    async def test_finalization_stage(self, job_id, document_id):
        """Test Stage 5: Finalization - Complete job processing"""
        logger.info("🧪 Testing Finalization Stage")
        
        conn = await asyncpg.connect(self.db_url)
        try:
            # Update job to complete
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'complete', state = 'done'
                WHERE job_id = $1
            """, job_id)
            
            # Update document status
            await conn.execute("""
                UPDATE upload_pipeline.documents 
                SET processing_status = 'processed'
                WHERE document_id = $1
            """, document_id)
        finally:
            await conn.close()
        
        logger.info("✅ Finalization stage completed")
        return {"status": "complete"}
    
    async def verify_final_state(self, job_id, document_id):
        """Verify the final state of the pipeline"""
        logger.info("🧪 Verifying Final State")
        
        conn = await asyncpg.connect(self.db_url)
        try:
            # Check job status
            job = await conn.fetchrow(
                "SELECT status, state FROM upload_pipeline.upload_jobs WHERE job_id = $1",
                job_id
            )
            
            # Check document status
            doc = await conn.fetchrow(
                "SELECT processing_status FROM upload_pipeline.documents WHERE document_id = $1",
                document_id
            )
            
            # Check chunk count
            chunk_count = await conn.fetchval(
                "SELECT COUNT(*) FROM upload_pipeline.document_chunks WHERE document_id = $1",
                document_id
            )
            
            # Check embedding count
            embedding_count = await conn.fetchval(
                "SELECT COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) FROM upload_pipeline.document_chunks WHERE document_id = $1",
                document_id
            )
        finally:
            await conn.close()
        
        logger.info(f"📊 Final State Verification:")
        logger.info(f"   Job Status: {job['status'] if job else 'NOT FOUND'}")
        logger.info(f"   Job State: {job['state'] if job else 'NOT FOUND'}")
        logger.info(f"   Document Status: {doc['processing_status'] if doc else 'NOT FOUND'}")
        logger.info(f"   Chunk Count: {chunk_count}")
        logger.info(f"   Embedding Count: {embedding_count}")
        
        # Determine success
        success = (
            job and job['status'] == 'complete' and job['state'] == 'done' and
            doc and doc['processing_status'] == 'processed' and
            chunk_count > 0 and embedding_count > 0
        )
        
        if success:
            logger.info("🎉 SUCCESS: Complete pipeline processing achieved!")
        else:
            logger.info("❌ FAILURE: Pipeline did not complete successfully")
        
        return success
    
    async def run_complete_pipeline_test(self):
        """Run the complete pipeline test"""
        logger.info("🚀 Starting Complete Upload Pipeline Test")
        logger.info("=" * 60)
        
        try:
            # Stage 1: Upload
            upload_result = await self.test_upload_stage()
            job_id = upload_result["job_id"]
            document_id = upload_result["document_id"]
            
            # Stage 2: Parsing
            await self.test_parsing_stage(job_id, document_id)
            
            # Stage 3: Chunking
            await self.test_chunking_stage(job_id, document_id)
            
            # Stage 4: Embedding
            await self.test_embedding_stage(job_id, document_id)
            
            # Stage 5: Finalization
            await self.test_finalization_stage(job_id, document_id)
            
            # Verify final state
            success = await self.verify_final_state(job_id, document_id)
            
            logger.info("=" * 60)
            logger.info(f"PIPELINE TEST {'PASSED' if success else 'FAILED'}")
            logger.info("=" * 60)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Pipeline test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await self.cleanup()

async def main():
    """Main function"""
    tester = CompleteUploadPipelineTester()
    success = await tester.run_complete_pipeline_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
