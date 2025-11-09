#!/usr/bin/env python3
"""
Staging Environment Manual Test Suite
Based on development environment testing patterns for FRACAS FM-012

This script performs comprehensive manual testing of the staging environment
to validate storage access, upload pipeline, and worker functionality.
"""

import asyncio
import httpx
import json
import os
import hashlib
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load staging environment variables
load_dotenv('.env.staging')

class StagingManualTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.user_id = None
        self.staging_url = os.getenv("SUPABASE_URL", "https://dfgzeastcxnoqshgyotp.supabase.co")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
        self.anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        
        # Test configuration
        self.test_email = f"test_user_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        self.test_file = "examples/simulated_insurance_document.pdf"
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def print_header(self, title):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step_num, title):
        """Print a formatted step"""
        print(f"\n📋 STEP {step_num}: {title}")
        print("-" * 40)
    
    def print_status(self, status, message):
        """Print status with emoji"""
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {message}")
    
    async def test_environment_configuration(self):
        """Test 1: Environment Configuration"""
        self.print_step(1, "ENVIRONMENT CONFIGURATION")
        
        # Check required environment variables
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY", 
            "SUPABASE_ANON_KEY",
            "DATABASE_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.print_status("FAIL", f"Missing environment variables: {missing_vars}")
            return False
        
        # Check service role key format
        if len(self.service_role_key) < 200:
            self.print_status("FAIL", f"Service role key too short: {len(self.service_role_key)} chars")
            return False
        
        # Check if service role key is not anon key
        if self.service_role_key == self.anon_key:
            self.print_status("FAIL", "Service role key appears to be anon key")
            return False
        
        self.print_status("PASS", "Environment configuration valid")
        return True
    
    async def test_basic_api_access(self):
        """Test 2: Basic API Access"""
        self.print_step(2, "BASIC API ACCESS")
        
        try:
            response = await self.client.get(f"{self.staging_url}/rest/v1/")
            if response.status_code == 200:
                self.print_status("PASS", f"API accessible (200)")
                return True
            else:
                self.print_status("FAIL", f"API returned {response.status_code}")
                return False
        except Exception as e:
            self.print_status("FAIL", f"API access error: {e}")
            return False
    
    async def test_storage_access(self):
        """Test 3: Storage Access with Service Role"""
        self.print_step(3, "STORAGE ACCESS")
        
        # Test file path from FRACAS FM-012
        test_file_path = "files/user/468add2d-e124-4771-8895-958ad38430fb/raw/0bb233ff_f076c0c1.pdf"
        
        try:
            response = await self.client.get(
                f"{self.staging_url}/storage/v1/object/{test_file_path}",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )
            
            if response.status_code == 200:
                self.print_status("PASS", "Storage access successful")
                return True
            elif response.status_code == 400:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                if "not_found" in str(error_data):
                    self.print_status("FAIL", "File not found (404) - may be expected")
                else:
                    self.print_status("FAIL", f"400 Bad Request - Permission issue: {error_data}")
                return False
            else:
                self.print_status("FAIL", f"Storage access failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Storage access error: {e}")
            return False
    
    async def test_storage_policies(self):
        """Test 4: Storage Policies via Database Query"""
        self.print_step(4, "STORAGE POLICIES")
        
        try:
            # Query storage policies
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
                    ORDER BY policyname;
                    """
                }
            )
            
            if response.status_code == 200:
                policies = response.json()
                service_role_policy = any(
                    "Allow service role to download files" in str(policy) 
                    for policy in policies
                )
                
                if service_role_policy:
                    self.print_status("PASS", "Storage policy exists")
                    return True
                else:
                    self.print_status("FAIL", "Missing 'Allow service role to download files' policy")
                    return False
            else:
                self.print_status("FAIL", f"Policy query failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Policy query error: {e}")
            return False
    
    async def test_upload_pipeline_schema(self):
        """Test 5: Upload Pipeline Schema Access"""
        self.print_step(5, "UPLOAD PIPELINE SCHEMA")
        
        try:
            # Test upload_pipeline.documents table
            response = await self.client.get(
                f"{self.staging_url}/rest/v1/upload_pipeline.documents?select=*&limit=1",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )
            
            if response.status_code == 200:
                self.print_status("PASS", "Upload pipeline schema accessible")
                return True
            else:
                self.print_status("FAIL", f"Schema access failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Schema access error: {e}")
            return False
    
    async def test_worker_endpoints(self):
        """Test 6: Worker Service Endpoints"""
        self.print_step(6, "WORKER ENDPOINTS")
        
        # Test worker health endpoint
        worker_url = "https://insurance-navigator-staging-worker-v2.onrender.com"
        
        try:
            response = await self.client.get(f"{worker_url}/health", timeout=10.0)
            if response.status_code == 200:
                self.print_status("PASS", "Worker health endpoint accessible")
                return True
            else:
                self.print_status("FAIL", f"Worker health failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_status("FAIL", f"Worker endpoint error: {e}")
            return False
    
    async def test_document_upload_simulation(self):
        """Test 7: Document Upload Simulation"""
        self.print_step(7, "DOCUMENT UPLOAD SIMULATION")
        
        try:
            # Create a test upload job
            upload_data = {
                "filename": "test_document.pdf",
                "content_type": "application/pdf",
                "file_size": 1024
            }
            
            response = await self.client.post(
                f"{self.staging_url}/rest/v1/upload_pipeline.upload_jobs",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key,
                    "Content-Type": "application/json"
                },
                json=upload_data
            )
            
            if response.status_code == 201:
                self.print_status("PASS", "Upload job creation successful")
                return True
            else:
                self.print_status("FAIL", f"Upload job creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Upload simulation error: {e}")
            return False
    
    async def test_storage_bucket_listing(self):
        """Test 8: Storage Bucket Listing"""
        self.print_step(8, "STORAGE BUCKET LISTING")
        
        try:
            response = await self.client.get(
                f"{self.staging_url}/storage/v1/bucket",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )
            
            if response.status_code == 200:
                buckets = response.json()
                files_bucket = any(bucket.get("name") == "files" for bucket in buckets)
                
                if files_bucket:
                    self.print_status("PASS", "Files bucket exists")
                    return True
                else:
                    self.print_status("FAIL", "Files bucket not found")
                    return False
            else:
                self.print_status("FAIL", f"Bucket listing failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Bucket listing error: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests and generate report"""
        self.print_header("STAGING ENVIRONMENT MANUAL TEST SUITE")
        print(f"Target: {self.staging_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        tests = [
            ("Environment Configuration", self.test_environment_configuration),
            ("Basic API Access", self.test_basic_api_access),
            ("Storage Access", self.test_storage_access),
            ("Storage Policies", self.test_storage_policies),
            ("Upload Pipeline Schema", self.test_upload_pipeline_schema),
            ("Worker Endpoints", self.test_worker_endpoints),
            ("Document Upload Simulation", self.test_document_upload_simulation),
            ("Storage Bucket Listing", self.test_storage_bucket_listing)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Generate summary report
        self.print_header("TEST SUMMARY REPORT")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"📊 Test Results: {passed}/{total} passed")
        
        if passed < total:
            print(f"⚠️  {total - passed} tests failed - Review issues below")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        # Critical issues
        critical_failures = []
        for test_name, result in results:
            if not result and test_name in ["Storage Access", "Storage Policies"]:
                critical_failures.append(test_name)
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_failures:
                print(f"   - {issue}")
            print(f"\n🔧 REQUIRED ACTIONS:")
            print(f"   1. Apply storage migration via Supabase SQL Editor")
            print(f"   2. Verify storage policies exist")
            print(f"   3. Re-run this test suite")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED - Staging environment is ready!")
        else:
            print(f"\n❌ STAGING ENVIRONMENT VALIDATION FAILED")
            print(f"   Please review the failed tests and fix issues")
        
        return passed == total

async def main():
    """Main test execution"""
    async with StagingManualTester() as tester:
        success = await tester.run_comprehensive_test()
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
