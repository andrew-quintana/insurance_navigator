#!/usr/bin/env python3
"""
Phase C.1.1: Cloud Infrastructure UUID Validation
Test UUID generation in containerized cloud environment with deterministic generation,
multi-instance consistency, and environment variable validation.

This test validates that UUID generation works correctly in cloud deployment scenarios
including Docker containers, multiple instances, and cloud-specific constraints.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Tuple
import aiohttp
import asyncpg
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.uuid_generation import UUIDGenerator, SYSTEM_NAMESPACE


class CloudUUIDValidator:
    """Validates UUID generation in cloud environment scenarios."""
    
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "phase": "C.1.1",
            "test_name": "Cloud Infrastructure UUID Validation",
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "critical_failures": 0
            }
        }
        
    async def run_all_tests(self):
        """Execute all cloud infrastructure UUID validation tests."""
        print("🚀 Starting Phase C.1.1: Cloud Infrastructure UUID Validation")
        print("=" * 70)
        
        # Test 1: Container Environment UUID Generation
        await self.test_container_uuid_generation()
        
        # Test 2: Multi-Instance UUID Consistency
        await self.test_multi_instance_consistency()
        
        # Test 3: Environment Variable Impact
        await self.test_environment_variable_impact()
        
        # Test 4: Cloud Resource Constraints
        await self.test_cloud_resource_constraints()
        
        # Test 5: Database UUID Operations
        await self.test_cloud_database_uuid_operations()
        
        # Test 6: Performance Under Cloud Load
        await self.test_performance_under_cloud_load()
        
        # Generate final report
        self.generate_final_report()
        
    async def test_container_uuid_generation(self):
        """Test UUID generation in containerized environment."""
        test_name = "container_uuid_generation"
        print(f"\n📦 Testing UUID generation in containerized environment...")
        
        try:
            # Test deterministic generation in container
            test_cases = [
                ("user123", "abc123def456"),
                ("user456", "def456ghi789"),
                ("user789", "ghi789jkl012")
            ]
            
            results = []
            for user_id, content_hash in test_cases:
                # Generate UUID multiple times to ensure consistency
                uuids = []
                for _ in range(5):
                    uuid_val = UUIDGenerator.document_uuid(user_id, content_hash)
                    uuids.append(uuid_val)
                
                # All UUIDs should be identical (deterministic)
                is_consistent = len(set(uuids)) == 1
                results.append({
                    "user_id": user_id,
                    "content_hash": content_hash,
                    "generated_uuids": uuids,
                    "is_consistent": is_consistent,
                    "uuid": uuids[0] if is_consistent else None
                })
            
            # Validate namespace consistency
            namespace_consistent = all(
                UUIDGenerator.get_namespace() == str(SYSTEM_NAMESPACE)
                for _ in range(10)
            )
            
            # Test UUID format validation
            format_valid = all(
                UUIDGenerator.validate_uuid_format(result["uuid"])
                for result in results
                if result["uuid"]
            )
            
            all_consistent = all(result["is_consistent"] for result in results)
            
            self.results["tests"][test_name] = {
                "status": "PASS" if all_consistent and namespace_consistent and format_valid else "FAIL",
                "details": {
                    "test_cases": results,
                    "namespace_consistent": namespace_consistent,
                    "format_valid": format_valid,
                    "all_deterministic": all_consistent
                },
                "performance": {
                    "avg_generation_time_ms": self._measure_uuid_generation_time()
                }
            }
            
            if all_consistent and namespace_consistent and format_valid:
                print("✅ Container UUID generation: PASSED")
            else:
                print("❌ Container UUID generation: FAILED")
                self.results["summary"]["critical_failures"] += 1
                
        except Exception as e:
            print(f"❌ Container UUID generation: ERROR - {str(e)}")
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_multi_instance_consistency(self):
        """Test UUID consistency across multiple container instances."""
        test_name = "multi_instance_consistency"
        print(f"\n🔄 Testing UUID consistency across multiple instances...")
        
        try:
            # Simulate multiple container instances
            instances = []
            test_input = ("user_multi", "content_multi_test")
            
            # Generate UUIDs from "different instances" (simulated)
            for instance_id in range(5):
                # Simulate different container environments
                os.environ[f"CONTAINER_INSTANCE_{instance_id}"] = f"instance_{instance_id}"
                
                uuid_val = UUIDGenerator.document_uuid(*test_input)
                instances.append({
                    "instance_id": instance_id,
                    "uuid": uuid_val,
                    "environment": os.environ.get(f"CONTAINER_INSTANCE_{instance_id}")
                })
            
            # All instances should generate identical UUIDs
            unique_uuids = set(instance["uuid"] for instance in instances)
            is_consistent = len(unique_uuids) == 1
            
            # Test chunk UUID consistency across instances
            chunk_uuids = []
            document_id = instances[0]["uuid"] if instances else "test-doc-id"
            
            for instance_id in range(3):
                chunk_uuid = UUIDGenerator.chunk_uuid(document_id, "test_chunker", "1.0", 0)
                chunk_uuids.append(chunk_uuid)
            
            chunk_consistent = len(set(chunk_uuids)) == 1
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_consistent and chunk_consistent else "FAIL",
                "details": {
                    "instances": instances,
                    "document_uuid_consistent": is_consistent,
                    "chunk_uuid_consistent": chunk_consistent,
                    "unique_document_uuids": len(unique_uuids),
                    "chunk_uuids": chunk_uuids
                }
            }
            
            if is_consistent and chunk_consistent:
                print("✅ Multi-instance consistency: PASSED")
            else:
                print("❌ Multi-instance consistency: FAILED")
                self.results["summary"]["critical_failures"] += 1
                
        except Exception as e:
            print(f"❌ Multi-instance consistency: ERROR - {str(e)}")
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_environment_variable_impact(self):
        """Test that environment variables don't affect UUID generation."""
        test_name = "environment_variable_impact"
        print(f"\n🌍 Testing environment variable impact on UUID generation...")
        
        try:
            test_input = ("user_env", "content_env_test")
            baseline_uuid = UUIDGenerator.document_uuid(*test_input)
            
            # Test various environment variables that might affect UUID generation
            env_vars_to_test = [
                ("PYTHONPATH", "/different/path"),
                ("PYTHONUNBUFFERED", "0"),
                ("PYTHONDONTWRITEBYTECODE", "0"),
                ("ENVIRONMENT", "production"),
                ("LOG_LEVEL", "DEBUG"),
                ("CONTAINER_ID", "test-container-123"),
                ("POD_NAME", "test-pod-456"),
                ("NODE_NAME", "test-node-789")
            ]
            
            results = []
            for env_var, env_value in env_vars_to_test:
                # Set environment variable
                original_value = os.environ.get(env_var)
                os.environ[env_var] = env_value
                
                # Generate UUID with environment variable set
                uuid_with_env = UUIDGenerator.document_uuid(*test_input)
                
                # Restore original value
                if original_value is not None:
                    os.environ[env_var] = original_value
                else:
                    os.environ.pop(env_var, None)
                
                # Generate UUID without environment variable
                uuid_without_env = UUIDGenerator.document_uuid(*test_input)
                
                results.append({
                    "env_var": env_var,
                    "env_value": env_value,
                    "uuid_with_env": uuid_with_env,
                    "uuid_without_env": uuid_without_env,
                    "is_consistent": uuid_with_env == uuid_without_env == baseline_uuid
                })
            
            all_consistent = all(result["is_consistent"] for result in results)
            
            self.results["tests"][test_name] = {
                "status": "PASS" if all_consistent else "FAIL",
                "details": {
                    "baseline_uuid": baseline_uuid,
                    "env_var_tests": results,
                    "all_consistent": all_consistent
                }
            }
            
            if all_consistent:
                print("✅ Environment variable impact: PASSED")
            else:
                print("❌ Environment variable impact: FAILED")
                self.results["summary"]["critical_failures"] += 1
                
        except Exception as e:
            print(f"❌ Environment variable impact: ERROR - {str(e)}")
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_cloud_resource_constraints(self):
        """Test UUID generation under cloud resource constraints."""
        test_name = "cloud_resource_constraints"
        print(f"\n⚡ Testing UUID generation under cloud resource constraints...")
        
        try:
            # Test memory constraints (simulate limited memory)
            memory_results = []
            for i in range(1000):  # Generate many UUIDs to test memory usage
                uuid_val = UUIDGenerator.document_uuid(f"user_{i}", f"content_{i}")
                memory_results.append(uuid_val)
            
            # Test CPU constraints (simulate high CPU load)
            cpu_results = []
            start_time = time.time()
            while time.time() - start_time < 2:  # Run for 2 seconds under load
                uuid_val = UUIDGenerator.document_uuid("cpu_test", f"content_{time.time()}")
                cpu_results.append(uuid_val)
            
            # Test concurrent generation (simulate multiple requests)
            async def generate_concurrent_uuid(index):
                return UUIDGenerator.document_uuid(f"concurrent_{index}", f"content_{index}")
            
            concurrent_tasks = [generate_concurrent_uuid(i) for i in range(50)]
            concurrent_results = await asyncio.gather(*concurrent_tasks)
            
            # Validate all generated UUIDs are unique and properly formatted
            all_uuids = memory_results + cpu_results + concurrent_results
            unique_uuids = set(all_uuids)
            all_formatted = all(UUIDGenerator.validate_uuid_format(uuid) for uuid in all_uuids)
            
            # Test deterministic behavior under constraints
            test_input = ("constraint_test", "constraint_content")
            constraint_uuids = []
            for _ in range(10):
                constraint_uuids.append(UUIDGenerator.document_uuid(*test_input))
            
            constraint_consistent = len(set(constraint_uuids)) == 1
            
            self.results["tests"][test_name] = {
                "status": "PASS" if len(unique_uuids) == len(all_uuids) and all_formatted and constraint_consistent else "FAIL",
                "details": {
                    "memory_test": {
                        "uuids_generated": len(memory_results),
                        "unique_uuids": len(set(memory_results))
                    },
                    "cpu_test": {
                        "uuids_generated": len(cpu_results),
                        "unique_uuids": len(set(cpu_results))
                    },
                    "concurrent_test": {
                        "uuids_generated": len(concurrent_results),
                        "unique_uuids": len(set(concurrent_results))
                    },
                    "all_unique": len(unique_uuids) == len(all_uuids),
                    "all_formatted": all_formatted,
                    "constraint_consistent": constraint_consistent
                },
                "performance": {
                    "total_uuids_generated": len(all_uuids),
                    "avg_generation_time_ms": self._measure_uuid_generation_time()
                }
            }
            
            if len(unique_uuids) == len(all_uuids) and all_formatted and constraint_consistent:
                print("✅ Cloud resource constraints: PASSED")
            else:
                print("❌ Cloud resource constraints: FAILED")
                self.results["summary"]["critical_failures"] += 1
                
        except Exception as e:
            print(f"❌ Cloud resource constraints: ERROR - {str(e)}")
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_cloud_database_uuid_operations(self):
        """Test UUID operations with cloud database connections."""
        test_name = "cloud_database_uuid_operations"
        print(f"\n🗄️ Testing UUID operations with cloud database...")
        
        try:
            # Get database URL from environment
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                print("⚠️ No DATABASE_URL found, skipping database tests")
                self.results["tests"][test_name] = {
                    "status": "SKIP",
                    "reason": "No DATABASE_URL environment variable"
                }
                return
            
            # Test database connection and UUID operations
            conn = await asyncpg.connect(database_url)
            
            try:
                # Test UUID generation and storage
                test_user_id = "db_test_user"
                test_content_hash = "db_test_content_hash"
                document_uuid = UUIDGenerator.document_uuid(test_user_id, test_content_hash)
                
                # Test UUID format in database
                await conn.execute("""
                    CREATE TEMP TABLE uuid_test (
                        id SERIAL PRIMARY KEY,
                        document_uuid UUID,
                        user_id TEXT,
                        content_hash TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Insert UUID into database
                await conn.execute("""
                    INSERT INTO uuid_test (document_uuid, user_id, content_hash)
                    VALUES ($1, $2, $3)
                """, document_uuid, test_user_id, test_content_hash)
                
                # Retrieve and validate UUID
                row = await conn.fetchrow("""
                    SELECT document_uuid, user_id, content_hash
                    FROM uuid_test
                    WHERE user_id = $1
                """, test_user_id)
                
                retrieved_uuid = str(row['document_uuid'])
                is_consistent = retrieved_uuid == document_uuid
                is_valid_format = UUIDGenerator.validate_uuid_format(retrieved_uuid)
                
                # Test UUID-based queries
                query_result = await conn.fetchrow("""
                    SELECT COUNT(*) as count
                    FROM uuid_test
                    WHERE document_uuid = $1
                """, document_uuid)
                
                query_success = query_result['count'] == 1
                
                # Test chunk UUID operations
                chunk_uuid = UUIDGenerator.chunk_uuid(document_uuid, "test_chunker", "1.0", 0)
                
                await conn.execute("""
                    CREATE TEMP TABLE chunk_test (
                        id SERIAL PRIMARY KEY,
                        chunk_uuid UUID,
                        document_uuid UUID,
                        chunker TEXT,
                        version TEXT,
                        ordinal INTEGER
                    )
                """)
                
                await conn.execute("""
                    INSERT INTO chunk_test (chunk_uuid, document_uuid, chunker, version, ordinal)
                    VALUES ($1, $2, $3, $4, $5)
                """, chunk_uuid, document_uuid, "test_chunker", "1.0", 0)
                
                chunk_row = await conn.fetchrow("""
                    SELECT chunk_uuid, document_uuid
                    FROM chunk_test
                    WHERE chunk_uuid = $1
                """, chunk_uuid)
                
                chunk_consistent = str(chunk_row['chunk_uuid']) == chunk_uuid
                chunk_valid_format = UUIDGenerator.validate_uuid_format(str(chunk_row['chunk_uuid']))
                
                self.results["tests"][test_name] = {
                    "status": "PASS" if is_consistent and is_valid_format and query_success and chunk_consistent and chunk_valid_format else "FAIL",
                    "details": {
                        "document_uuid_test": {
                            "generated": document_uuid,
                            "retrieved": retrieved_uuid,
                            "consistent": is_consistent,
                            "valid_format": is_valid_format
                        },
                        "chunk_uuid_test": {
                            "generated": chunk_uuid,
                            "retrieved": str(chunk_row['chunk_uuid']),
                            "consistent": chunk_consistent,
                            "valid_format": chunk_valid_format
                        },
                        "query_test": {
                            "success": query_success,
                            "count": query_result['count']
                        }
                    },
                    "performance": {
                        "database_operation_time_ms": self._measure_database_operation_time()
                    }
                }
                
                if is_consistent and is_valid_format and query_success and chunk_consistent and chunk_valid_format:
                    print("✅ Cloud database UUID operations: PASSED")
                else:
                    print("❌ Cloud database UUID operations: FAILED")
                    self.results["summary"]["critical_failures"] += 1
                    
            finally:
                await conn.close()
                
        except Exception as e:
            print(f"❌ Cloud database UUID operations: ERROR - {str(e)}")
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    async def test_performance_under_cloud_load(self):
        """Test UUID generation performance under cloud load conditions."""
        test_name = "performance_under_cloud_load"
        print(f"\n📊 Testing UUID generation performance under cloud load...")
        
        try:
            # Test single-threaded performance
            single_threaded_times = []
            for _ in range(100):
                start_time = time.time()
                UUIDGenerator.document_uuid("perf_test", f"content_{time.time()}")
                end_time = time.time()
                single_threaded_times.append((end_time - start_time) * 1000)  # Convert to ms
            
            # Test concurrent performance (simulate multiple requests)
            async def concurrent_uuid_generation(index):
                start_time = time.time()
                uuid_val = UUIDGenerator.document_uuid(f"concurrent_{index}", f"content_{index}")
                end_time = time.time()
                return (end_time - start_time) * 1000, uuid_val
            
            concurrent_tasks = [concurrent_uuid_generation(i) for i in range(50)]
            concurrent_results = await asyncio.gather(*concurrent_tasks)
            concurrent_times = [result[0] for result in concurrent_results]
            concurrent_uuids = [result[1] for result in concurrent_results]
            
            # Test batch generation performance
            batch_start = time.time()
            batch_uuids = []
            for i in range(1000):
                batch_uuids.append(UUIDGenerator.document_uuid(f"batch_{i}", f"content_{i}"))
            batch_end = time.time()
            batch_time = (batch_end - batch_start) * 1000
            
            # Calculate performance metrics
            single_avg = sum(single_threaded_times) / len(single_threaded_times)
            concurrent_avg = sum(concurrent_times) / len(concurrent_times)
            batch_avg = batch_time / len(batch_uuids)
            
            # Performance thresholds (adjust based on requirements)
            single_threshold = 1.0  # 1ms per UUID
            concurrent_threshold = 2.0  # 2ms per UUID under load
            batch_threshold = 0.5  # 0.5ms per UUID in batch
            
            single_perf_ok = single_avg < single_threshold
            concurrent_perf_ok = concurrent_avg < concurrent_threshold
            batch_perf_ok = batch_avg < batch_threshold
            
            # Validate all UUIDs are unique and properly formatted
            all_uuids = concurrent_uuids + batch_uuids
            unique_uuids = set(all_uuids)
            all_formatted = all(UUIDGenerator.validate_uuid_format(uuid) for uuid in all_uuids)
            
            self.results["tests"][test_name] = {
                "status": "PASS" if single_perf_ok and concurrent_perf_ok and batch_perf_ok and len(unique_uuids) == len(all_uuids) and all_formatted else "FAIL",
                "details": {
                    "single_threaded": {
                        "avg_time_ms": single_avg,
                        "threshold_ms": single_threshold,
                        "meets_threshold": single_perf_ok,
                        "samples": len(single_threaded_times)
                    },
                    "concurrent": {
                        "avg_time_ms": concurrent_avg,
                        "threshold_ms": concurrent_threshold,
                        "meets_threshold": concurrent_perf_ok,
                        "samples": len(concurrent_times)
                    },
                    "batch": {
                        "avg_time_ms": batch_avg,
                        "threshold_ms": batch_threshold,
                        "meets_threshold": batch_perf_ok,
                        "total_uuids": len(batch_uuids)
                    },
                    "uniqueness": {
                        "total_uuids": len(all_uuids),
                        "unique_uuids": len(unique_uuids),
                        "all_unique": len(unique_uuids) == len(all_uuids)
                    },
                    "format_validation": {
                        "all_formatted": all_formatted
                    }
                }
            }
            
            if single_perf_ok and concurrent_perf_ok and batch_perf_ok and len(unique_uuids) == len(all_uuids) and all_formatted:
                print("✅ Performance under cloud load: PASSED")
            else:
                print("❌ Performance under cloud load: FAILED")
                self.results["summary"]["critical_failures"] += 1
                
        except Exception as e:
            print(f"❌ Performance under cloud load: ERROR - {str(e)}")
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            self.results["summary"]["critical_failures"] += 1
        
        self.results["summary"]["total_tests"] += 1
        if self.results["tests"].get(test_name, {}).get("status") == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    def _measure_uuid_generation_time(self, iterations: int = 100) -> float:
        """Measure average UUID generation time."""
        times = []
        for _ in range(iterations):
            start_time = time.time()
            UUIDGenerator.document_uuid("timing_test", f"content_{time.time()}")
            end_time = time.time()
            times.append((end_time - start_time) * 1000)  # Convert to ms
        return sum(times) / len(times)
    
    def _measure_database_operation_time(self) -> float:
        """Measure database operation time (placeholder)."""
        # This would measure actual database operations
        return 5.0  # Placeholder value
    
    def generate_final_report(self):
        """Generate final test report."""
        print("\n" + "=" * 70)
        print("📋 PHASE C.1.1 CLOUD INFRASTRUCTURE UUID VALIDATION REPORT")
        print("=" * 70)
        
        total_tests = self.results["summary"]["total_tests"]
        passed_tests = self.results["summary"]["passed"]
        failed_tests = self.results["summary"]["failed"]
        critical_failures = self.results["summary"]["critical_failures"]
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Critical Failures: {critical_failures}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        if critical_failures > 0:
            print(f"\n🚨 CRITICAL FAILURES DETECTED: {critical_failures}")
            print("These failures may block Phase 3 cloud deployment.")
        elif failed_tests > 0:
            print(f"\n⚠️ NON-CRITICAL FAILURES: {failed_tests}")
            print("These failures should be addressed but may not block deployment.")
        else:
            print(f"\n✅ ALL TESTS PASSED")
            print("Cloud infrastructure UUID validation successful.")
        
        # Save results to file
        results_file = f"phase_c_cloud_infrastructure_uuid_validation_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return self.results


async def main():
    """Main execution function."""
    validator = CloudUUIDValidator()
    results = await validator.run_all_tests()
    
    # Exit with appropriate code
    if results["summary"]["critical_failures"] > 0:
        sys.exit(1)  # Critical failures
    elif results["summary"]["failed"] > 0:
        sys.exit(2)  # Non-critical failures
    else:
        sys.exit(0)  # All tests passed


if __name__ == "__main__":
    asyncio.run(main())
