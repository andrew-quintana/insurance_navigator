#!/usr/bin/env python3
"""
Phase 3 Complete Database Flow Test
Test the complete upload pipeline by monitoring database status changes:
1. Create upload job through API service
2. Monitor worker picking up and processing the job
3. Track status changes in the database
"""

import asyncio
import httpx
import json
import time
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, List
import logging
import asyncpg

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'phase3_database_flow_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cloud service URLs
API_BASE_URL = "***REMOVED***"
DATABASE_URL = "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

class Phase3DatabaseFlowTester:
    """Test complete upload pipeline with database monitoring."""
    
    def __init__(self):
        self.api_url = API_BASE_URL
        self.database_url = DATABASE_URL
        self.test_results = []
        self.start_time = time.time()
        self.db_connection = None
        
        logger.info("=" * 80)
        logger.info("🚀 PHASE 3 COMPLETE DATABASE FLOW TEST INITIALIZED")
        logger.info("=" * 80)
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"Database URL: {self.database_url[:50]}...")
        logger.info(f"Test Start Time: {datetime.now().isoformat()}")
        logger.info("=" * 80)
    
    async def connect_to_database(self) -> bool:
        """Connect to the production database."""
        logger.info("🔗 Connecting to production database...")
        
        try:
            self.db_connection = await asyncpg.connect(
                self.database_url,
                statement_cache_size=0
            )
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def disconnect_from_database(self):
        """Disconnect from the database."""
        if self.db_connection:
            await self.db_connection.close()
            logger.info("🔌 Database connection closed")
    
    def _generate_mock_pdf_content(self, title: str) -> bytes:
        """Generate mock PDF content for testing."""
        pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
