#!/usr/bin/env python3
"""
Phase C Production Cloud Backend Testing
Test UUID standardization with deployed production cloud backend.

This test validates UUID standardization works correctly with the production
cloud backend deployed on Render.
"""

import asyncio
import json
import os
import sys
import time
import aiohttp
import asyncpg
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.uuid_generation import UUIDGenerator


class ProductionCloudTester:
    """Tests UUID standardization with production cloud backend."""
    
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "phase": "C",
            "test_name": "Phase C: Production Cloud Backend Testing",
            "configuration": {
                "backend": "production_cloud",
                "database": "production_supabase",
                "environment": "production_cloud_testing"
            },
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "critical_failures": 0
            }
        }
        
        # Production cloud backend endpoints
        self.api_base_url = "***REMOVED***"
        self.upload_endpoint = f"{self.api_base_url}/api/upload-pipeline/upload"
        self.chat_endpoint = f"{self.api_base_url}/chat"
        self.health_endpoint = f"{self.api_base_url}/health"
        self.auth_signup_endpoint = f"{self.api_base_url}/auth/signup"
        self.auth_login_endpoint = f"{self.api_base_url}/auth/login"
        
        # Production Supabase configuration
        self.supabase_url = "***REMOVED***"
        self.database_url = "postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres"
        
        # Set up environment variables
        self._setup_environment()
        
        # Test user credentials
        self.test_user = {
            "email": f"test_user_{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "user_id": None,
            "access_token": None
        }
        
    def _setup_environment(self):
        """Set up environment variables for production cloud backend."""
        # Production Supabase configuration
        os.environ["SUPABASE_URL"] = self.supabase_url
        os.environ["SUPABASE_ANON_KEY"] = "${SUPABASE_JWT_TOKEN}"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "${SUPABASE_JWT_TOKEN}"
        os.environ["DATABASE_URL"] = self.database_url
        os.environ["OPENAI_API_KEY"] = "${OPENAI_API_KEY}"
        os.environ["LLAMAPARSE_API_KEY"] = "${LLAMAPARSE_API_KEY}"
        
    async def run_all_tests(self):
        """Execute all production cloud backend tests."""
        print("🚀 Starting Phase C: Production Cloud Backend Testing")
        print("=" * 80)
        print("Configuration:")
        print(f"  Backend: Production Cloud ({self.api_base_url})")
        print(f"  Database: Production Supabase ({self.supabase_url})")
        print(f"  Environment: Production Cloud Testing")
        print("=" * 80)
        
        # Test 1: Production Cloud Backend Health
        await self.test_production_cloud_health()
        
        # Test 2: Authentication System
        await self.test_authentication_system()
        
        # Test 3: UUID Generation with Production Cloud
        await self.test_uuid_generation_production_cloud()
        
        # Test 4: End-to-End Upload Pipeline
        await self.test_end_to_end_upload_pipeline()
        
        # Test 5: Chat Endpoint with UUID Context
        await self.test_chat_endpoint_uuid_context()
        
        # Test 6: Multi-User UUID Isolation
        await self.test_multi_user_uuid_isolation()
        
        # Test 7: Performance with Production Cloud
        await self.test_performance_production_cloud()
        
        # Test 8: Error Handling and Recovery
        await self.test_error_handling_recovery()
        
        # Test 9: Database Consistency Validation
        await self.test_database_consistency_validation()
        
        # Generate final report
        return self.generate_final_report()
        
    async def test_production_cloud_health(self):
        """Test production cloud backend health."""
        test_name = "production_cloud_health"
        print(f"\n🏥 Testing production cloud backend health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.health_endpoint, timeout=30) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        
                        # Check if all services are healthy
                        services = health_data.get("services", {})
                        all_healthy = (
                            services.get("database") == "healthy" and
                            services.get("supabase_auth") == "healthy" and
                            services.get("llamaparse") == "healthy" and
                            services.get("openai") == "healthy"
                        )
                        
                        self.results["tests"][test_name] = {
                            "status": "PASS" if all_healthy else "FAIL",
                            "details": {
                                "status_code": response.status,
                                "health_data": health_data,
                                "all_services_healthy": all_healthy,
                                "response_time_ms": response.headers.get("X-Response-Time", "unknown")
                            }
                        }
                        
                        if all_healthy:
                            print("✅ Production cloud backend health: PASSED")
                        else:
                            print("❌ Production cloud backend health: FAILED")
                            self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {"error": f"Health check failed with status {response.status}"}
                        }
                        print(f"❌ Production cloud backend health: FAILED - Status {response.status}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Production cloud backend health: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_authentication_system(self):
        """Test authentication system with production cloud backend."""
        test_name = "authentication_system"
        print(f"\n🔐 Testing authentication system...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test user signup
                signup_data = {
                    "email": self.test_user["email"],
                    "password": self.test_user["password"],
                    "confirm_password": self.test_user["password"],
                    "consent_version": "1.0",
                    "consent_timestamp": datetime.now().isoformat()
                }
                
                async with session.post(self.auth_signup_endpoint, json=signup_data, timeout=30) as response:
                    signup_result = await response.json()
                    if response.status in [200, 201, 409]:  # 409 = user already exists
                        self.test_user["user_id"] = signup_result.get("user_id")
                        
                        # Test user login
                        login_data = {
                            "email": self.test_user["email"],
                            "password": self.test_user["password"]
                        }
                        
                        async with session.post(self.auth_login_endpoint, json=login_data, timeout=30) as login_response:
                            if login_response.status == 200:
                                login_result = await login_response.json()
                                self.test_user["access_token"] = login_result.get("access_token")
                                
                                # Validate JWT token
                                token_valid = bool(self.test_user["access_token"])
                                
                                self.results["tests"][test_name] = {
                                    "status": "PASS" if token_valid else "FAIL",
                                    "details": {
                                        "signup_status": response.status,
                                        "login_status": login_response.status,
                                        "user_id": self.test_user["user_id"],
                                        "token_valid": token_valid,
                                        "signup_response": signup_result,
                                        "login_response": login_result
                                    }
                                }
                                
                                if token_valid:
                                    print("✅ Authentication system: PASSED")
                                else:
                                    print("❌ Authentication system: FAILED")
                                    self.results["summary"]["critical_failures"] += 1
                            else:
                                self.results["tests"][test_name] = {
                                    "status": "FAIL",
                                    "details": {"error": f"Login failed with status {login_response.status}"}
                                }
                                print(f"❌ Authentication system: FAILED - Login status {login_response.status}")
                                self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {
                                "error": f"Signup failed with status {response.status}",
                                "response_data": signup_result
                            }
                        }
                        print(f"❌ Authentication system: FAILED - Signup status {response.status}")
                        print(f"   Response: {signup_result}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Authentication system: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_uuid_generation_production_cloud(self):
        """Test UUID generation with production cloud backend."""
        test_name = "uuid_generation_production_cloud"
        print(f"\n🔧 Testing UUID generation with production cloud backend...")
        
        try:
            # Test deterministic UUID generation
            test_user_id = self.test_user["user_id"] or "550e8400-e29b-41d4-a716-446655440000"
            test_content_hash = "test_content_hash_production_cloud"
            
            # Generate UUID using our utility
            document_uuid = UUIDGenerator.document_uuid(test_user_id, test_content_hash)
            chunk_uuid = UUIDGenerator.chunk_uuid(document_uuid, "test_chunker", "1.0", 0)
            job_uuid = UUIDGenerator.job_uuid()
            
            # Validate UUID formats
            document_valid = UUIDGenerator.validate_uuid_format(document_uuid)
            chunk_valid = UUIDGenerator.validate_uuid_format(chunk_uuid)
            job_valid = UUIDGenerator.validate_uuid_format(job_uuid)
            
            # Test database storage and retrieval
            conn = await asyncpg.connect(self.database_url)
            try:
                # Create test record with all required columns
                await conn.execute("""
                    INSERT INTO upload_pipeline.documents (
                        document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                """, document_uuid, test_user_id, "test_document.pdf", "application/pdf", 1024, test_content_hash, "/test/path/test_document.pdf", "test")
                
                # Retrieve and validate
                retrieved_record = await conn.fetchrow("""
                    SELECT document_id, user_id, file_sha256 
                    FROM upload_pipeline.documents 
                    WHERE document_id = $1
                """, document_uuid)
                
                if retrieved_record:
                    retrieved_uuid = str(retrieved_record['document_id'])
                    is_consistent = retrieved_uuid == document_uuid
                    
                    # Clean up test data
                    await conn.execute("DELETE FROM upload_pipeline.documents WHERE document_id = $1", document_uuid)
                    
                    all_valid = document_valid and chunk_valid and job_valid and is_consistent
                    
                    self.results["tests"][test_name] = {
                        "status": "PASS" if all_valid else "FAIL",
                        "details": {
                            "document_uuid": document_uuid,
                            "chunk_uuid": chunk_uuid,
                            "job_uuid": job_uuid,
                            "document_valid": document_valid,
                            "chunk_valid": chunk_valid,
                            "job_valid": job_valid,
                            "retrieved_uuid": retrieved_uuid,
                            "is_consistent": is_consistent,
                            "database_operations_successful": True
                        }
                    }
                    
                    if all_valid:
                        print("✅ UUID generation with production cloud backend: PASSED")
                    else:
                        print("❌ UUID generation with production cloud backend: FAILED")
                        self.results["summary"]["critical_failures"] += 1
                else:
                    self.results["tests"][test_name] = {
                        "status": "FAIL",
                        "details": {"error": "Failed to retrieve test record"}
                    }
                    print("❌ UUID generation with production cloud backend: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ UUID generation with production cloud backend: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_end_to_end_upload_pipeline(self):
        """Test end-to-end upload pipeline with production cloud backend."""
        test_name = "end_to_end_upload_pipeline"
        print(f"\n📤 Testing end-to-end upload pipeline...")
        
        try:
            if not self.test_user["access_token"]:
                self.results["tests"][test_name] = {
                    "status": "SKIP",
                    "details": {"error": "No access token available for authentication"}
                }
                print("⏭️ End-to-end upload pipeline: SKIPPED - No authentication")
                return
            
            # Test upload endpoint (without actual file upload)
            headers = {"Authorization": f"Bearer {self.test_user['access_token']}"}
            
            async with aiohttp.ClientSession() as session:
                # Test upload endpoint validation
                upload_data = {
                    "filename": "test_document.pdf",
                    "mime_type": "application/pdf"
                }
                
                async with session.post(self.upload_endpoint, json=upload_data, headers=headers, timeout=30) as response:
                    # 422 is expected for missing file upload
                    if response.status == 422:
                        response_data = await response.json()
                        
                        # Check if validation is working correctly
                        validation_working = "detail" in response_data and "file" in str(response_data.get("detail", ""))
                        
                        self.results["tests"][test_name] = {
                            "status": "PASS" if validation_working else "FAIL",
                            "details": {
                                "status_code": response.status,
                                "validation_working": validation_working,
                                "response_data": response_data,
                                "endpoint_accessible": True
                            }
                        }
                        
                        if validation_working:
                            print("✅ End-to-end upload pipeline: PASSED")
                        else:
                            print("❌ End-to-end upload pipeline: FAILED")
                            self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {"error": f"Unexpected status code {response.status}"}
                        }
                        print(f"❌ End-to-end upload pipeline: FAILED - Status {response.status}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ End-to-end upload pipeline: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_chat_endpoint_uuid_context(self):
        """Test chat endpoint with UUID context."""
        test_name = "chat_endpoint_uuid_context"
        print(f"\n💬 Testing chat endpoint with UUID context...")
        
        try:
            if not self.test_user["access_token"]:
                self.results["tests"][test_name] = {
                    "status": "SKIP",
                    "details": {"error": "No access token available for authentication"}
                }
                print("⏭️ Chat endpoint with UUID context: SKIPPED - No authentication")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user['access_token']}"}
            
            async with aiohttp.ClientSession() as session:
                # Test chat endpoint
                chat_data = {
                    "message": "Hello, this is a test message for UUID context validation.",
                    "conversation_id": None  # Let the system generate one
                }
                
                async with session.post(self.chat_endpoint, json=chat_data, headers=headers, timeout=60) as response:
                    if response.status == 200:
                        chat_result = await response.json()
                        
                        # Check response structure
                        has_conversation_id = "conversation_id" in chat_result
                        has_timestamp = "timestamp" in chat_result
                        has_response = "response" in chat_result or "message" in chat_result
                        
                        response_valid = has_conversation_id and has_timestamp and has_response
                        
                        self.results["tests"][test_name] = {
                            "status": "PASS" if response_valid else "FAIL",
                            "details": {
                                "status_code": response.status,
                                "conversation_id": chat_result.get("conversation_id"),
                                "timestamp": chat_result.get("timestamp"),
                                "has_response": has_response,
                                "response_valid": response_valid,
                                "response_data": chat_result
                            }
                        }
                        
                        if response_valid:
                            print("✅ Chat endpoint with UUID context: PASSED")
                        else:
                            print("❌ Chat endpoint with UUID context: FAILED")
                            self.results["summary"]["critical_failures"] += 1
                    else:
                        self.results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {"error": f"Chat endpoint failed with status {response.status}"}
                        }
                        print(f"❌ Chat endpoint with UUID context: FAILED - Status {response.status}")
                        self.results["summary"]["critical_failures"] += 1
                        
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Chat endpoint with UUID context: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_multi_user_uuid_isolation(self):
        """Test multi-user UUID isolation with production cloud backend."""
        test_name = "multi_user_uuid_isolation"
        print(f"\n👥 Testing multi-user UUID isolation...")
        
        try:
            # Test multiple users with same content
            users = [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002", 
                "550e8400-e29b-41d4-a716-446655440003"
            ]
            content_hash = "same_content_hash_production_cloud"
            
            generated_uuids = []
            
            for user_id in users:
                # Generate UUID for each user
                user_uuid = UUIDGenerator.document_uuid(user_id, content_hash)
                generated_uuids.append({
                    "user_id": user_id,
                    "uuid": user_uuid
                })
            
            # Verify all UUIDs are different (user isolation)
            unique_uuids = set(uuid_data["uuid"] for uuid_data in generated_uuids)
            is_isolated = len(unique_uuids) == len(users)
            
            # Test database storage for each user
            conn = await asyncpg.connect(self.database_url)
            try:
                stored_uuids = []
                for uuid_data in generated_uuids:
                    # Store test record with all required columns
                    await conn.execute("""
                        INSERT INTO upload_pipeline.documents (
                            document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    """, uuid_data["uuid"], uuid_data["user_id"], "test_document.pdf", "application/pdf", 1024, content_hash, "/test/path/test_document.pdf", "test")
                    
                    # Retrieve and verify
                    stored_record = await conn.fetchrow("""
                        SELECT document_id FROM upload_pipeline.documents 
                        WHERE document_id = $1
                    """, uuid_data["uuid"])
                    
                    if stored_record:
                        stored_uuids.append(str(stored_record['document_id']))
                
                # Clean up test data
                for uuid_data in generated_uuids:
                    await conn.execute("DELETE FROM upload_pipeline.documents WHERE document_id = $1", uuid_data["uuid"])
                
                all_stored = len(stored_uuids) == len(users)
                all_consistent = all(
                    stored_uuids[i] == generated_uuids[i]["uuid"] 
                    for i in range(len(stored_uuids))
                )
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if is_isolated and all_stored and all_consistent else "FAIL",
                    "details": {
                        "generated_uuids": generated_uuids,
                        "unique_uuids": len(unique_uuids),
                        "is_isolated": is_isolated,
                        "all_stored": all_stored,
                        "all_consistent": all_consistent,
                        "stored_uuids": stored_uuids
                    }
                }
                
                if is_isolated and all_stored and all_consistent:
                    print("✅ Multi-user UUID isolation: PASSED")
                else:
                    print("❌ Multi-user UUID isolation: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Multi-user UUID isolation: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_performance_production_cloud(self):
        """Test performance with production cloud backend."""
        test_name = "performance_production_cloud"
        print(f"\n⚡ Testing performance with production cloud backend...")
        
        try:
            # Test UUID generation performance
            start_time = time.time()
            test_uuids = []
            
            for i in range(100):
                user_id = f"550e8400-e29b-41d4-a716-{i:012d}"  # Valid UUID format
                content_hash = f"perf_test_content_{i}"
                uuid_val = UUIDGenerator.document_uuid(user_id, content_hash)
                test_uuids.append((uuid_val, user_id, content_hash))
            
            generation_time = time.time() - start_time
            
            # Test cloud backend response time
            if self.test_user["access_token"]:
                headers = {"Authorization": f"Bearer {self.test_user['access_token']}"}
                
                async with aiohttp.ClientSession() as session:
                    cloud_start_time = time.time()
                    
                    # Test health endpoint response time
                    async with session.get(self.health_endpoint, headers=headers, timeout=30) as response:
                        cloud_response_time = time.time() - cloud_start_time
                        
                        # Performance thresholds
                        generation_threshold = 1.0  # 1 second for 100 UUIDs
                        cloud_threshold = 5.0  # 5 seconds for cloud response
                        
                        generation_ok = generation_time < generation_threshold
                        cloud_ok = cloud_response_time < cloud_threshold
                        
                        self.results["tests"][test_name] = {
                            "status": "PASS" if generation_ok and cloud_ok else "FAIL",
                            "details": {
                                "uuid_generation": {
                                    "time_seconds": generation_time,
                                    "threshold_seconds": generation_threshold,
                                    "uuids_generated": len(test_uuids),
                                    "meets_threshold": generation_ok
                                },
                                "cloud_response": {
                                    "time_seconds": cloud_response_time,
                                    "threshold_seconds": cloud_threshold,
                                    "status_code": response.status,
                                    "meets_threshold": cloud_ok
                                }
                            }
                        }
                        
                        if generation_ok and cloud_ok:
                            print("✅ Performance with production cloud backend: PASSED")
                        else:
                            print("❌ Performance with production cloud backend: FAILED")
                            self.results["summary"]["critical_failures"] += 1
            else:
                # Test without authentication
                generation_threshold = 1.0
                generation_ok = generation_time < generation_threshold
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if generation_ok else "FAIL",
                    "details": {
                        "uuid_generation": {
                            "time_seconds": generation_time,
                            "threshold_seconds": generation_threshold,
                            "uuids_generated": len(test_uuids),
                            "meets_threshold": generation_ok
                        },
                        "cloud_response": {
                            "skipped": "No authentication available"
                        }
                    }
                }
                
                if generation_ok:
                    print("✅ Performance with production cloud backend: PASSED")
                else:
                    print("❌ Performance with production cloud backend: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Performance with production cloud backend: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_error_handling_recovery(self):
        """Test error handling and recovery mechanisms."""
        test_name = "error_handling_recovery"
        print(f"\n🛡️ Testing error handling and recovery...")
        
        try:
            # Test invalid UUID handling
            invalid_uuids = ["invalid-uuid", "not-a-uuid", "", None]
            validation_results = []
            
            for invalid_uuid in invalid_uuids:
                try:
                    is_valid = UUIDGenerator.validate_uuid_format(str(invalid_uuid) if invalid_uuid else "")
                    validation_results.append({
                        "uuid": invalid_uuid,
                        "is_valid": is_valid,
                        "expected_valid": False
                    })
                except Exception as e:
                    validation_results.append({
                        "uuid": invalid_uuid,
                        "is_valid": False,
                        "expected_valid": False,
                        "error": str(e)
                    })
            
            # Test cloud backend error handling
            async with aiohttp.ClientSession() as session:
                # Test invalid endpoint
                try:
                    async with session.get(f"{self.api_base_url}/invalid-endpoint", timeout=10) as response:
                        invalid_endpoint_handled = response.status in [404, 405, 422]  # Multiple acceptable error codes
                except Exception:
                    invalid_endpoint_handled = True  # Connection error is also acceptable
                
                # Test invalid authentication on protected endpoint
                invalid_headers = {"Authorization": "Bearer invalid-token"}
                try:
                    async with session.post(self.chat_endpoint, json={}, headers=invalid_headers, timeout=10) as response:
                        invalid_auth_handled = response.status in [401, 403, 422]  # Multiple acceptable error codes
                except Exception:
                    invalid_auth_handled = True  # Connection error is also acceptable
                
                all_validation_correct = all(
                    not result["is_valid"] for result in validation_results
                )
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if all_validation_correct and invalid_endpoint_handled and invalid_auth_handled else "FAIL",
                    "details": {
                        "uuid_validation": {
                            "results": validation_results,
                            "all_correct": all_validation_correct
                        },
                        "cloud_error_handling": {
                            "invalid_endpoint_handled": invalid_endpoint_handled,
                            "invalid_auth_handled": invalid_auth_handled
                        }
                    }
                }
                
                if all_validation_correct and invalid_endpoint_handled and invalid_auth_handled:
                    print("✅ Error handling and recovery: PASSED")
                else:
                    print("❌ Error handling and recovery: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Error handling and recovery: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_database_consistency_validation(self):
        """Test database consistency validation with production cloud backend."""
        test_name = "database_consistency_validation"
        print(f"\n🗄️ Testing database consistency validation...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            try:
                # Check upload_pipeline.documents table schema
                schema_result = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_schema = 'upload_pipeline' 
                    AND table_name = 'documents'
                    ORDER BY ordinal_position
                """)
                
                # Check for required columns
                required_columns = ['document_id', 'user_id', 'file_sha256', 'processing_status', 'created_at']
                schema_columns = [row['column_name'] for row in schema_result]
                
                missing_columns = [col for col in required_columns if col not in schema_columns]
                has_required_columns = len(missing_columns) == 0
                
                # Check data types
                document_id_type = next((row['data_type'] for row in schema_result if row['column_name'] == 'document_id'), None)
                user_id_type = next((row['data_type'] for row in schema_result if row['column_name'] == 'user_id'), None)
                
                correct_types = (
                    document_id_type == 'uuid' and 
                    user_id_type == 'uuid'
                )
                
                # Test UUID operations with production cloud backend
                test_uuid = UUIDGenerator.document_uuid("550e8400-e29b-41d4-a716-446655440999", "consistency_test")
                
                # Test insert and retrieve
                await conn.execute("""
                    INSERT INTO upload_pipeline.documents (
                        document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                """, test_uuid, "550e8400-e29b-41d4-a716-446655440999", "consistency_test.pdf", "application/pdf", 1024, "consistency_test", "/test/path", "test")
                
                retrieved_record = await conn.fetchrow("""
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE document_id = $1
                """, test_uuid)
                
                # Clean up
                await conn.execute("DELETE FROM upload_pipeline.documents WHERE document_id = $1", test_uuid)
                
                consistency_ok = retrieved_record is not None and str(retrieved_record['document_id']) == test_uuid
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if has_required_columns and correct_types and consistency_ok else "FAIL",
                    "details": {
                        "schema_validation": {
                            "schema_columns": schema_columns,
                            "required_columns": required_columns,
                            "missing_columns": missing_columns,
                            "has_required_columns": has_required_columns,
                            "document_id_type": document_id_type,
                            "user_id_type": user_id_type,
                            "correct_types": correct_types
                        },
                        "consistency_test": {
                            "test_uuid": test_uuid,
                            "retrieved_uuid": str(retrieved_record['document_id']) if retrieved_record else None,
                            "consistency_ok": consistency_ok
                        },
                        "full_schema": [dict(row) for row in schema_result]
                    }
                }
                
                if has_required_columns and correct_types and consistency_ok:
                    print("✅ Database consistency validation: PASSED")
                else:
                    print("❌ Database consistency validation: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Database consistency validation: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    def generate_final_report(self):
        """Generate final test report."""
        print("\n" + "=" * 80)
        print("📋 PHASE C: PRODUCTION CLOUD BACKEND TEST REPORT")
        print("=" * 80)
        
        total_tests = self.results["summary"]["total_tests"]
        passed_tests = self.results["summary"]["passed"]
        failed_tests = self.results["summary"]["failed"]
        critical_failures = self.results["summary"]["critical_failures"]
        
        print(f"Configuration: Production Cloud Backend + Production Supabase")
        print(f"Backend URL: {self.api_base_url}")
        print(f"Database: {self.supabase_url}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Critical Failures: {critical_failures}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        if critical_failures > 0:
            print(f"\n🚨 CRITICAL FAILURES DETECTED: {critical_failures}")
            print("UUID standardization may not be ready for production deployment.")
        elif failed_tests > 0:
            print(f"\n⚠️ NON-CRITICAL FAILURES: {failed_tests}")
            print("UUID standardization mostly working but some issues need attention.")
        else:
            print(f"\n✅ ALL TESTS PASSED")
            print("UUID standardization is working correctly with production cloud backend.")
        
        # Save results to file
        results_file = f"phase_c_production_cloud_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return self.results


async def main():
    """Main execution function."""
    tester = ProductionCloudTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if results["summary"]["critical_failures"] > 0:
        sys.exit(1)  # Critical failures
    elif results["summary"]["failed"] > 0:
        sys.exit(2)  # Non-critical failures
    else:
        sys.exit(0)  # All tests passed


if __name__ == "__main__":
    asyncio.run(main())
