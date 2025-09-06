#!/usr/bin/env python3
"""
Simple External API Test
Test what we can actually validate with real external APIs

This test focuses on:
1. OpenAI API connectivity and embedding generation
2. Basic API key validation
3. Rate limiting and error handling
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from typing import Dict, Any
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.production')

# Test configuration
RUN_ID = f"simple_external_api_{int(time.time())}"

# API Configuration
API_CONFIG = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "OPENAI_API_URL": "https://api.openai.com/v1",
    "LLAMAPARSE_API_KEY": os.getenv("LLAMAPARSE_API_KEY"),
    "LLAMAPARSE_BASE_URL": "https://api.cloud.llamaindex.ai"
}

class SimpleExternalAPITester:
    def __init__(self):
        self.results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "environment": "real_external_apis_simple",
            "tests": [],
            "summary": {}
        }
        
    async def test_openai_models(self) -> Dict[str, Any]:
        """Test OpenAI models endpoint"""
        print("🤖 Testing OpenAI models endpoint...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_CONFIG['OPENAI_API_URL']}/models",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    models = response.json()
                    embedding_models = [m for m in models.get('data', []) if 'embedding' in m.get('id', '').lower()]
                    print(f"✅ OpenAI models endpoint successful - {len(embedding_models)} embedding models")
                    return {
                        "success": True,
                        "total_models": len(models.get('data', [])),
                        "embedding_models": len(embedding_models),
                        "embedding_model_ids": [m['id'] for m in embedding_models]
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_openai_embedding_simple(self) -> Dict[str, Any]:
        """Test OpenAI embedding generation with simple text"""
        print("🧠 Testing OpenAI embedding generation...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Simple test text
            test_text = "This is a test document for insurance policy analysis."
            
            embedding_data = {
                "input": test_text,
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
                            "embedding_preview": embedding[:5]
                        }
                    else:
                        return {"success": False, "error": "No embeddings in response"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code} - {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_openai_embedding_batch(self) -> Dict[str, Any]:
        """Test OpenAI embedding generation with multiple texts"""
        print("📚 Testing OpenAI batch embedding generation...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Test multiple texts
            test_texts = [
                "Insurance policy coverage details",
                "Medical expense reimbursement terms",
                "Deductible and copayment information"
            ]
            
            embedding_data = {
                "input": test_texts,
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
                    print(f"✅ Batch embedding generated - {len(embeddings)} embeddings")
                    return {
                        "success": True,
                        "embedding_count": len(embeddings),
                        "model": result.get('model'),
                        "usage": result.get('usage', {}),
                        "dimensions": len(embeddings[0].get('embedding', [])) if embeddings else 0
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status_code} - {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_llamaparse_basic_connectivity(self) -> Dict[str, Any]:
        """Test basic LlamaParse connectivity"""
        print("🔗 Testing LlamaParse basic connectivity...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Test the working jobs endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_CONFIG['LLAMAPARSE_BASE_URL']}/api/v1/jobs",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    jobs_data = response.json()
                    job_count = jobs_data.get('total_count', 0)
                    print(f"✅ LlamaParse connectivity successful - {job_count} jobs found")
                    return {
                        "success": True,
                        "job_count": job_count,
                        "status_code": response.status_code
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting behavior"""
        print("⏱️ Testing rate limiting behavior...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            # Make multiple rapid requests to test rate limiting
            requests_made = 0
            successful_requests = 0
            rate_limited = False
            
            async with httpx.AsyncClient() as client:
                for i in range(5):  # Make 5 rapid requests
                    try:
                        embedding_data = {
                            "input": f"Test request {i+1}",
                            "model": "text-embedding-3-small"
                        }
                        
                        response = await client.post(
                            f"{API_CONFIG['OPENAI_API_URL']}/embeddings",
                            headers=headers,
                            json=embedding_data,
                            timeout=30
                        )
                        
                        requests_made += 1
                        
                        if response.status_code == 200:
                            successful_requests += 1
                        elif response.status_code == 429:
                            rate_limited = True
                            print(f"⚠️ Rate limited on request {i+1}")
                            break
                        else:
                            print(f"⚠️ Request {i+1} failed: {response.status_code}")
                            
                    except Exception as e:
                        print(f"⚠️ Request {i+1} error: {e}")
                    
                    # Small delay between requests
                    await asyncio.sleep(0.5)
            
            print(f"✅ Rate limiting test complete - {successful_requests}/{requests_made} successful")
            return {
                "success": True,
                "requests_made": requests_made,
                "successful_requests": successful_requests,
                "rate_limited": rate_limited
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_test(self):
        """Run the simple external API test"""
        print("🚀 Starting Simple External API Test")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 Environment: Real External APIs (Simple)")
        
        # Test OpenAI functionality
        print("\n" + "="*50)
        print("OPENAI API TESTS")
        print("="*50)
        
        models_test = await self.test_openai_models()
        self.results["tests"].append({"test": "openai_models", "result": models_test})
        
        embedding_simple_test = await self.test_openai_embedding_simple()
        self.results["tests"].append({"test": "openai_embedding_simple", "result": embedding_simple_test})
        
        embedding_batch_test = await self.test_openai_embedding_batch()
        self.results["tests"].append({"test": "openai_embedding_batch", "result": embedding_batch_test})
        
        rate_limiting_test = await self.test_rate_limiting()
        self.results["tests"].append({"test": "rate_limiting", "result": rate_limiting_test})
        
        # Test LlamaParse connectivity
        print("\n" + "="*50)
        print("LLAMAPARSE API TESTS")
        print("="*50)
        
        llamaparse_test = await self.test_llamaparse_basic_connectivity()
        self.results["tests"].append({"test": "llamaparse_connectivity", "result": llamaparse_test})
        
        # Generate summary
        total_tests = len(self.results["tests"])
        successful_tests = sum(1 for test in self.results["tests"] if test["result"]["success"])
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "end_time": datetime.now().isoformat()
        }
        
        # Save results
        results_file = f"simple_external_api_test_results_{RUN_ID}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Simple External API Test Complete!")
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main test execution"""
    tester = SimpleExternalAPITester()
    results = await tester.run_test()
    
    # Print summary
    print("\n" + "="*60)
    print("SIMPLE EXTERNAL API TEST SUMMARY")
    print("="*60)
    print(f"Environment: Real External APIs (Simple)")
    print(f"Run ID: {RUN_ID}")
    print(f"Success Rate: {results['summary']['success_rate']}")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Successful: {results['summary']['successful_tests']}")
    print(f"Failed: {results['summary']['failed_tests']}")
    
    # Detailed results
    for test in results['tests']:
        status = "✅" if test['result']['success'] else "❌"
        print(f"{status} {test['test']}")

if __name__ == "__main__":
    asyncio.run(main())
