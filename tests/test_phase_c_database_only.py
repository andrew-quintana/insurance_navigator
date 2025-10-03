#!/usr/bin/env python3
"""
Phase C Database-Only Testing
Test UUID standardization with production Supabase database only.

This test focuses on database operations without requiring the local backend.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncpg
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.uuid_generation import UUIDGenerator


class DatabaseOnlyTester:
    """Tests UUID standardization with production Supabase database only."""
    
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "phase": "C",
            "test_name": "Phase C: Database-Only Testing",
            "configuration": {
                "backend": "none",
                "database": "production_supabase",
                "environment": "database_only_testing"
            },
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "critical_failures": 0
            }
        }
        
        # Production Supabase configuration
        self.supabase_url = "https://your-project.supabase.co"
        self.database_url = "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres"
        
        # Set up environment variables
        self._setup_environment()
        
    def _setup_environment(self):
        """Set up environment variables for production Supabase."""
        # Production Supabase configuration
        os.environ["SUPABASE_URL"] = self.supabase_url
        os.environ["SUPABASE_ANON_KEY"] = "${SUPABASE_JWT_TOKEN}"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "${SUPABASE_JWT_TOKEN}"
        os.environ["DATABASE_URL"] = self.database_url
        
    async def run_all_tests(self):
        """Execute all database-only tests."""
        print("🚀 Starting Phase C: Database-Only Testing")
        print("=" * 80)
        print("Configuration:")
        print(f"  Backend: None (database-only testing)")
        print(f"  Database: Production Supabase ({self.supabase_url})")
        print(f"  Environment: Database-Only Testing")
        print("=" * 80)
        
        # Test 1: Production Supabase Connection
        await self.test_production_supabase_connection()
        
        # Test 2: UUID Generation with Production Database
        await self.test_uuid_generation_production_database()
        
        # Test 3: Multi-User UUID Isolation
        await self.test_multi_user_uuid_isolation()
        
        # Test 4: Performance with Production Database
        await self.test_performance_production_database()
        
        # Test 5: Error Handling and Recovery
        await self.test_error_handling_recovery()
        
        # Test 6: Database Schema Validation
        await self.test_database_schema_validation()
        
        # Generate final report
        return self.generate_final_report()
        
    async def test_production_supabase_connection(self):
        """Test production Supabase database connection."""
        test_name = "production_supabase_connection"
        print(f"\n🗄️ Testing production Supabase connection...")
        
        try:
            # Test direct database connection
            conn = await asyncpg.connect(self.database_url)
            
            try:
                # Test basic query
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    # Test UUID table access
                    uuid_test_result = await conn.fetchval("SELECT uuid_generate_v4()")
                    uuid_valid = UUIDGenerator.validate_uuid_format(str(uuid_test_result))
                    
                    # Test upload_pipeline schema access
                    schema_check = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = 'upload_pipeline' 
                            AND table_name = 'documents'
                        )
                    """)
                    
                    self.results["tests"][test_name] = {
                        "status": "PASS" if uuid_valid and schema_check else "FAIL",
                        "details": {
                            "connection_successful": True,
                            "uuid_generation_working": uuid_valid,
                            "upload_pipeline_schema_exists": schema_check,
                            "test_uuid": str(uuid_test_result)
                        }
                    }
                    
                    if uuid_valid and schema_check:
                        print("✅ Production Supabase connection: PASSED")
                    else:
                        print("❌ Production Supabase connection: FAILED")
                        self.results["summary"]["critical_failures"] += 1
                else:
                    self.results["tests"][test_name] = {
                        "status": "FAIL",
                        "details": {"error": "Basic query failed"}
                    }
                    print("❌ Production Supabase connection: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Production Supabase connection: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_uuid_generation_production_database(self):
        """Test UUID generation with production database."""
        test_name = "uuid_generation_production_database"
        print(f"\n🔧 Testing UUID generation with production database...")
        
        try:
            # Test deterministic UUID generation
            test_user_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID
            test_content_hash = "test_content_hash_prod_db"
            
            # Generate UUID using our utility
            document_uuid = UUIDGenerator.document_uuid(test_user_id, test_content_hash)
            
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
                    is_valid_format = UUIDGenerator.validate_uuid_format(retrieved_uuid)
                    
                    # Test chunk UUID generation
                    chunk_uuid = UUIDGenerator.chunk_uuid(document_uuid, "test_chunker", "1.0", 0)
                    
                    # Clean up test data
                    await conn.execute("DELETE FROM upload_pipeline.documents WHERE document_id = $1", document_uuid)
                    
                    self.results["tests"][test_name] = {
                        "status": "PASS" if is_consistent and is_valid_format else "FAIL",
                        "details": {
                            "document_uuid": document_uuid,
                            "retrieved_uuid": retrieved_uuid,
                            "is_consistent": is_consistent,
                            "is_valid_format": is_valid_format,
                            "chunk_uuid": chunk_uuid,
                            "database_operations_successful": True
                        }
                    }
                    
                    if is_consistent and is_valid_format:
                        print("✅ UUID generation with production database: PASSED")
                    else:
                        print("❌ UUID generation with production database: FAILED")
                        self.results["summary"]["critical_failures"] += 1
                else:
                    self.results["tests"][test_name] = {
                        "status": "FAIL",
                        "details": {"error": "Failed to retrieve test record"}
                    }
                    print("❌ UUID generation with production database: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ UUID generation with production database: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_multi_user_uuid_isolation(self):
        """Test multi-user UUID isolation with production database."""
        test_name = "multi_user_uuid_isolation"
        print(f"\n👥 Testing multi-user UUID isolation...")
        
        try:
            # Test multiple users with same content
            users = [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002", 
                "550e8400-e29b-41d4-a716-446655440003"
            ]
            content_hash = "same_content_hash"
            
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
    
    async def test_performance_production_database(self):
        """Test performance with production database."""
        test_name = "performance_production_database"
        print(f"\n⚡ Testing performance with production database...")
        
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
            
            # Test database operations performance
            conn = await asyncpg.connect(self.database_url)
            try:
                db_start_time = time.time()
                
                # Test batch insert
                await conn.executemany("""
                    INSERT INTO upload_pipeline.documents (
                        document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                """, [(uuid_val, user_id, "test_document.pdf", "application/pdf", 1024, content_hash, "/test/path/test_document.pdf", "test") 
                      for uuid_val, user_id, content_hash in test_uuids[:10]])  # Insert first 10 for performance test
                
                db_operation_time = time.time() - db_start_time
                
                # Test query performance
                query_start_time = time.time()
                query_result = await conn.fetch("""
                    SELECT document_id, user_id 
                    FROM upload_pipeline.documents 
                    WHERE user_id::text LIKE '550e8400-e29b-41d4-a716-%'
                    LIMIT 10
                """)
                query_time = time.time() - query_start_time
                
                # Clean up test data
                await conn.execute("DELETE FROM upload_pipeline.documents WHERE user_id::text LIKE '550e8400-e29b-41d4-a716-%'")
                
                # Performance thresholds
                generation_threshold = 1.0  # 1 second for 100 UUIDs
                db_threshold = 2.0  # 2 seconds for database operations
                query_threshold = 1.0  # 1 second for query
                
                generation_ok = generation_time < generation_threshold
                db_ok = db_operation_time < db_threshold
                query_ok = query_time < query_threshold
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if generation_ok and db_ok and query_ok else "FAIL",
                    "details": {
                        "uuid_generation": {
                            "time_seconds": generation_time,
                            "threshold_seconds": generation_threshold,
                            "uuids_generated": len(test_uuids),
                            "meets_threshold": generation_ok
                        },
                        "database_operations": {
                            "time_seconds": db_operation_time,
                            "threshold_seconds": db_threshold,
                            "records_inserted": 10,
                            "meets_threshold": db_ok
                        },
                        "query_performance": {
                            "time_seconds": query_time,
                            "threshold_seconds": query_threshold,
                            "records_queried": len(query_result),
                            "meets_threshold": query_ok
                        }
                    }
                }
                
                if generation_ok and db_ok and query_ok:
                    print("✅ Performance with production database: PASSED")
                else:
                    print("❌ Performance with production database: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Performance with production database: ERROR - {str(e)}")
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
            
            # Test database error handling
            conn = await asyncpg.connect(self.database_url)
            try:
                # Test invalid UUID insertion
                try:
                    await conn.execute("""
                        INSERT INTO upload_pipeline.documents (
                            document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    """, "invalid-uuid", "550e8400-e29b-41d4-a716-446655440000", "test.pdf", "application/pdf", 1024, "test_hash", "/test/path", "test")
                    db_error_handling = False  # Should have failed
                except Exception as e:
                    db_error_handling = True  # Correctly handled error
                    db_error = str(e)
                
                # Test recovery from connection issues
                recovery_successful = True
                try:
                    # Test normal operation after error
                    test_uuid = UUIDGenerator.document_uuid("550e8400-e29b-41d4-a716-446655440999", "recovery_hash")
                    await conn.execute("""
                        INSERT INTO upload_pipeline.documents (
                            document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    """, test_uuid, "550e8400-e29b-41d4-a716-446655440999", "recovery.pdf", "application/pdf", 1024, "recovery_hash", "/test/path", "test")
                    
                    # Clean up
                    await conn.execute("DELETE FROM upload_pipeline.documents WHERE document_id = $1", test_uuid)
                    
                except Exception as e:
                    recovery_successful = False
                    recovery_error = str(e)
                
                all_validation_correct = all(
                    not result["is_valid"] for result in validation_results
                )
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if all_validation_correct and db_error_handling and recovery_successful else "FAIL",
                    "details": {
                        "uuid_validation": {
                            "results": validation_results,
                            "all_correct": all_validation_correct
                        },
                        "database_error_handling": {
                            "handled_correctly": db_error_handling,
                            "error": db_error if not db_error_handling else None
                        },
                        "recovery": {
                            "successful": recovery_successful,
                            "error": recovery_error if not recovery_successful else None
                        }
                    }
                }
                
                if all_validation_correct and db_error_handling and recovery_successful:
                    print("✅ Error handling and recovery: PASSED")
                else:
                    print("❌ Error handling and recovery: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
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
    
    async def test_database_schema_validation(self):
        """Test database schema validation."""
        test_name = "database_schema_validation"
        print(f"\n📋 Testing database schema validation...")
        
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
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if has_required_columns and correct_types else "FAIL",
                    "details": {
                        "schema_columns": schema_columns,
                        "required_columns": required_columns,
                        "missing_columns": missing_columns,
                        "has_required_columns": has_required_columns,
                        "document_id_type": document_id_type,
                        "user_id_type": user_id_type,
                        "correct_types": correct_types,
                        "full_schema": [dict(row) for row in schema_result]
                    }
                }
                
                if has_required_columns and correct_types:
                    print("✅ Database schema validation: PASSED")
                else:
                    print("❌ Database schema validation: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Database schema validation: ERROR - {str(e)}")
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    def generate_final_report(self):
        """Generate final test report."""
        print("\n" + "=" * 80)
        print("📋 PHASE C: DATABASE-ONLY TEST REPORT")
        print("=" * 80)
        
        total_tests = self.results["summary"]["total_tests"]
        passed_tests = self.results["summary"]["passed"]
        failed_tests = self.results["summary"]["failed"]
        critical_failures = self.results["summary"]["critical_failures"]
        
        print(f"Configuration: Database-Only Testing")
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
            print("UUID standardization is working correctly with production Supabase database.")
        
        # Save results to file
        results_file = f"phase_c_database_only_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return self.results


async def main():
    """Main execution function."""
    tester = DatabaseOnlyTester()
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
