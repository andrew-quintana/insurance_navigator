#!/usr/bin/env python3

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def test_doc_parser_environment():
    load_dotenv()
    
    print('🔍 Testing Doc-Parser Environment Access')
    print('=' * 42)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Test with a minimal request first to see the environment logging
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    print(f'🧪 Testing doc-parser environment variable access...')
    print(f'📄 Document ID: {document_id}')
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {'documentId': document_id}
    
    timeout = aiohttp.ClientTimeout(total=30)  # Shorter timeout for quick test
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Calling doc-parser: {doc_parser_url}')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'\n📊 Response Details:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Response: {response_text}')
                
                # Check headers for execution ID to view logs
                execution_id = response.headers.get('x-deno-execution-id')
                if execution_id:
                    print(f'   Execution ID: {execution_id}')
                    print(f'   💡 Check logs in Supabase Dashboard with this execution ID')
                
                # Analyze the response
                if status == 400 and "Failed to download file" in response_text:
                    print(f'\n🔍 Analysis: Still getting download error')
                    print(f'💡 This suggests one of:')
                    print(f'   1. Environment variable not accessible yet')
                    print(f'   2. Environment variable name incorrect')
                    print(f'   3. Environment variable value incorrect')
                    print(f'   4. Supabase client initialization still failing')
                    
                    print(f'\n🛠️ Next Steps:')
                    print(f'   1. Check Supabase Dashboard > Edge Functions > doc-parser > Logs')
                    print(f'   2. Look for the "Environment check" log entry')
                    print(f'   3. Verify CUSTOM_SERVICE_ROLE_KEY appears in environment check')
                    print(f'   4. If not visible, wait 10 more minutes and try again')
                    
                elif status == 200:
                    print(f'\n🎉 SUCCESS! Doc-parser is working!')
                    
                elif status == 404:
                    print(f'\n⚠️ Document not found - but environment variables are working!')
                    
                else:
                    print(f'\n⚠️ Unexpected status: {status}')
                    print(f'💡 Check function logs for details')
                
                # Additional environment variable check
                print(f'\n📋 Environment Variable Summary:')
                print(f'   Expected in function:')
                print(f'   • SUPABASE_URL: ✅ (default secret)')
                print(f'   • SUPABASE_SERVICE_ROLE_KEY: ❌ (default, wrong value)')
                print(f'   • CUSTOM_SERVICE_ROLE_KEY: ❓ (our custom secret)')
                print(f'   • LLAMAPARSE_API_KEY: ❓ (optional)')
                
                return status == 200
                
        except asyncio.TimeoutError:
            print(f'\n⚠️ Function timeout - may indicate processing is working')
            return False
            
        except Exception as e:
            print(f'\n❌ Request error: {e}')
            return False

async def check_dashboard_instructions():
    print(f'\n📋 Dashboard Check Instructions')
    print('=' * 32)
    print(f'1. Go to: https://supabase.com/dashboard/project/jhrespvvhbnloxrieycf')
    print(f'2. Navigate: Edge Functions > doc-parser > Logs')
    print(f'3. Look for recent log entries with "Environment check"')
    print(f'4. Verify you see something like:')
    print(f'   �� Environment check: {{')
    print(f'     hasUrl: true,')
    print(f'     hasCustomKey: true,  ← This should be true!')
    print(f'     hasDefaultKey: true,')
    print(f'     usingCustom: true    ← This should be true!')
    print(f'   }}')
    print(f'5. If hasCustomKey: false, the secret isn\'t set correctly')
    print(f'6. If usingCustom: false, the default key is being used')

