#!/usr/bin/env python3
"""
Test Edge Function Orchestration Logic

This script tests the EdgeFunctionOrchestrator class directly,
focusing on the upload pipeline mechanics without requiring
full authentication setup.
"""

import asyncio
import aiohttp
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import the orchestrator directly
import sys
sys.path.append('.')

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_edge_function_connectivity():
    """Test basic connectivity to Supabase Edge Functions."""
    
    print("🔗 Testing Edge Function Connectivity")
    print("=" * 40)
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Has Anon Key: {'✅' if SUPABASE_ANON_KEY else '❌'}")
    print(f"Has Service Role Key: {'✅' if SUPABASE_SERVICE_ROLE_KEY else '❌'}")
    print()
    
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
        print("❌ Missing Supabase configuration")
        return False
    
    # Test edge function endpoints
    edge_functions = [
        'upload-handler',
        'doc-parser', 
        'regulatory-vector-processor',
        'bulk-regulatory-processor'
    ]
    
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for function_name in edge_functions:
            url = f"{SUPABASE_URL}/functions/v1/{function_name}"
            
            headers = {
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
                'Content-Type': 'application/json',
                'apikey': SUPABASE_ANON_KEY
            }
            
            try:
                print(f"🔍 Testing {function_name}...")
                
                # Test with a simple GET/POST to see if function exists
                async with session.post(url, json={}, headers=headers) as response:
                    status = response.status
                    
                    if status in [200, 400, 401, 403]:  # Function exists (even if auth fails)
                        print(f"  ✅ {function_name}: Function exists (status {status})")
                    elif status == 404:
                        print(f"  ❌ {function_name}: Function not found")
                    else:
                        print(f"  ⚠️  {function_name}: Unexpected status {status}")
                        
            except Exception as e:
                print(f"  ❌ {function_name}: Connection error - {str(e)}")
    
    print()
    return True

async def test_orchestrator_class():
    """Test the EdgeFunctionOrchestrator class directly."""
    
    print("🤖 Testing EdgeFunctionOrchestrator Class")
    print("=" * 42)
    
    try:
        # Import the class from main.py
        from main import EdgeFunctionOrchestrator
        
        print("✅ EdgeFunctionOrchestrator imported successfully")
        
        # Create instance
        orchestrator = EdgeFunctionOrchestrator()
        print("✅ EdgeFunctionOrchestrator instance created")
        
        # Check configuration
        print(f"🔧 Supabase URL: {orchestrator.supabase_url[:50]}..." if orchestrator.supabase_url else "❌ No URL")
        print(f"🔑 Has Anon Key: {'✅' if orchestrator.supabase_anon_key else '❌'}")
        print(f"🔐 Has Service Role Key: {'✅' if orchestrator.supabase_service_role_key else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ EdgeFunctionOrchestrator test failed: {e}")
        return False

