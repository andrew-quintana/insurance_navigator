#!/usr/bin/env python3
"""
CORS Test Script for Insurance Navigator API

This script helps debug CORS issues by testing various origins
against the deployed backend API to verify CORS configuration.
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any
import time

# Test URLs
BACKEND_URLS = [
    "http://localhost:8000",
    "https://insurance-navigator-api.onrender.com"
]

FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "https://insurance-navigator.vercel.app",
    "https://insurance-navigator-hrf0s88oh-andrew-quintanas-projects.vercel.app",
    "https://insurance-navigator-q2ukn6eih-andrew-quintanas-projects.vercel.app", 
    "https://insurance-navigator-cylkkqsmn-andrew-quintanas-projects.vercel.app",
    # Add more as needed
]

async def test_cors_preflight(session: aiohttp.ClientSession, backend_url: str, origin: str) -> Dict[str, Any]:
    """Test CORS preflight request (OPTIONS)."""
    try:
        print(f"🔍 Testing CORS preflight: {origin} -> {backend_url}")
        
        async with session.options(
            f"{backend_url}/upload-policy",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type"
            },
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            cors_headers = {
                "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
                "access-control-allow-methods": response.headers.get("Access-Control-Allow-Methods"),
                "access-control-allow-headers": response.headers.get("Access-Control-Allow-Headers"),
                "access-control-allow-credentials": response.headers.get("Access-Control-Allow-Credentials"),
            }
            
            return {
                "origin": origin,
                "backend_url": backend_url,
                "status": response.status,
                "cors_headers": cors_headers,
                "success": response.status in [200, 204],
                "error": None
            }
            
    except Exception as e:
        return {
            "origin": origin,
            "backend_url": backend_url,
            "status": None,
            "cors_headers": {},
            "success": False,
            "error": str(e)
        }

async def test_health_endpoint(session: aiohttp.ClientSession, backend_url: str) -> Dict[str, Any]:
    """Test backend health endpoint."""
    try:
        print(f"🏥 Testing health endpoint: {backend_url}/health")
        
        async with session.get(
            f"{backend_url}/health",
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            data = await response.json()
            return {
                "backend_url": backend_url,
                "status": response.status,
                "success": response.status == 200,
                "data": data,
                "error": None
            }
            
    except Exception as e:
        return {
            "backend_url": backend_url,
            "status": None,
            "success": False,
            "data": None,
            "error": str(e)
        }

async def main():
    """Run comprehensive CORS tests."""
    print("🧪 Starting CORS Test Suite for Insurance Navigator API")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoints first
        print("\n🏥 HEALTH CHECK TESTS")
        print("-" * 30)
        
        health_results = []
        for backend_url in BACKEND_URLS:
            result = await test_health_endpoint(session, backend_url)
            health_results.append(result)
            
            if result["success"]:
                print(f"✅ {backend_url} - Status: {result['status']}")
                if result["data"]:
                    print(f"   Database: {result['data'].get('database', 'unknown')}")
                    print(f"   Version: {result['data'].get('version', 'unknown')}")
            else:
                print(f"❌ {backend_url} - Error: {result['error']}")
        
        # Test CORS preflight requests
        print("\n🌐 CORS PREFLIGHT TESTS")
        print("-" * 30)
        
        cors_results = []
        for backend_url in BACKEND_URLS:
            if not any(r["success"] for r in health_results if r["backend_url"] == backend_url):
                print(f"⏭️  Skipping CORS tests for {backend_url} (health check failed)")
                continue
                
            print(f"\nTesting {backend_url}:")
            
            for origin in FRONTEND_ORIGINS:
                result = await test_cors_preflight(session, backend_url, origin)
                cors_results.append(result)
                
                if result["success"]:
                    allowed_origin = result["cors_headers"]["access-control-allow-origin"]
                    print(f"  ✅ {origin} -> Allowed: {allowed_origin}")
                else:
                    print(f"  ❌ {origin} -> Status: {result['status']}, Error: {result['error']}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
    
    # Summary report
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    
    # Health summary
    healthy_backends = [r for r in health_results if r["success"]]
    print(f"Healthy backends: {len(healthy_backends)}/{len(BACKEND_URLS)}")
    
    # CORS summary
    successful_cors = [r for r in cors_results if r["success"]]
    total_cors_tests = len(cors_results)
    print(f"Successful CORS tests: {len(successful_cors)}/{total_cors_tests}")
    
    # Failed CORS tests
    failed_cors = [r for r in cors_results if not r["success"]]
    if failed_cors:
        print(f"\n❌ Failed CORS Tests ({len(failed_cors)}):")
        for result in failed_cors:
            print(f"  • {result['origin']} -> {result['backend_url']}")
            if result['error']:
                print(f"    Error: {result['error']}")
            elif result['status']:
                print(f"    Status: {result['status']}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 20)
    
    if len(healthy_backends) == 0:
        print("🚨 CRITICAL: No backend services are responding!")
        print("   - Check if services are deployed and running")
        print("   - Verify network connectivity")
    
    if len(successful_cors) < len(FRONTEND_ORIGINS):
        print("⚠️  Some CORS tests failed:")
        print("   - Check CORS configuration in main.py")
        print("   - Verify Vercel deployment URLs are current")
        print("   - Consider using wildcard patterns for preview deployments")
    
    if len(successful_cors) == len(cors_results) and len(healthy_backends) > 0:
        print("✅ All tests passed! CORS configuration looks good.")
    
    print(f"\n🕒 Test completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main()) 