#!/usr/bin/env python3
"""
Webhook Diagnosis and Testing Script

This script tests webhook functionality locally and diagnoses common issues:
1. Webhook URL configuration
2. Webhook endpoint accessibility
3. Silent errors in webhook processing
4. LlamaParse integration issues
"""

import asyncio
import json
import os
import sys
import httpx
import uuid
from typing import Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_webhook_url_configuration():
    """Test webhook URL configuration and environment variables."""
    print("🔍 TESTING WEBHOOK URL CONFIGURATION")
    print("=" * 50)
    
    # Check environment variables
    environment = os.getenv("ENVIRONMENT", "development")
    webhook_base_url = os.getenv("WEBHOOK_BASE_URL")
    api_base_url = os.getenv("API_BASE_URL")
    
    print(f"Environment: {environment}")
    print(f"WEBHOOK_BASE_URL: {webhook_base_url}")
    print(f"API_BASE_URL: {api_base_url}")
    
    # Determine expected webhook URL
    if webhook_base_url:
        base_url = webhook_base_url
        print(f"✅ Using explicit WEBHOOK_BASE_URL: {base_url}")
    elif environment == "development":
        base_url = "http://localhost:8000"
        print(f"✅ Using development localhost: {base_url}")
    else:
        base_url = "https://insurance-navigator-api.onrender.com"
        print(f"✅ Using production default: {base_url}")
    
    webhook_url = f"{base_url}/api/upload-pipeline/webhook/llamaparse/test-job-123"
    print(f"Expected webhook URL: {webhook_url}")
    
    return webhook_url

