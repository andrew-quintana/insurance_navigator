#!/usr/bin/env python3
"""
Simple Webhook Test

This script tests webhook functionality with a minimal setup to identify issues.
"""

import asyncio
import json
import httpx
import uuid

async def test_webhook_simple():
    """Test webhook with a simple approach."""
    print("🔍 SIMPLE WEBHOOK TEST")
    print("=" * 40)
    
    # Test local webhook
    local_url = "http://localhost:8000/api/upload-pipeline/webhook/llamaparse/test-job-123"
    
    test_payload = {
        "status": "completed",
        "result": {
            "md": "# Test Document\n\nThis is a test document.",
            "txt": "Test Document\n\nThis is a test document."
        }
    }
    
    print(f"Testing URL: {local_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                local_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Webhook test successful!")
                return True
            else:
                print(f"❌ Webhook test failed with status {response.status_code}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Webhook test timed out - this suggests a database connection issue")
        return False
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False

async def test_health_endpoint():
    """Test if the API server is running."""
    print("\n🔍 HEALTH CHECK")
    print("=" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            print(f"Health Status: {response.status_code}")
            print(f"Health Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ API server is running")
                return True
            else:
                print("❌ API server health check failed")
                return False
                
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_webhook_endpoint_exists():
    """Test if the webhook endpoint exists."""
    print("\n🔍 WEBHOOK ENDPOINT CHECK")
    print("=" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test with GET to see if endpoint exists
            response = await client.get("http://localhost:8000/api/upload-pipeline/webhook/llamaparse/test-job-123")
            print(f"GET Response: {response.status_code}")
            print(f"GET Response Body: {response.text}")
            
            if response.status_code == 405:  # Method Not Allowed is expected
                print("✅ Webhook endpoint exists (GET not allowed as expected)")
                return True
            elif response.status_code == 404:
                print("❌ Webhook endpoint not found")
                return False
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                return True
                
    except Exception as e:
        print(f"❌ Endpoint check failed: {e}")
        return False

async def main():
    """Run simple webhook tests."""
    print("🚀 SIMPLE WEBHOOK TESTING")
    print("=" * 50)
    
    # Test 1: Health check
    health_ok = await test_health_endpoint()
    
    # Test 2: Endpoint exists
    endpoint_ok = await test_webhook_endpoint_exists()
    
    # Test 3: Webhook functionality
    webhook_ok = await test_webhook_simple()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"Endpoint Exists: {'✅' if endpoint_ok else '❌'}")
    print(f"Webhook Functionality: {'✅' if webhook_ok else '❌'}")
    
    if not health_ok:
        print("\n🔧 ISSUE: API server is not running")
        print("   Solution: Start the server with: uvicorn main:app --reload")
    
    if not endpoint_ok:
        print("\n🔧 ISSUE: Webhook endpoint not found")
        print("   Solution: Check if webhook router is properly included in main.py")
    
    if not webhook_ok:
        print("\n🔧 ISSUE: Webhook processing failed")
        print("   Solution: Check database connection and webhook handler logic")

if __name__ == "__main__":
    asyncio.run(main())
