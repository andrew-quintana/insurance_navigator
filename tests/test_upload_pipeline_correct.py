#!/usr/bin/env python3
"""
Test the upload pipeline with correct request format.
"""

import asyncio
import aiohttp
import json
import time
import uuid
import hashlib
from typing import Dict, Any

class CorrectUploadPipelineTester:
    """Test the upload pipeline with correct request format."""
    
    def __init__(self):
        self.external_api_url = "https://insurance-navigator-api.onrender.com"
        self.test_user_email = f"upload_test_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        
    def calculate_file_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def test_complete_pipeline(self):
        """Test the complete upload pipeline with correct format."""
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
                
                print("\n📤 Step 2: Document Upload with Correct Format")
                # Prepare document content
                document_content = """
                INSURANCE POLICY DOCUMENT - UPLOAD PIPELINE TEST
                
                Policy Number: UPLOAD-TEST-001
                Policyholder: Test User
                Coverage Type: Comprehensive Auto Insurance
                Premium: $1,200 annually
                Deductible: $500
                
                This is a test document for upload pipeline validation.
                The document contains various insurance terms and conditions.
                """
                
                # Calculate required fields
                content_bytes = document_content.encode('utf-8')
                bytes_len = len(content_bytes)
                sha256_hash = self.calculate_file_hash(document_content)
                
                # Test upload with correct format
                document_data = {
                    "filename": "upload_test_policy.pdf",
                    "bytes_len": bytes_len,
                    "mime": "application/pdf",
                    "sha256": sha256_hash,
                    "ocr": False
                }
                
                print(f"📊 Upload data: {json.dumps(document_data, indent=2)}")
                
                async with session.post(
                    f"{self.external_api_url}/api/upload-pipeline/upload",
                    json=document_data,
                    headers=headers
                ) as response:
                    upload_result = await response.json()
                
                print(f"✅ Upload response: {json.dumps(upload_result, indent=2)}")
                
                if upload_result.get("success"):
                    document_id = upload_result.get("document_id")
                    job_id = upload_result.get("job_id")
                    signed_url = upload_result.get("signed_url")
                    
                    print(f"📄 Document ID: {document_id}")
                    print(f"⚙️ Job ID: {job_id}")
                    print(f"🔗 Signed URL: {signed_url[:50]}...")
                    
                    print("\n📤 Step 3: Upload File Content to Signed URL")
                    # Upload the actual file content to the signed URL
                    if signed_url:
                        async with session.put(
                            signed_url,
                            data=content_bytes,
                            headers={"Content-Type": "application/pdf"}
                        ) as response:
                            upload_status = response.status
                            print(f"📤 File upload status: {upload_status}")
                    
                    print("\n⏳ Step 4: Wait for Processing")
                    # Wait for processing
                    await asyncio.sleep(15)
                    
                    # Check job status
                    async with session.get(
                        f"{self.external_api_url}/jobs/{job_id}",
                        headers=headers
                    ) as response:
                        job_status = await response.json()
                    
                    print(f"📊 Job Status: {json.dumps(job_status, indent=2)}")
                    
                    print("\n🔍 Step 5: Test RAG Retrieval")
                    # Test RAG queries
                    test_queries = [
                        "What is the policy number?",
                        "What is the premium amount?",
                        "What is the deductible?",
                        "What type of insurance is this?"
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
                        print(f"💬 Response: {chat_result.get('response', 'No response')[:150]}...")
                        print(f"✅ Success: {chat_result.get('success', False)}")
                        print()
                    
                    print("\n📋 Step 6: Check Documents")
                    # Check if documents are retrievable
                    async with session.get(
                        f"{self.external_api_url}/documents",
                        headers=headers
                    ) as response:
                        documents_result = await response.json()
                    
                    print(f"📚 Documents: {json.dumps(documents_result, indent=2)}")
                    
                    print("\n🔍 Step 7: Test Direct RAG Similarity Search")
                    # Test direct similarity search
                    async with session.post(
                        f"{self.external_api_url}/rag/similarity_search",
                        json={"query": "insurance policy coverage"},
                        headers=headers
                    ) as response:
                        similarity_result = await response.json()
                    
                    print(f"🔍 Similarity Search: {json.dumps(similarity_result, indent=2)}")
                    
                else:
                    print(f"❌ Upload failed: {upload_result}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()

async def main():
    """Main test function."""
    print("🚀 Starting Correct Upload Pipeline Test")
    print("=" * 60)
    
    tester = CorrectUploadPipelineTester()
    await tester.test_complete_pipeline()
    
    print("=" * 60)
    print("✅ Upload Pipeline Test Complete")

if __name__ == "__main__":
    asyncio.run(main())
