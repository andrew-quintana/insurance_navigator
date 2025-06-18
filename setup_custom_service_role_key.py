#!/usr/bin/env python3

import os
from dotenv import load_dotenv

def setup_custom_service_role_key():
    load_dotenv()
    
    print('🔧 Setting Up Custom Service Role Key')
    print('=' * 40)
    
    # The correct service role key value
    correct_service_role_key = 'de8ae826023b476e726c3ac390834049200b7ce6b532e4c27b98e32f039a0e87'
    
    # Current environment values
    current_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    supabase_url = os.getenv('SUPABASE_URL', '')
    
    print(f'✅ Correct Service Role Key: {correct_service_role_key}')
    print(f'⚠️ Current .env Key: {current_key[:20]}...')
    print(f'📊 Keys Match: {"Yes" if correct_service_role_key == current_key else "No"}')
    print(f'🌐 Supabase URL: {supabase_url}')
    
    print(f'\n🛠️ MANUAL SETUP REQUIRED:')
    print('=' * 26)
    
    print(f'1. Go to Supabase Dashboard:')
    print(f'   https://supabase.com/dashboard/project/jhrespvvhbnloxrieycf')
    
    print(f'\n2. Navigate to Edge Functions > doc-parser > Settings')
    
    print(f'\n3. Add Custom Environment Variable:')
    print(f'   Key: CUSTOM_SERVICE_ROLE_KEY')
    print(f'   Value: {correct_service_role_key}')
    
    print(f'\n4. Click "Deploy" to redeploy the function')
    
    print(f'\n💡 Why This Works:')
    print(f'   • SUPABASE_SERVICE_ROLE_KEY is a reserved secret (can\'t modify)')
    print(f'   • CUSTOM_SERVICE_ROLE_KEY is our custom variable (we can set it)')
    print(f'   • Doc-parser now checks CUSTOM_SERVICE_ROLE_KEY first')
    print(f'   • Falls back to SUPABASE_SERVICE_ROLE_KEY if custom not found')
    
    print(f'\n🧪 After Setup, Test With:')
    print(f'   python verify_doc_parser_fix.py')
    
    print(f'\n📋 Summary of Environment Variables Needed:')
    print(f'   ✅ SUPABASE_URL (default, already set)')
    print(f'   ❌ SUPABASE_SERVICE_ROLE_KEY (default, wrong value, can\'t change)')
    print(f'   🆕 CUSTOM_SERVICE_ROLE_KEY (our solution, need to set)')
    print(f'   ⚙️ LLAMAPARSE_API_KEY (optional, for PDF processing)')

if __name__ == "__main__":
    setup_custom_service_role_key() 

import os
from dotenv import load_dotenv

def setup_custom_service_role_key():
    load_dotenv()
    
    print('🔧 Setting Up Custom Service Role Key')
    print('=' * 40)
    
    # The correct service role key value
    correct_service_role_key = 'de8ae826023b476e726c3ac390834049200b7ce6b532e4c27b98e32f039a0e87'
    
    # Current environment values
    current_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    supabase_url = os.getenv('SUPABASE_URL', '')
    
    print(f'✅ Correct Service Role Key: {correct_service_role_key}')
    print(f'⚠️ Current .env Key: {current_key[:20]}...')
    print(f'📊 Keys Match: {"Yes" if correct_service_role_key == current_key else "No"}')
    print(f'🌐 Supabase URL: {supabase_url}')
    
    print(f'\n🛠️ MANUAL SETUP REQUIRED:')
    print('=' * 26)
    
    print(f'1. Go to Supabase Dashboard:')
    print(f'   https://supabase.com/dashboard/project/jhrespvvhbnloxrieycf')
    
    print(f'\n2. Navigate to Edge Functions > doc-parser > Settings')
    
    print(f'\n3. Add Custom Environment Variable:')
    print(f'   Key: CUSTOM_SERVICE_ROLE_KEY')
    print(f'   Value: {correct_service_role_key}')
    
    print(f'\n4. Click "Deploy" to redeploy the function')
    
    print(f'\n💡 Why This Works:')
    print(f'   • SUPABASE_SERVICE_ROLE_KEY is a reserved secret (can\'t modify)')
    print(f'   • CUSTOM_SERVICE_ROLE_KEY is our custom variable (we can set it)')
    print(f'   • Doc-parser now checks CUSTOM_SERVICE_ROLE_KEY first')
    print(f'   • Falls back to SUPABASE_SERVICE_ROLE_KEY if custom not found')
    
    print(f'\n🧪 After Setup, Test With:')
    print(f'   python verify_doc_parser_fix.py')
    
    print(f'\n📋 Summary of Environment Variables Needed:')
    print(f'   ✅ SUPABASE_URL (default, already set)')
    print(f'   ❌ SUPABASE_SERVICE_ROLE_KEY (default, wrong value, can\'t change)')
    print(f'   🆕 CUSTOM_SERVICE_ROLE_KEY (our solution, need to set)')
    print(f'   ⚙️ LLAMAPARSE_API_KEY (optional, for PDF processing)')

if __name__ == "__main__":
    setup_custom_service_role_key() 