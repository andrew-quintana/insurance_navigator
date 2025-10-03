#!/usr/bin/env python3
"""
Simple test to verify chunk generation is working.
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

async def test_simple_upload_and_chunks():
    """Test simple upload and check for chunks."""
    
    base_url = "https://insurance-navigator-api.onrender.com"
    
    # Create test user
    test_user_email = f"chunk_test_{uuid.uuid4().hex[:8]}@example.com"
    test_user_password = "TestPassword123!"
    
    async with aiohttp.ClientSession() as session:
        # 1. Create user
        logger.info("Creating test user...")
        signup_data = {
            "email": test_user_email,
            "password": test_user_password,
            "full_name": "Chunk Test User",
            "consent_version": "1.0",
            "consent_timestamp": datetime.utcnow().isoformat()
        }
        
        async with session.post(f"{base_url}/auth/signup", json=signup_data) as response:
            if response.status not in [200, 201, 409]:
                logger.error(f"User creation failed: {response.status}")
                return False
            logger.info("✅ User created successfully")
        
        # 2. Authenticate
        logger.info("Authenticating user...")
        auth_data = {
            "email": test_user_email,
            "password": test_user_password
        }
        
        async with session.post(f"{base_url}/auth/login", json=auth_data) as response:
            if response.status != 200:
                logger.error(f"Authentication failed: {response.status}")
                return False
            
            result = await response.json()
            auth_token = result.get("access_token")
            logger.info("✅ User authenticated successfully")
        
        # 3. Upload document
        logger.info("Uploading test document...")
        test_doc_content = f"""
        INSURANCE POLICY TEST DOCUMENT
        Policy Number: CHUNK-TEST-{uuid.uuid4().hex[:8]}
        Policyholder: {test_user_email}
        
        This is a test insurance policy document for chunk generation validation.
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
        filename = f"chunk_test_{uuid.uuid4().hex[:8]}.pdf"
        
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
                logger.error(f"Upload failed: {response.status}")
                return False
            
            result = await response.json()
            job_id = result.get("job_id")
            document_id = result.get("document_id")
            signed_url = result.get("signed_url")
            logger.info(f"✅ Document upload initiated - Job ID: {job_id}, Document ID: {document_id}")
        
        # 4. Upload content to signed URL
        logger.info("Uploading content to signed URL...")
        async with session.put(signed_url, data=test_doc_content.encode(), headers={"Content-Type": "application/pdf"}) as response:
            if response.status != 200:
                logger.error(f"Content upload failed: {response.status}")
                return False
            logger.info("✅ Content uploaded successfully")
        
        # 5. Wait a bit for processing
        logger.info("Waiting for processing...")
        await asyncio.sleep(10)
        
        # 6. Check job status
        logger.info("Checking job status...")
        try:
            async with session.get(f"{base_url}/documents/{document_id}/status", headers=headers) as response:
                if response.status == 200:
                    status_data = await response.json()
                    logger.info(f"Job status: {status_data}")
                else:
                    logger.warning(f"Status check failed: {response.status}")
        except Exception as e:
            logger.warning(f"Status check error: {e}")
        
        # 7. Check for chunks
        logger.info("Checking for chunks...")
        try:
            async with session.get(f"{base_url}/documents/{document_id}/chunks", headers=headers) as response:
                if response.status == 200:
                    chunks_data = await response.json()
                    if chunks_data and len(chunks_data) > 0:
                        logger.info(f"✅ Found {len(chunks_data)} chunks!")
                        for i, chunk in enumerate(chunks_data[:3]):
                            logger.info(f"Chunk {i+1}: {chunk.get('text', '')[:100]}...")
                        return True
                    else:
                        logger.warning("No chunks found")
                        return False
                else:
                    logger.warning(f"Chunks check failed: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"Chunks check error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_upload_and_chunks())
    if success:
        logger.info("🎉 CHUNK GENERATION IS WORKING!")
    else:
        logger.info("❌ Chunk generation test failed")
