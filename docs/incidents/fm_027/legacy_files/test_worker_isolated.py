#!/usr/bin/env python3
"""
Isolated Worker Testing for FM-027

This script tests the worker's file download and LlamaParse processing
in isolation to identify what's going wrong.
"""

import os
import httpx
import asyncio
import json
from dotenv import load_dotenv
from datetime import datetime

# Load staging environment
load_dotenv('.env.staging')

async def test_worker_isolated():
    """Test worker behavior in isolation"""
    
    storage_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    llamaparse_api_key = os.getenv('LLAMAPARSE_API_KEY')
    
    print(f"🧪 Isolated Worker Testing")
    print(f"📅 Test time: {datetime.now().isoformat()}")
    print(f"🌐 Storage URL: {storage_url}")
    print(f"🔑 Service role key: {service_role_key[:20]}...{service_role_key[-20:]}")
    print(f"🤖 LlamaParse API key: {'✅ Present' if llamaparse_api_key else '❌ Missing'}")
    
    # Test 1: Create a test file and immediately try to process it
    print(f"\n📤 Test 1: Upload and immediate processing")
    
    test_file_path = 'test/worker_test_immediate.pdf'
    test_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Worker Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF'
    
    headers = {
        'apikey': service_role_key,
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/pdf'
    }
    
    async with httpx.AsyncClient() as client:
        # Upload test file
        print(f"📤 Uploading test file...")
        response = await client.post(
            f'{storage_url}/storage/v1/object/files/{test_file_path}',
            content=test_content,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ File uploaded successfully")
            
            # Wait a moment for storage to be consistent
            print(f"⏳ Waiting for storage consistency...")
            await asyncio.sleep(2)
            
            # Test immediate download (like worker does)
            print(f"🔍 Testing immediate download...")
            worker_headers = {
                'apikey': service_role_key,
                'Authorization': f'Bearer {service_role_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'Insurance-Navigator/1.0'
            }
            
            response = await client.get(
                f'{storage_url}/storage/v1/object/files/{test_file_path}',
                headers=worker_headers
            )
            
            if response.status_code == 200:
                print(f"✅ File download successful! Size: {len(response.content)} bytes")
                
                # Test LlamaParse call
                if llamaparse_api_key:
                    print(f"🤖 Testing LlamaParse call...")
                    await test_llamaparse_call(client, test_content, worker_headers)
                else:
                    print(f"⚠️  LlamaParse API key not available, skipping LlamaParse test")
                
            else:
                print(f"❌ File download failed: {response.status_code} - {response.text}")
        else:
            print(f"❌ File upload failed: {response.status_code} - {response.text}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up test file...")
        response = await client.delete(
            f'{storage_url}/storage/v1/object/files/{test_file_path}',
            headers=headers
        )
        if response.status_code in [200, 204]:
            print(f"✅ Test file cleaned up")
        else:
            print(f"⚠️  Cleanup failed: {response.status_code}")

async def test_llamaparse_call(client, file_content, headers):
    """Test LlamaParse API call exactly like the worker does"""
    
    llamaparse_api_key = os.getenv('LLAMAPARSE_API_KEY')
    llamaparse_base_url = "https://api.cloud.llamaindex.ai"
    
    print(f"🤖 Testing LlamaParse API call...")
    
    try:
        # Prepare multipart form data exactly like worker
        files = {
            'file': ('test.pdf', file_content, 'application/pdf')
        }
        
        llamaparse_headers = {
            'Authorization': f'Bearer {llamaparse_api_key}'
        }
        
        # Prepare form data exactly like the worker
        form_data = {
            'parsingInstructions': 'Extract the complete text content from this PDF document exactly as it appears. Do not summarize, analyze, or modify the content. Return the raw text with all details, numbers, and specific information preserved.',
            'result_type': 'markdown',
            'webhook_url': 'https://webhook.site/unique-id'  # Public test webhook URL
        }
        
        # Make the API call with the correct endpoint
        response = await client.post(
            f'{llamaparse_base_url}/api/parsing/upload',
            files=files,
            data=form_data,
            headers=llamaparse_headers,
            timeout=300
        )
        
        print(f"🤖 LlamaParse response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ LlamaParse successful! Result keys: {list(result.keys())}")
            if 'text' in result:
                print(f"📄 Text preview: {result['text'][:100]}...")
        else:
            print(f"❌ LlamaParse failed: {response.text}")
            
    except Exception as e:
        print(f"❌ LlamaParse error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_worker_isolated())
