#!/usr/bin/env python3
"""
Comprehensive Webhook Testing Script

This script tests webhook functionality against both local and production environments
to validate webhook configuration and identify issues.
"""

import asyncio
import json
import httpx
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Environment configurations
ENVIRONMENTS = {
    "local": {
        "api_url": "http://localhost:8000",
        "health_endpoint": "/health",
        "webhook_endpoint": "/api/upload-pipeline/webhook/llamaparse"
    },
    "production": {
        "api_url": "***REMOVED***",
        "health_endpoint": "/health",
        "webhook_endpoint": "/api/upload-pipeline/webhook/llamaparse"
    }
}

async def test_environment_connectivity(env_name: str, config: Dict[str, str]) -> bool:
    """Test basic connectivity to an environment."""
    print(f"🔍 Testing {env_name.upper()} Environment Connectivity")
    print("-" * 50)
    print(f"API URL: {config['api_url']}")
    
    # Test 1: Basic connectivity
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config['api_url']}/")
            print(f"Root endpoint status: {response.status_code}")
            if response.status_code != 404:
                print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test 2: Health check
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config['api_url']}{config['health_endpoint']}")
            print(f"Health check status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_webhook_endpoint(env_name: str, config: Dict[str, str]) -> bool:
    """Test webhook endpoint functionality."""
    print(f"\n🔍 Testing {env_name.upper()} Webhook Endpoint")
    print("-" * 50)
    
    webhook_url = f"{config['api_url']}{config['webhook_endpoint']}/test-job-{uuid.uuid4().hex[:8]}"
    print(f"Webhook URL: {webhook_url}")
    
    test_payload = {
        "status": "completed",
        "result": {
            "md": "# Test Document\n\nThis is a test document for webhook testing.",
            "txt": "Test Document\n\nThis is a test document for webhook testing."
        },
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "environment": env_name
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
                return True
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

async def test_webhook_error_handling(env_name: str, config: Dict[str, str]) -> None:
    """Test webhook error handling."""
    print(f"\n🔍 Testing {env_name.upper()} Webhook Error Handling")
    print("-" * 50)
    
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
        }
    ]
    
    for test_case in error_test_cases:
        print(f"Testing: {test_case['name']}")
        test_job_id = f"error-test-{uuid.uuid4().hex[:8]}"
        webhook_url = f"{config['api_url']}{config['webhook_endpoint']}/{test_job_id}"
        
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

async def test_llamaparse_integration(env_name: str, config: Dict[str, str]) -> bool:
    """Test LlamaParse webhook integration specifically."""
    print(f"\n🔍 Testing {env_name.upper()} LlamaParse Integration")
    print("-" * 50)
    
    # Test with realistic LlamaParse webhook payload
    llamaparse_payload = {
        "status": "completed",
        "result": {
            "md": "# Insurance Policy Document\n\n## Policy Details\n\n**Policy Number:** 12345\n**Coverage Type:** Health Insurance\n**Premium:** $500/month\n\n## Coverage Information\n\nThis policy covers:\n- Hospital stays\n- Doctor visits\n- Prescription drugs\n- Emergency services",
            "txt": "Insurance Policy Document\n\nPolicy Details\n\nPolicy Number: 12345\nCoverage Type: Health Insurance\nPremium: $500/month\n\nCoverage Information\n\nThis policy covers:\n- Hospital stays\n- Doctor visits\n- Prescription drugs\n- Emergency services"
        },
        "metadata": {
            "source": "llamaparse",
            "document_type": "insurance_policy",
            "processing_time": 2.5,
            "confidence": 0.95
        }
    }
    
    test_job_id = f"llamaparse-test-{uuid.uuid4().hex[:8]}"
    webhook_url = f"{config['api_url']}{config['webhook_endpoint']}/{test_job_id}"
    
    print(f"Test Job ID: {test_job_id}")
    print(f"Webhook URL: {webhook_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Sending LlamaParse webhook request...")
            response = await client.post(
                webhook_url,
                json=llamaparse_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ LlamaParse webhook integration successful")
                try:
                    response_data = response.json()
                    print(f"Response Data: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"Response Text: {response.text}")
                return True
            else:
                print(f"❌ LlamaParse webhook integration failed: {response.status_code}")
                print(f"Error Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ LlamaParse webhook request timed out (30s)")
        return False
    except Exception as e:
        print(f"❌ LlamaParse webhook integration failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Comprehensive Webhook Tests")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = {}
    
    for env_name, config in ENVIRONMENTS.items():
        print(f"\n{'='*60}")
        print(f"TESTING {env_name.upper()} ENVIRONMENT")
        print(f"{'='*60}")
        
        # Test connectivity
        connectivity_ok = await test_environment_connectivity(env_name, config)
        results[env_name] = {"connectivity": connectivity_ok}
        
        if connectivity_ok:
            # Test webhook functionality
            webhook_ok = await test_webhook_endpoint(env_name, config)
            results[env_name]["webhook"] = webhook_ok
            
            # Test error handling
            await test_webhook_error_handling(env_name, config)
            
            # Test LlamaParse integration
            llamaparse_ok = await test_llamaparse_integration(env_name, config)
            results[env_name]["llamaparse"] = llamaparse_ok
        else:
            results[env_name]["webhook"] = False
            results[env_name]["llamaparse"] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for env_name, result in results.items():
        print(f"\n{env_name.upper()}:")
        print(f"  Connectivity: {'✅' if result['connectivity'] else '❌'}")
        print(f"  Webhook: {'✅' if result['webhook'] else '❌'}")
        print(f"  LlamaParse: {'✅' if result['llamaparse'] else '❌'}")
    
    print(f"\n🏁 All tests completed!")
    
    # Recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if not results["production"]["connectivity"]:
        print("❌ Production API is not accessible - check deployment status")
        print("   - Verify the service is running on Render")
        print("   - Check for deployment failures")
        print("   - Verify environment variables are set correctly")
    
    if results["local"]["connectivity"] and not results["production"]["connectivity"]:
        print("✅ Local environment is working - use for development and testing")
        print("   - Test webhook functionality locally first")
        print("   - Fix any issues before deploying to production")
    
    if results["production"]["connectivity"] and not results["production"]["webhook"]:
        print("❌ Production webhook is not working - check webhook handler")
        print("   - Verify database connection in production")
        print("   - Check webhook endpoint registration")
        print("   - Review production logs for errors")

if __name__ == "__main__":
    asyncio.run(main())
