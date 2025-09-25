#!/usr/bin/env python3
"""
Debug script to check what signed URL is being generated.
"""

import asyncio
import aiohttp
import hashlib
import json
import uuid
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_signed_url():
    """Debug the signed URL generation."""
    
    base_url = "***REMOVED***"
    
    # Create test user
    test_user_email = f"debug_url_{uuid.uuid4().hex[:8]}@example.com"
    test_user_password = "TestPassword123!"
    
    async with aiohttp.ClientSession() as session:
        logger.info("🔍 Debugging signed URL generation...")
        
        # 1. Create user
        logger.info("1️⃣ Creating test user...")
        signup_data = {
            "email": test_user_email,
            "password": test_user_password,
            "full_name": "Debug URL User",
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
        test_doc_content = "Test document content"
        test_doc_hash = hashlib.sha256(test_doc_content.encode()).hexdigest()
        filename = f"debug_url_{uuid.uuid4().hex[:8]}.pdf"
        
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
            logger.info(f"🔗 SIGNED URL: {signed_url}")
            
            # Parse the URL to see what domain it's using
            if "storage.supabase.co" in signed_url:
                logger.error("❌ Still using incorrect storage.supabase.co domain!")
            elif "znvwzkdblknkkztqyfnu.supabase.co" in signed_url:
                logger.info("✅ Using correct Supabase domain!")
            else:
                logger.warning(f"⚠️ Unknown domain in signed URL: {signed_url}")
            
            return True

if __name__ == "__main__":
    asyncio.run(debug_signed_url())
