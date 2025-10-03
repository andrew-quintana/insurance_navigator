#!/usr/bin/env python3
"""
Debug script to trace through the entire chunk generation pipeline.
"""

import asyncio
import aiohttp
import hashlib
import json
import time
import uuid
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_chunk_pipeline():
    """Debug the entire chunk generation pipeline step by step."""
    
    base_url = "https://insurance-navigator-api.onrender.com"
    
    # Create test user
    test_user_email = f"debug_chunk_{uuid.uuid4().hex[:8]}@example.com"
    test_user_password = "TestPassword123!"
    
    async with aiohttp.ClientSession() as session:
        logger.info("🔍 Starting chunk pipeline debug...")
        
        # 1. Create user
        logger.info("1️⃣ Creating test user...")
        signup_data = {
            "email": test_user_email,
            "password": test_user_password,
            "full_name": "Debug Chunk User",
            "consent_version": "1.0",
            "consent_timestamp": datetime.utcnow().isoformat()
        }
        
        async with session.post(f"{base_url}/auth/signup", json=signup_data) as response:
            if response.status not in [200, 201, 409]:
                logger.error(f"❌ User creation failed: {response.status}")
                return False
            logger.info("✅ User created successfully")
        
        # 2. Authenticate
        logger.info("2️⃣ Authenticating user...")
        auth_data = {
            "email": test_user_email,
            "password": test_user_password
        }
        
        async with session.post(f"{base_url}/auth/login", json=auth_data) as response:
            if response.status != 200:
                logger.error(f"❌ Authentication failed: {response.status}")
                return False
            
            result = await response.json()
            auth_token = result.get("access_token")
            user_id = result.get("user", {}).get("id")
            logger.info(f"✅ User authenticated successfully - User ID: {user_id}")
        
        # 3. Upload document
        logger.info("3️⃣ Uploading test document...")
        test_doc_content = f"""
        INSURANCE POLICY DEBUG DOCUMENT
        Policy Number: DEBUG-{uuid.uuid4().hex[:8]}
        Policyholder: {test_user_email}
        
        This is a debug insurance policy document for chunk generation testing.
        It contains multiple sections that should be properly chunked and vectorized.
        
        SECTION 1: COVERAGE DETAILS
        - Medical Coverage: $1,000,000
        - Dental Coverage: $50,000
        - Vision Coverage: $25,000
        
        SECTION 2: DEDUCTIBLES
        - Annual Deductible: $2,500
        - Office Visit Copay: $25
        - Emergency Room Copay: $200
        
        SECTION 3: EXCLUSIONS
        - Cosmetic procedures
        - Experimental treatments
        - Pre-existing conditions
        
        This document should generate multiple meaningful chunks for testing.
        """
        
        test_doc_hash = hashlib.sha256(test_doc_content.encode()).hexdigest()
        filename = f"debug_chunk_{uuid.uuid4().hex[:8]}.pdf"
        
        upload_data = {
            "filename": filename,
            "bytes_len": len(test_doc_content),
            "mime": "application/pdf",
            "sha256": test_doc_hash,
            "ocr": False
        }
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        async with session.post(f"{base_url}/api/upload-pipeline/upload", json=upload_data, headers=headers) as response:
            if response.status != 200:
                logger.error(f"❌ Upload failed: {response.status}")
                response_text = await response.text()
                logger.error(f"Response: {response_text}")
                return False
            
            result = await response.json()
            job_id = result.get("job_id")
            document_id = result.get("document_id")
            signed_url = result.get("signed_url")
            logger.info(f"✅ Document upload initiated - Job ID: {job_id}, Document ID: {document_id}")
            logger.info(f"📎 Signed URL: {signed_url}")
        
        # 4. Upload content to signed URL
        logger.info("4️⃣ Uploading content to signed URL...")
        async with session.put(signed_url, data=test_doc_content.encode(), headers={"Content-Type": "application/pdf"}) as response:
            if response.status != 200:
                logger.error(f"❌ Content upload failed: {response.status}")
                response_text = await response.text()
                logger.error(f"Response: {response_text}")
                return False
            logger.info("✅ Content uploaded successfully")
        
        # 5. Check worker status
        logger.info("5️⃣ Checking worker status...")
        try:
            async with session.get(f"{base_url}/api/v1/status") as response:
                if response.status == 200:
                    worker_status = await response.json()
                    logger.info(f"✅ Worker status: {worker_status}")
                else:
                    logger.warning(f"⚠️ Worker status check failed: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Worker status check error: {e}")
        
        # 6. Monitor job progress
        logger.info("6️⃣ Monitoring job progress...")
        max_attempts = 30  # 5 minutes
        for attempt in range(max_attempts):
            logger.info(f"   Attempt {attempt + 1}/{max_attempts} - Checking job status...")
            
            try:
                # Check job status
                async with session.get(f"{base_url}/api/v2/jobs/{job_id}", headers=headers) as response:
                    if response.status == 200:
                        job_data = await response.json()
                        status = job_data.get("status", "unknown")
                        progress = job_data.get("progress", 0)
                        logger.info(f"   📊 Job status: {status}, Progress: {progress}%")
                        
                        if status in ["complete", "completed"]:
                            logger.info("✅ Job completed successfully!")
                            break
                        elif status in ["failed", "error"]:
                            error_msg = job_data.get("error", "Unknown error")
                            logger.error(f"❌ Job failed: {error_msg}")
                            return False
                    else:
                        logger.warning(f"   ⚠️ Job status check failed: {response.status}")
                
                # Check for chunks
                async with session.get(f"{base_url}/documents/{document_id}/chunks", headers=headers) as response:
                    if response.status == 200:
                        chunks_data = await response.json()
                        if chunks_data and len(chunks_data) > 0:
                            logger.info(f"🎉 Found {len(chunks_data)} chunks!")
                            for i, chunk in enumerate(chunks_data[:3]):
                                logger.info(f"   Chunk {i+1}: {chunk.get('text', '')[:100]}...")
                            return True
                        else:
                            logger.info(f"   📝 No chunks yet (attempt {attempt + 1})")
                    else:
                        logger.warning(f"   ⚠️ Chunks check failed: {response.status}")
                
                await asyncio.sleep(10)  # Wait 10 seconds between checks
                
            except Exception as e:
                logger.warning(f"   ⚠️ Error during monitoring: {e}")
                await asyncio.sleep(10)
        
        logger.warning("⏰ Timeout waiting for chunks to be generated")
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_chunk_pipeline())
    if success:
        logger.info("🎉 CHUNK GENERATION IS WORKING!")
    else:
        logger.info("❌ Chunk generation debug failed")
