#!/usr/bin/env python3
"""
Production Webhook Testing Script

This script tests webhook functionality against the production API service
to validate that webhooks are working correctly in production.
"""

import asyncio
import json
import httpx
import uuid
from datetime import datetime
from typing import Dict, Any

# Production API configuration
PRODUCTION_API_URL = "***REMOVED***"
WEBHOOK_ENDPOINT = f"{PRODUCTION_API_URL}/api/upload-pipeline/webhook/llamaparse"

async def test_production_webhook():
    """Test webhook functionality against production API service."""
    print("🔍 TESTING PRODUCTION WEBHOOK FUNCTIONALITY")
    print("=" * 60)
    print(f"Production API URL: {PRODUCTION_API_URL}")
    print(f"Webhook Endpoint: {WEBHOOK_ENDPOINT}")
    print()
    
    # Test 1: Health check
    print("1️⃣ Testing Production API Health Check")
    print("-" * 40)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            health_response = await client.get(f"{PRODUCTION_API_URL}/health")
            print(f"Health Check Status: {health_response.status_code}")
            if health_response.status_code == 200:
                print("✅ Production API is healthy")
            else:
                print(f"❌ Production API health check failed: {health_response.text}")
                return False
    except Exception as e:
        print(f"❌ Production API health check failed: {e}")
        return False
    
    print()
    
    # Test 2: Test webhook endpoint accessibility
    print("2️⃣ Testing Webhook Endpoint Accessibility")
    print("-" * 40)
    test_job_id = f"test-webhook-{uuid.uuid4().hex[:8]}"
    webhook_url = f"{WEBHOOK_ENDPOINT}/{test_job_id}"
    
    print(f"Test Job ID: {test_job_id}")
    print(f"Webhook URL: {webhook_url}")
    
    # Test 3: Send test webhook payload
    print()
    print("3️⃣ Sending Test Webhook Payload")
    print("-" * 40)
    
    test_payload = {
        "status": "completed",
        "result": {
            "md": "# Test Document\n\nThis is a test document for webhook testing.\n\n## Test Content\n\nThis document contains test content to validate webhook processing.",
            "txt": "Test Document\n\nThis is a test document for webhook testing.\n\nTest Content\n\nThis document contains test content to validate webhook processing."
        },
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "source": "webhook_test_script"
        }
    }
    
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Sending webhook request...")
            response = await client.post(
                webhook_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Webhook request successful")
                try:
                    response_data = response.json()
                    print(f"Response Data: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"Response Text: {response.text}")
            else:
                print(f"❌ Webhook request failed: {response.status_code}")
                print(f"Error Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Webhook request timed out (30s)")
        print("This suggests the webhook handler is hanging or has database connection issues")
        return False
    except Exception as e:
        print(f"❌ Webhook request failed: {e}")
        return False
    
    print()
    
    # Test 4: Test with different job statuses
    print("4️⃣ Testing Different Job Statuses")
    print("-" * 40)
    
    test_cases = [
        {
            "status": "processing",
            "result": None,
            "description": "Processing status"
        },
        {
            "status": "failed",
            "result": {"error": "Test error message"},
            "description": "Failed status"
        },
        {
            "status": "completed",
            "result": {
                "md": "# Another Test Document\n\nThis is another test document.",
                "txt": "Another Test Document\n\nThis is another test document."
            },
            "description": "Completed status with different content"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['description']}")
        test_job_id = f"test-{test_case['status']}-{uuid.uuid4().hex[:8]}"
        webhook_url = f"{WEBHOOK_ENDPOINT}/{test_job_id}"
        
        payload = {
            "status": test_case["status"],
            "result": test_case["result"],
            "metadata": {
                "test": True,
                "test_case": i,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    print(f"  ✅ {test_case['description']} - Success")
                else:
                    print(f"  ❌ {test_case['description']} - Failed: {response.status_code}")
                    print(f"  Error: {response.text}")
                    
        except Exception as e:
            print(f"  ❌ {test_case['description']} - Exception: {e}")
    
    print()
    print("🎉 Production Webhook Testing Complete!")
    return True

async def test_webhook_error_handling():
    """Test webhook error handling and edge cases."""
    print("🔍 TESTING WEBHOOK ERROR HANDLING")
    print("=" * 60)
    
    error_test_cases = [
        {
            "name": "Invalid JSON",
            "payload": "invalid json",
            "content_type": "application/json"
        },
        {
            "name": "Missing status field",
            "payload": {"result": {"md": "test"}},
            "content_type": "application/json"
        },
        {
            "name": "Invalid status value",
            "payload": {"status": "invalid_status", "result": {"md": "test"}},
            "content_type": "application/json"
        },
        {
            "name": "Empty payload",
            "payload": {},
            "content_type": "application/json"
        }
    ]
    
    for test_case in error_test_cases:
        print(f"Testing: {test_case['name']}")
        test_job_id = f"error-test-{uuid.uuid4().hex[:8]}"
        webhook_url = f"{WEBHOOK_ENDPOINT}/{test_job_id}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if isinstance(test_case["payload"], str):
                    response = await client.post(
                        webhook_url,
                        content=test_case["payload"],
                        headers={"Content-Type": test_case["content_type"]}
                    )
                else:
                    response = await client.post(
                        webhook_url,
                        json=test_case["payload"],
                        headers={"Content-Type": test_case["content_type"]}
                    )
                
                print(f"  Status: {response.status_code}")
                if response.status_code >= 400:
                    print(f"  ✅ Properly handled error: {response.text[:100]}")
                else:
                    print(f"  ⚠️  Unexpected success: {response.text[:100]}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")

async def main():
    """Main test function."""
    print("🚀 Starting Production Webhook Tests")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test basic webhook functionality
    success = await test_production_webhook()
    
    if success:
        print()
        # Test error handling
        await test_webhook_error_handling()
    
    print()
    print("🏁 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