async def test_webhook_endpoint_accessibility(webhook_url: str):
    """Test if webhook endpoint is accessible."""
    print("\n🔍 TESTING WEBHOOK ENDPOINT ACCESSIBILITY")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test with a simple GET request first
            print(f"Testing GET request to: {webhook_url}")
            response = await client.get(webhook_url)
            print(f"GET Response: {response.status_code} - {response.text[:200]}")
            
            # Test with POST request (actual webhook call)
            print(f"\nTesting POST request to: {webhook_url}")
            test_payload = {
                "status": "completed",
                "result": {
                    "md": "# Test Document\n\nThis is a test document for webhook testing.",
                    "txt": "Test Document\n\nThis is a test document for webhook testing."
                }
            }
            
            response = await client.post(
                webhook_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"POST Response: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text[:500]}")
            
            if response.status_code == 200:
                print("✅ Webhook endpoint is accessible and responding")
                return True
            else:
                print(f"❌ Webhook endpoint returned error: {response.status_code}")
                return False
                
    except httpx.ConnectError as e:
        print(f"❌ Connection error: {e}")
        print("   This usually means the server is not running or the URL is wrong")
        return False
    except httpx.TimeoutException as e:
        print(f"❌ Timeout error: {e}")
        print("   The server might be slow to respond")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_webhook_with_database():
    """Test webhook with actual database interaction."""
    print("\n🔍 TESTING WEBHOOK WITH DATABASE")
    print("=" * 50)
    
    try:
        # Import webhook handler
        from api.upload_pipeline.webhooks import llamaparse_webhook
        from fastapi import Request
        from unittest.mock import Mock
        
        # Create a mock request
        job_id = f"test-job-{uuid.uuid4().hex[:8]}"
        test_payload = {
            "status": "completed",
            "result": {
                "md": "# Test Document\n\nThis is a test document for webhook testing.",
                "txt": "Test Document\n\nThis is a test document for webhook testing."
            }
        }
        
        # Mock request object
        mock_request = Mock()
        mock_request.body = asyncio.coroutine(lambda: json.dumps(test_payload).encode())()
        mock_request.json = asyncio.coroutine(lambda: test_payload)()
        mock_request.headers = {"Content-Type": "application/json"}
        
        print(f"Testing webhook handler with job_id: {job_id}")
        print(f"Test payload: {json.dumps(test_payload, indent=2)}")
        
        # This will fail because we don't have a real job in the database
        # but it will show us where the error occurs
        try:
            result = await llamaparse_webhook(job_id, mock_request)
            print(f"✅ Webhook handler executed successfully: {result}")
            return True
        except Exception as e:
            print(f"❌ Webhook handler failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            print(f"   This is expected for a test job that doesn't exist in the database")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This suggests there might be missing dependencies")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_llamaparse_integration():
    """Test LlamaParse integration and webhook callback simulation."""
    print("\n🔍 TESTING LLAMAPARSE INTEGRATION")
    print("=" * 50)
    
    try:
        # Check if we can import LlamaParse client
        from backend.shared.external.llamaparse_real import LlamaParseRealClient
        
        print("✅ LlamaParse client imported successfully")
        
        # Check environment variables
        llamaparse_api_key = os.getenv("LLAMAPARSE_API_KEY")
        if not llamaparse_api_key:
            print("❌ LLAMAPARSE_API_KEY not found in environment")
            return False
        
        print("✅ LLAMAPARSE_API_KEY found")
        
        # Test webhook URL construction
        webhook_url = await test_webhook_url_configuration()
        
        # Create a test client
        client = LlamaParseRealClient(api_key=llamaparse_api_key)
        
        print(f"✅ LlamaParse client created successfully")
        print(f"   API Key: {llamaparse_api_key[:8]}...")
        print(f"   Webhook URL: {webhook_url}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_webhook_silent_errors():
    """Test for silent errors in webhook processing."""
    print("\n🔍 TESTING FOR SILENT ERRORS")
    print("=" * 50)
    
    # Test common silent error scenarios
    test_cases = [
        {
            "name": "Empty payload",
            "payload": {},
            "expected_error": True
        },
        {
            "name": "Missing result field",
            "payload": {"status": "completed"},
            "expected_error": True
        },
        {
            "name": "Empty result field",
            "payload": {"status": "completed", "result": {}},
            "expected_error": True
        },
        {
            "name": "Valid payload",
            "payload": {
                "status": "completed",
                "result": {
                    "md": "# Test Document\n\nContent here.",
                    "txt": "Test Document\n\nContent here."
                }
            },
            "expected_error": False
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Payload: {json.dumps(test_case['payload'], indent=2)}")
        
        try:
            # Simulate webhook processing logic
            result = test_case['payload'].get("result", {})
            if isinstance(result, dict):
                parsed_content = (
                    result.get("md", "") or
                    result.get("txt", "") or
                    result.get("parsed_content", "")
                )
            else:
                parsed_content = ""
            
            if not parsed_content:
                print(f"   ❌ No parsed content found (expected: {test_case['expected_error']})")
            else:
                print(f"   ✅ Parsed content found: {len(parsed_content)} chars")
                
        except Exception as e:
            print(f"   ❌ Error processing payload: {e}")

async def test_production_webhook_url():
    """Test the actual production webhook URL."""
    print("\n🔍 TESTING PRODUCTION WEBHOOK URL")
    print("=" * 50)
    
    production_url = "https://insurance-navigator-api.onrender.com/api/upload-pipeline/webhook/llamaparse/test-job-123"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"Testing production URL: {production_url}")
            
            # Test with a simple GET request
            response = await client.get(production_url)
            print(f"GET Response: {response.status_code}")
            
            if response.status_code == 405:  # Method Not Allowed is expected for GET
                print("✅ Production webhook endpoint is accessible (GET not allowed as expected)")
            elif response.status_code == 200:
                print("✅ Production webhook endpoint is accessible")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
            
            # Test with POST request
            test_payload = {
                "status": "completed",
                "result": {
                    "md": "# Test Document\n\nThis is a test document for webhook testing.",
                    "txt": "Test Document\n\nThis is a test document for webhook testing."
                }
            }
            
            response = await client.post(
                production_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"POST Response: {response.status_code}")
            print(f"Response Body: {response.text[:200]}")
            
            if response.status_code in [200, 404]:  # 404 is expected for non-existent job
                print("✅ Production webhook endpoint is working")
                return True
            else:
                print(f"❌ Production webhook endpoint error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Production webhook test failed: {e}")
        return False

async def main():
    """Run all webhook diagnostic tests."""
    print("🚀 WEBHOOK DIAGNOSTIC TESTING")
    print("=" * 60)
    
    # Test 1: Webhook URL configuration
    webhook_url = await test_webhook_url_configuration()
    
    # Test 2: Local webhook endpoint accessibility
    local_accessible = await test_webhook_endpoint_accessibility(webhook_url)
    
    # Test 3: Webhook with database
    db_working = await test_webhook_with_database()
    
    # Test 4: LlamaParse integration
    llamaparse_working = await test_llamaparse_integration()
    
    # Test 5: Silent errors
    await test_webhook_silent_errors()
    
    # Test 6: Production webhook URL
    production_working = await test_production_webhook_url()
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"Webhook URL Configuration: ✅")
    print(f"Local Endpoint Accessible: {'✅' if local_accessible else '❌'}")
    print(f"Database Integration: {'✅' if db_working else '❌'}")
    print(f"LlamaParse Integration: {'✅' if llamaparse_working else '❌'}")
    print(f"Production Endpoint: {'✅' if production_working else '❌'}")
    
    if not local_accessible:
        print("\n🔧 RECOMMENDATIONS:")
        print("1. Start the local API server: uvicorn main:app --reload")
        print("2. Check if the webhook endpoint is properly registered")
        print("3. Verify the webhook URL construction logic")
    
    if not production_working:
        print("\n🔧 PRODUCTION ISSUES:")
        print("1. Check if the production server is running")
        print("2. Verify the webhook URL is correct")
        print("3. Check production logs for errors")
        print("4. Verify environment variables are set correctly")

if __name__ == "__main__":
    asyncio.run(main())
