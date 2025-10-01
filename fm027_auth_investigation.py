#!/usr/bin/env python3
"""
FM-027 Authentication Investigation Script

This script investigates the authentication/policy issues causing 400 errors
when accessing Supabase Storage from the Render worker environment.

Key areas of investigation:
1. Authentication system migration status
2. RLS policy verification
3. Service role key validity and permissions
4. Storage bucket access patterns
5. JWT token analysis
"""

import os
import sys
import json
import httpx
import jwt
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import asyncio

# Configuration
SUPABASE_URL = "***REMOVED***"

# Load environment variables from .env.production file
def load_env_file(filepath: str) -> Dict[str, str]:
    """Load environment variables from a .env file"""
    env_vars = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}")
    return env_vars

# Load staging environment (which has the correct key)
env_vars = load_env_file('.env.staging')
SERVICE_ROLE_KEY = env_vars.get("SUPABASE_SERVICE_ROLE_KEY", env_vars.get("SERVICE_ROLE_KEY", ""))
TEST_FILE_PATH = "files/user/8d65c725-ff38-4726-809e-018c05dfb874/raw/efa65fd1_222c3864.pdf"

class SupabaseAuthInvestigator:
    def __init__(self, supabase_url: str, service_role_key: str):
        self.supabase_url = supabase_url
        self.service_role_key = service_role_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        await self.client.aclose()
    
    def decode_jwt_payload(self, token: str) -> Dict[str, Any]:
        """Decode JWT payload without verification (for inspection only)"""
        try:
            # Split token and decode payload
            parts = token.split('.')
            if len(parts) != 3:
                return {"error": "Invalid JWT format"}
            
            # Decode payload (add padding if needed)
            payload = parts[1]
            padding = len(payload) % 4
            if padding:
                payload += '=' * (4 - padding)
            
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception as e:
            return {"error": f"Failed to decode JWT: {e}"}
    
    async def test_service_role_key_validity(self) -> Dict[str, Any]:
        """Test if the service role key is valid and has proper permissions"""
        print("🔑 Testing Service Role Key Validity...")
        
        # Decode JWT to inspect claims
        jwt_payload = self.decode_jwt_payload(self.service_role_key)
        print(f"JWT Payload: {json.dumps(jwt_payload, indent=2)}")
        
        # Test basic API access
        try:
            headers = {
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json"
            }
            
            # Test auth API access
            auth_response = await self.client.get(
                f"{self.supabase_url}/auth/v1/admin/users",
                headers=headers
            )
            
            print(f"Auth API Test: {auth_response.status_code}")
            if auth_response.status_code == 200:
                print("✅ Service role key has auth admin access")
            else:
                print(f"❌ Auth API access failed: {auth_response.text[:200]}")
            
            return {
                "jwt_payload": jwt_payload,
                "auth_api_status": auth_response.status_code,
                "auth_api_response": auth_response.text[:200] if auth_response.status_code != 200 else "Success"
            }
            
        except Exception as e:
            print(f"❌ Service role key test failed: {e}")
            return {"error": str(e)}
    
    async def test_storage_access_patterns(self) -> Dict[str, Any]:
        """Test different storage access patterns to identify the issue"""
        print("\n📁 Testing Storage Access Patterns...")
        
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "User-Agent": "python-httpx/0.28.1",
            "Accept": "*/*"
        }
        
        results = {}
        
        # Test 1: List buckets
        try:
            buckets_response = await self.client.get(
                f"{self.supabase_url}/storage/v1/bucket",
                headers=headers
            )
            results["buckets_status"] = buckets_response.status_code
            results["buckets_response"] = buckets_response.text[:200] if buckets_response.status_code != 200 else "Success"
            print(f"Buckets API: {buckets_response.status_code}")
        except Exception as e:
            results["buckets_error"] = str(e)
            print(f"❌ Buckets API failed: {e}")
        
        # Test 2: List objects in files bucket
        try:
            objects_response = await self.client.get(
                f"{self.supabase_url}/storage/v1/object/list/files",
                headers=headers
            )
            results["objects_status"] = objects_response.status_code
            results["objects_response"] = objects_response.text[:200] if objects_response.status_code != 200 else "Success"
            print(f"Objects API: {objects_response.status_code}")
        except Exception as e:
            results["objects_error"] = str(e)
            print(f"❌ Objects API failed: {e}")
        
        # Test 3: Direct file access (the failing case)
        try:
            file_response = await self.client.head(
                f"{self.supabase_url}/storage/v1/object/{TEST_FILE_PATH}",
                headers=headers
            )
            results["file_status"] = file_response.status_code
            results["file_headers"] = dict(file_response.headers)
            results["file_response"] = file_response.text[:200] if file_response.status_code != 200 else "Success"
            print(f"File Access: {file_response.status_code} - CF-Ray: {file_response.headers.get('cf-ray', 'N/A')}")
        except Exception as e:
            results["file_error"] = str(e)
            print(f"❌ File access failed: {e}")
        
        return results
    
    async def test_different_auth_methods(self) -> Dict[str, Any]:
        """Test different authentication methods"""
        print("\n🔐 Testing Different Authentication Methods...")
        
        results = {}
        
        # Method 1: Only apikey header
        try:
            headers1 = {"apikey": self.service_role_key}
            response1 = await self.client.head(
                f"{self.supabase_url}/storage/v1/object/{TEST_FILE_PATH}",
                headers=headers1
            )
            results["apikey_only"] = {
                "status": response1.status_code,
                "cf_ray": response1.headers.get('cf-ray', 'N/A')
            }
            print(f"API Key Only: {response1.status_code}")
        except Exception as e:
            results["apikey_only"] = {"error": str(e)}
            print(f"❌ API Key Only failed: {e}")
        
        # Method 2: Only Authorization header
        try:
            headers2 = {"Authorization": f"Bearer {self.service_role_key}"}
            response2 = await self.client.head(
                f"{self.supabase_url}/storage/v1/object/{TEST_FILE_PATH}",
                headers=headers2
            )
            results["auth_only"] = {
                "status": response2.status_code,
                "cf_ray": response2.headers.get('cf-ray', 'N/A')
            }
            print(f"Auth Only: {response2.status_code}")
        except Exception as e:
            results["auth_only"] = {"error": str(e)}
            print(f"❌ Auth Only failed: {e}")
        
        # Method 3: Both headers (current method)
        try:
            headers3 = {
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}"
            }
            response3 = await self.client.head(
                f"{self.supabase_url}/storage/v1/object/{TEST_FILE_PATH}",
                headers=headers3
            )
            results["both_headers"] = {
                "status": response3.status_code,
                "cf_ray": response3.headers.get('cf-ray', 'N/A')
            }
            print(f"Both Headers: {response3.status_code}")
        except Exception as e:
            results["both_headers"] = {"error": str(e)}
            print(f"❌ Both Headers failed: {e}")
        
        return results
    
    async def test_rls_policies(self) -> Dict[str, Any]:
        """Test RLS policy access patterns"""
        print("\n🛡️ Testing RLS Policy Access...")
        
        # Test with different user contexts
        results = {}
        
        # Test 1: Direct SQL query to check RLS policies
        try:
            headers = {
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json"
            }
            
            # Query to check storage policies
            policy_query = {
                "query": """
                SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
                FROM pg_policies 
                WHERE schemaname = 'storage' 
                ORDER BY tablename, policyname;
                """
            }
            
            policy_response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/exec",
                headers=headers,
                json=policy_query
            )
            
            results["policy_query_status"] = policy_response.status_code
            results["policy_query_response"] = policy_response.text[:500] if policy_response.status_code != 200 else "Success"
            print(f"Policy Query: {policy_response.status_code}")
            
        except Exception as e:
            results["policy_query_error"] = str(e)
            print(f"❌ Policy query failed: {e}")
        
        return results
    
    async def test_file_existence_verification(self) -> Dict[str, Any]:
        """Verify if the file actually exists using different methods"""
        print("\n🔍 Verifying File Existence...")
        
        results = {}
        
        # Method 1: Direct object query
        try:
            headers = {
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json"
            }
            
            # Query storage.objects table directly
            object_query = {
                "query": f"""
                SELECT id, bucket_id, name, created_at, metadata 
                FROM storage.objects 
                WHERE bucket_id = 'files' 
                AND name = '{TEST_FILE_PATH}';
                """
            }
            
            object_response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/exec",
                headers=headers,
                json=object_query
            )
            
            results["object_query_status"] = object_response.status_code
            results["object_query_response"] = object_response.text[:500] if object_response.status_code != 200 else "Success"
            print(f"Object Query: {object_response.status_code}")
            
        except Exception as e:
            results["object_query_error"] = str(e)
            print(f"❌ Object query failed: {e}")
        
        # Method 2: List all objects in the user's directory
        try:
            user_path = "files/user/8d65c725-ff38-4726-809e-018c05dfb874/"
            list_query = {
                "query": f"""
                SELECT id, bucket_id, name, created_at 
                FROM storage.objects 
                WHERE bucket_id = 'files' 
                AND name LIKE '{user_path}%'
                ORDER BY created_at DESC;
                """
            }
            
            list_response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/exec",
                headers=headers,
                json=list_query
            )
            
            results["list_query_status"] = list_response.status_code
            results["list_query_response"] = list_response.text[:500] if list_response.status_code != 200 else "Success"
            print(f"List Query: {list_response.status_code}")
            
        except Exception as e:
            results["list_query_error"] = str(e)
            print(f"❌ List query failed: {e}")
        
        return results

