#!/usr/bin/env python3

import asyncio
import os
import subprocess
import json
from dotenv import load_dotenv

def fix_doc_parser_environment():
    load_dotenv()
    
    print('🔧 Fixing Doc-Parser Environment Variables')
    print('=' * 45)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    llamaparse_key = os.getenv('LLAMAPARSE_API_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables in local .env file")
        print("Please ensure your .env file contains:")
        print("   SUPABASE_URL=...")
        print("   SUPABASE_SERVICE_ROLE_KEY=...")
        return False
    
    print(f'✅ Local environment variables found')
    print(f'   SUPABASE_URL: {supabase_url}')
    print(f'   SUPABASE_SERVICE_ROLE_KEY: {service_role_key[:20]}...')
    print(f'   LLAMAPARSE_API_KEY: {"✅ Set" if llamaparse_key else "❌ Missing"}')
    
    # Step 1: Check if Supabase CLI is installed
    print(f'\n1️⃣ Checking Supabase CLI')
    print('-' * 24)
    
    try:
        result = subprocess.run(['supabase', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f'✅ Supabase CLI installed: {result.stdout.strip()}')
        else:
            print(f'❌ Supabase CLI not working properly')
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f'❌ Supabase CLI not installed or not in PATH')
        print(f'💡 Install with: npm install -g supabase')
        return False
    
    # Step 2: Check project status
    print(f'\n2️⃣ Checking Project Status')
    print('-' * 26)
    
    try:
        result = subprocess.run(['supabase', 'status'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f'✅ Supabase project status:')
            print(f'{result.stdout}')
        else:
            print(f'⚠️ Project not linked or not logged in')
            print(f'💡 Run: supabase login')
            print(f'💡 Then: supabase link --project-ref YOUR_PROJECT_REF')
    except subprocess.TimeoutExpired:
        print(f'⚠️ Status check timed out')
    
    # Step 3: Check current secrets
    print(f'\n3️⃣ Checking Current Edge Function Secrets')
    print('-' * 42)
    
    try:
        result = subprocess.run(['supabase', 'secrets', 'list'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f'✅ Current secrets:')
            print(f'{result.stdout}')
        else:
            print(f'❌ Failed to list secrets: {result.stderr}')
    except subprocess.TimeoutExpired:
        print(f'⚠️ Secrets list timed out')
    
    # Step 4: Set required environment variables
    print(f'\n4️⃣ Setting Required Environment Variables')
    print('-' * 41)
    
    # Create secrets to set
    secrets_to_set = {
        'SUPABASE_URL': supabase_url,
        'SUPABASE_SERVICE_ROLE_KEY': service_role_key
    }
    
    if llamaparse_key:
        secrets_to_set['LLAMAPARSE_API_KEY'] = llamaparse_key
    
    print(f'📝 Setting {len(secrets_to_set)} environment variables...')
    
    success_count = 0
    for secret_name, secret_value in secrets_to_set.items():
        try:
            print(f'   Setting {secret_name}...')
            result = subprocess.run([
                'supabase', 'secrets', 'set', 
                f'{secret_name}={secret_value}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f'   ✅ {secret_name} set successfully')
                success_count += 1
            else:
                print(f'   ❌ Failed to set {secret_name}: {result.stderr}')
                
        except subprocess.TimeoutExpired:
            print(f'   ⚠️ Timeout setting {secret_name}')
    
    if success_count == len(secrets_to_set):
        print(f'\n✅ All environment variables set successfully!')
    else:
        print(f'\n⚠️ Only {success_count}/{len(secrets_to_set)} variables set')
    
    # Step 5: Redeploy doc-parser function
    print(f'\n5️⃣ Redeploying Doc-Parser Function')
    print('-' * 35)
    
    doc_parser_path = 'db/supabase/functions/doc-parser'
    if os.path.exists(doc_parser_path):
        print(f'📁 Found doc-parser at: {doc_parser_path}')
        
        try:
            print(f'🚀 Deploying doc-parser...')
            result = subprocess.run([
                'supabase', 'functions', 'deploy', 'doc-parser',
                '--project-ref', supabase_url.split('//')[1].split('.')[0]
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f'✅ Doc-parser deployed successfully!')
                print(f'{result.stdout}')
            else:
                print(f'❌ Deployment failed: {result.stderr}')
                print(f'💡 Try manual deployment from Supabase dashboard')
                
        except subprocess.TimeoutExpired:
            print(f'⚠️ Deployment timed out')
            
    else:
        print(f'❌ Doc-parser function not found at {doc_parser_path}')
        print(f'💡 Check the function path and ensure it exists')
    
    # Step 6: Create test script to verify fix
    print(f'\n6️⃣ Creating Verification Test')
    print('-' * 28)
    
    test_script = '''#!/usr/bin/env python3

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def verify_doc_parser_fix():
    load_dotenv()
    
    print('🧪 Verifying Doc-Parser Fix')
    print('=' * 28)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use a test document ID (update this to match your test document)
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {'documentId': document_id}
    
    timeout = aiohttp.ClientTimeout(total=120)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Testing doc-parser: {doc_parser_url}')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Response Status: {status}')
                print(f'📄 Response: {response_text}')
                
                if status == 200:
                    print(f'🎉 ✅ DOC-PARSER FIXED!')
                    print(f'✅ Environment variables are now accessible')
                    print(f'✅ File download working')
                    print(f'✅ Document processing functional')
                    return True
                elif status == 400 and "Failed to download file" in response_text:
                    print(f'❌ Still getting download error')
                    print(f'💡 Environment variables may not have propagated yet')
                    print(f'💡 Wait 5-10 minutes and try again')
                    return False
                else:
                    print(f'⚠️ Unexpected response: {status}')
                    return False
                    
        except Exception as e:
            print(f'❌ Test failed: {e}')
            return False

if __name__ == "__main__":
    success = asyncio.run(verify_doc_parser_fix())
    print(f'\\n🏁 Verification: {"PASSED" if success else "FAILED"}')
'''
    
    with open('verify_doc_parser_fix.py', 'w') as f:
        f.write(test_script)
    
    print(f'✅ Created verification test: verify_doc_parser_fix.py')
    
    # Final instructions
    print(f'\n🎯 Next Steps')
    print('=' * 13)
    print(f'1. Wait 5-10 minutes for environment variables to propagate')
    print(f'2. Run: python verify_doc_parser_fix.py')
    print(f'3. If still failing, check Supabase Dashboard > Edge Functions > doc-parser > Logs')
    print(f'4. Ensure you are logged into the correct Supabase project')
    
    print(f'\n💡 Manual Alternative:')
    print(f'   • Go to Supabase Dashboard > Edge Functions > doc-parser')
    print(f'   • Click "Settings" tab')
    print(f'   • Add environment variables manually:')
    print(f'     - SUPABASE_URL: {supabase_url}')
    print(f'     - SUPABASE_SERVICE_ROLE_KEY: [your-service-role-key]')
    print(f'   • Click "Deploy" to redeploy function')
    
    return True

if __name__ == "__main__":
    fix_doc_parser_environment() 

import asyncio
import os
import subprocess
import json
from dotenv import load_dotenv

def fix_doc_parser_environment():
    load_dotenv()
    
    print('🔧 Fixing Doc-Parser Environment Variables')
    print('=' * 45)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    llamaparse_key = os.getenv('LLAMAPARSE_API_KEY')
    
    if not all([supabase_url, service_role_key]):
        print("❌ Missing required environment variables in local .env file")
        print("Please ensure your .env file contains:")
        print("   SUPABASE_URL=...")
        print("   SUPABASE_SERVICE_ROLE_KEY=...")
        return False
    
    print(f'✅ Local environment variables found')
    print(f'   SUPABASE_URL: {supabase_url}')
    print(f'   SUPABASE_SERVICE_ROLE_KEY: {service_role_key[:20]}...')
    print(f'   LLAMAPARSE_API_KEY: {"✅ Set" if llamaparse_key else "❌ Missing"}')
    
    # Step 1: Check if Supabase CLI is installed
    print(f'\n1️⃣ Checking Supabase CLI')
    print('-' * 24)
    
    try:
        result = subprocess.run(['supabase', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f'✅ Supabase CLI installed: {result.stdout.strip()}')
        else:
            print(f'❌ Supabase CLI not working properly')
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f'❌ Supabase CLI not installed or not in PATH')
        print(f'💡 Install with: npm install -g supabase')
        return False
    
    # Step 2: Check project status
    print(f'\n2️⃣ Checking Project Status')
    print('-' * 26)
    
    try:
        result = subprocess.run(['supabase', 'status'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f'✅ Supabase project status:')
            print(f'{result.stdout}')
        else:
            print(f'⚠️ Project not linked or not logged in')
            print(f'💡 Run: supabase login')
            print(f'💡 Then: supabase link --project-ref YOUR_PROJECT_REF')
    except subprocess.TimeoutExpired:
        print(f'⚠️ Status check timed out')
    
    # Step 3: Check current secrets
    print(f'\n3️⃣ Checking Current Edge Function Secrets')
    print('-' * 42)
    
    try:
        result = subprocess.run(['supabase', 'secrets', 'list'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f'✅ Current secrets:')
            print(f'{result.stdout}')
        else:
            print(f'❌ Failed to list secrets: {result.stderr}')
    except subprocess.TimeoutExpired:
        print(f'⚠️ Secrets list timed out')
    
    # Step 4: Set required environment variables
    print(f'\n4️⃣ Setting Required Environment Variables')
    print('-' * 41)
    
    # Create secrets to set
    secrets_to_set = {
        'SUPABASE_URL': supabase_url,
        'SUPABASE_SERVICE_ROLE_KEY': service_role_key
    }
    
    if llamaparse_key:
        secrets_to_set['LLAMAPARSE_API_KEY'] = llamaparse_key
    
    print(f'📝 Setting {len(secrets_to_set)} environment variables...')
    
    success_count = 0
    for secret_name, secret_value in secrets_to_set.items():
        try:
            print(f'   Setting {secret_name}...')
            result = subprocess.run([
                'supabase', 'secrets', 'set', 
                f'{secret_name}={secret_value}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f'   ✅ {secret_name} set successfully')
                success_count += 1
            else:
                print(f'   ❌ Failed to set {secret_name}: {result.stderr}')
                
        except subprocess.TimeoutExpired:
            print(f'   ⚠️ Timeout setting {secret_name}')
    
    if success_count == len(secrets_to_set):
        print(f'\n✅ All environment variables set successfully!')
    else:
        print(f'\n⚠️ Only {success_count}/{len(secrets_to_set)} variables set')
    
    # Step 5: Redeploy doc-parser function
    print(f'\n5️⃣ Redeploying Doc-Parser Function')
    print('-' * 35)
    
    doc_parser_path = 'db/supabase/functions/doc-parser'
    if os.path.exists(doc_parser_path):
        print(f'📁 Found doc-parser at: {doc_parser_path}')
        
        try:
            print(f'🚀 Deploying doc-parser...')
            result = subprocess.run([
                'supabase', 'functions', 'deploy', 'doc-parser',
                '--project-ref', supabase_url.split('//')[1].split('.')[0]
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f'✅ Doc-parser deployed successfully!')
                print(f'{result.stdout}')
            else:
                print(f'❌ Deployment failed: {result.stderr}')
                print(f'💡 Try manual deployment from Supabase dashboard')
                
        except subprocess.TimeoutExpired:
            print(f'⚠️ Deployment timed out')
            
    else:
        print(f'❌ Doc-parser function not found at {doc_parser_path}')
        print(f'💡 Check the function path and ensure it exists')
    
    # Step 6: Create test script to verify fix
    print(f'\n6️⃣ Creating Verification Test')
    print('-' * 28)
    
    test_script = '''#!/usr/bin/env python3

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

async def verify_doc_parser_fix():
    load_dotenv()
    
    print('🧪 Verifying Doc-Parser Fix')
    print('=' * 28)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Use a test document ID (update this to match your test document)
    document_id = 'cd05bfc9-60bf-4e3c-acd0-48a47c36fafb'
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    payload = {'documentId': document_id}
    
    timeout = aiohttp.ClientTimeout(total=120)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        doc_parser_url = f"{supabase_url}/functions/v1/doc-parser"
        
        print(f'🌐 Testing doc-parser: {doc_parser_url}')
        
        try:
            async with session.post(doc_parser_url, json=payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f'📊 Response Status: {status}')
                print(f'📄 Response: {response_text}')
                
                if status == 200:
                    print(f'🎉 ✅ DOC-PARSER FIXED!')
                    print(f'✅ Environment variables are now accessible')
                    print(f'✅ File download working')
                    print(f'✅ Document processing functional')
                    return True
                elif status == 400 and "Failed to download file" in response_text:
                    print(f'❌ Still getting download error')
                    print(f'💡 Environment variables may not have propagated yet')
                    print(f'💡 Wait 5-10 minutes and try again')
                    return False
                else:
                    print(f'⚠️ Unexpected response: {status}')
                    return False
                    
        except Exception as e:
            print(f'❌ Test failed: {e}')
            return False

if __name__ == "__main__":
    success = asyncio.run(verify_doc_parser_fix())
    print(f'\\n🏁 Verification: {"PASSED" if success else "FAILED"}')
'''
    
    with open('verify_doc_parser_fix.py', 'w') as f:
        f.write(test_script)
    
    print(f'✅ Created verification test: verify_doc_parser_fix.py')
    
    # Final instructions
    print(f'\n🎯 Next Steps')
    print('=' * 13)
    print(f'1. Wait 5-10 minutes for environment variables to propagate')
    print(f'2. Run: python verify_doc_parser_fix.py')
    print(f'3. If still failing, check Supabase Dashboard > Edge Functions > doc-parser > Logs')
    print(f'4. Ensure you are logged into the correct Supabase project')
    
    print(f'\n💡 Manual Alternative:')
    print(f'   • Go to Supabase Dashboard > Edge Functions > doc-parser')
    print(f'   • Click "Settings" tab')
    print(f'   • Add environment variables manually:')
    print(f'     - SUPABASE_URL: {supabase_url}')
    print(f'     - SUPABASE_SERVICE_ROLE_KEY: [your-service-role-key]')
    print(f'   • Click "Deploy" to redeploy function')
    
    return True

if __name__ == "__main__":
    fix_doc_parser_environment() 