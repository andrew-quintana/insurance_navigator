#!/usr/bin/env python3
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

async def check_table_schemas():
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession() as session:
        # Check document_vectors table
        try:
            async with session.get(f'{supabase_url}/rest/v1/document_vectors?select=*&limit=0', headers=headers) as response:
                if response.status == 200:
                    print('✅ document_vectors table EXISTS')
                else:
                    print(f'❌ document_vectors table not found: {response.status}')
        except Exception as e:
            print(f'Error checking document_vectors: {e}')
        
        # Check user_document_vectors table 
        try:
            async with session.get(f'{supabase_url}/rest/v1/user_document_vectors?select=*&limit=0', headers=headers) as response:
                if response.status == 200:
                    print('✅ user_document_vectors table EXISTS')
                else:
                    print(f'❌ user_document_vectors table not found: {response.status}')
        except Exception as e:
            print(f'Error checking user_document_vectors: {e}')

if __name__ == "__main__":
    asyncio.run(check_table_schemas()) 