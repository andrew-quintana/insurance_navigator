#!/usr/bin/env python3
"""
Test Staging API Functionality
Tests the staging API service after FRACAS FM-012 resolution

This script tests the API endpoints to verify document processing functionality.
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

class StagingAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_url = "https://insurance-navigator-staging-api.onrender.com"
        self.staging_url = os.getenv("SUPABASE_URL", "https://dfgzeastcxnoqshgyotp.supabase.co")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
        self.anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        
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
    
    async def test_api_health(self):
        """Test 1: API Health Check"""
        self.print_step(1, "API HEALTH CHECK")
        
        try:
            response = await self.client.get(f"{self.api_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self.print_status("PASS", f"API healthy - Status: {data.get('status')}")
                self.print_status("PASS", f"Version: {data.get('version')}")
                
                # Check individual services
                services = data.get('services', {})
                for service, status in services.items():
                    if status.get('healthy'):
                        self.print_status("PASS", f"{service}: {status.get('status')}")
                    else:
                        self.print_status("FAIL", f"{service}: {status.get('status')}")
                
                return True
            else:
                self.print_status("FAIL", f"API health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"API health check error: {e}")
            return False
    
    async def test_storage_access_via_api(self):
        """Test 2: Storage Access via API"""
        self.print_step(2, "STORAGE ACCESS VIA API")
        
        try:
            # Test storage access using service role
            test_path = "files/user/test/raw/test_document.pdf"
            
            response = await self.client.get(
                f"{self.staging_url}/storage/v1/object/{test_path}",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )
            
            if response.status_code == 200:
                self.print_status("PASS", "Storage access successful via API")
                return True
            elif response.status_code == 404:
                self.print_status("PASS", "Storage access working (file not found is expected)")
                return True
            else:
                self.print_status("FAIL", f"Storage access failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Storage access error: {e}")
            return False
    
    async def test_upload_pipeline_schema(self):
        """Test 3: Upload Pipeline Schema Access"""
        self.print_step(3, "UPLOAD PIPELINE SCHEMA ACCESS")
        
        try:
            # Test accessing upload_pipeline schema
            response = await self.client.get(
                f"{self.staging_url}/rest/v1/upload_pipeline.upload_jobs?select=*&limit=1",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_status("PASS", f"Upload pipeline schema accessible - Found {len(data)} jobs")
                return True
            else:
                self.print_status("FAIL", f"Schema access failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Schema access error: {e}")
            return False
    
    async def test_document_upload_simulation(self):
        """Test 4: Document Upload Simulation"""
        self.print_step(4, "DOCUMENT UPLOAD SIMULATION")
        
        try:
            # Create a test upload job
            job_data = {
                "user_id": "test-user-123",
                "filename": "test_document.pdf",
                "content_type": "application/pdf",
                "file_size": 1024,
                "status": "uploaded"
            }
            
            response = await self.client.post(
                f"{self.staging_url}/rest/v1/upload_pipeline.upload_jobs",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key,
                    "Content-Type": "application/json"
                },
                json=job_data
            )
            
            if response.status_code == 201:
                data = response.json()
                job_id = data[0].get("job_id")
                self.print_status("PASS", f"Upload job created successfully - Job ID: {job_id}")
                return True
            else:
                self.print_status("FAIL", f"Upload job creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Upload simulation error: {e}")
            return False
    
    async def test_storage_bucket_operations(self):
        """Test 5: Storage Bucket Operations"""
        self.print_step(5, "STORAGE BUCKET OPERATIONS")
        
        try:
            # Test bucket listing
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
                    self.print_status("PASS", "Files bucket exists and accessible")
                    return True
                else:
                    self.print_status("FAIL", "Files bucket not found")
                    return False
            else:
                self.print_status("FAIL", f"Bucket listing failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Bucket operations error: {e}")
            return False
    
    async def test_worker_processing_simulation(self):
        """Test 6: Worker Processing Simulation"""
        self.print_step(6, "WORKER PROCESSING SIMULATION")
        
        try:
            # Check if there are any jobs in the queue
            response = await self.client.get(
                f"{self.staging_url}/rest/v1/upload_pipeline.upload_jobs?select=*&status=eq.uploaded&limit=5",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )
            
            if response.status_code == 200:
                jobs = response.json()
                self.print_status("PASS", f"Worker can access job queue - Found {len(jobs)} jobs")
                
                if jobs:
                    job = jobs[0]
                    self.print_status("PASS", f"Sample job: {job.get('job_id')} - Status: {job.get('status')}")
                
                return True
            else:
                self.print_status("FAIL", f"Worker processing simulation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("FAIL", f"Worker processing error: {e}")
            return False
    
    async def run_api_tests(self):
        """Run all API tests"""
        self.print_header("STAGING API FUNCTIONALITY TEST")
        print(f"API URL: {self.api_url}")
        print(f"Staging URL: {self.staging_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("Storage Access via API", self.test_storage_access_via_api),
            ("Upload Pipeline Schema", self.test_upload_pipeline_schema),
            ("Document Upload Simulation", self.test_document_upload_simulation),
            ("Storage Bucket Operations", self.test_storage_bucket_operations),
            ("Worker Processing Simulation", self.test_worker_processing_simulation)
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
        self.print_header("API TEST SUMMARY")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"📊 Test Results: {passed}/{total} passed")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        # Critical tests
        critical_tests = ["API Health Check", "Storage Access via API", "Upload Pipeline Schema"]
        critical_failures = [test_name for test_name, result in results 
                           if not result and test_name in critical_tests]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_failures:
                print(f"   - {issue}")
        else:
            print(f"\n🎉 ALL CRITICAL TESTS PASSED!")
        
        if passed == total:
            print(f"\n🎉 API FUNCTIONALITY TEST COMPLETED SUCCESSFULLY!")
            print(f"   Staging API is ready for document processing")
        else:
            print(f"\n⚠️  API FUNCTIONALITY TEST PARTIALLY SUCCESSFUL")
            print(f"   Review failed tests and address issues")
        
        return passed == total

async def main():
    """Main test execution"""
    async with StagingAPITester() as tester:
        success = await tester.run_api_tests()
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
