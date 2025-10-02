#!/usr/bin/env python3
"""
Comprehensive Staging Environment Test
Tests API service and worker functionality after migration deployment
"""

import os
import sys
import asyncio
import asyncpg
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def load_staging_environment():
    """Load staging environment variables"""
    env_file = Path(".env.staging")
    if not env_file.exists():
        print("❌ Staging environment file (.env.staging) not found!")
        return None
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    return env_vars

class StagingEnvironmentTester:
    """Comprehensive testing of staging environment"""
    
    def __init__(self):
        self.env_vars = load_staging_environment()
        self.api_base_url = self.env_vars.get('NEXT_PUBLIC_API_BASE_URL', 'https://insurance-navigator-staging-api.onrender.com')
        self.database_url = self.env_vars.get('DATABASE_URL')
        self.test_results = {}
        
    async def test_database_connectivity(self):
        """Test database connectivity and basic queries"""
        print("🔍 Testing database connectivity...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            # Test basic query
            version = await conn.fetchval("SELECT version()")
            print(f"  ✅ Database connected: {version[:50]}...")
            
            # Test auth.users access
            user_count = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
            print(f"  ✅ auth.users accessible: {user_count} users")
            
            # Test documents schema
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents.documents")
            print(f"  ✅ documents.documents accessible: {doc_count} documents")
            
            # Test upload_pipeline schema
            upload_doc_count = await conn.fetchval("SELECT COUNT(*) FROM upload_pipeline.documents")
            print(f"  ✅ upload_pipeline.documents accessible: {upload_doc_count} documents")
            
            # Verify public.users is gone
            try:
                await conn.fetchval("SELECT COUNT(*) FROM public.users")
                print("  ❌ public.users still exists!")
                return False
            except Exception:
                print("  ✅ public.users successfully removed")
            
            await conn.close()
            self.test_results['database'] = True
            return True
            
        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
            self.test_results['database'] = False
            return False
    
    async def test_api_health(self):
        """Test API service health endpoint"""
        print("🔍 Testing API service health...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.api_base_url}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ API health check passed: {data.get('status', 'unknown')}")
                    self.test_results['api_health'] = True
                    return True
                else:
                    print(f"  ❌ API health check failed: {response.status_code}")
                    self.test_results['api_health'] = False
                    return False
                    
        except Exception as e:
            print(f"  ❌ API health test failed: {e}")
            self.test_results['api_health'] = False
            return False
    
    async def test_authentication_flow(self):
        """Test user registration and authentication"""
        print("🔍 Testing authentication flow...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test user registration
                test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
                test_password = "TestPassword123!"
                
                signup_data = {
                    "email": test_email,
                    "password": test_password,
                    "consent_version": "1.0",
                    "consent_timestamp": datetime.now().isoformat()
                }
                
                print(f"  📝 Testing registration for: {test_email}")
                signup_response = await client.post(f"{self.api_base_url}/auth/signup", json=signup_data)
                
                if signup_response.status_code == 201:
                    signup_result = signup_response.json()
                    print("  ✅ User registration successful")
                    
                    # Test login
                    login_data = {
                        "email": test_email,
                        "password": test_password
                    }
                    
                    login_response = await client.post(f"{self.api_base_url}/auth/login", json=login_data)
                    
                    if login_response.status_code == 200:
                        login_result = login_response.json()
                        print("  ✅ User login successful")
                        
                        # Test protected endpoint
                        token = login_result.get('access_token')
                        if token:
                            headers = {"Authorization": f"Bearer {token}"}
                            user_response = await client.get(f"{self.api_base_url}/auth/user", headers=headers)
                            
                            if user_response.status_code == 200:
                                user_data = user_response.json()
                                print(f"  ✅ Protected endpoint accessible: {user_data.get('email', 'unknown')}")
                                self.test_results['authentication'] = True
                                return True
                            else:
                                print(f"  ❌ Protected endpoint failed: {user_response.status_code}")
                        else:
                            print("  ❌ No access token received")
                    else:
                        print(f"  ❌ Login failed: {login_response.status_code}")
                else:
                    print(f"  ❌ Registration failed: {signup_response.status_code}")
                    print(f"    Response: {signup_response.text}")
                
                self.test_results['authentication'] = False
                return False
                
        except Exception as e:
            print(f"  ❌ Authentication test failed: {e}")
            self.test_results['authentication'] = False
            return False
    
    async def test_document_upload(self):
        """Test document upload functionality"""
        print("🔍 Testing document upload...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # First, create a test user
                test_email = f"upload_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
                test_password = "TestPassword123!"
                
                signup_data = {
                    "email": test_email,
                    "password": test_password,
                    "consent_version": "1.0",
                    "consent_timestamp": datetime.now().isoformat()
                }
                
                signup_response = await client.post(f"{self.api_base_url}/auth/signup", json=signup_data)
                
                if signup_response.status_code != 201:
                    print(f"  ❌ Failed to create test user: {signup_response.status_code}")
                    self.test_results['document_upload'] = False
                    return False
                
                # Get access token
                login_response = await client.post(f"{self.api_base_url}/auth/login", json={
                    "email": test_email,
                    "password": test_password
                })
                
                if login_response.status_code != 200:
                    print(f"  ❌ Failed to login test user: {login_response.status_code}")
                    self.test_results['document_upload'] = False
                    return False
                
                token = login_response.json().get('access_token')
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test document upload endpoint
                upload_response = await client.get(f"{self.api_base_url}/api/upload-pipeline/upload/limits", headers=headers)
                
                if upload_response.status_code == 200:
                    print("  ✅ Document upload endpoint accessible")
                    self.test_results['document_upload'] = True
                    return True
                else:
                    print(f"  ❌ Document upload endpoint failed: {upload_response.status_code}")
                    self.test_results['document_upload'] = False
                    return False
                    
        except Exception as e:
            print(f"  ❌ Document upload test failed: {e}")
            self.test_results['document_upload'] = False
            return False
    
    async def test_worker_functionality(self):
        """Test worker service functionality"""
        print("🔍 Testing worker functionality...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test worker functionality via upload pipeline endpoint
                health_response = await client.get(f"{self.api_base_url}/api/upload-pipeline/test-endpoint")
                
                if health_response.status_code == 200:
                    print("  ✅ Worker health check passed")
                    self.test_results['worker'] = True
                    return True
                else:
                    print(f"  ❌ Worker health check failed: {health_response.status_code}")
                    self.test_results['worker'] = False
                    return False
                    
        except Exception as e:
            print(f"  ❌ Worker test failed: {e}")
            self.test_results['worker'] = False
            return False
    
    async def test_storage_access(self):
        """Test storage bucket access"""
        print("🔍 Testing storage access...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            # Check storage buckets
            buckets = await conn.fetch("SELECT id, name FROM storage.buckets")
            print(f"  ✅ Storage buckets accessible: {len(buckets)} buckets")
            
            for bucket in buckets:
                print(f"    - {bucket['id']} ({bucket['name']})")
            
            # Check storage policies
            policies = await conn.fetch("""
                SELECT schemaname, tablename, policyname 
                FROM pg_policies 
                WHERE schemaname = 'storage'
            """)
            
            print(f"  ✅ Storage policies: {len(policies)} policies")
            
            await conn.close()
            self.test_results['storage'] = True
            return True
            
        except Exception as e:
            print(f"  ❌ Storage test failed: {e}")
            self.test_results['storage'] = False
            return False
    
    async def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting Staging Environment Tests")
        print("=" * 50)
        
        tests = [
            ("Database Connectivity", self.test_database_connectivity),
            ("API Health", self.test_api_health),
            ("Authentication Flow", self.test_authentication_flow),
            ("Document Upload", self.test_document_upload),
            ("Worker Functionality", self.test_worker_functionality),
            ("Storage Access", self.test_storage_access)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 30)
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"  ❌ Test failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Staging environment is ready.")
            return True
        else:
            print("💥 Some tests failed. Review issues before production deployment.")
            return False

def main():
    """Main function"""
    tester = StagingEnvironmentTester()
    return asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
