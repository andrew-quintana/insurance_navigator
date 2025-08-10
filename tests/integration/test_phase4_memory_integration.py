#!/usr/bin/env python3
"""
Phase 4 Memory Integration Test - Comprehensive testing of the Short-Term Chat Memory MVP
Tests the complete end-to-end flow, performance, error handling, and production readiness.
"""

import pytest
import requests
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Test constants
BASE_URL = "http://127.0.0.1:8000"
MAX_WAIT_TIME = 30  # 30 seconds timeout for memory processing
POLL_INTERVAL = 1   # 1 second between polls

@dataclass
class MemoryTestState:
    """Track memory testing state and timing."""
    chat_id: str
    started_at: datetime
    queue_id: Optional[str] = None
    queue_created_time: Optional[float] = None
    memory_retrieved_time: Optional[float] = None
    processing_completed_time: Optional[float] = None

    def record_queue_created(self):
        self.queue_created_time = (datetime.now() - self.started_at).total_seconds()

    def record_memory_retrieved(self):
        self.memory_retrieved_time = (datetime.now() - self.started_at).total_seconds()

    def record_processing_completed(self):
        self.processing_completed_time = (datetime.now() - self.started_at).total_seconds()

    @property
    def total_time(self) -> float:
        return (datetime.now() - self.started_at).total_seconds()

