#!/usr/bin/env python3
"""
Simple test to verify the production worker is using real APIs.
Uses existing user and focuses on monitoring worker behavior.
"""

import asyncio
import sys
import os
import json
import aiohttp
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

class SimpleWorkerTester:
    def __init__(self):
        self.api_base_url = "***REMOVED***"
        # Use existing user from previous tests
        self.auth_token = "***REMOVED***.eyJzdWIiOiI5MzY1NTFiNi1iN2E0LTRkM2QtOWZlMC1hNDkxNzk0ZmQ2NjYiLCJlbWFpbCI6InRlc3RfdXNlckBleGFtcGxlLmNvbSIsImV4cCI6MTczNjQ0NDAwMH0.test_token"
        self.test_document_id = None
        self.test_job_id = None
        
    async def run_test(self):
        """Run simple test to verify real APIs are working."""
        print("🔍 Testing Production Worker - Real APIs Verification")
        print("=" * 60)
        
        try:
            # Step 1: Check API health
            print("\n1️⃣ Checking API health...")
            await self.check_api_health()
            
            # Step 2: Upload test document
            print("\n2️⃣ Uploading test document...")
            await self.upload_test_document()
            
            # Step 3: Wait and check processing
            print("\n3️⃣ Waiting for worker processing...")
            await self.wait_for_processing()
            
            # Step 4: Test RAG with new document
            print("\n4️⃣ Testing RAG with processed document...")
            await self.test_rag_system()
            
            print("\n✅ Test completed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            return False
        
        return True
    
    async def check_api_health(self):
        """Check API health and service status."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ API Status: {health_data.get('status')}")
                    
                    services = health_data.get('services', {})
                    for service, status in services.items():
                        print(f"   {service}: {status}")
                    
                    # Check if real services are healthy
                    if services.get('openai') == 'healthy' and services.get('llamaparse') == 'healthy':
                        print("✅ Real APIs are healthy!")
                        return True
                    else:
                        print("⚠️  Some real APIs may not be healthy")
                        return False
                else:
                    print(f"❌ API health check failed: {response.status}")
                    return False
    
    async def upload_test_document(self):
        """Upload test document."""
        test_doc_path = "examples/test_insurance_document.pdf"
        
        if not os.path.exists(test_doc_path):
            raise Exception(f"Test document not found: {test_doc_path}")
        
        async with aiohttp.ClientSession() as session:
            # Prepare file upload
            with open(test_doc_path, 'rb') as f:
                file_data = f.read()
            
            # Create multipart form data
            data = aiohttp.FormData()
            data.add_field('file', file_data, filename='test_insurance_document.pdf', content_type='application/pdf')
            data.add_field('policy_id', f'test_production_{int(time.time())}')
            
            # Set authorization header
            headers = {
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            async with session.post(f"{self.api_base_url}/upload-document-backend", data=data, headers=headers) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"Document upload failed: {response.status} - {response_text}")
                
                result = await response.json()
                self.test_document_id = result.get("document_id")
                self.test_job_id = result.get("job_id")
                
                print(f"✅ Document uploaded successfully")
                print(f"   Document ID: {self.test_document_id}")
                print(f"   Job ID: {self.test_job_id}")
    
    async def wait_for_processing(self):
        """Wait for worker to process the document."""
        print("⏳ Waiting for worker processing (up to 3 minutes)...")
        
        max_wait_time = 180  # 3 minutes
        check_interval = 15  # 15 seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check job status
                async with aiohttp.ClientSession() as session:
                    headers = {'Authorization': f'Bearer {self.auth_token}'}
                    
                    async with session.get(f"{self.api_base_url}/api/v2/jobs/{self.test_job_id}", headers=headers) as response:
                        if response.status == 200:
                            job_data = await response.json()
                            status = job_data.get("status", "unknown")
                            
                            print(f"   Job status: {status}")
                            
                            if status in ["completed", "failed", "error"]:
                                if status == "completed":
                                    print("✅ Document processing completed!")
                                    return True
                                else:
                                    print(f"❌ Document processing failed: {status}")
                                    return False
                        
                        await asyncio.sleep(check_interval)
                        
            except Exception as e:
                print(f"   Error checking job status: {str(e)}")
                await asyncio.sleep(check_interval)
        
        print("⏰ Timeout waiting for processing")
        return False
    
    async def test_rag_system(self):
        """Test RAG system with the processed document."""
        print("🔍 Testing RAG system...")
        
        # Set production database URL
        os.environ["DATABASE_URL"] = "postgresql://postgres.znvwzkdblknkkztqyfnu:Accessa2024!@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
        
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Use the user ID from the uploaded document
        user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"
        
        # Initialize RAG system
        config = RetrievalConfig(
            max_chunks=5,
            similarity_threshold=0.3
        )
        
        rag_tool = RAGTool(user_id, config)
        
        # Test queries
        test_queries = [
            "What is my deductible?",
            "What are the coverage details?",
            "What is covered under this policy?"
        ]
        
        results = {}
        
        for query in test_queries:
            print(f"   Testing: {query}")
            
            try:
                # Get chunks directly from RAG tool
                chunks = await rag_tool.retrieve_chunks_from_text(query)
                
                print(f"     Retrieved {len(chunks)} chunks")
                
                # Check content quality
                real_content_found = False
                for chunk in chunks:
                    content = chunk.content.lower()
                    if any(keyword in content for keyword in ['deductible', 'coverage', 'policy', 'insurance', 'premium', 'copay']):
                        real_content_found = True
                        print(f"     ✅ Found real insurance content: {chunk.content[:100]}...")
                        break
                
                if not real_content_found and chunks:
                    print(f"     ⚠️  Content may be mock: {chunks[0].content[:100]}...")
                
                results[query] = {
                    "chunks_count": len(chunks),
                    "has_real_content": real_content_found,
                    "chunks": [chunk.content[:200] for chunk in chunks]
                }
                
            except Exception as e:
                print(f"     ❌ Error: {str(e)}")
                results[query] = {"error": str(e)}
        
        # Save results
        timestamp = int(datetime.now().timestamp())
        results_file = f"worker_real_apis_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {results_file}")
        
        # Summary
        successful_queries = sum(1 for r in results.values() if "error" not in r)
        real_content_queries = sum(1 for r in results.values() if r.get("has_real_content", False))
        
        print(f"\n📊 Test Summary:")
        print(f"   Successful queries: {successful_queries}/{len(test_queries)}")
        print(f"   Queries with real content: {real_content_queries}/{len(test_queries)}")
        
        if real_content_queries > 0:
            print("✅ Real APIs appear to be working!")
        else:
            print("⚠️  May still be using mock services")

async def main():
    """Run the simple worker test."""
    tester = SimpleWorkerTester()
    success = await tester.run_test()
    
    if success:
        print("\n🎉 Worker test completed!")
    else:
        print("\n❌ Worker test failed!")

if __name__ == "__main__":
    asyncio.run(main())
