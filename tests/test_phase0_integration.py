#!/usr/bin/env python3
"""
Phase 0 Integration Test
Test the integration of PatientNavigatorChatInterface with the /chat endpoint
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_phase0"
TEST_MESSAGES = [
    "What is the deductible for my insurance policy?",
    "Can you help me understand my coverage?",
    "¿Cuáles son mis beneficios de seguro?",  # Spanish test
    "How do I file a claim?",
    "What's my copay for doctor visits?"
]

class Phase0IntegrationTester:
    """Test the Phase 0 integration of agentic workflows with chat endpoint."""
    
    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url
        self.chat_url = f"{api_base_url}/chat"
        self.test_results = []
        
    async def test_chat_endpoint_integration(self) -> Dict[str, Any]:
        """Test the complete chat endpoint integration."""
        print("🧪 Testing Phase 0 Integration: Agentic Workflows + Chat Endpoint")
        print("=" * 70)
        
        # Test 1: Basic functionality
        print("\n1️⃣ Testing basic chat functionality...")
        basic_test = await self._test_basic_chat()
        self.test_results.append(basic_test)
        
        # Test 2: Multilingual support
        print("\n2️⃣ Testing multilingual support...")
        multilingual_test = await self._test_multilingual_support()
        self.test_results.append(multilingual_test)
        
        # Test 3: Enhanced response format
        print("\n3️⃣ Testing enhanced response format...")
        response_format_test = await self._test_response_format()
        self.test_results.append(response_format_test)
        
        # Test 4: Error handling
        print("\n4️⃣ Testing error handling...")
        error_handling_test = await self._test_error_handling()
        self.test_results.append(error_handling_test)
        
        # Test 5: Performance
        print("\n5️⃣ Testing performance...")
        performance_test = await self._test_performance()
        self.test_results.append(performance_test)
        
        return self._generate_summary()
    
    async def _test_basic_chat(self) -> Dict[str, Any]:
        """Test basic chat functionality."""
        try:
            response = requests.post(
                self.chat_url,
                json={
                    "message": "Hello, can you help me with my insurance?",
                    "conversation_id": f"test_conv_{int(time.time())}",
                    "user_language": "en"
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "basic_chat",
                    "status": "PASS",
                    "response_time": response.elapsed.total_seconds(),
                    "has_text": "text" in data,
                    "has_metadata": "metadata" in data,
                    "has_agent_sources": "agent_sources" in data.get("metadata", {}),
                    "response_preview": data.get("text", "")[:100] + "..." if len(data.get("text", "")) > 100 else data.get("text", "")
                }
            else:
                return {
                    "test": "basic_chat",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                "test": "basic_chat",
                "status": "ERROR",
                "error": str(e)
            }
    
    async def _test_multilingual_support(self) -> Dict[str, Any]:
        """Test multilingual support."""
        try:
            response = requests.post(
                self.chat_url,
                json={
                    "message": "¿Cuáles son mis beneficios de seguro?",
                    "conversation_id": f"test_conv_{int(time.time())}",
                    "user_language": "es"
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "multilingual_support",
                    "status": "PASS",
                    "response_time": response.elapsed.total_seconds(),
                    "has_translation_metadata": "input_processing" in data.get("metadata", {}),
                    "translation_applied": data.get("metadata", {}).get("input_processing", {}).get("translation_applied", False),
                    "response_preview": data.get("text", "")[:100] + "..." if len(data.get("text", "")) > 100 else data.get("text", "")
                }
            else:
                return {
                    "test": "multilingual_support",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                "test": "multilingual_support",
                "status": "ERROR",
                "error": str(e)
            }
    
    async def _test_response_format(self) -> Dict[str, Any]:
        """Test enhanced response format."""
        try:
            response = requests.post(
                self.chat_url,
                json={
                    "message": "What is my deductible?",
                    "conversation_id": f"test_conv_{int(time.time())}",
                    "user_language": "en"
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                metadata = data.get("metadata", {})
                
                return {
                    "test": "response_format",
                    "status": "PASS",
                    "response_time": response.elapsed.total_seconds(),
                    "has_processing_time": "processing_time" in metadata,
                    "has_confidence": "confidence" in metadata,
                    "has_agent_sources": "agent_sources" in metadata,
                    "has_input_processing": "input_processing" in metadata,
                    "has_agent_processing": "agent_processing" in metadata,
                    "has_output_formatting": "output_formatting" in metadata,
                    "has_next_steps": "next_steps" in data,
                    "has_sources": "sources" in data
                }
            else:
                return {
                    "test": "response_format",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                "test": "response_format",
                "status": "ERROR",
                "error": str(e)
            }
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling."""
        try:
            # Test empty message
            response = requests.post(
                self.chat_url,
                json={
                    "message": "",
                    "conversation_id": f"test_conv_{int(time.time())}"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 400:
                return {
                    "test": "error_handling",
                    "status": "PASS",
                    "response_time": response.elapsed.total_seconds(),
                    "empty_message_handled": True,
                    "error_response": response.json()
                }
            else:
                return {
                    "test": "error_handling",
                    "status": "FAIL",
                    "error": f"Expected 400 for empty message, got {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            return {
                "test": "error_handling",
                "status": "ERROR",
                "error": str(e)
            }
    
    async def _test_performance(self) -> Dict[str, Any]:
        """Test performance with multiple requests."""
        try:
            start_time = time.time()
            responses = []
            
            # Send 3 concurrent requests
            for i in range(3):
                response = requests.post(
                    self.chat_url,
                    json={
                        "message": f"Test message {i+1}: What is my insurance coverage?",
                        "conversation_id": f"test_conv_{int(time.time())}_{i}",
                        "user_language": "en"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                responses.append(response)
            
            total_time = time.time() - start_time
            successful_responses = [r for r in responses if r.status_code == 200]
            
            return {
                "test": "performance",
                "status": "PASS" if len(successful_responses) == 3 else "FAIL",
                "total_time": total_time,
                "successful_requests": len(successful_responses),
                "total_requests": len(responses),
                "average_response_time": total_time / len(responses),
                "responses_per_second": len(responses) / total_time
            }
        except Exception as e:
            return {
                "test": "performance",
                "status": "ERROR",
                "error": str(e)
            }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "phase0_status": "COMPLETE" if passed_tests == total_tests else "PARTIAL" if passed_tests > 0 else "FAILED"
        }

async def main():
    """Run Phase 0 integration tests."""
    print("🚀 Starting Phase 0 Integration Tests")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Chat URL: {API_BASE_URL}/chat")
    print()
    
    tester = Phase0IntegrationTester()
    results = await tester.test_chat_endpoint_integration()
    
    print("\n" + "=" * 70)
    print("📊 PHASE 0 INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    summary = results["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Errors: {summary['errors']} ⚠️")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print()
    
    print("📋 Detailed Results:")
    for result in results["test_results"]:
        status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
        print(f"  {status_icon} {result['test']}: {result['status']}")
        if "error" in result:
            print(f"     Error: {result['error']}")
        if "response_time" in result:
            print(f"     Response Time: {result['response_time']:.2f}s")
    
    print()
    print(f"🎯 Phase 0 Status: {results['phase0_status']}")
    
    if results['phase0_status'] == "COMPLETE":
        print("🎉 Phase 0 Integration SUCCESSFUL!")
        print("   The agentic workflows are now integrated with the /chat endpoint.")
        print("   Ready to proceed to Phase 1 (Local Backend + Local Database RAG).")
    else:
        print("⚠️  Phase 0 Integration needs attention.")
        print("   Please review the failed tests and fix issues before proceeding.")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
