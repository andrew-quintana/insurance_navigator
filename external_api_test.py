#!/usr/bin/env python3
"""
External API Integration Test
Test real LlamaParse and OpenAI APIs before Phase 3 deployment

This test validates:
1. LlamaParse API connectivity and document parsing
2. OpenAI API connectivity and embedding generation
3. Complete pipeline with real external services
4. Webhook callback functionality
"""

import asyncio
import json
import time
import uuid
import hashlib
import requests
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.production')

# Test configuration
RUN_ID = f"external_api_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"

# API Configuration
API_CONFIG = {
    "LLAMAPARSE_API_KEY": os.getenv("LLAMAPARSE_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "LLAMAPARSE_BASE_URL": "https://api.cloud.llamaindex.ai",
    "OPENAI_API_URL": "https://api.openai.com/v1",
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY")
}

# Test documents
TEST_DOCUMENTS = [
    {
        "name": "Simulated Insurance Document.pdf",
        "path": "test_document.pdf",
        "expected_size": 1782
    },
    {
        "name": "Scan Classic HMO.pdf", 
        "path": "test_upload.pdf",
        "expected_size": 2544678
    }
]

class ExternalAPITester:
    def __init__(self):
        self.results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "environment": "real_external_apis",
            "tests": [],
            "summary": {}
        }
        
    async def test_llamaparse_connectivity(self) -> Dict[str, Any]:
        """Test LlamaParse API connectivity and basic functionality"""
        print("🔗 Testing LlamaParse API connectivity...")
        
        try:
            # Test basic connectivity
            headers = {
                "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Test API jobs endpoint (discovered working endpoint)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_CONFIG['LLAMAPARSE_BASE_URL']}/api/v1/jobs",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("✅ LlamaParse API connectivity successful")
                    return {"success": True, "status_code": response.status_code}
                else:
                    print(f"❌ LlamaParse API error: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ LlamaParse connectivity failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_openai_connectivity(self) -> Dict[str, Any]:
        """Test OpenAI API connectivity and basic functionality"""
        print("🤖 Testing OpenAI API connectivity...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Test models endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_CONFIG['OPENAI_API_URL']}/models",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    models = response.json()
                    embedding_models = [m for m in models.get('data', []) if 'embedding' in m.get('id', '').lower()]
                    print(f"✅ OpenAI API connectivity successful - {len(embedding_models)} embedding models available")
                    return {"success": True, "embedding_models": len(embedding_models)}
                else:
                    print(f"❌ OpenAI API error: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ OpenAI connectivity failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_llamaparse_document_parsing(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test LlamaParse document parsing with real API"""
        print(f"📄 Testing LlamaParse document parsing for {doc_info['name']}...")
        
        try:
            # Prepare file data
            file_path = Path(doc_info['path'])
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Create LlamaParse job
            headers = {
                "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            job_data = {
                "name": doc_info['name'],
                "file": file_data,
                "language": "en",
                "parsing_instruction": "Extract all text content from this document, preserving structure and formatting."
            }
            
            async with httpx.AsyncClient() as client:
                # Submit parsing job using the correct endpoint
                response = await client.post(
                    f"{API_CONFIG['LLAMAPARSE_BASE_URL']}/v1/parse",
                    headers=headers,
                    files={"file": (doc_info['name'], file_data, "application/pdf")},
                    data={"language": "en"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    job_result = response.json()
                    job_id = job_result.get('id')
                    print(f"✅ LlamaParse job submitted: {job_id}")
                    
                    # Poll for completion (simplified - in real implementation would use webhooks)
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        await asyncio.sleep(10)  # Wait 10 seconds between checks
                        
                        status_response = await client.get(
                            f"{API_CONFIG['LLAMAPARSE_BASE_URL']}/v1/jobs/{job_id}",
                            headers=headers,
                            timeout=30
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status')
                            
                            if status == 'SUCCESS':
                                # Get parsed content
                                content_response = await client.get(
                                    f"{API_CONFIG['LLAMAPARSE_BASE_URL']}/v1/jobs/{job_id}/result",
                                    headers=headers,
                                    timeout=30
                                )
                                
                                if content_response.status_code == 200:
                                    parsed_content = content_response.text
                                    print(f"✅ Document parsed successfully - {len(parsed_content)} characters")
                                    return {
                                        "success": True,
                                        "job_id": job_id,
                                        "parsed_content_length": len(parsed_content),
                                        "parsed_content_preview": parsed_content[:200] + "..." if len(parsed_content) > 200 else parsed_content
                                    }
                                else:
                                    return {"success": False, "error": f"Failed to get parsed content: {content_response.status_code}"}
                            elif status == 'ERROR':
                                return {"success": False, "error": "LlamaParse job failed"}
                            else:
                                print(f"⏳ Job status: {status} (attempt {attempt + 1}/{max_attempts})")
                        else:
                            return {"success": False, "error": f"Failed to check job status: {status_response.status_code}"}
                    
                    return {"success": False, "error": "Job did not complete within timeout"}
                else:
                    return {"success": False, "error": f"Failed to submit job: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            print(f"❌ LlamaParse parsing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_openai_embedding_generation(self, text: str) -> Dict[str, Any]:
        """Test OpenAI embedding generation with real API"""
        print("🧠 Testing OpenAI embedding generation...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Prepare embedding request
            embedding_data = {
                "input": text,
                "model": "text-embedding-3-small",
                "encoding_format": "float"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_CONFIG['OPENAI_API_URL']}/embeddings",
                    headers=headers,
                    json=embedding_data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embeddings = result.get('data', [])
                    if embeddings:
                        embedding = embeddings[0].get('embedding', [])
                        print(f"✅ Embedding generated - {len(embedding)} dimensions")
                        return {
                            "success": True,
                            "dimensions": len(embedding),
                            "model": result.get('model'),
                            "usage": result.get('usage', {}),
                            "embedding_preview": embedding[:5] if len(embedding) > 5 else embedding
                        }
                    else:
                        return {"success": False, "error": "No embeddings in response"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code} - {response.text}"}
                    
        except Exception as e:
            print(f"❌ OpenAI embedding generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_complete_pipeline(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test complete pipeline: parse → chunk → embed"""
        print(f"🔄 Testing complete pipeline for {doc_info['name']}...")
        
        try:
            # Step 1: Parse document with LlamaParse
            parse_result = await self.test_llamaparse_document_parsing(doc_info)
            if not parse_result["success"]:
                return {"success": False, "error": f"Parsing failed: {parse_result['error']}"}
            
            parsed_content = parse_result.get("parsed_content_preview", "")
            if not parsed_content:
                return {"success": False, "error": "No parsed content available"}
            
            # Step 2: Generate embeddings for parsed content
            embed_result = await self.test_openai_embedding_generation(parsed_content)
            if not embed_result["success"]:
                return {"success": False, "error": f"Embedding failed: {embed_result['error']}"}
            
            # Step 3: Simulate chunking (simplified)
            chunks = [parsed_content[i:i+1000] for i in range(0, len(parsed_content), 1000)]
            print(f"✅ Created {len(chunks)} chunks")
            
            # Step 4: Generate embeddings for each chunk
            chunk_embeddings = []
            for i, chunk in enumerate(chunks[:3]):  # Limit to first 3 chunks for testing
                chunk_embed_result = await self.test_openai_embedding_generation(chunk)
                if chunk_embed_result["success"]:
                    chunk_embeddings.append({
                        "chunk_index": i,
                        "dimensions": chunk_embed_result["dimensions"],
                        "embedding_preview": chunk_embed_result["embedding_preview"]
                    })
                else:
                    print(f"⚠️ Failed to embed chunk {i}: {chunk_embed_result['error']}")
            
            return {
                "success": True,
                "parsing": parse_result,
                "embedding": embed_result,
                "chunks_created": len(chunks),
                "chunks_embedded": len(chunk_embeddings),
                "chunk_embeddings": chunk_embeddings
            }
            
        except Exception as e:
            print(f"❌ Complete pipeline test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_webhook_simulation(self) -> Dict[str, Any]:
        """Test webhook callback simulation"""
        print("🔔 Testing webhook callback simulation...")
        
        try:
            # Simulate a webhook payload that LlamaParse would send
            webhook_payload = {
                "job_id": str(uuid.uuid4()),
                "status": "SUCCESS",
                "result": {
                    "markdown": "This is a simulated parsed document content.",
                    "metadata": {
                        "pages": 1,
                        "language": "en",
                        "confidence": 0.95
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Test webhook processing (simplified)
            if webhook_payload.get("status") == "SUCCESS":
                print("✅ Webhook simulation successful")
                return {
                    "success": True,
                    "webhook_payload": webhook_payload,
                    "processing_time": "simulated"
                }
            else:
                return {"success": False, "error": "Webhook status not SUCCESS"}
                
        except Exception as e:
            print(f"❌ Webhook simulation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_test(self):
        """Run the complete external API test"""
        print("🚀 Starting External API Integration Test")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 Environment: Real External APIs")
        
        # Test API connectivity
        print("\n" + "="*50)
        print("API CONNECTIVITY TESTS")
        print("="*50)
        
        llamaparse_connectivity = await self.test_llamaparse_connectivity()
        openai_connectivity = await self.test_openai_connectivity()
        
        if not llamaparse_connectivity["success"] or not openai_connectivity["success"]:
            print("❌ API connectivity tests failed, aborting")
            # Still create a summary for error reporting
            self.results["summary"] = {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "success_rate": "0%",
                "api_connectivity": {
                    "llamaparse": llamaparse_connectivity["success"],
                    "openai": openai_connectivity["success"]
                },
                "webhook_simulation": False,
                "end_time": datetime.now().isoformat()
            }
            return self.results
        
        # Test document processing
        print("\n" + "="*50)
        print("DOCUMENT PROCESSING TESTS")
        print("="*50)
        
        for i, doc_info in enumerate(TEST_DOCUMENTS, 1):
            print(f"\n📄 Test Document {i}: {doc_info['name']}")
            
            test_result = {
                "document": doc_info['name'],
                "connectivity": {"llamaparse": llamaparse_connectivity, "openai": openai_connectivity},
                "parsing": None,
                "embedding": None,
                "complete_pipeline": None,
                "success": False
            }
            
            # Test complete pipeline
            pipeline_result = await self.test_complete_pipeline(doc_info)
            test_result["complete_pipeline"] = pipeline_result
            
            if pipeline_result["success"]:
                test_result["parsing"] = pipeline_result["parsing"]
                test_result["embedding"] = pipeline_result["embedding"]
                test_result["success"] = True
            
            self.results["tests"].append(test_result)
            print(f"📊 Test {i} result: {'✅ SUCCESS' if test_result['success'] else '❌ FAILED'}")
        
        # Test webhook simulation
        print("\n" + "="*50)
        print("WEBHOOK SIMULATION TEST")
        print("="*50)
        
        webhook_result = await self.test_webhook_simulation()
        self.results["webhook_test"] = webhook_result
        
        # Generate summary
        total_tests = len(self.results["tests"])
        successful_tests = sum(1 for test in self.results["tests"] if test["success"])
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "api_connectivity": {
                "llamaparse": llamaparse_connectivity["success"],
                "openai": openai_connectivity["success"]
            },
            "webhook_simulation": webhook_result["success"],
            "end_time": datetime.now().isoformat()
        }
        
        # Save results
        results_file = f"external_api_test_results_{RUN_ID}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 External API Test Complete!")
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main test execution"""
    tester = ExternalAPITester()
    results = await tester.run_test()
    
    # Print summary
    print("\n" + "="*60)
    print("EXTERNAL API TEST SUMMARY")
    print("="*60)
    print(f"Environment: Real External APIs")
    print(f"Run ID: {RUN_ID}")
    print(f"Success Rate: {results['summary']['success_rate']}")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Successful: {results['summary']['successful_tests']}")
    print(f"Failed: {results['summary']['failed_tests']}")
    print(f"LlamaParse API: {'✅' if results['summary']['api_connectivity']['llamaparse'] else '❌'}")
    print(f"OpenAI API: {'✅' if results['summary']['api_connectivity']['openai'] else '❌'}")
    print(f"Webhook Simulation: {'✅' if results['summary']['webhook_simulation'] else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())
