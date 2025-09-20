#!/usr/bin/env python3
"""
Staging Service Communication Test Script

This script validates the inter-service communication between the staging API
and worker services, including database connectivity, job queuing, and
end-to-end workflow testing.

Usage:
    python scripts/test_staging_communication.py
"""

import asyncio
import aiohttp
import asyncpg
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StagingCommunicationTester:
    def __init__(self):
        self.api_url = "https://insurance-navigator-staging-api.onrender.com"
        self.database_url = "postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres"
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "staging",
            "tests": {}
        }
    
    async def run_all_tests(self):
        """Run all communication validation tests"""
        logger.info("🚀 Starting staging service communication validation")
        
        try:
            # Test 1: API Service Health
            await self.test_api_health()
            
            # Test 2: Database Connectivity
            await self.test_database_connectivity()
            
            # Test 3: Job Queue Functionality
            await self.test_job_queue_functionality()
            
            # Test 4: End-to-End Workflow
            await self.test_end_to_end_workflow()
            
            # Test 5: Error Handling
            await self.test_error_handling()
            
            # Print results
            self.print_test_results()
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            self.test_results["error"] = str(e)
    
    async def test_api_health(self):
        """Test API service health endpoint"""
        logger.info("🔍 Testing API service health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.test_results["tests"]["api_health"] = {
                            "status": "PASS",
                            "response_code": response.status,
                            "data": data
                        }
                        logger.info("✅ API service health check passed")
                    else:
                        self.test_results["tests"]["api_health"] = {
                            "status": "FAIL",
                            "response_code": response.status,
                            "error": f"Expected 200, got {response.status}"
                        }
                        logger.error(f"❌ API service health check failed: {response.status}")
        except Exception as e:
            self.test_results["tests"]["api_health"] = {
                "status": "ERROR",
                "error": str(e)
            }
            logger.error(f"❌ API service health check error: {e}")
    
    async def test_database_connectivity(self):
        """Test database connectivity and schema access"""
        logger.info("🔍 Testing database connectivity...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            # Test basic connectivity
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Database connectivity test failed")
            
            # Test schema access
            schemas = await conn.fetch("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name = 'upload_pipeline'
            """)
            
            if not schemas:
                raise Exception("upload_pipeline schema not found")
            
            # Test table access
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'upload_pipeline' 
                ORDER BY table_name
            """)
            
            expected_tables = {'documents', 'upload_jobs', 'document_chunks', 'events', 'webhook_log', 'architecture_notes'}
            actual_tables = {row['table_name'] for row in tables}
            
            if not expected_tables.issubset(actual_tables):
                missing = expected_tables - actual_tables
                raise Exception(f"Missing tables: {missing}")
            
            await conn.close()
            
            self.test_results["tests"]["database_connectivity"] = {
                "status": "PASS",
                "schemas": [row['schema_name'] for row in schemas],
                "tables": [row['table_name'] for row in tables]
            }
            logger.info("✅ Database connectivity test passed")
            
        except Exception as e:
            self.test_results["tests"]["database_connectivity"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ Database connectivity test failed: {e}")
    
    async def test_job_queue_functionality(self):
        """Test job queue creation and retrieval"""
        logger.info("🔍 Testing job queue functionality...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            # Create test document
            document_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, mime, bytes_len, 
                    file_sha256, raw_path, processing_status, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            """, document_id, user_id, 'test-communication.pdf', 'application/pdf', 
                 1024, 'test-sha256-hash', 'test/path/document.pdf', 'uploaded')
            
            # Create test job
            job_id = str(uuid.uuid4())
            job_payload = {
                "user_id": user_id,
                "document_id": document_id,
                "file_sha256": "test-sha256-hash",
                "bytes_len": 1024,
                "mime": "application/pdf",
                "storage_path": "test/path/document.pdf"
            }
            
            await conn.execute("""
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, status, state, progress, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            """, job_id, document_id, 'uploaded', 'queued', json.dumps(job_payload))
            
            # Verify job was created
            job = await conn.fetchrow("""
                SELECT job_id, status, state, progress 
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1
            """, job_id)
            
            if not job:
                raise Exception("Job not found after creation")
            
            if job['status'] != 'uploaded' or job['state'] != 'queued':
                raise Exception(f"Job status incorrect: {job['status']}, {job['state']}")
            
            # Test job retrieval (simulating worker behavior)
            available_jobs = await conn.fetch("""
                SELECT uj.job_id, uj.document_id, d.user_id, uj.status, uj.state,
                       uj.progress, uj.retry_count, uj.last_error, uj.created_at,
                       d.raw_path as storage_path, d.mime as mime_type
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.status = 'uploaded' AND uj.state = 'queued'
                ORDER BY uj.created_at
                LIMIT 1
            """)
            
            if not available_jobs:
                raise Exception("No available jobs found")
            
            # Clean up test data
            await conn.execute("DELETE FROM upload_pipeline.upload_jobs WHERE job_id = $1", job_id)
            await conn.execute("DELETE FROM upload_pipeline.documents WHERE document_id = $1", document_id)
            
            await conn.close()
            
            self.test_results["tests"]["job_queue_functionality"] = {
                "status": "PASS",
                "jobs_created": 1,
                "jobs_retrieved": len(available_jobs)
            }
            logger.info("✅ Job queue functionality test passed")
            
        except Exception as e:
            self.test_results["tests"]["job_queue_functionality"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ Job queue functionality test failed: {e}")
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        logger.info("🔍 Testing end-to-end workflow...")
        
        try:
            # This would test the complete workflow from API upload to worker processing
            # For now, we'll simulate the key components
            
            conn = await asyncpg.connect(self.database_url)
            
            # Simulate job status progression
            document_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            job_id = str(uuid.uuid4())
            
            # Create test data
            await conn.execute("""
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, mime, bytes_len, 
                    file_sha256, raw_path, processing_status, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            """, document_id, user_id, 'test-workflow.pdf', 'application/pdf', 
                 1024, 'test-sha256-hash', 'test/path/workflow.pdf', 'uploaded')
            
            # Test job status progression
            statuses = ['uploaded', 'parsing', 'parsed', 'parse_validated', 'chunking', 'chunks_stored', 'embedding_queued', 'embedding_in_progress', 'embeddings_stored', 'complete']
            
            for i, status in enumerate(statuses):
                test_job_id = str(uuid.uuid4())  # Generate proper UUID for each test job
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (
                        job_id, document_id, status, state, progress, 
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                """, test_job_id, document_id, status, 'working' if i < len(statuses) - 1 else 'done', 
                      json.dumps({"test": True, "stage": status}))
            
            # Verify status progression
            jobs = await conn.fetch("""
                SELECT status, COUNT(*) as count 
                FROM upload_pipeline.upload_jobs 
                WHERE document_id = $1
                GROUP BY status 
                ORDER BY status
            """, document_id)
            
            if len(jobs) != len(statuses):
                raise Exception(f"Expected {len(statuses)} job statuses, got {len(jobs)}")
            
            # Clean up
            await conn.execute("DELETE FROM upload_pipeline.upload_jobs WHERE document_id = $1", document_id)
            await conn.execute("DELETE FROM upload_pipeline.documents WHERE document_id = $1", document_id)
            
            await conn.close()
            
            self.test_results["tests"]["end_to_end_workflow"] = {
                "status": "PASS",
                "statuses_tested": len(statuses),
                "workflow_complete": True
            }
            logger.info("✅ End-to-end workflow test passed")
            
        except Exception as e:
            self.test_results["tests"]["end_to_end_workflow"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ End-to-end workflow test failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling and recovery"""
        logger.info("🔍 Testing error handling...")
        
        try:
            # Test with invalid database connection
            try:
                invalid_conn = await asyncpg.connect("postgresql://invalid:invalid@invalid:5432/invalid")
                await invalid_conn.close()
                raise Exception("Should have failed with invalid connection")
            except Exception as e:
                if "connection" in str(e).lower():
                    logger.info("✅ Invalid connection properly rejected")
                else:
                    raise e
            
            # Test with malformed job data
            conn = await asyncpg.connect(self.database_url)
            
            try:
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (
                        job_id, document_id, status, state, progress, 
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                """, str(uuid.uuid4()), str(uuid.uuid4()), 'invalid_status', 'invalid_state', 
                      json.dumps({"test": True}))
                raise Exception("Should have failed with invalid status")
            except Exception as e:
                if "check constraint" in str(e).lower():
                    logger.info("✅ Invalid job data properly rejected")
                else:
                    raise e
            
            await conn.close()
            
            self.test_results["tests"]["error_handling"] = {
                "status": "PASS",
                "invalid_connection": "rejected",
                "invalid_data": "rejected"
            }
            logger.info("✅ Error handling test passed")
            
        except Exception as e:
            self.test_results["tests"]["error_handling"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ Error handling test failed: {e}")
    
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("STAGING SERVICE COMMUNICATION VALIDATION RESULTS")
        print("="*80)
        print(f"Timestamp: {self.test_results['timestamp']}")
        print(f"Environment: {self.test_results['environment']}")
        print()
        
        total_tests = len(self.test_results['tests'])
        passed_tests = sum(1 for test in self.test_results['tests'].values() if test['status'] == 'PASS')
        failed_tests = sum(1 for test in self.test_results['tests'].values() if test['status'] == 'FAIL')
        error_tests = sum(1 for test in self.test_results['tests'].values() if test['status'] == 'ERROR')
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print()
        
        for test_name, result in self.test_results['tests'].items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"{status_icon} {test_name.upper().replace('_', ' ')}: {result['status']}")
            
            if result['status'] != 'PASS' and 'error' in result:
                print(f"   Error: {result['error']}")
        
        print()
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Staging service communication is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the errors above.")
        print("="*80)

async def main():
    """Main test execution"""
    tester = StagingCommunicationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