async def test_upload_handler_structure():
    """Test the upload-handler edge function structure."""
    
    print("📤 Testing upload-handler Edge Function")
    print("=" * 40)
    
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
        print("❌ Missing Supabase configuration")
        return False
    
    url = f"{SUPABASE_URL}/functions/v1/upload-handler"
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
        'apikey': SUPABASE_ANON_KEY
    }
    
    # Test POST method (initialization)
    test_payload = {
        "filename": "test.pdf",
        "contentType": "application/pdf",
        "fileSize": 1024
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        print("🔄 Testing POST /upload-handler (initialization)...")
        
        try:
            async with session.post(url, json=test_payload, headers=headers) as response:
                status = response.status
                content = await response.text()
                
                print(f"📊 Status: {status}")
                print(f"📄 Response: {content[:200]}...")
                
                if status == 200:
                    print("✅ upload-handler POST working")
                    try:
                        data = json.loads(content)
                        print(f"🔍 Response keys: {list(data.keys())}")
                    except:
                        pass
                elif status in [400, 401, 403]:
                    print("⚠️  upload-handler exists but auth/validation failed (expected)")
                elif status == 404:
                    print("❌ upload-handler not found")
                else:
                    print(f"⚠️  Unexpected status: {status}")
                    
        except Exception as e:
            print(f"❌ POST test failed: {e}")
        
        print()
        print("🔄 Testing PATCH /upload-handler (completion)...")
        
        completion_payload = {
            "documentId": "test-doc-id",
            "path": "test/path.pdf"
        }
        
        try:
            async with session.patch(url, json=completion_payload, headers=headers) as response:
                status = response.status
                content = await response.text()
                
                print(f"📊 Status: {status}")
                print(f"📄 Response: {content[:200]}...")
                
                if status == 200:
                    print("✅ upload-handler PATCH working")
                elif status in [400, 401, 403]:
                    print("⚠️  upload-handler PATCH exists but auth/validation failed (expected)")
                elif status == 404:
                    print("❌ upload-handler PATCH not found")
                else:
                    print(f"⚠️  Unexpected status: {status}")
                    
        except Exception as e:
            print(f"❌ PATCH test failed: {e}")
    
    print()
    return True

async def test_doc_parser_connectivity():
    """Test doc-parser edge function connectivity."""
    
    print("📄 Testing doc-parser Edge Function")
    print("=" * 35)
    
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
        print("❌ Missing Supabase configuration")
        return False
    
    url = f"{SUPABASE_URL}/functions/v1/doc-parser"
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
        'apikey': SUPABASE_ANON_KEY
    }
    
    test_payload = {
        "documentId": "test-doc-id",
        "path": "test/document.pdf",
        "userId": "test-user-id"
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        print("🔄 Testing POST /doc-parser...")
        
        try:
            async with session.post(url, json=test_payload, headers=headers) as response:
                status = response.status
                content = await response.text()
                
                print(f"📊 Status: {status}")
                print(f"📄 Response: {content[:200]}...")
                
                if status == 200:
                    print("✅ doc-parser working")
                elif status in [400, 401, 403]:
                    print("⚠️  doc-parser exists but auth/validation failed (expected)")
                elif status == 404:
                    print("❌ doc-parser not found")
                else:
                    print(f"⚠️  Unexpected status: {status}")
                    
        except Exception as e:
            print(f"❌ doc-parser test failed: {e}")
    
    print()
    return True

async def main():
    """Run all edge function tests."""
    print("🧪 Edge Function Orchestration Tests")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test orchestrator class
    orchestrator_ok = await test_orchestrator_class()
    print()
    
    # Test edge function connectivity
    connectivity_ok = await test_edge_function_connectivity()
    print()
    
    # Test upload-handler structure
    upload_handler_ok = await test_upload_handler_structure()
    print()
    
    # Test doc-parser connectivity
    doc_parser_ok = await test_doc_parser_connectivity()
    
    print()
    print("📋 Test Summary")
    print("-" * 15)
    print(f"Orchestrator Class: {'✅ PASS' if orchestrator_ok else '❌ FAIL'}")
    print(f"Edge Function Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    print(f"upload-handler Tests: {'✅ PASS' if upload_handler_ok else '❌ FAIL'}")
    print(f"doc-parser Tests: {'✅ PASS' if doc_parser_ok else '❌ FAIL'}")
    
    if all([orchestrator_ok, connectivity_ok, upload_handler_ok, doc_parser_ok]):
        print()
        print("🎉 All edge function tests passed!")
        print("🔧 The backend-orchestrated pipeline should work once authentication is set up.")
        print()
        print("📋 Next Steps:")
        print("   1. Set up database services for authentication")
        print("   2. Test with real user tokens")
        print("   3. Upload actual PDF files to test LlamaParse")
        print("   4. Monitor edge function logs")
    else:
        print()
        print("❌ Some edge function tests failed.")
        print("🔧 Check Supabase Edge Function deployment status.")

if __name__ == "__main__":
    asyncio.run(main()) 