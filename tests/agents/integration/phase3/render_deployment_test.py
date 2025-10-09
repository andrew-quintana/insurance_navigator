#!/usr/bin/env python3
"""
Phase 3 - Render Deployment Test

This test validates the Render deployment of the agents integration system
with production database RAG integration via the /chat endpoint.
"""

import asyncio
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase3RenderDeploymentTest:
    def __init__(self):
        self.results = {
            "test_name": "Phase 3 Render Deployment Test",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
        
        # Load production environment
        load_dotenv('.env.production')
        
        # Test configuration - Render URLs
        self.api_url = os.getenv("RENDER_API_URL", "https://your-api-url.example.com")
        self.worker_url = os.getenv("RENDER_WORKER_URL", "https://your-worker-url.example.com")
        self.test_user_email = f"phase3_render_test_{int(time.time())}@example.com"
        self.test_user_password = "TestPassword123!"
        self.access_token = None
        
        # Test queries
        self.test_queries = [
            "What is health insurance?",
            "How do I file a claim?",
            "What's the difference between HMO and PPO?",
            "How do I find a doctor in my network?"
        ]
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            test_result = {
                "name": test_name,
                "status": "PASSED" if result else "FAILED",
                "duration": duration,
                "details": result if isinstance(result, dict) else {"success": result}
            }
            
            self.results["tests"].append(test_result)
            self.results["summary"]["total_tests"] += 1
            
            if result:
                self.results["summary"]["passed"] += 1
                logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            else:
                self.results["summary"]["failed"] += 1
                logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "name": test_name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            }
            
            self.results["tests"].append(test_result)
            self.results["summary"]["total_tests"] += 1
            self.results["summary"]["failed"] += 1
            logger.error(f"❌ {test_name} - ERROR: {str(e)} ({duration:.2f}s)")
    
    async def test_api_service_health(self) -> Dict[str, Any]:
        """Test that the API service is healthy and accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/health", timeout=30.0)
                
                if response.status_code == 200:
                    health_data = response.json()
                    return {
                        "success": True,
                        "api_accessible": True,
                        "health_status": health_data.get("status"),
                        "response_time": response.elapsed.total_seconds(),
                        "render_deployment": True
                    }
                else:
                    return {
                        "success": False,
                        "api_accessible": False,
                        "status_code": response.status_code,
                        "error": f"Health check failed with status {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_worker_service_health(self) -> Dict[str, Any]:
        """Test that the worker service is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                # Try to access worker health endpoint (if available)
                try:
                    response = await client.get(f"{self.worker_url}/health", timeout=30.0)
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "worker_accessible": True,
                            "response_time": response.elapsed.total_seconds()
                        }
                except Exception:
                    # Worker might not have health endpoint, that's okay
                    pass
                
                # Just check if worker URL is reachable
                try:
                    response = await client.get(f"{self.worker_url}/", timeout=10.0)
                    return {
                        "success": True,
                        "worker_accessible": True,
                        "status_code": response.status_code,
                        "note": "Worker accessible but no health endpoint"
                    }
                except Exception:
                    return {
                        "success": False,
                        "worker_accessible": False,
                        "error": "Worker service not accessible"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_user_authentication(self) -> Dict[str, Any]:
        """Test user authentication with Render deployment"""
        try:
            async with httpx.AsyncClient() as client:
                # Try to register a test user
                register_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password,
                    "name": "Phase3 Render Test User"
                }
                
                try:
                    register_response = await client.post(
                        f"{self.api_url}/register",
                        json=register_data,
                        timeout=30.0
                    )
                    user_created = register_response.status_code in [200, 201]
                except Exception as e:
                    user_created = False
                    logger.info(f"User registration failed (may already exist): {str(e)}")
                
                # Try to login
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                login_response = await client.post(
                    f"{self.api_url}/login",
                    json=login_data,
                    timeout=30.0
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.access_token = login_data.get("access_token")
                    
                    return {
                        "success": True,
                        "user_created": user_created,
                        "login_successful": True,
                        "has_access_token": bool(self.access_token),
                        "render_authentication": True
                    }
                else:
                    return {
                        "success": False,
                        "user_created": user_created,
                        "login_successful": False,
                        "status_code": login_response.status_code,
                        "error": f"Login failed with status {login_response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_chat_endpoint_functionality(self) -> Dict[str, Any]:
        """Test /chat endpoint functionality with production RAG"""
        try:
            if not self.access_token:
                return {
                    "success": False,
                    "error": "No access token available"
                }
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Test basic chat message
                chat_data = {
                    "message": "Hello, can you help me with health insurance?",
                    "conversation_id": f"render_test_conv_{int(time.time())}"
                }
                
                response = await client.post(
                    f"{self.api_url}/chat",
                    json=chat_data,
                    headers=headers,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    chat_response = response.json()
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds(),
                        "has_response_text": bool(chat_response.get("text")),
                        "response_length": len(chat_response.get("text", "")),
                        "has_sources": bool(chat_response.get("sources")),
                        "has_confidence": "confidence" in chat_response,
                        "conversation_id": chat_response.get("conversation_id"),
                        "render_chat_functionality": True
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"Chat request failed with status {response.status_code}",
                        "response_text": response.text[:200]
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_rag_integration(self) -> Dict[str, Any]:
        """Test RAG integration with production database"""
        try:
            if not self.access_token:
                return {
                    "success": False,
                    "error": "No access token available"
                }
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Test RAG-specific queries
                rag_results = []
                
                for query in self.test_queries:
                    try:
                        chat_data = {
                            "message": query,
                            "conversation_id": f"render_rag_test_conv_{int(time.time())}"
                        }
                        
                        start_time = time.time()
                        response = await client.post(
                            f"{self.api_url}/chat",
                            json=chat_data,
                            headers=headers,
                            timeout=60.0
                        )
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            chat_response = response.json()
                            rag_results.append({
                                "query": query,
                                "success": True,
                                "response_time": end_time - start_time,
                                "response_length": len(chat_response.get("text", "")),
                                "has_sources": bool(chat_response.get("sources")),
                                "source_count": len(chat_response.get("sources", [])),
                                "confidence": chat_response.get("confidence")
                            })
                        else:
                            rag_results.append({
                                "query": query,
                                "success": False,
                                "status_code": response.status_code,
                                "error": f"Request failed with status {response.status_code}"
                            })
                            
                    except Exception as e:
                        rag_results.append({
                            "query": query,
                            "success": False,
                            "error": str(e)
                        })
                
                # Calculate success metrics
                successful_queries = [r for r in rag_results if r.get("success")]
                success_rate = (len(successful_queries) / len(rag_results) * 100) if rag_results else 0
                
                return {
                    "success": len(successful_queries) > 0,
                    "total_queries": len(rag_results),
                    "successful_queries": len(successful_queries),
                    "success_rate": success_rate,
                    "rag_results": rag_results,
                    "render_rag_integration": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics on Render deployment"""
        try:
            if not self.access_token:
                return {
                    "success": False,
                    "error": "No access token available"
                }
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Test response times
                response_times = []
                successful_requests = 0
                
                for i, query in enumerate(self.test_queries):
                    try:
                        chat_data = {
                            "message": query,
                            "conversation_id": f"render_perf_test_conv_{i}"
                        }
                        
                        start_time = time.time()
                        response = await client.post(
                            f"{self.api_url}/chat",
                            json=chat_data,
                            headers=headers,
                            timeout=60.0
                        )
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            response_time = end_time - start_time
                            response_times.append(response_time)
                            successful_requests += 1
                            
                            logger.info(f"Query {i+1}: {response_time:.2f}s")
                        else:
                            logger.warning(f"Query {i+1} failed with status {response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Query {i+1} failed: {str(e)}")
                
                if response_times:
                    import statistics
                    performance_metrics = {
                        "total_queries": len(self.test_queries),
                        "successful_requests": successful_requests,
                        "success_rate": (successful_requests / len(self.test_queries)) * 100,
                        "average_response_time": statistics.mean(response_times),
                        "median_response_time": statistics.median(response_times),
                        "min_response_time": min(response_times),
                        "max_response_time": max(response_times),
                        "response_times": response_times
                    }
                    
                    # Check if performance meets targets
                    meets_targets = (
                        performance_metrics["average_response_time"] < 5.0 and  # < 5 seconds average
                        performance_metrics["success_rate"] >= 80.0             # >= 80% success rate
                    )
                    
                    return {
                        "success": meets_targets,
                        "performance_metrics": performance_metrics,
                        "meets_targets": meets_targets,
                        "render_performance": True
                    }
                else:
                    return {
                        "success": False,
                        "error": "No successful requests"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """Run all Phase 3 Render deployment tests"""
        logger.info("🚀 Starting Phase 3 Render Deployment Tests")
        
        # Run all tests
        await self.run_test("API Service Health", self.test_api_service_health)
        await self.run_test("Worker Service Health", self.test_worker_service_health)
        await self.run_test("User Authentication", self.test_user_authentication)
        await self.run_test("Chat Endpoint Functionality", self.test_chat_endpoint_functionality)
        await self.run_test("RAG Integration", self.test_rag_integration)
        await self.run_test("Performance Metrics", self.test_performance_metrics)
        
        # Calculate success rate
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]
        self.results["summary"]["success_rate"] = (passed / total * 100) if total > 0 else 0
        
        # Log summary
        logger.info(f"📊 Phase 3 Render Deployment Tests Complete")
        logger.info(f"   Total Tests: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {self.results['summary']['failed']}")
        logger.info(f"   Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        return self.results

async def main():
    """Main test execution"""
    test = Phase3RenderDeploymentTest()
    results = await test.run_all_tests()
    
    # Save results
    results_file = os.path.join(
        os.path.dirname(__file__), 
        '../results/render_deployment_results.json'
    )
    
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📁 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
