#!/usr/bin/env python3
"""
Debug Upload Endpoint - Detailed error analysis
"""

import asyncio
import httpx
import json
import time
import uuid
from datetime import datetime
import logging

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_upload_endpoint():
    """Debug the upload endpoint with detailed error analysis"""
    
    api_url = "https://insurance-navigator-api.onrender.com"
    
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Register user
            logger.info("🔍 Step 1: Registering user...")
            registration_data = {
                "email": f"debug-test-{int(time.time())}@example.com",
                "password": "testpassword123",
                "name": "Debug Test User"
            }
            
            reg_response = await client.post(
                f"{api_url}/register", 
                json=registration_data, 
                timeout=30
            )
            
            logger.info(f"Registration response: {reg_response.status_code}")
            logger.info(f"Registration headers: {dict(reg_response.headers)}")
            logger.info(f"Registration body: {reg_response.text}")
            
            if reg_response.status_code != 200:
                logger.error(f"Registration failed: {reg_response.status_code} - {reg_response.text}")
                return
            
            reg_data = reg_response.json()
            user_id = reg_data.get("user", {}).get("id")
            logger.info(f"✅ User registered: {user_id}")
            
            # Step 2: Login user
            logger.info("🔍 Step 2: Logging in user...")
            login_data = {
                "email": registration_data["email"],
                "password": registration_data["password"]
            }
            
            login_response = await client.post(
                f"{api_url}/login", 
                json=login_data, 
                timeout=30
            )
            
            logger.info(f"Login response: {login_response.status_code}")
            logger.info(f"Login headers: {dict(login_response.headers)}")
            logger.info(f"Login body: {login_response.text}")
            
            if login_response.status_code != 200:
                logger.error(f"Login failed: {login_response.status_code} - {login_response.text}")
                return
            
            login_data = login_response.json()
            access_token = login_data.get("access_token")
            logger.info(f"✅ User logged in, token: {access_token[:20]}...")
            
            # Step 3: Test upload endpoint with detailed debugging
            logger.info("🔍 Step 3: Testing upload endpoint...")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Create a simple test file
            test_content = f"""# Test Document

This is a test document for debugging.

Document ID: {uuid.uuid4()}
Generated: {datetime.utcnow().isoformat()}
""".encode('utf-8')
            
            test_file = ("test_document.pdf", test_content, "application/pdf")
            
            upload_data = {
                "policy_id": f"policy-{uuid.uuid4().hex[:8]}",
                "document_type": "test_document"
            }
            
            files = {"file": test_file}
            
            logger.info(f"Upload data: {upload_data}")
            logger.info(f"Files: {[(name, len(content), mime) for name, content, mime in files.values()]}")
            logger.info(f"Headers: {headers}")
            
            upload_response = await client.post(
                f"{api_url}/upload-document-backend",
                data=upload_data,
                files=files,
                headers=headers,
                timeout=60
            )
            
            logger.info(f"Upload response status: {upload_response.status_code}")
            logger.info(f"Upload response headers: {dict(upload_response.headers)}")
            logger.info(f"Upload response body: {upload_response.text}")
            
            if upload_response.status_code == 200:
                logger.info("✅ Upload successful!")
                result = upload_response.json()
                logger.info(f"Upload result: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"❌ Upload failed: {upload_response.status_code}")
                logger.error(f"Error details: {upload_response.text}")
                
                # Try to parse error response
                try:
                    error_data = upload_response.json()
                    logger.error(f"Parsed error: {json.dumps(error_data, indent=2)}")
                except:
                    logger.error("Could not parse error response as JSON")
            
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(debug_upload_endpoint())
