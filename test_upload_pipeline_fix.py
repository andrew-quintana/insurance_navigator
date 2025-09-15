#!/usr/bin/env python3
"""
Test the upload pipeline fix with correct endpoint and authentication.
"""

import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, Any

class UploadPipelineTester:
    """Test the fixed upload pipeline."""
    
    def __init__(self):
        self.external_api_url = "***REMOVED***"
        self.test_user_email = f"upload_test_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        
    async def test_complete_pipeline(self):
        """Test the complete upload pipeline."""
        async with aiohttp.ClientSession() as session:
            try:
                print("🔐 Step 1: User Authentication")
                # Register and login user
                registration_data = {
                    "email": self.test_user_email,
                    "password": self.test_password,
                    "full_name": "Upload Test User"
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/register",
                    json=registration_data
                ) as response:
                    registration_result = await response.json()
                
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                print(f"✅ Authentication successful: {login_result.get('success', False)}")
                print(f"📝 User ID: {login_result.get('user', {}).get('id')}")
                
                print("\n📤 Step 2: Document Upload")
                # Test upload with correct endpoint
                document_data = {
                    "content": """
                    INSURANCE POLICY DOCUMENT - UPLOAD PIPELINE TEST
                    
                    Policy Number: UPLOAD-TEST-001
                    Policyholder: Test User
                    Coverage Type: Comprehensive Auto Insurance
                    Premium: $1,200 annually
                    Deductible: $500
                    
                    This is a test document for upload pipeline validation.
                    """,
                    "filename": "upload_test_policy.pdf",
                    "content_type": "application/pdf"
                }
                
                async with session.post(
                    f"{self.external_api_url}/api/v2/upload",
                    json=document_data,
                    headers=headers
                ) as response:
                    upload_result = await response.json()
                
                print(f"✅ Upload response: {upload_result}")
                
                if upload_result.get("success"):
                    document_id = upload_result.get("document_id")
                    job_id = upload_result.get("job_id")
                    
                    print(f"📄 Document ID: {document_id}")
                    print(f"⚙️ Job ID: {job_id}")
                    
                    print("\n⏳ Step 3: Wait for Processing")
                    # Wait for processing
                    await asyncio.sleep(10)
                    
                    # Check job status
                    async with session.get(
                        f"{self.external_api_url}/jobs/{job_id}",
                        headers=headers
                    ) as response:
                        job_status = await response.json()
                    
                    print(f"📊 Job Status: {job_status}")
                    
                    print("\n🔍 Step 4: Test RAG Retrieval")
                    # Test RAG queries
                    test_queries = [
                        "What is the policy number?",
                        "What is the premium amount?",
                        "What is the deductible?"
                    ]
                    
                    for query in test_queries:
                        chat_data = {
                            "message": query,
                            "conversation_id": str(uuid.uuid4())
                        }
                        
                        async with session.post(
                            f"{self.external_api_url}/chat",
                            json=chat_data,
                            headers=headers
                        ) as response:
                            chat_result = await response.json()
                        
                        print(f"❓ Query: {query}")
                        print(f"💬 Response: {chat_result.get('response', 'No response')[:100]}...")
                        print(f"✅ Success: {chat_result.get('success', False)}")
                        print()
                    
                    print("\n📋 Step 5: Check Documents")
                    # Check if documents are retrievable
                    async with session.get(
                        f"{self.external_api_url}/documents",
                        headers=headers
                    ) as response:
                        documents_result = await response.json()
                    
                    print(f"📚 Documents: {documents_result}")
                    
                else:
                    print(f"❌ Upload failed: {upload_result}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()

async def main():
    """Main test function."""
    print("🚀 Starting Upload Pipeline Test")
    print("=" * 50)
    
    tester = UploadPipelineTester()
    await tester.test_complete_pipeline()
    
    print("=" * 50)
    print("✅ Upload Pipeline Test Complete")

if __name__ == "__main__":
    asyncio.run(main())
