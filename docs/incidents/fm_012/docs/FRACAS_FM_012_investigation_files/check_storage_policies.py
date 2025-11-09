#!/usr/bin/env python3
"""
Check Storage Policies
Check what storage policies exist in the staging environment
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load staging environment variables
load_dotenv('.env.staging')

async def check_storage_policies():
    """Check what storage policies exist"""
    client = httpx.AsyncClient(timeout=30.0)
    
    staging_url = os.getenv("SUPABASE_URL", "https://dfgzeastcxnoqshgyotp.supabase.co")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
    
    print("🔍 CHECKING STORAGE POLICIES")
    print("=" * 50)
    print(f"Staging URL: {staging_url}")
    print(f"Service Role Key: {service_role_key[:20]}...")
    
    try:
        # Check storage policies using RPC function
        response = await client.post(
            f"{staging_url}/rest/v1/rpc/exec_sql",
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key,
                "Content-Type": "application/json"
            },
            json={
                "sql": """
                SELECT 
                    schemaname,
                    tablename,
                    policyname,
                    permissive,
                    roles,
                    cmd,
                    qual,
                    with_check
                FROM pg_policies 
                WHERE schemaname = 'storage' 
                AND tablename = 'objects'
                ORDER BY policyname;
                """
            }
        )
        
        if response.status_code == 200:
            policies = response.json()
            print(f"\n✅ Found {len(policies)} storage policies:")
            
            for policy in policies:
                print(f"\n📋 Policy: {policy.get('policyname')}")
                print(f"   Table: {policy.get('tablename')}")
                print(f"   Command: {policy.get('cmd')}")
                print(f"   Roles: {policy.get('roles')}")
                print(f"   Qual: {policy.get('qual')}")
                print(f"   With Check: {policy.get('with_check')}")
        else:
            print(f"❌ Failed to get policies: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking policies: {e}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_storage_policies())