({title}) Tj
72 700 Td
(Phase 3 Database Flow Test) Tj
72 680 Td
(Generated: {datetime.now().isoformat()}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
400
%%EOF"""
        return pdf_content.encode('utf-8')
    
    async def get_auth_token(self) -> str:
        """Get authentication token for API access."""
        logger.info("🔐 Getting authentication token...")
        
        try:
            # Try to login with existing user
            login_data = {
                "email": "phase3-test@example.com",
                "password": "Phase3Test123!"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_url}/auth/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    token = result.get("access_token")
                    logger.info(f"✅ Login successful, token: {token[:50]}...")
                    return token
                else:
                    logger.warning(f"⚠️ Login failed: {response.status_code}, trying signup...")
                    
                    # Try to create new user
                    signup_data = {
                        "email": "phase3-test@example.com",
                        "password": "Phase3Test123!",
                        "name": "Phase 3 Test User",
                        "consent_version": "1.0",
                        "consent_timestamp": "2025-09-07T00:00:00Z"
                    }
                    
                    response = await client.post(
                        f"{self.api_url}/auth/signup",
                        json=signup_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        token = result.get("access_token")
                        logger.info(f"✅ Signup successful, token: {token[:50]}...")
                        return token
                    else:
                        logger.error(f"❌ Both login and signup failed: {response.text}")
                        return None
                        
        except Exception as e:
            logger.error(f"💥 Authentication error: {e}")
            return None
    
    async def create_upload_job_manually(self) -> Dict[str, Any]:
        """Create an upload job manually in the database to simulate API creation."""
        logger.info("📝 Creating upload job manually in database...")
        
        try:
            # Generate test data
            document_id = str(uuid.uuid4())
            job_id = str(uuid.uuid4())
            # Use an existing user_id from the database
            user_id = "e6114f0c-df44-41e6-a5df-33d69f95bab1"
            filename = "phase3_database_flow_test.pdf"
            pdf_content = self._generate_mock_pdf_content("Phase 3 Database Flow Test")
            file_hash = hashlib.sha256(pdf_content).hexdigest()
            raw_path = f"files/user/{user_id}/raw/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}.pdf"
            
            logger.info(f"📄 Document ID: {document_id}")
            logger.info(f"📄 Job ID: {job_id}")
            logger.info(f"📄 File hash: {file_hash}")
            logger.info(f"📄 Raw path: {raw_path}")
            
            # Create document record
            await self.db_connection.execute("""
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, mime, bytes_len, 
                    file_sha256, raw_path, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """, document_id, user_id, filename, "application/pdf", len(pdf_content), file_hash, raw_path)
            
            logger.info("✅ Document record created")
            
            # Create upload job record
            job_payload = {
                "filename": filename,
                "mime": "application/pdf",
                "bytes_len": len(pdf_content),
                "sha256": file_hash,
                "raw_path": raw_path,
                "ocr": False
            }
            
            await self.db_connection.execute("""
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, status, state, 
                    progress, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            """, job_id, document_id, "uploaded", "queued", json.dumps({"percent": 0}))
            
            logger.info("✅ Upload job record created")
            
            return {
                "document_id": document_id,
                "job_id": job_id,
                "user_id": user_id,
                "filename": filename,
                "file_hash": file_hash,
                "raw_path": raw_path,
                "status": "uploaded",
                "state": "queued"
            }
            
        except Exception as e:
            logger.error(f"💥 Failed to create upload job: {e}")
            return None
    
    async def monitor_job_status_changes(self, job_id: str, max_wait_minutes: int = 10) -> List[Dict[str, Any]]:
        """Monitor job status changes in the database."""
        logger.info(f"👀 Monitoring job status changes for job: {job_id}")
        logger.info(f"⏰ Max wait time: {max_wait_minutes} minutes")
        
        status_history = []
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 5  # Check every 5 seconds
        
        try:
            while time.time() - start_time < max_wait_seconds:
                elapsed = time.time() - start_time
                
                # Query current job status
                job = await self.db_connection.fetchrow("""
                    SELECT job_id, document_id, status, state, progress, 
                           last_error, retry_count, created_at, updated_at
                    FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, job_id)
                
                if job:
                    current_status = {
                        "timestamp": time.time(),
                        "elapsed": elapsed,
                        "job_id": str(job["job_id"]),
                        "document_id": str(job["document_id"]),
                        "status": job["status"],
                        "state": job["state"],
                        "progress": job["progress"],
                        "retry_count": job["retry_count"],
                        "last_error": job["last_error"],
                        "updated_at": job["updated_at"]
                    }
                    
                    # Check if status changed
                    if not status_history or status_history[-1]["status"] != current_status["status"]:
                        logger.info(f"📊 Status change detected: {current_status['status']} (state: {current_status['state']})")
                        if current_status["last_error"]:
                            logger.warning(f"⚠️ Last error: {current_status['last_error']}")
                    
                    status_history.append(current_status)
                    
                    # Check if job is complete or failed
                    if current_status["status"] == "complete":
                        logger.info("🎉 Job completed successfully!")
                        break
                    elif current_status["state"] == "deadletter":
                        logger.error(f"❌ Job failed: {current_status['last_error']}")
                        break
                    elif current_status["status"] in ["uploaded", "parse_queued", "parsed", "parse_validated", 
                                                    "chunking", "chunks_stored", "embedding_queued", 
                                                    "embedding_in_progress", "embeddings_stored"]:
                        logger.info(f"⏳ Job in progress: {current_status['status']} (progress: {current_status['progress']}%)")
                    else:
                        logger.info(f"📊 Job status: {current_status['status']} (state: {current_status['state']})")
                else:
                    logger.warning(f"⚠️ Job not found: {job_id}")
                    break
                
                await asyncio.sleep(check_interval)
            
            if time.time() - start_time >= max_wait_seconds:
                logger.warning(f"⏰ Job monitoring timed out after {max_wait_minutes} minutes")
            
            return status_history
            
        except Exception as e:
            logger.error(f"💥 Job monitoring error: {e}")
            return status_history
    
    async def check_database_tables(self) -> Dict[str, Any]:
        """Check the state of database tables."""
        logger.info("🗄️ Checking database tables...")
        
        try:
            # Check documents table
            documents_count = await self.db_connection.fetchval("SELECT COUNT(*) FROM upload_pipeline.documents")
            logger.info(f"📄 Documents table: {documents_count} records")
            
            # Check upload_jobs table
            jobs_count = await self.db_connection.fetchval("SELECT COUNT(*) FROM upload_pipeline.upload_jobs")
            logger.info(f"📋 Upload jobs table: {jobs_count} records")
            
            # Check job status distribution
            job_statuses = await self.db_connection.fetch("""
                SELECT status, state, COUNT(*) as count
                FROM upload_pipeline.upload_jobs 
                GROUP BY status, state
                ORDER BY count DESC
            """)
            
            logger.info("📊 Job status distribution:")
            for row in job_statuses:
                logger.info(f"   {row['status']} ({row['state']}): {row['count']} jobs")
            
            # Check recent jobs
            recent_jobs = await self.db_connection.fetch("""
                SELECT job_id, document_id, status, state, created_at
                FROM upload_pipeline.upload_jobs 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            logger.info("📋 Recent jobs:")
            for row in recent_jobs:
                logger.info(f"   {row['job_id']}: {row['status']} ({row['state']}) - {row['created_at']}")
            
            return {
                "documents_count": documents_count,
                "jobs_count": jobs_count,
                "job_statuses": [dict(row) for row in job_statuses],
                "recent_jobs": [dict(row) for row in recent_jobs]
            }
            
        except Exception as e:
            logger.error(f"💥 Database check error: {e}")
            return {"error": str(e)}
    
    async def test_complete_database_flow(self) -> Dict[str, Any]:
        """Test the complete database flow."""
        logger.info("🔍 TESTING COMPLETE DATABASE FLOW")
        logger.info("-" * 50)
        
        flow_start_time = time.time()
        flow_stages = []
        
        try:
            # Stage 1: Connect to database
            logger.info("🔗 STAGE 1: Database Connection")
            if not await self.connect_to_database():
                return {
                    "test": "complete_database_flow",
                    "status": "failed",
                    "failed_stage": "database_connection",
                    "error": "Failed to connect to database"
                }
            
            flow_stages.append({"stage": "database_connection", "status": "passed"})
            
            # Stage 2: Check initial database state
            logger.info("🗄️ STAGE 2: Initial Database State")
            initial_state = await self.check_database_tables()
            flow_stages.append({"stage": "initial_database_state", "status": "passed", "data": initial_state})
            
            # Stage 3: Create upload job
            logger.info("📝 STAGE 3: Create Upload Job")
            job_data = await self.create_upload_job_manually()
            if not job_data:
                return {
                    "test": "complete_database_flow",
                    "status": "failed",
                    "failed_stage": "create_upload_job",
                    "error": "Failed to create upload job"
                }
            
            flow_stages.append({"stage": "create_upload_job", "status": "passed", "data": job_data})
            
            # Stage 4: Monitor job processing
            logger.info("👀 STAGE 4: Monitor Job Processing")
            status_history = await self.monitor_job_status_changes(job_data["job_id"], max_wait_minutes=5)
            flow_stages.append({"stage": "monitor_job_processing", "status": "passed", "data": status_history})
            
            # Stage 5: Check final database state
            logger.info("🗄️ STAGE 5: Final Database State")
            final_state = await self.check_database_tables()
            flow_stages.append({"stage": "final_database_state", "status": "passed", "data": final_state})
            
            # Calculate total flow time
            total_time = time.time() - flow_start_time
            
            # Analyze results
            final_status = status_history[-1]["status"] if status_history else "unknown"
            final_state = status_history[-1]["state"] if status_history else "unknown"
            
            success = final_status == "complete"
            
            logger.info("🔍 DATABASE FLOW ANALYSIS:")
            logger.info(f"   - Total flow time: {total_time:.3f}s")
            logger.info(f"   - Final status: {final_status}")
            logger.info(f"   - Final state: {final_state}")
            logger.info(f"   - Status changes: {len(status_history)}")
            logger.info(f"   - Success: {success}")
            
            return {
                "test": "complete_database_flow",
                "status": "passed" if success else "failed",
                "total_time": total_time,
                "final_status": final_status,
                "final_state": final_state,
                "status_changes": len(status_history),
                "stages": flow_stages,
                "job_data": job_data,
                "status_history": status_history,
                "initial_state": initial_state,
                "final_state": final_state
            }
            
        except Exception as e:
            logger.error(f"💥 Complete database flow test error: {e}")
            return {
                "test": "complete_database_flow",
                "status": "error",
                "error": str(e),
                "stages": flow_stages
            }
        finally:
            await self.disconnect_from_database()
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete Phase 3 database flow test."""
        logger.info("🚀 STARTING PHASE 3 COMPLETE DATABASE FLOW TEST")
        logger.info("=" * 80)
        
        all_results = []
        
        # Test 1: Complete Database Flow
        logger.info("🔍 TEST 1: Complete Database Flow")
        flow_result = await self.test_complete_database_flow()
        all_results.append(flow_result)
        
        # Calculate summary
        total_tests = len(all_results)
        passed_tests = len([r for r in all_results if r.get("status") == "passed"])
        failed_tests = len([r for r in all_results if r.get("status") in ["failed", "error"]])
        
        total_time = time.time() - self.start_time
        
        # Final RCA Analysis
        logger.info("🔍 FINAL RCA ANALYSIS")
        logger.info("=" * 50)
        logger.info(f"Total test time: {total_time:.3f} seconds")
        logger.info(f"Tests passed: {passed_tests}/{total_tests}")
        logger.info(f"Tests failed: {failed_tests}/{total_tests}")
        logger.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "total_time": total_time,
            "test_results": all_results,
            "timestamp": datetime.now().isoformat(),
            "api_url": self.api_url,
            "database_url": self.database_url
        }
        
        # Print final results
        logger.info("📊 PHASE 3 COMPLETE DATABASE FLOW TEST RESULTS")
        logger.info("=" * 80)
        
        for i, result in enumerate(all_results, 1):
            status_icon = "✅" if result["status"] == "passed" else "❌"
            logger.info(f"{status_icon} Test {i}: {result['test']} - {result['status']}")
            
            if "final_status" in result:
                logger.info(f"   📊 Final status: {result['final_status']}")
                logger.info(f"   📊 Final state: {result['final_state']}")
                logger.info(f"   📊 Status changes: {result['status_changes']}")
        
        logger.info(f"\n🎯 Overall Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"⏱️  Total Test Time: {summary['total_time']:.3f} seconds")
        
        if summary['success_rate'] >= 75:
            logger.info("🎉 PHASE 3 DATABASE FLOW: SUCCESS!")
        elif summary['success_rate'] >= 50:
            logger.info("⚠️ PHASE 3 DATABASE FLOW: PARTIAL SUCCESS")
        else:
            logger.info("❌ PHASE 3 DATABASE FLOW: FAILED")
        
        return summary

async def main():
    """Main test function."""
    tester = Phase3DatabaseFlowTester()
    results = await tester.run_complete_test()
    
    # Save results to file
    results_file = f"phase3_database_flow_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["success_rate"] >= 75:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
