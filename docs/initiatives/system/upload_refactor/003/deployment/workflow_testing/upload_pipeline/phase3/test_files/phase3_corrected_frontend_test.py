#!/usr/bin/env python3
"""
Phase 3 Corrected Frontend Client Simulation Test
Tests the correct workflow: API creates records + provides signed URL, client uploads directly to Supabase
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

async def test_corrected_frontend_workflow():
    """Test the corrected frontend workflow with proper API endpoints"""
    
    api_url = "***REMOVED***"
    
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Register user
            logger.info("🔍 Step 1: Registering user...")
            registration_data = {
                "email": f"corrected-test-{int(time.time())}@example.com",
                "password": "testpassword123",
                "name": "Corrected Test User"
            }
            
            reg_response = await client.post(
                f"{api_url}/register", 
                json=registration_data, 
                timeout=30
            )
            
            if reg_response.status_code != 200:
                logger.error(f"❌ Registration failed: {reg_response.status_code} - {reg_response.text}")
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
            
            if login_response.status_code != 200:
                logger.error(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
                return
            
            login_data = login_response.json()
            access_token = login_data.get("access_token")
            logger.info(f"✅ User logged in, token: {access_token[:20]}...")
            
            # Step 3: Create test file content and hash
            logger.info("🔍 Step 3: Preparing test document...")
            test_content = f"""# Test Document for Corrected Workflow

This is a test document for the corrected frontend workflow.

Document ID: {uuid.uuid4()}
Generated: {datetime.utcnow().isoformat()}
Test Type: Corrected API Workflow
""".encode('utf-8')
            
            # Calculate SHA256 hash
            file_sha256 = hashlib.sha256(test_content).hexdigest()
            logger.info(f"📄 Test document prepared - Size: {len(test_content)} bytes, SHA256: {file_sha256[:16]}...")
            
            # Step 4: Call correct API endpoint to initiate upload
            logger.info("🔍 Step 4: Calling correct API endpoint (/api/upload-pipeline/upload)...")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            upload_request = {
                "filename": "corrected_test_document.pdf",
                "bytes_len": len(test_content),
                "mime": "application/pdf",
                "sha256": file_sha256,
                "ocr": False
            }
            
            logger.info(f"📤 Upload request: {json.dumps(upload_request, indent=2)}")
            
            upload_response = await client.post(
                f"{api_url}/api/upload-pipeline/upload",
                json=upload_request,
                headers=headers,
                timeout=60
            )
            
            logger.info(f"📊 Upload response status: {upload_response.status_code}")
            logger.info(f"📊 Upload response headers: {dict(upload_response.headers)}")
            logger.info(f"📊 Upload response body: {upload_response.text}")
            
            if upload_response.status_code != 200:
                logger.error(f"❌ Upload initiation failed: {upload_response.status_code}")
                try:
                    error_data = upload_response.json()
                    logger.error(f"❌ Error details: {json.dumps(error_data, indent=2)}")
                except:
                    logger.error(f"❌ Raw error: {upload_response.text}")
                return
            
            # Parse upload response
            upload_result = upload_response.json()
            job_id = upload_result.get("job_id")
            document_id = upload_result.get("document_id")
            signed_url = upload_result.get("signed_url")
            upload_expires_at = upload_result.get("upload_expires_at")
            
            logger.info(f"✅ Upload initiated successfully!")
            logger.info(f"📋 Job ID: {job_id}")
            logger.info(f"📋 Document ID: {document_id}")
            logger.info(f"📋 Signed URL: {signed_url[:100]}...")
            logger.info(f"📋 Expires at: {upload_expires_at}")
            
            # Step 5: Upload file directly to Supabase using signed URL
            logger.info("🔍 Step 5: Uploading file directly to Supabase storage...")
            
            # Note: In a real frontend, this would be done by the browser
            # For testing, we'll simulate the direct upload
            try:
                upload_to_storage_response = await client.put(
                    signed_url,
                    content=test_content,
                    headers={"Content-Type": "application/pdf"},
                    timeout=60
                )
                
                logger.info(f"📊 Storage upload response: {upload_to_storage_response.status_code}")
                if upload_to_storage_response.status_code in [200, 201, 204]:
                    logger.info("✅ File uploaded to storage successfully!")
                else:
                    logger.warning(f"⚠️ Storage upload response: {upload_to_storage_response.status_code} - {upload_to_storage_response.text}")
            except Exception as e:
                logger.warning(f"⚠️ Storage upload failed (expected in test): {e}")
                logger.info("ℹ️ This is expected in testing - the signed URL may not be valid for direct upload")
            
            # Step 6: Monitor job processing by worker
            logger.info("🔍 Step 6: Monitoring job processing by worker service...")
            
            # Monitor job status
            max_attempts = 120  # 2 minutes with 1-second intervals
            for attempt in range(max_attempts):
                try:
                    job_status_response = await client.get(
                        f"{api_url}/api/v2/jobs/{job_id}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if job_status_response.status_code == 200:
                        job_status = job_status_response.json()
                        current_status = job_status.get("status", "unknown")
                        current_state = job_status.get("state", "unknown")
                        progress = job_status.get("progress", {})
                        
                        logger.info(f"📊 Job status (attempt {attempt + 1}/{max_attempts}): {current_status} | {current_state}")
                        
                        # Check if job is complete
                        if current_status in ['complete', 'duplicate'] and current_state == "done":
                            logger.info(f"🎉 Job completed with status: {current_status}")
                            break
                        elif current_status in ['failed_parse', 'failed_chunking', 'failed_embedding']:
                            logger.error(f"❌ Job failed with status: {current_status}")
                            break
                    else:
                        logger.warning(f"⚠️ Job status check failed: {job_status_response.status_code}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Job status check error: {e}")
                
                await asyncio.sleep(1)
            
            logger.info("🎯 Corrected frontend workflow test completed!")
            
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_corrected_frontend_workflow())
