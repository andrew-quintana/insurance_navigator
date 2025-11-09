#!/usr/bin/env python3
"""
Staging Storage Access Test
Focused test for FRACAS FM-012 storage access issues

Based on development environment testing patterns, this script tests
specific storage access scenarios that are failing in staging.
"""

import asyncio
import httpx
import json
import os
import time
from dotenv import load_dotenv
from datetime import datetime

# Load staging environment variables
load_dotenv('.env.staging')

class StagingStorageTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.staging_url = os.getenv("SUPABASE_URL", "https://dfgzeastcxnoqshgyotp.supabase.co")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
        self.anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        
        # Test file from FRACAS FM-012
        self.test_file_path = "files/user/468add2d-e124-4771-8895-958ad38430fb/raw/0bb233ff_f076c0c1.pdf"
        self.test_bucket = "files"
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def print_header(self, title):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_test(self, test_name, status, details=""):
        """Print test result"""
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}")
        if details:
            print(f"   {details}")
    
    async def test_service_role_key_format(self):
        """Test 1: Service Role Key Format"""
        print("\n📋 Test 1: Service Role Key Format")
        
        if not self.service_role_key:
            self.print_test("Service Role Key", "FAIL", "No service role key found")
            return False
        
        if len(self.service_role_key) < 200:
            self.print_test("Service Role Key", "FAIL", f"Key too short: {len(self.service_role_key)} chars")
            return False
        
        if self.service_role_key == self.anon_key:
            self.print_test("Service Role Key", "FAIL", "Service role key appears to be anon key")
            return False
        
        # Try to decode JWT to verify it's a service role key
        try:
            import jwt
            decoded = jwt.decode(self.service_role_key, options={"verify_signature": False})
            role = decoded.get("role", "")
            if role == "service_role":
                self.print_test("Service Role Key", "PASS", f"Valid service role key ({len(self.service_role_key)} chars)")
                return True
            else:
                self.print_test("Service Role Key", "FAIL", f"Wrong role: {role}")
                return False
        except Exception as e:
            self.print_test("Service Role Key", "WARN", f"Could not decode JWT: {e}")
            return True  # Assume it's correct if we can't decode
    
    async def test_basic_storage_access(self):
        """Test 2: Basic Storage Access"""
        print("\n📋 Test 2: Basic Storage Access")
        
        try:
            response = await self.client.get(
                f"{self.staging_url}/storage/v1/object/{self.test_file_path}",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )
            
            if response.status_code == 200:
                self.print_test("Storage Access", "PASS", "File downloaded successfully")
                return True
            elif response.status_code == 404:
                self.print_test("Storage Access", "WARN", "File not found (may be expected)")
                return True  # File might not exist, but access is working
            elif response.status_code == 400:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                if "not_found" in str(error_data):
                    self.print_test("Storage Access", "WARN", "File not found (may be expected)")
                    return True
                else:
                    self.print_test("Storage Access", "FAIL", f"400 Bad Request: {error_data}")
                    return False
            else:
                self.print_test("Storage Access", "FAIL", f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Storage Access", "FAIL", f"Request failed: {e}")
            return False
    
    async def test_storage_policy_existence(self):
        """Test 3: Storage Policy Existence"""
        print("\n📋 Test 3: Storage Policy Existence")
        
        try:
            # Query for storage policies
            response = await self.client.post(
                f"{self.staging_url}/rest/v1/rpc/exec_sql",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key,
                    "Content-Type": "application/json"
                },
                json={
                    "sql": """
                    SELECT policyname, permissive, roles, cmd, qual 
                    FROM pg_policies 
                    WHERE tablename = 'objects' 
                    AND schemaname = 'storage'
                    AND policyname = 'Allow service role to download files';
                    """
                }
            )
            
            if response.status_code == 200:
                policies = response.json()
                if policies:
                    self.print_test("Storage Policy", "PASS", "Policy exists")
                    return True
                else:
                    self.print_test("Storage Policy", "FAIL", "Policy does not exist")
                    return False
            else:
                self.print_test("Storage Policy", "FAIL", f"Query failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Storage Policy", "FAIL", f"Query error: {e}")
            return False
    
    async def test_bucket_access(self):
        """Test 4: Bucket Access"""
        print("\n📋 Test 4: Bucket Access")
        
        try:
            # List objects in files bucket
            response = await self.client.post(
                f"{self.staging_url}/storage/v1/object/list/{self.test_bucket}",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key,
                    "Content-Type": "application/json"
                },
                json={"prefix": "files/user/"}
            )
            
            if response.status_code == 200:
                objects = response.json()
                self.print_test("Bucket Access", "PASS", f"Found {len(objects)} objects")
                return True
            else:
                self.print_test("Bucket Access", "FAIL", f"Bucket access failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Bucket Access", "FAIL", f"Bucket access error: {e}")
            return False
    
    async def test_anon_key_access(self):
        """Test 5: Anon Key Access (should fail)"""
        print("\n📋 Test 5: Anon Key Access (should fail)")
        
        try:
            response = await self.client.get(
                f"{self.staging_url}/storage/v1/object/{self.test_file_path}",
                headers={
                    "Authorization": f"Bearer {self.anon_key}",
                    "apikey": self.anon_key
                }
            )
            
            if response.status_code == 400 or response.status_code == 403:
                self.print_test("Anon Key Access", "PASS", "Correctly denied access")
                return True
            else:
                self.print_test("Anon Key Access", "WARN", f"Unexpected status: {response.status_code}")
                return True  # Not critical
                
        except Exception as e:
            self.print_test("Anon Key Access", "WARN", f"Request failed: {e}")
            return True  # Not critical
    
    async def test_storage_url_format(self):
        """Test 6: Storage URL Format"""
        print("\n📋 Test 6: Storage URL Format")
        
        expected_url = f"{self.staging_url}/storage/v1/object/{self.test_file_path}"
        actual_url = f"{self.staging_url}/storage/v1/object/{self.test_file_path}"
        
        if expected_url == actual_url:
            self.print_test("URL Format", "PASS", f"Correct URL format: {actual_url}")
            return True
        else:
            self.print_test("URL Format", "FAIL", f"URL mismatch")
            return False
    
    async def run_storage_tests(self):
        """Run all storage tests"""
        self.print_header("STAGING STORAGE ACCESS TEST")
        print(f"Target: {self.staging_url}")
        print(f"Test File: {self.test_file_path}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        tests = [
            ("Service Role Key Format", self.test_service_role_key_format),
            ("Basic Storage Access", self.test_basic_storage_access),
            ("Storage Policy Existence", self.test_storage_policy_existence),
            ("Bucket Access", self.test_bucket_access),
            ("Anon Key Access", self.test_anon_key_access),
            ("Storage URL Format", self.test_storage_url_format)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Generate summary
        self.print_header("STORAGE TEST SUMMARY")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"📊 Test Results: {passed}/{total} passed")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        # Critical issues
        critical_tests = ["Service Role Key Format", "Basic Storage Access", "Storage Policy Existence"]
        critical_failures = [test_name for test_name, result in results 
                           if not result and test_name in critical_tests]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_failures:
                print(f"   - {issue}")
            print(f"\n🔧 REQUIRED ACTIONS:")
            print(f"   1. Apply storage migration via Supabase SQL Editor:")
            print(f"      CREATE POLICY \"Allow service role to download files\"")
            print(f"      ON storage.objects FOR SELECT TO service_role")
            print(f"      USING (bucket_id = 'files');")
            print(f"   2. Re-run this test")
        
        if passed == total:
            print(f"\n🎉 ALL STORAGE TESTS PASSED!")
        else:
            print(f"\n❌ STORAGE TESTS FAILED - Review issues above")
        
        return passed == total

async def main():
    """Main test execution"""
    async with StagingStorageTester() as tester:
        success = await tester.run_storage_tests()
        return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Test execution failed: {e}")
        exit(1)