if __name__ == "__main__":
    print('🔬 Doc-Parser Environment Debug Test')
    print('=' * 38)
    print('This test helps debug environment variable access in the Edge Function')
    print('Look for "Environment check" logs in the Supabase Dashboard\n')
    
    success = asyncio.run(test_doc_parser_environment())
    
    asyncio.run(check_dashboard_instructions())
    
    print(f'\n🏁 Test Result: {"SUCCESS" if success else "NEEDS_INVESTIGATION"}')
    
    if not success:
        print(f'\n💡 Most likely causes:')
        print(f'   1. CUSTOM_SERVICE_ROLE_KEY not set correctly in dashboard')
        print(f'   2. Environment variables haven\'t propagated (wait 10 minutes)')
        print(f'   3. Function needs manual redeploy')
        print(f'   4. Typo in environment variable name or value') 

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def test_doc_parser_environment():
    load_dotenv()
    
    print('🔍 Testing Doc-Parser Environment Access')
    print('=' * 42)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Test with a minimal request first to see the environment logging
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    print(f'🧪 Testing doc-parser environment variable access...')
    print(f'📄 Document ID: {document_id}')
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {'documentId': document_id}
    
    timeout = aiohttp.ClientTimeout(total=30)  # Shorter timeout for quick test
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Calling doc-parser: {doc_parser_url}')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'\n📊 Response Details:')
                print(f'   Status: {status} {response.reason}')
                print(f'   Response: {response_text}')
                
                # Check headers for execution ID to view logs
                execution_id = response.headers.get('x-deno-execution-id')
                if execution_id:
                    print(f'   Execution ID: {execution_id}')
                    print(f'   💡 Check logs in Supabase Dashboard with this execution ID')
                
                # Analyze the response
                if status == 400 and "Failed to download file" in response_text:
                    print(f'\n🔍 Analysis: Still getting download error')
                    print(f'💡 This suggests one of:')
                    print(f'   1. Environment variable not accessible yet')
                    print(f'   2. Environment variable name incorrect')
                    print(f'   3. Environment variable value incorrect')
                    print(f'   4. Supabase client initialization still failing')
                    
                    print(f'\n🛠️ Next Steps:')
                    print(f'   1. Check Supabase Dashboard > Edge Functions > doc-parser > Logs')
                    print(f'   2. Look for the "Environment check" log entry')
                    print(f'   3. Verify CUSTOM_SERVICE_ROLE_KEY appears in environment check')
                    print(f'   4. If not visible, wait 10 more minutes and try again')
                    
                elif status == 200:
                    print(f'\n🎉 SUCCESS! Doc-parser is working!')
                    
                elif status == 404:
                    print(f'\n⚠️ Document not found - but environment variables are working!')
                    
                else:
                    print(f'\n⚠️ Unexpected status: {status}')
                    print(f'💡 Check function logs for details')
                
                # Additional environment variable check
                print(f'\n📋 Environment Variable Summary:')
                print(f'   Expected in function:')
                print(f'   • SUPABASE_URL: ✅ (default secret)')
                print(f'   • SUPABASE_SERVICE_ROLE_KEY: ❌ (default, wrong value)')
                print(f'   • CUSTOM_SERVICE_ROLE_KEY: ❓ (our custom secret)')
                print(f'   • LLAMAPARSE_API_KEY: ❓ (optional)')
                
                return status == 200
                
        except asyncio.TimeoutError:
            print(f'\n⚠️ Function timeout - may indicate processing is working')
            return False
            
        except Exception as e:
            print(f'\n❌ Request error: {e}')
            return False

async def check_dashboard_instructions():
    print(f'\n📋 Dashboard Check Instructions')
    print('=' * 32)
    print(f'1. Go to: https://supabase.com/dashboard/project/jhrespvvhbnloxrieycf')
    print(f'2. Navigate: Edge Functions > doc-parser > Logs')
    print(f'3. Look for recent log entries with "Environment check"')
    print(f'4. Verify you see something like:')
    print(f'   �� Environment check: {{')
    print(f'     hasUrl: true,')
    print(f'     hasCustomKey: true,  ← This should be true!')
    print(f'     hasDefaultKey: true,')
    print(f'     usingCustom: true    ← This should be true!')
    print(f'   }}')
    print(f'5. If hasCustomKey: false, the secret isn\'t set correctly')
    print(f'6. If usingCustom: false, the default key is being used')

if __name__ == "__main__":
    print('🔬 Doc-Parser Environment Debug Test')
    print('=' * 38)
    print('This test helps debug environment variable access in the Edge Function')
    print('Look for "Environment check" logs in the Supabase Dashboard\n')
    
    success = asyncio.run(test_doc_parser_environment())
    
    asyncio.run(check_dashboard_instructions())
    
    print(f'\n🏁 Test Result: {"SUCCESS" if success else "NEEDS_INVESTIGATION"}')
    
    if not success:
        print(f'\n💡 Most likely causes:')
        print(f'   1. CUSTOM_SERVICE_ROLE_KEY not set correctly in dashboard')
        print(f'   2. Environment variables haven\'t propagated (wait 10 minutes)')
        print(f'   3. Function needs manual redeploy')
        print(f'   4. Typo in environment variable name or value') 