async def main():
    """Main investigation function"""
    print("🔍 FM-027 Authentication Investigation")
    print("=" * 50)
    
    if not SERVICE_ROLE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY environment variable not set")
        sys.exit(1)
    
    investigator = SupabaseAuthInvestigator(SUPABASE_URL, SERVICE_ROLE_KEY)
    
    try:
        # Run all investigations
        results = {}
        
        # Test 1: Service role key validity
        results["service_role_test"] = await investigator.test_service_role_key_validity()
        
        # Test 2: Storage access patterns
        results["storage_access"] = await investigator.test_storage_access_patterns()
        
        # Test 3: Different auth methods
        results["auth_methods"] = await investigator.test_different_auth_methods()
        
        # Test 4: RLS policies
        results["rls_policies"] = await investigator.test_rls_policies()
        
        # Test 5: File existence verification
        results["file_verification"] = await investigator.test_file_existence_verification()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fm027_auth_investigation_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Investigation Results saved to: {filename}")
        
        # Summary
        print("\n📋 Investigation Summary:")
        print("-" * 30)
        
        if results["service_role_test"].get("auth_api_status") == 200:
            print("✅ Service role key is valid")
        else:
            print("❌ Service role key has issues")
        
        if results["storage_access"].get("file_status") == 200:
            print("✅ File access works")
        else:
            print(f"❌ File access failed: {results['storage_access'].get('file_status', 'Unknown')}")
        
        print(f"📁 File verification: {results['file_verification'].get('object_query_status', 'Unknown')}")
        
    finally:
        await investigator.close()

if __name__ == "__main__":
    asyncio.run(main())
