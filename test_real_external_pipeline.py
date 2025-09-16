#!/usr/bin/env python3
"""
Real External API Pipeline Test
Tests the complete pipeline with actual file upload and real external APIs
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.development')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealExternalAPITester:
    """Test the complete upload pipeline with real external APIs and file upload"""
    
    def __init__(self):
        self.db_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable"
        self.api_base_url = "http://localhost:8000"
        self.http_client = httpx.AsyncClient(timeout=120.0)
        
        # External API configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.llamaparse_api_key = os.getenv('LLAMAPARSE_API_KEY')
        self.llamaparse_base_url = os.getenv('LLAMAPARSE_BASE_URL', 'https://api.cloud.llamaindex.ai')
        self.openai_api_url = os.getenv('OPENAI_API_URL', 'https://api.openai.com')
        
        logger.info(f"Real External APIs configured:")
        logger.info(f"  LlamaParse: {self.llamaparse_base_url}")
        logger.info(f"  OpenAI: {self.openai_api_url}")
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()
    
    def create_test_pdf(self):
        """Create a test PDF file for upload"""
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(Real External API Test Document) Tj
0 -20 Td
(This is a test document for external API integration) Tj
0 -20 Td
(Testing LlamaParse and OpenAI APIs) Tj
0 -20 Td
(Insurance Navigator Upload Pipeline) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
404
%%EOF"""
        
        test_file_path = "test_real_external_api.pdf"
        with open(test_file_path, "wb") as f:
            f.write(pdf_content)
        
        return test_file_path
    
    async def test_real_upload_pipeline(self):
        """Test the complete pipeline with real file upload and external APIs"""
        logger.info("🚀 Starting Real External API Pipeline Test")
        logger.info("=" * 70)
        
        try:
            # Create test PDF
            test_file_path = self.create_test_pdf()
            logger.info(f"✅ Created test PDF: {test_file_path}")
            
            # Calculate file hash
            import hashlib
            with open(test_file_path, "rb") as f:
                file_content = f.read()
                file_hash = hashlib.sha256(file_content).hexdigest()
            
            logger.info(f"✅ File hash: {file_hash}")
            
            # Step 1: Create upload job
            logger.info("🧪 Step 1: Creating upload job")
            upload_data = {
                "filename": "real_external_api_test.pdf",
                "bytes_len": len(file_content),
                "mime": "application/pdf",
                "sha256": file_hash,
                "ocr": False
            }
            
            response = await self.http_client.post(
                f"{self.api_base_url}/api/upload-pipeline/upload-test",
                json=upload_data
            )
            
            if response.status_code != 200:
                raise Exception(f"Upload job creation failed: {response.status_code} - {response.text}")
            
            result = response.json()
            job_id = result["job_id"]
            document_id = result["document_id"]
            signed_url = result["signed_url"]
            
            logger.info(f"✅ Upload job created - Job: {job_id}, Document: {document_id}")
            logger.info(f"✅ Signed URL: {signed_url}")
            
            # Step 2: Upload file to storage
            logger.info("🧪 Step 2: Uploading file to storage")
            with open(test_file_path, "rb") as f:
                upload_response = await self.http_client.put(
                    signed_url,
                    content=f.read(),
                    headers={"Content-Type": "application/pdf"}
                )
            
            if upload_response.status_code not in [200, 201, 204]:
                logger.warning(f"⚠️ File upload failed: {upload_response.status_code} - {upload_response.text}")
                logger.info("Continuing with pipeline test...")
            else:
                logger.info("✅ File uploaded to storage successfully")
            
            # Step 3: Wait for enhanced worker to process
            logger.info("🧪 Step 3: Waiting for enhanced worker to process job")
            await self.wait_for_job_processing(job_id, document_id, timeout=60)
            
            # Step 4: Verify final state
            logger.info("🧪 Step 4: Verifying final state")
            success = await self.verify_final_state(job_id, document_id)
            
            # Cleanup test file
            os.remove(test_file_path)
            logger.info(f"✅ Cleaned up test file: {test_file_path}")
            
            logger.info("=" * 70)
            logger.info(f"REAL EXTERNAL API PIPELINE TEST {'PASSED' if success else 'FAILED'}")
            logger.info("=" * 70)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Real external API pipeline test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await self.cleanup()
    
    async def wait_for_job_processing(self, job_id, document_id, timeout=60):
        """Wait for the enhanced worker to process the job"""
        logger.info(f"⏳ Waiting for job {job_id} to be processed (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            conn = await asyncpg.connect(self.db_url)
            try:
                # Check job status
                job = await conn.fetchrow(
                    "SELECT status, state, updated_at FROM upload_pipeline.upload_jobs WHERE job_id = $1",
                    job_id
                )
                
                if job:
                    logger.info(f"   Job status: {job['status']}, state: {job['state']}")
                    
                    # Check if job is complete
                    if job['status'] in ['complete', 'failed', 'failed_parse', 'failed_chunk', 'failed_embed']:
                        logger.info(f"✅ Job processing completed with status: {job['status']}")
                        return job['status']
                
                # Check document status
                doc = await conn.fetchrow(
                    "SELECT processing_status FROM upload_pipeline.documents WHERE document_id = $1",
                    document_id
                )
                
                if doc and doc['processing_status']:
                    logger.info(f"   Document status: {doc['processing_status']}")
                
                # Check if chunks were created
                chunk_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM upload_pipeline.document_chunks WHERE document_id = $1",
                    document_id
                )
                
                if chunk_count > 0:
                    logger.info(f"✅ Chunks created: {chunk_count}")
                
            finally:
                await conn.close()
            
            await asyncio.sleep(2)  # Wait 2 seconds before checking again
        
        logger.warning(f"⚠️ Job processing timeout after {timeout} seconds")
        return "timeout"
    
    async def verify_final_state(self, job_id, document_id):
        """Verify the final state of the pipeline"""
        logger.info("🧪 Verifying Final State with Real External APIs")
        
        conn = await asyncpg.connect(self.db_url)
        try:
            # Check job status
            job = await conn.fetchrow(
                "SELECT status, state, created_at, updated_at FROM upload_pipeline.upload_jobs WHERE job_id = $1",
                job_id
            )
            
            # Check document status
            doc = await conn.fetchrow(
                "SELECT processing_status, parsed_path FROM upload_pipeline.documents WHERE document_id = $1",
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
            
            # Get chunk details
            chunks = await conn.fetch(
                "SELECT chunk_id, chunk_ord, text, embed_model FROM upload_pipeline.document_chunks WHERE document_id = $1 ORDER BY chunk_ord",
                document_id
            )
            
        finally:
            await conn.close()
        
        logger.info(f"📊 Final State Verification with Real External APIs:")
        logger.info(f"   Job Status: {job['status'] if job else 'NOT FOUND'}")
        logger.info(f"   Job State: {job['state'] if job else 'NOT FOUND'}")
        logger.info(f"   Document Status: {doc['processing_status'] if doc else 'NOT FOUND'}")
        logger.info(f"   Parsed Path: {doc['parsed_path'] if doc else 'NOT FOUND'}")
        logger.info(f"   Chunk Count: {chunk_count}")
        logger.info(f"   Embedding Count: {embedding_count}")
        
        if chunks:
            logger.info(f"   Chunk Details:")
            for chunk in chunks[:3]:  # Show first 3 chunks
                logger.info(f"     Chunk {chunk['chunk_ord']}: {chunk['text'][:50]}... (model: {chunk['embed_model']})")
        
        # Determine success
        success = (
            job and job['status'] == 'complete' and job['state'] == 'done' and
            doc and doc['processing_status'] == 'processed' and
            chunk_count > 0 and embedding_count > 0
        )
        
        if success:
            logger.info("🎉 SUCCESS: Complete pipeline with real external APIs achieved!")
        else:
            logger.info("❌ FAILURE: Pipeline with real external APIs did not complete successfully")
            if job and job['status'] in ['failed', 'failed_parse', 'failed_chunk', 'failed_embed']:
                logger.info(f"   Failure reason: {job['status']}")
        
        return success

async def main():
    """Main function"""
    tester = RealExternalAPITester()
    success = await tester.test_real_upload_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
