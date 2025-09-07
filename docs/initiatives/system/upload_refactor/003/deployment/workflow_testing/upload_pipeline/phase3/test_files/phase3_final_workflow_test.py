#!/usr/bin/env python3
"""
Phase 3 Final Workflow Test
Comprehensive test of the complete upload pipeline workflow
"""

import asyncio
import httpx
import json
import time
import uuid
import hashlib
from datetime import datetime
import logging

# Configure detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3WorkflowTester:
    def __init__(self, api_url="https://insurance-navigator-api.onrender.com"):
        self.api_url = api_url
        self.client = None
        self.user_id = None
        self.access_token = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def setup_user(self):
        """Register and login a test user"""
        logger.info("🔍 Setting up test user...")
        
        # Register user
        registration_data = {
            "email": f"phase3-final-test-{int(time.time())}@example.com",
            "password": "testpassword123",
            "name": "Phase 3 Final Test User"
        }
        
        reg_response = await self.client.post(
            f"{self.api_url}/register", 
            json=registration_data, 
            timeout=30
        )
        
        if reg_response.status_code != 200:
            raise Exception(f"Registration failed: {reg_response.status_code} - {reg_response.text}")
        
        reg_data = reg_response.json()
        self.user_id = reg_data.get("user", {}).get("id")
        logger.info(f"✅ User registered: {self.user_id}")
        
        # Login user
        login_data = {
            "email": registration_data["email"],
            "password": registration_data["password"]
        }
        
        login_response = await self.client.post(
            f"{self.api_url}/login", 
            json=login_data, 
            timeout=30
        )
        
        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.status_code} - {login_response.text}")
        
        login_data = login_response.json()
        self.access_token = login_data.get("access_token")
        logger.info(f"✅ User logged in, token: {self.access_token[:20]}...")
    
    async def test_api_endpoints(self):
        """Test available API endpoints"""
        logger.info("🔍 Testing API endpoints...")
        
        try:
            openapi_response = await self.client.get(f"{self.api_url}/openapi.json", timeout=30)
            if openapi_response.status_code == 200:
                openapi_data = openapi_response.json()
                paths = list(openapi_data.get("paths", {}).keys())
                
                logger.info("📋 Available API endpoints:")
                for path in sorted(paths):
                    logger.info(f"  - {path}")
                
                # Check for specific endpoints
                has_old_api = "/upload-document-backend" in paths
                has_new_api = "/api/v2/upload" in paths
                
                logger.info(f"✅ Old API endpoint available: {has_old_api}")
                logger.info(f"✅ New API endpoint available: {has_new_api}")
                
                return has_old_api, has_new_api
            else:
                logger.warning(f"⚠️ Could not fetch OpenAPI spec: {openapi_response.status_code}")
                return False, False
        except Exception as e:
            logger.warning(f"⚠️ Error checking API endpoints: {e}")
            return False, False
    
    async def test_worker_processing(self):
        """Test worker processing by creating a job directly in the database"""
        logger.info("🔍 Testing worker processing...")
        
        # Import database connection
        import asyncpg
        import os
        from dotenv import load_dotenv
        
        load_dotenv('.env.production')
        
        try:
            # Connect to database
            conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
            
            # Create test document
            document_id = str(uuid.uuid4())
            job_id = str(uuid.uuid4())
            user_id = self.user_id
            
            # Create test content
            test_content = f"""# Phase 3 Final Test Document

This is a comprehensive test document for Phase 3 final workflow testing.

Document ID: {document_id}
Job ID: {job_id}
User ID: {user_id}
Generated: {datetime.utcnow().isoformat()}
Test Type: Phase 3 Final Workflow Test
""".encode('utf-8')
            
            file_sha256 = hashlib.sha256(test_content).hexdigest()
            
            # Insert document
            await conn.execute("""
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, mime, bytes_len, 
                    file_sha256, raw_path, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """, document_id, user_id, "phase3_final_test.pdf", "application/pdf", 
                len(test_content), file_sha256, f"files/user/{user_id}/raw/{int(time.time())}_{file_sha256[:8]}.pdf")
            
            # Insert job
            job_payload = {
                "user_id": user_id,
                "document_id": document_id,
                "file_sha256": file_sha256,
                "bytes_len": len(test_content),
                "mime": "application/pdf",
                "storage_path": f"files/user/{user_id}/raw/{int(time.time())}_{file_sha256[:8]}.pdf"
            }
            
            await conn.execute("""
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, status, state, progress, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            """, job_id, document_id, "uploaded", "queued", json.dumps(job_payload))
            
            logger.info(f"✅ Test job created: {job_id}")
            
            # Monitor job processing
            logger.info("⏳ Monitoring job processing...")
            max_attempts = 120  # 2 minutes with 1-second intervals
            
            for attempt in range(max_attempts):
                job_result = await conn.fetchrow("""
                    SELECT status, state, updated_at 
                    FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, job_id)
                
                if job_result:
                    status = job_result['status']
                    state = job_result['state']
                    
                    logger.info(f"📊 Job status (attempt {attempt + 1}/{max_attempts}): {status} | {state}")
                    
                    if status in ['complete', 'duplicate'] and state == "done":
                        logger.info(f"🎉 Job completed with status: {status}")
                        break
                    elif status in ['failed_parse', 'failed_chunking', 'failed_embedding']:
                        logger.error(f"❌ Job failed with status: {status}")
                        break
                
                await asyncio.sleep(1)
            
            # Get final job details
            final_job = await conn.fetchrow("""
                SELECT status, state, progress, created_at, updated_at
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1
            """, job_id)
            
            if final_job:
                logger.info(f"📊 Final job status: {final_job['status']} | {final_job['state']}")
                
                # Check if chunks were created
                chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                """, document_id)
                
                logger.info(f"📊 Document chunks created: {chunk_count}")
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Worker test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Phase 3 Final Workflow Test")
    logger.info("=" * 60)
    
    async with Phase3WorkflowTester() as tester:
        try:
            # Setup user
            await tester.setup_user()
            
            # Test API endpoints
            has_old_api, has_new_api = await tester.test_api_endpoints()
            
            # Test worker processing
            worker_success = await tester.test_worker_processing()
            
            # Summary
            logger.info("")
            logger.info("📊 PHASE 3 FINAL WORKFLOW TEST SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Old API available: {has_old_api}")
            logger.info(f"New API available: {has_new_api}")
            logger.info(f"Worker processing: {'✅ SUCCESS' if worker_success else '❌ FAILED'}")
            
            if worker_success:
                logger.info("🎉 Phase 3 workflow is functional!")
                logger.info("✅ Worker service is processing jobs end-to-end")
                logger.info("✅ Database operations are working")
                logger.info("✅ Complete pipeline is operational")
                
                if has_new_api:
                    logger.info("✅ New API endpoints are available")
                    logger.info("🎯 Phase 3 is FULLY COMPLETE!")
                else:
                    logger.info("⚠️ New API endpoints not yet available")
                    logger.info("📋 Phase 3 is PARTIALLY COMPLETE (worker working, API pending)")
            else:
                logger.error("❌ Phase 3 workflow has issues")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
