#!/usr/bin/env python3
"""
Phase 3 - Cloud Chat Endpoint Test

This test validates the /chat endpoint functionality in the cloud environment
with production database RAG integration and full agent communication.
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

class Phase3CloudChatEndpointTest:
    def __init__(self):
        self.results = {
            "test_name": "Phase 3 Cloud Chat Endpoint Test",
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
        
        # Test configuration
        self.agent_api_url = os.getenv('AGENT_API_URL', 'https://agents-api.yourdomain.com')
        self.test_user_email = f"phase3_cloud_test_{int(time.time())}@example.com"
        self.test_user_password = "TestPassword123!"
        self.access_token = None
        
        # Test queries for chat endpoint
        self.test_queries = [
            "What is health insurance?",
            "How do I file a claim?",
            "What's the difference between HMO and PPO?",
            "How do I find a doctor in my network?",
            "What is the deductible for my insurance?",
            "How do I check my benefits?",
            "What is a copay?"
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
    
    async def test_cloud_api_availability(self) -> Dict[str, Any]:
        """Test that the cloud API is available and accessible"""
        try:
            async with httpx.AsyncClient() as client:
                # Test health endpoint
                response = await client.get(f"{self.agent_api_url}/health", timeout=30.0)
                
                if response.status_code == 200:
                    health_data = response.json()
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "health_status": health_data.get("status"),
                        "services": health_data.get("services", {}),
                        "response_time": response.elapsed.total_seconds(),
                        "cloud_deployment": True
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"Health check failed with status {response.status_code}",
                        "response_text": response.text[:200]
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_cloud_user_authentication(self) -> Dict[str, Any]:
        """Test user authentication in cloud environment"""
        try:
            async with httpx.AsyncClient() as client:
                # Try to register a test user
                register_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password,
                    "name": "Phase3 Cloud Test User"
                }
                
                try:
                    register_response = await client.post(
                        f"{self.agent_api_url}/register",
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
                    f"{self.agent_api_url}/login",
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
                        "user_data": login_data.get("user", {}),
                        "cloud_authentication": True
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
    
    async def test_cloud_chat_endpoint_basic(self) -> Dict[str, Any]:
        """Test basic chat endpoint functionality in cloud"""
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
                    "conversation_id": f"cloud_test_conv_{int(time.time())}"
                }
                
                response = await client.post(
                    f"{self.agent_api_url}/chat",
                    json=chat_data,
                    headers=headers,
                    timeout=60.0  # Longer timeout for cloud
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
                        "has_metadata": "metadata" in chat_response,
                        "conversation_id": chat_response.get("conversation_id"),
                        "cloud_response": True
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
    
    async def test_cloud_rag_integration(self) -> Dict[str, Any]:
        """Test RAG integration with production database in cloud"""
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
                
                for query in self.test_queries[:5]:  # Test first 5 queries
                    try:
                        chat_data = {
                            "message": query,
                            "conversation_id": f"cloud_rag_test_conv_{int(time.time())}"
                        }
                        
                        start_time = time.time()
                        response = await client.post(
                            f"{self.agent_api_url}/chat",
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
                                "confidence": chat_response.get("confidence"),
                                "processing_time": chat_response.get("processing_time"),
                                "cloud_rag": True
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
                    "cloud_rag_integration": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_cloud_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics in cloud environment"""
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
                
                # Performance test with multiple concurrent requests
                performance_results = []
                
                async def single_chat_request(query, request_id):
                    try:
                        chat_data = {
                            "message": query,
                            "conversation_id": f"cloud_perf_test_conv_{request_id}"
                        }
                        
                        start_time = time.time()
                        response = await client.post(
                            f"{self.agent_api_url}/chat",
                            json=chat_data,
                            headers=headers,
                            timeout=60.0
                        )
                        end_time = time.time()
                        
                        return {
                            "request_id": request_id,
                            "query": query,
                            "success": response.status_code == 200,
                            "response_time": end_time - start_time,
                            "status_code": response.status_code,
                            "cloud_performance": True
                        }
                    except Exception as e:
                        return {
                            "request_id": request_id,
                            "query": query,
                            "success": False,
                            "error": str(e)
                        }
                
                # Run concurrent requests
                tasks = []
                for i, query in enumerate(self.test_queries[:3]):  # Test first 3 queries
                    task = single_chat_request(query, i)
                    tasks.append(task)
                
                performance_results = await asyncio.gather(*tasks)
                
                # Calculate performance metrics
                successful_requests = [r for r in performance_results if r.get("success")]
                response_times = [r["response_time"] for r in successful_requests]
                
                performance_metrics = {
                    "total_requests": len(performance_results),
                    "successful_requests": len(successful_requests),
                    "success_rate": (len(successful_requests) / len(performance_results) * 100) if performance_results else 0,
                    "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
                    "min_response_time": min(response_times) if response_times else 0,
                    "max_response_time": max(response_times) if response_times else 0,
                    "cloud_performance": True
                }
                
                return {
                    "success": len(successful_requests) > 0,
                    "performance_metrics": performance_metrics,
                    "detailed_results": performance_results
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_cloud_error_handling(self) -> Dict[str, Any]:
        """Test error handling in cloud environment"""
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
                
                error_tests = []
                
                # Test 1: Empty message
                try:
                    response = await client.post(
                        f"{self.agent_api_url}/chat",
                        json={"message": ""},
                        headers=headers,
                        timeout=30.0
                    )
                    error_tests.append({
                        "test": "empty_message",
                        "status_code": response.status_code,
                        "expected_error": True,
                        "got_error": response.status_code != 200,
                        "cloud_error_handling": True
                    })
                except Exception as e:
                    error_tests.append({
                        "test": "empty_message",
                        "error": str(e),
                        "expected_error": True,
                        "got_error": True,
                        "cloud_error_handling": True
                    })
                
                # Test 2: Missing message field
                try:
                    response = await client.post(
                        f"{self.agent_api_url}/chat",
                        json={},
                        headers=headers,
                        timeout=30.0
                    )
                    error_tests.append({
                        "test": "missing_message",
                        "status_code": response.status_code,
                        "expected_error": True,
                        "got_error": response.status_code != 200,
                        "cloud_error_handling": True
                    })
                except Exception as e:
                    error_tests.append({
                        "test": "missing_message",
                        "error": str(e),
                        "expected_error": True,
                        "got_error": True,
                        "cloud_error_handling": True
                    })
                
                # Test 3: Very long message
                try:
                    long_message = "A" * 10000  # 10k character message
                    response = await client.post(
                        f"{self.agent_api_url}/chat",
                        json={"message": long_message},
                        headers=headers,
                        timeout=60.0
                    )
                    error_tests.append({
                        "test": "long_message",
                        "status_code": response.status_code,
                        "expected_error": False,  # Should handle gracefully
                        "got_error": response.status_code != 200,
                        "cloud_error_handling": True
                    })
                except Exception as e:
                    error_tests.append({
                        "test": "long_message",
                        "error": str(e),
                        "expected_error": False,
                        "got_error": True,
                        "cloud_error_handling": True
                    })
                
                # Calculate error handling metrics
                proper_error_handling = sum(1 for test in error_tests if test.get("expected_error") == test.get("got_error"))
                total_error_tests = len(error_tests)
                
                return {
                    "success": proper_error_handling >= total_error_tests * 0.75,  # 75% success rate
                    "proper_error_handling": proper_error_handling,
                    "total_error_tests": total_error_tests,
                    "error_handling_rate": (proper_error_handling / total_error_tests * 100) if total_error_tests > 0 else 0,
                    "error_tests": error_tests
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_cloud_conversation_continuity(self) -> Dict[str, Any]:
        """Test conversation continuity in cloud environment"""
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
                
                conversation_id = f"cloud_continuity_test_conv_{int(time.time())}"
                conversation_results = []
                
                # Test conversation flow
                conversation_flow = [
                    "Hello, I need help with health insurance.",
                    "What is the difference between HMO and PPO?",
                    "Which one should I choose?",
                    "Thank you for your help!"
                ]
                
                for i, message in enumerate(conversation_flow):
                    try:
                        chat_data = {
                            "message": message,
                            "conversation_id": conversation_id
                        }
                        
                        response = await client.post(
                            f"{self.agent_api_url}/chat",
                            json=chat_data,
                            headers=headers,
                            timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            chat_response = response.json()
                            conversation_results.append({
                                "message_index": i,
                                "message": message,
                                "success": True,
                                "response_length": len(chat_response.get("text", "")),
                                "conversation_id": chat_response.get("conversation_id"),
                                "has_context": bool(chat_response.get("text")),
                                "cloud_conversation": True
                            })
                        else:
                            conversation_results.append({
                                "message_index": i,
                                "message": message,
                                "success": False,
                                "status_code": response.status_code,
                                "error": f"Request failed with status {response.status_code}"
                            })
                            
                    except Exception as e:
                        conversation_results.append({
                            "message_index": i,
                            "message": message,
                            "success": False,
                            "error": str(e)
                        })
                
                # Calculate continuity metrics
                successful_messages = [r for r in conversation_results if r.get("success")]
                continuity_success = len(successful_messages) >= len(conversation_flow) * 0.8  # 80% success rate
                
                return {
                    "success": continuity_success,
                    "total_messages": len(conversation_flow),
                    "successful_messages": len(successful_messages),
                    "continuity_rate": (len(successful_messages) / len(conversation_flow) * 100) if conversation_flow else 0,
                    "conversation_results": conversation_results
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """Run all Phase 3 cloud chat endpoint tests"""
        logger.info("🚀 Starting Phase 3 Cloud Chat Endpoint Tests")
        
        # Run all tests
        await self.run_test("Cloud API Availability", self.test_cloud_api_availability)
        await self.run_test("Cloud User Authentication", self.test_cloud_user_authentication)
        await self.run_test("Cloud Chat Endpoint Basic", self.test_cloud_chat_endpoint_basic)
        await self.run_test("Cloud RAG Integration", self.test_cloud_rag_integration)
        await self.run_test("Cloud Performance Metrics", self.test_cloud_performance_metrics)
        await self.run_test("Cloud Error Handling", self.test_cloud_error_handling)
        await self.run_test("Cloud Conversation Continuity", self.test_cloud_conversation_continuity)
        
        # Calculate success rate
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]
        self.results["summary"]["success_rate"] = (passed / total * 100) if total > 0 else 0
        
        # Log summary
        logger.info(f"📊 Phase 3 Cloud Chat Endpoint Tests Complete")
        logger.info(f"   Total Tests: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {self.results['summary']['failed']}")
        logger.info(f"   Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        return self.results

async def main():
    """Main test execution"""
    test = Phase3CloudChatEndpointTest()
    results = await test.run_all_tests()
    
    # Save results
    results_file = os.path.join(
        os.path.dirname(__file__), 
        '../results/cloud_chat_endpoint_results.json'
    )
    
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📁 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
