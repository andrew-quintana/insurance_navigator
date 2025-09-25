#!/usr/bin/env python3
"""
LlamaParse Endpoint Discovery
Discover the correct LlamaParse API endpoints for document parsing
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv('.env.production')

API_CONFIG = {
    "LLAMAPARSE_API_KEY": os.getenv("LLAMAPARSE_API_KEY"),
    "LLAMAPARSE_BASE_URL": "https://api.cloud.llamaindex.ai",
}

async def discover_llamaparse_endpoints():
    """Discover LlamaParse API endpoints by testing various patterns"""
    print("🔍 Discovering LlamaParse API endpoints...")
    
    headers = {
        "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    # Test various endpoint patterns
    test_patterns = [
        # Standard REST patterns
        "/api/v1/parse",
        "/api/v1/parsing",
        "/api/v1/documents",
        "/api/v1/files",
        "/api/upload-pipeline/upload",
        "/api/v1/jobs",
        
        # Alternative patterns
        "/v1/parse",
        "/v1/parsing", 
        "/v1/documents",
        "/v1/files",
        "/v1/upload",
        "/v1/jobs",
        
        # Root level patterns
        "/parse",
        "/parsing",
        "/documents",
        "/files",
        "/upload",
        "/jobs",
        
        # LlamaParse specific patterns
        "/llamaparse/v1/parse",
        "/llamaparse/v1/parsing",
        "/llamaparse/parse",
        "/llamaparse/parsing",
        
        # Cloud patterns
        "/cloud/v1/parse",
        "/cloud/v1/parsing",
        "/cloud/parse",
        "/cloud/parsing",
    ]
    
    results = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for pattern in test_patterns:
            url = f"{API_CONFIG['LLAMAPARSE_BASE_URL']}{pattern}"
            
            # Test GET request
            try:
                response = await client.get(url, headers=headers)
                results[pattern] = {
                    "url": url,
                    "method": "GET",
                    "status_code": response.status_code,
                    "exists": response.status_code not in [404, 405],
                    "response_preview": response.text[:200] if response.text else None
                }
                print(f"GET {pattern}: {response.status_code}")
            except Exception as e:
                results[pattern] = {
                    "url": url,
                    "method": "GET",
                    "status_code": "ERROR",
                    "exists": False,
                    "response_preview": str(e)
                }
                print(f"GET {pattern}: ERROR - {e}")
            
            # Test POST request
            try:
                response = await client.post(url, headers=headers, json={})
                results[f"{pattern}_POST"] = {
                    "url": url,
                    "method": "POST",
                    "status_code": response.status_code,
                    "exists": response.status_code not in [404, 405],
                    "response_preview": response.text[:200] if response.text else None
                }
                print(f"POST {pattern}: {response.status_code}")
            except Exception as e:
                results[f"{pattern}_POST"] = {
                    "url": url,
                    "method": "POST",
                    "status_code": "ERROR",
                    "exists": False,
                    "response_preview": str(e)
                }
                print(f"POST {pattern}: ERROR - {e}")
    
    # Save results
    results_file = f"llamaparse_endpoint_discovery_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    
    # Find working endpoints
    working_endpoints = {k: v for k, v in results.items() if v['exists']}
    print(f"\n✅ Working endpoints found: {len(working_endpoints)}")
    
    for endpoint, data in working_endpoints.items():
        print(f"  {endpoint}: {data['status_code']} - {data['url']}")
    
    return results, working_endpoints

async def test_document_parsing():
    """Test document parsing with discovered endpoints"""
    print("\n🧪 Testing document parsing with discovered endpoints...")
    
    # Read test document
    with open("test_document.pdf", "rb") as f:
        file_data = f.read()
    
    headers = {
        "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
    }
    
    # Test file upload patterns
    test_endpoints = [
        "/api/v1/parse",
        "/v1/parse", 
        "/parse",
        "/api/upload-pipeline/upload",
        "/v1/upload",
        "/upload"
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for endpoint in test_endpoints:
            url = f"{API_CONFIG['LLAMAPARSE_BASE_URL']}{endpoint}"
            
            try:
                # Test with file upload
                files = {"file": ("test_document.pdf", file_data, "application/pdf")}
                data = {"language": "en"}
                
                response = await client.post(url, headers=headers, files=files, data=data)
                
                print(f"POST {endpoint}: {response.status_code}")
                if response.status_code not in [404, 405]:
                    print(f"  Response: {response.text[:200]}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  Success! Job ID: {result.get('id', 'N/A')}")
                        return endpoint, result
                        
            except Exception as e:
                print(f"POST {endpoint}: ERROR - {e}")
    
    return None, None

async def main():
    """Main discovery process"""
    print("🚀 Starting LlamaParse Endpoint Discovery")
    print(f"🔑 API Key: {API_CONFIG['LLAMAPARSE_API_KEY'][:20]}...")
    print(f"🌐 Base URL: {API_CONFIG['LLAMAPARSE_BASE_URL']}")
    
    # Discover endpoints
    results, working_endpoints = await discover_llamaparse_endpoints()
    
    # Test document parsing
    if working_endpoints:
        endpoint, result = await test_document_parsing()
        if endpoint:
            print(f"\n✅ Document parsing successful with endpoint: {endpoint}")
        else:
            print(f"\n❌ Document parsing failed with all endpoints")
    else:
        print(f"\n❌ No working endpoints found")

if __name__ == "__main__":
    asyncio.run(main())