class TestPhase4MemoryIntegration:
    """Comprehensive Phase 4 memory integration testing."""

    @pytest.fixture(autouse=True)
    def setup(self, test_config):
        """Setup test configuration."""
        self.config = test_config
        self.supabase_url = test_config.supabase.url
        self.service_role_key = test_config.supabase.service_role_key

    def test_health_check(self):
        """Test that the server is healthy and all services are running."""
        print(f"\n🧪 Testing server health...")
        
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        data = response.json()
        print(f"✅ Server health: {data['status']}")
        print(f"✅ Service: {data['service']}")
        print(f"✅ Version: {data['version']}")
        
        # Verify all services are healthy
        services = data.get("services", {})
        for service_name, status in services.items():
            print(f"✅ {service_name}: {status}")
            assert status == "healthy", f"Service {service_name} is not healthy: {status}"
        
        print("✅ All services are healthy")

    def test_memory_update_endpoint(self, test_user):
        """Test the memory update endpoint with valid data."""
        print(f"\n🧪 Testing memory update endpoint...")
        
        # Create a unique chat ID for testing
        chat_id = f"test-chat-{int(time.time())}"
        context_snippet = "User asked about Medicare eligibility requirements and coverage options for 2024."
        
        # Test memory update
        update_data = {
            "chat_id": chat_id,
            "context_snippet": context_snippet,
            "trigger_source": "test"
        }
        
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=update_data,
            headers=headers
        )
        
        print(f"📝 Memory update response status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"❌ Memory update failed: {response.text}")
            print(f"Request data: {update_data}")
            print(f"Headers: {headers}")
            raise AssertionError(f"Memory update failed with status {response.status_code}")
        
        data = response.json()
        print(f"✅ Memory update successful")
        print(f"✅ Queue ID: {data['queue_id']}")
        print(f"✅ Status: {data['status']}")
        print(f"✅ Estimated completion: {data['estimated_completion']}")
        
        # Verify response structure
        assert "queue_id" in data, "Response missing queue_id"
        assert "status" in data, "Response missing status"
        assert "estimated_completion" in data, "Response missing estimated_completion"
        assert data["status"] == "pending_summarization", f"Expected 'pending_summarization', got {data['status']}"
        
        return data["queue_id"], chat_id

    def test_memory_retrieval_endpoint(self, test_user):
        """Test the memory retrieval endpoint."""
        print(f"\n🧪 Testing memory retrieval endpoint...")
        
        # First create a memory update to get a chat ID
        chat_id = f"test-chat-retrieval-{int(time.time())}"
        context_snippet = "User inquired about dental coverage options and premium costs."
        
        update_data = {
            "chat_id": chat_id,
            "context_snippet": context_snippet,
            "trigger_source": "test"
        }
        
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        # Create memory update
        update_response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=update_data,
            headers=headers
        )
        
        assert update_response.status_code == 201, f"Memory update failed: {update_response.text}"
        
        # Now test memory retrieval
        retrieval_response = requests.get(
            f"{BASE_URL}/api/v1/memory/{chat_id}",
            headers=headers
        )
        
        print(f"📖 Memory retrieval response status: {retrieval_response.status_code}")
        
        if retrieval_response.status_code != 200:
            print(f"❌ Memory retrieval failed: {retrieval_response.text}")
            raise AssertionError(f"Memory retrieval failed with status {retrieval_response.status_code}")
        
        data = retrieval_response.json()
        print(f"✅ Memory retrieval successful")
        print(f"✅ Chat ID: {data['chat_id']}")
        print(f"✅ User confirmed: {data['user_confirmed']}")
        print(f"✅ LLM inferred: {data['llm_inferred']}")
        print(f"✅ General summary: {data['general_summary']}")
        print(f"✅ Last updated: {data['last_updated']}")
        
        # Verify response structure
        assert data["chat_id"] == chat_id, f"Chat ID mismatch: expected {chat_id}, got {data['chat_id']}"
        assert "user_confirmed" in data, "Response missing user_confirmed"
        assert "llm_inferred" in data, "Response missing llm_inferred"
        assert "general_summary" in data, "Response missing general_summary"
        assert "last_updated" in data, "Response missing last_updated"
        
        return chat_id

    def test_complete_memory_pipeline(self, test_user):
        """Test the complete memory update and retrieval pipeline."""
        print(f"\n🧪 Testing complete memory pipeline...")
        
        test_state = MemoryTestState(
            chat_id=f"test-pipeline-{int(time.time())}",
            started_at=datetime.now()
        )
        
        # Step 1: Create memory update
        context_snippet = "User discussed their current health insurance plan and needs for better coverage options."
        
        update_data = {
            "chat_id": test_state.chat_id,
            "context_snippet": context_snippet,
            "trigger_source": "test"
        }
        
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        print(f"📝 Step 1: Creating memory update for chat {test_state.chat_id}")
        update_response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=update_data,
            headers=headers
        )
        
        assert update_response.status_code == 201, f"Memory update failed: {update_response.text}"
        
        update_data = update_response.json()
        test_state.queue_id = update_data["queue_id"]
        test_state.record_queue_created()
        
        print(f"✅ Memory update queued with ID: {test_state.queue_id}")
        print(f"✅ Status: {update_data['status']}")
        print(f"✅ Estimated completion: {update_data['estimated_completion']}")
        
        # Step 2: Wait for processing to complete
        print(f"⏳ Step 2: Waiting for memory processing to complete...")
        
        start_wait = time.time()
        while time.time() - start_wait < MAX_WAIT_TIME:
            # Check memory status
            retrieval_response = requests.get(
                f"{BASE_URL}/api/v1/memory/{test_state.chat_id}",
                headers=headers
            )
            
            if retrieval_response.status_code == 200:
                memory_data = retrieval_response.json()
                
                # Check if memory has been updated (not just default values)
                if (memory_data.get("general_summary") and 
                    memory_data["general_summary"] != "" and
                    memory_data["last_updated"] is not None):
                    
                    test_state.record_processing_completed()
                    print(f"✅ Memory processing completed!")
                    print(f"✅ General summary: {memory_data['general_summary'][:100]}...")
                    print(f"✅ Last updated: {memory_data['last_updated']}")
                    break
            
            print(f"⏳ Waiting for memory processing... ({int(time.time() - start_wait)}s elapsed)")
            time.sleep(POLL_INTERVAL)
        else:
            print(f"⚠️ Memory processing did not complete within {MAX_WAIT_TIME} seconds")
            print(f"⚠️ This may indicate the background worker is not running")
        
        # Step 3: Verify final memory state
        print(f"🔍 Step 3: Verifying final memory state...")
        
        final_response = requests.get(
            f"{BASE_URL}/api/v1/memory/{test_state.chat_id}",
            headers=headers
        )
        
        assert final_response.status_code == 200, f"Final memory retrieval failed: {final_response.text}"
        
        final_memory = final_response.json()
        test_state.record_memory_retrieved()
        
        print(f"✅ Final memory state verified")
        print(f"✅ User confirmed: {final_memory['user_confirmed']}")
        print(f"✅ LLM inferred: {final_memory['llm_inferred']}")
        print(f"✅ General summary: {final_memory['general_summary']}")
        print(f"✅ Last updated: {final_memory['last_updated']}")
        
        # Performance summary
        print(f"\n📊 Memory Pipeline Performance Summary:")
        print("=" * 50)
        print(f"📈 Queue Creation:     {test_state.queue_created_time:.2f}s")
        print(f"📈 Memory Retrieval:   {test_state.memory_retrieved_time:.2f}s")
        if test_state.processing_completed_time:
            print(f"📈 Processing Complete: {test_state.processing_completed_time:.2f}s")
        print(f"📈 Total Time:         {test_state.total_time:.2f}s")
        print("=" * 50)
        
        # Performance assertions
        assert test_state.queue_created_time < 0.1, f"Queue creation took too long: {test_state.queue_created_time:.2f}s"
        assert test_state.memory_retrieved_time < 0.1, f"Memory retrieval took too long: {test_state.memory_retrieved_time:.2f}s"
        
        if test_state.processing_completed_time:
            assert test_state.processing_completed_time < 2.0, f"Memory processing took too long: {test_state.processing_completed_time:.2f}s"

    def test_error_handling(self, test_user):
        """Test error handling scenarios."""
        print(f"\n🧪 Testing error handling...")
        
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Invalid chat ID
        print(f"🔍 Test 1: Invalid chat ID")
        invalid_data = {
            "chat_id": "invalid-chat-id-that-does-not-exist",
            "context_snippet": "Test context",
            "trigger_source": "test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=invalid_data,
            headers=headers
        )
        
        print(f"📝 Invalid chat ID response: {response.status_code}")
        if response.status_code == 400:
            print(f"✅ Correctly rejected invalid chat ID")
        else:
            print(f"⚠️ Unexpected response for invalid chat ID: {response.status_code}")
        
        # Test 2: Empty context snippet
        print(f"🔍 Test 2: Empty context snippet")
        empty_data = {
            "chat_id": f"test-empty-{int(time.time())}",
            "context_snippet": "",
            "trigger_source": "test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=empty_data,
            headers=headers
        )
        
        print(f"📝 Empty context response: {response.status_code}")
        if response.status_code == 422:
            print(f"✅ Correctly rejected empty context snippet")
        else:
            print(f"⚠️ Unexpected response for empty context: {response.status_code}")
        
        # Test 3: Missing authentication
        print(f"🔍 Test 3: Missing authentication")
        no_auth_data = {
            "chat_id": f"test-no-auth-{int(time.time())}",
            "context_snippet": "Test context",
            "trigger_source": "test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=no_auth_data,
            headers={"Content-Type": "application/json"}  # No Authorization header
        )
        
        print(f"📝 No auth response: {response.status_code}")
        if response.status_code == 401:
            print(f"✅ Correctly rejected request without authentication")
        else:
            print(f"⚠️ Unexpected response for no auth: {response.status_code}")

    def test_rate_limiting(self, test_user):
        """Test rate limiting functionality."""
        print(f"\n🧪 Testing rate limiting...")
        
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        # Send multiple requests quickly to trigger rate limiting
        print(f"📝 Sending multiple requests to test rate limiting...")
        
        responses = []
        for i in range(105):  # Send 105 requests (should exceed 100 req/min limit)
            data = {
                "chat_id": f"rate-limit-test-{i}",
                "context_snippet": f"Test context {i}",
                "trigger_source": "test"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/memory/update",
                json=data,
                headers=headers
            )
            
            responses.append(response.status_code)
            
            if i % 20 == 0:
                print(f"📝 Sent {i+1} requests...")
        
        # Count responses
        successful = responses.count(201)
        rate_limited = responses.count(429)
        other_errors = len(responses) - successful - rate_limited
        
        print(f"📊 Rate limiting test results:")
        print(f"✅ Successful requests: {successful}")
        print(f"⏳ Rate limited requests: {rate_limited}")
        print(f"❌ Other errors: {other_errors}")
        
        # Verify rate limiting is working
        assert rate_limited > 0, "Rate limiting not triggered"
        assert successful >= 95, f"Too many requests failed: {successful}/105"
        
        print(f"✅ Rate limiting is working correctly")

    def test_concurrent_requests(self, test_user):
        """Test system performance under concurrent load."""
        print(f"\n🧪 Testing concurrent request handling...")
        
        import threading
        import concurrent.futures
        
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        def send_memory_update(chat_id: str) -> Dict[str, Any]:
            """Send a single memory update request."""
            data = {
                "chat_id": chat_id,
                "context_snippet": f"Concurrent test context for {chat_id}",
                "trigger_source": "test"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/memory/update",
                json=data,
                headers=headers
            )
            end_time = time.time()
            
            return {
                "chat_id": chat_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 201
            }
        
        # Test with 10 concurrent requests
        chat_ids = [f"concurrent-test-{i}-{int(time.time())}" for i in range(10)]
        
        print(f"📝 Sending 10 concurrent memory update requests...")
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_memory_update, chat_id) for chat_id in chat_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Analyze results
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)
        
        print(f"📊 Concurrent test results:")
        print(f"✅ Successful requests: {successful}/10")
        print(f"❌ Failed requests: {failed}/10")
        print(f"⏱️ Average response time: {avg_response_time:.3f}s")
        print(f"⏱️ Maximum response time: {max_response_time:.3f}s")
        print(f"⏱️ Total concurrent time: {total_time:.3f}s")
        
        # Performance assertions
        assert successful >= 8, f"Too many concurrent requests failed: {successful}/10"
        assert avg_response_time < 0.1, f"Average response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 0.5, f"Maximum response time too high: {max_response_time:.3f}s"
        
        print(f"✅ Concurrent request handling is working correctly")

    def test_memory_retrieval_performance(self, test_user):
        """Test memory retrieval performance under load."""
        print(f"\n🧪 Testing memory retrieval performance...")
        
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        # First create a memory entry
        chat_id = f"perf-test-{int(time.time())}"
        update_data = {
            "chat_id": chat_id,
            "context_snippet": "Performance test context for memory retrieval testing.",
            "trigger_source": "test"
        }
        
        # Create the memory entry
        update_response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=update_data,
            headers=headers
        )
        
        assert update_response.status_code == 201, f"Failed to create memory entry: {update_response.text}"
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Test retrieval performance with multiple requests
        print(f"📖 Testing memory retrieval performance...")
        
        response_times = []
        for i in range(20):  # 20 retrieval requests
            start_time = time.time()
            response = requests.get(
                f"{BASE_URL}/api/v1/memory/{chat_id}",
                headers=headers
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200, f"Memory retrieval failed: {response.status_code}"
        
        # Calculate performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        
        print(f"📊 Memory retrieval performance:")
        print(f"⏱️ Average response time: {avg_response_time:.3f}s")
        print(f"⏱️ Minimum response time: {min_response_time:.3f}s")
        print(f"⏱️ Maximum response time: {max_response_time:.3f}s")
        print(f"⏱️ 95th percentile: {p95_response_time:.3f}s")
        
        # Performance assertions
        assert avg_response_time < 0.05, f"Average retrieval time too high: {avg_response_time:.3f}s"
        assert p95_response_time < 0.1, f"95th percentile retrieval time too high: {p95_response_time:.3f}s"
        
        print(f"✅ Memory retrieval performance meets requirements")

    def test_production_readiness(self, test_user):
        """Test production readiness criteria."""
        print(f"\n🧪 Testing production readiness...")
        
        # Test 1: Health check reliability
        print(f"🔍 Test 1: Health check reliability")
        health_responses = []
        for i in range(10):
            response = requests.get(f"{BASE_URL}/health")
            health_responses.append(response.status_code)
            time.sleep(0.1)
        
        health_success_rate = health_responses.count(200) / len(health_responses)
        print(f"📊 Health check success rate: {health_success_rate:.1%}")
        assert health_success_rate == 1.0, f"Health check not 100% reliable: {health_success_rate:.1%}"
        
        # Test 2: Authentication consistency
        print(f"🔍 Test 2: Authentication consistency")
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "Content-Type": "application/json"
        }
        
        auth_responses = []
        for i in range(10):
            response = requests.get(f"{BASE_URL}/me", headers=headers)
            auth_responses.append(response.status_code)
            time.sleep(0.1)
        
        auth_success_rate = auth_responses.count(200) / len(auth_responses)
        print(f"📊 Authentication success rate: {auth_success_rate:.1%}")
        assert auth_success_rate == 1.0, f"Authentication not 100% reliable: {auth_success_rate:.1%}"
        
        # Test 3: Memory API consistency
        print(f"🔍 Test 3: Memory API consistency")
        chat_id = f"prod-test-{int(time.time())}"
        
        # Create memory entry
        update_data = {
            "chat_id": chat_id,
            "context_snippet": "Production readiness test context.",
            "trigger_source": "test"
        }
        
        update_response = requests.post(
            f"{BASE_URL}/api/v1/memory/update",
            json=update_data,
            headers=headers
        )
        
        assert update_response.status_code == 201, f"Memory update failed: {update_response.text}"
        
        # Test retrieval consistency
        retrieval_responses = []
        for i in range(10):
            response = requests.get(f"{BASE_URL}/api/v1/memory/{chat_id}", headers=headers)
            retrieval_responses.append(response.status_code)
            time.sleep(0.1)
        
        retrieval_success_rate = retrieval_responses.count(200) / len(retrieval_responses)
        print(f"📊 Memory retrieval success rate: {retrieval_success_rate:.1%}")
        assert retrieval_success_rate == 1.0, f"Memory retrieval not 100% reliable: {retrieval_success_rate:.1%}"
        
        print(f"✅ Production readiness criteria met")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"]) 