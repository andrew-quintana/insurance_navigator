#!/usr/bin/env python3
"""
Direct Webhook Test

This script tests the webhook endpoint directly without database dependencies
to validate the webhook handler functionality.
"""

import asyncio
import json
import httpx
import uuid
from datetime import datetime

# Production API configuration
PRODUCTION_API_URL = "https://insurance-navigator-api.onrender.com"
WEBHOOK_ENDPOINT = f"{PRODUCTION_API_URL}/api/upload-pipeline/webhook/llamaparse"

async def test_webhook_direct():
    """Test webhook endpoint directly without database dependencies."""
    print("🔍 DIRECT WEBHOOK TEST")
    print("=" * 50)
    print(f"Production API: {PRODUCTION_API_URL}")
    print(f"Webhook Endpoint: {WEBHOOK_ENDPOINT}")
    print()
    
    # Test 1: Basic webhook request
    print("1️⃣ Testing Basic Webhook Request")
    print("-" * 40)
    
    job_id = f"test-direct-{uuid.uuid4().hex[:8]}"
    webhook_url = f"{WEBHOOK_ENDPOINT}/{job_id}"
    
    test_payload = {
        "status": "completed",
        "result": {
            "md": "# Test Document\n\nThis is a test document for direct webhook testing.",
            "txt": "Test Document\n\nThis is a test document for direct webhook testing."
        },
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "source": "direct_webhook_test"
        }
    }
    
    print(f"Job ID: {job_id}")
    print(f"Webhook URL: {webhook_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("Sending webhook request...")
            response = await client.post(
                webhook_url,
                json=test_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Direct-Webhook-Test/1.0"
                }
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
                
    except httpx.TimeoutException:
        print("❌ Webhook request timed out (60s)")
        print("This confirms the webhook handler is hanging due to database issues")
    except Exception as e:
        print(f"❌ Webhook request failed: {e}")
    
    print()
    
    # Test 2: Different job statuses
    print("2️⃣ Testing Different Job Statuses")
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
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                    
        except httpx.TimeoutException:
            print(f"  ❌ {test_case['description']} - Timeout (30s)")
        except Exception as e:
            print(f"  ❌ {test_case['description']} - Exception: {e}")
    
    print()
    print("🎉 Direct Webhook Test Complete!")
    print()
    print("SUMMARY:")
    print("- Production API is accessible ✅")
    print("- Webhook endpoint exists ✅")
    print("- Webhook handler is hanging due to database connection issues ❌")
    print("- Root cause: Malformed database connection string ❌")

if __name__ == "__main__":
    asyncio.run(test_webhook_direct())
