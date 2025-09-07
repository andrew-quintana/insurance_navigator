#!/usr/bin/env python3
"""
Check Supabase storage configuration and test signed URL generation
"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

async def check_supabase_storage():
    """Check Supabase storage configuration"""
    load_dotenv('.env.production')
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"🔍 Checking Supabase storage configuration...")
    print(f"📋 Supabase URL: {supabase_url}")
    print(f"📋 Anon Key: {supabase_anon_key[:20]}...")
    
    # Test Supabase storage API
    async with httpx.AsyncClient() as client:
        try:
            # Test storage health
            storage_response = await client.get(
                f"{supabase_url}/storage/v1/",
                headers={"apikey": supabase_anon_key},
                timeout=30
            )
            
            print(f"📊 Storage API response: {storage_response.status_code}")
            if storage_response.status_code == 200:
                print("✅ Supabase storage API is accessible")
            else:
                print(f"⚠️ Storage API response: {storage_response.text}")
            
            # Test bucket listing
            buckets_response = await client.get(
                f"{supabase_url}/storage/v1/bucket",
                headers={"apikey": supabase_anon_key},
                timeout=30
            )
            
            print(f"📊 Buckets response: {buckets_response.status_code}")
            if buckets_response.status_code == 200:
                buckets = buckets_response.json()
                print(f"📋 Available buckets: {[bucket.get('name') for bucket in buckets]}")
            else:
                print(f"⚠️ Buckets response: {buckets_response.text}")
            
            # Test signed URL generation (this would normally be done by the API)
            test_path = "test/signed-url-test.txt"
            signed_url_response = await client.post(
                f"{supabase_url}/storage/v1/object/sign/{test_path}",
                headers={"apikey": supabase_anon_key},
                json={"expiresIn": 3600},
                timeout=30
            )
            
            print(f"📊 Signed URL response: {signed_url_response.status_code}")
            if signed_url_response.status_code == 200:
                signed_data = signed_url_response.json()
                print(f"✅ Signed URL generation works: {signed_data.get('signedURL', '')[:100]}...")
            else:
                print(f"⚠️ Signed URL response: {signed_url_response.text}")
                
        except Exception as e:
            print(f"❌ Error checking Supabase storage: {e}")

if __name__ == "__main__":
    asyncio.run(check_supabase_storage())
