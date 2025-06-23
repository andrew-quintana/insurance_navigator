#!/usr/bin/env python3
"""
End-to-End Document Processing Validation
Tests the complete document processing pipeline including:
1. Current status check
2. Queue management validation
3. Processing job triggers
4. Progress monitoring
"""

import asyncio
import asyncpg
import aiohttp
import json
import os
import tempfile
from datetime import datetime, timezone
import requests
import time
from typing import Dict, Any, Optional

# Configuration
DATABASE_URL = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
SUPABASE_URL = 'https://jhrespvvhbnloxrieycf.supabase.co'
SERVICE_ROLE_KEY = '***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpocmVzcHZ2aGJubG94cmleeeWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDIyNDgzNiwiZXhwIjoyMDQ1ODAwODM2fQ.m4lgWEY6lUQ7O4_iHp5QYHY-nxRxNSMpWZJR4S7xCZo'

BASE_URL = "***REMOVED***"
TEST_EMAIL = "validator@example.com"
TEST_PASSWORD = "validator123"
TEST_NAME = "End-to-End Validator"

class DocumentProcessingValidator:
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "unknown"
        }

    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log test results"""
        self.test_results["tests"][test_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }

        # Print colored output
        color = "\033[92m" if status == "PASS" else "\033[91m" if status == "FAIL" else "\033[93m"
        reset = "\033[0m"
        print(f"{color}[{status}]{reset} {test_name}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")

    def authenticate(self) -> bool:
        """Authenticate and get token"""
        try:
            # Try login first
            login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
            response = requests.post(
                f"{self.base_url}/login",
                json=login_data,
                timeout=10
            )

            if response.status_code == 200:
                self.auth_token = response.json()["access_token"]
                self.log_test("Authentication - Login", "PASS", {
                    "email": TEST_EMAIL,
                    "token_received": bool(self.auth_token)
                })
                return True
            elif response.status_code == 401:
                # User doesn't exist, try registration
                register_data = {
                    "full_name": TEST_NAME,
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
                response = requests.post(
                    f"{self.base_url}/register",
                    json=register_data,
                    timeout=10
                )

                if response.status_code in [200, 201]:
                    self.auth_token = response.json()["access_token"]
                    self.log_test("Authentication - Registration", "PASS", {
                        "email": TEST_EMAIL,
                        "token_received": bool(self.auth_token)
                    })
                    return True
                else:
                    self.log_test("Authentication - Registration", "FAIL", {
                        "status_code": response.status_code,
                        "error": response.text[:200]
                    })
                    return False
            else:
                self.log_test("Authentication - Login", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })
                return False

        except Exception as e:
            self.log_test("Authentication", "FAIL", {"error": str(e)})
            return False

    def test_regulatory_document_upload(self) -> bool:
        """Test regulatory document upload and processing"""
        try:
            payload = {
                "source_url": "https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf",
                "title": "E2E Test - Regulatory Document Sample",
                "document_type": "regulatory_document",
                "jurisdiction": "federal",
                "program": ["medicaid"],
                "metadata": {
                    "test_type": "end_to_end_validation",
                    "workflow": "regulatory_upload",
                    "timestamp": datetime.now().isoformat()
                }
            }

            response = requests.post(
                f"{self.base_url}/api/documents/upload-regulatory",
                json=payload,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30  # Allow time for processing
            )

            if response.status_code == 200:
                result = response.json()
                self.log_test("Regulatory Document Upload", "PASS", {
                    "document_id": result.get("document_id"),
                    "file_path": result.get("file_path"),
                    "processing_status": result.get("status"),
                    "vector_count": result.get("vector_count", 0)
                })
                return True
            else:
                self.log_test("Regulatory Document Upload", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:500]
                })
                return False

        except Exception as e:
            self.log_test("Regulatory Document Upload", "FAIL", {"error": str(e)})
            return False

    def test_user_document_upload(self) -> bool:
        """Test user document upload and processing"""
        try:
            # Test file upload with multipart/form-data
            request_data = {
                "document_type": "user_document",
                "source_type": "file_upload",
                "title": "E2E Test - User Document Sample",
                "metadata": {
                    "test_type": "end_to_end_validation",
                    "workflow": "user_upload",
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Create a test file
            test_content = b"""Sample Insurance Policy Document

Deductible: $1,000
Copay: $20
Out-of-pocket maximum: $5,000
Coinsurance: 20%
Plan type: PPO
Network: In-network benefits available

This is a sample document for testing the user upload workflow.
It contains insurance-related keywords to trigger policy extraction.
"""

            response = requests.post(
                f"{self.base_url}/api/documents/upload-unified",
                files={'file': ('test_policy.txt', test_content, 'text/plain')},
                data={'request_data': json.dumps(request_data)},
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30  # Allow time for processing
            )

            if response.status_code == 200:
                result = response.json()
                self.log_test("User Document Upload", "PASS", {
                    "document_id": result.get("document_id"),
                    "file_path": result.get("file_path"),
                    "processing_status": result.get("status"),
                    "vector_count": result.get("vector_count", 0)
                })
                return True
            else:
                self.log_test("User Document Upload", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:500]
                })
                return False

        except Exception as e:
            self.log_test("User Document Upload", "FAIL", {"error": str(e)})
            return False

    def test_document_search(self) -> bool:
        """Test document search functionality"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": "What is my deductible?"},
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                self.log_test("Document Search", "PASS", {
                    "response_received": True,
                    "message_length": len(result.get("message", "")),
                    "has_sources": bool(result.get("sources"))
                })
                return True
            else:
                self.log_test("Document Search", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:300]
                })
                return False

        except Exception as e:
            self.log_test("Document Search", "FAIL", {"error": str(e)})
            return False

    def test_document_listing(self) -> bool:
        """Test document listing functionality"""
        try:
            response = requests.get(
                f"{self.base_url}/api/documents/list",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                self.log_test("Document Listing", "PASS", {
                    "document_count": len(result.get("documents", [])),
                    "has_user_docs": any(doc.get("document_type") == "user_document" for doc in result.get("documents", [])),
                    "has_regulatory_docs": any(doc.get("document_type") == "regulatory_document" for doc in result.get("documents", []))
                })
                return True
            else:
                self.log_test("Document Listing", "FAIL", {
                    "status_code": response.status_code,
                    "error": response.text[:300]
                })
                return False

        except Exception as e:
            self.log_test("Document Listing", "FAIL", {"error": str(e)})
            return False

    def run_validation(self):
        """Run comprehensive validation"""
        print("\n🚀 Starting End-to-End Document Processing Validation")
        print(f"📍 Testing against: {self.base_url}")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Authentication
        if not self.authenticate():
            print("\n❌ Authentication failed - stopping validation")
            return

        # Core workflow tests
        tests = [
            ("Regulatory Document Upload", self.test_regulatory_document_upload),
            ("User Document Upload", self.test_user_document_upload),
            ("Document Search", self.test_document_search),
            ("Document Listing", self.test_document_listing)
        ]

        total_tests = len(tests)
        passed_tests = 0

        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            if test_func():
                passed_tests += 1
            time.sleep(1)  # Brief pause between tests

        # Calculate results
        success_rate = (passed_tests / total_tests) * 100

        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")

        # Overall status
        if success_rate == 100:
            status = "🟢 ALL SYSTEMS OPERATIONAL"
            self.test_results["overall_status"] = "success"
        elif success_rate >= 75:
            status = "🟡 MOSTLY FUNCTIONAL - Minor Issues"
            self.test_results["overall_status"] = "partial"
        else:
            status = "🔴 SIGNIFICANT ISSUES DETECTED"
            self.test_results["overall_status"] = "failure"

        print(f"\n🎯 Status: {status}")
        print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Save results
        with open(f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n📄 Detailed results saved to validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

async def main():
    """Run complete end-to-end validation"""
    print("🔍 End-to-End Document Processing Validation")
    print("=" * 60)
    
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        # Step 1: Check current system status
        await check_current_status(conn)
        
        # Step 2: Validate queue management
        await validate_queue_management(conn)
        
        # Step 3: Check processing functions
        await check_processing_functions(conn)
        
        # Step 4: Test job processor
        await test_job_processor()
        
        # Step 5: Test manual job creation
        await test_manual_job_creation(conn)
        
        # Step 6: Monitor queue activity
        await monitor_queue_activity(conn)
        
        print("\n✅ End-to-end validation complete!")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    finally:
        if conn:
            await conn.close()

async def check_current_status(conn):
    """Check current status of documents and jobs"""
    print("\n🔍 Step 1: Current System Status")
    print("-" * 40)
    
    # Check documents by status
    doc_stats = await conn.fetch("""
        SELECT 
            status, 
            COUNT(*) as count,
            MIN(created_at) as oldest,
            MAX(created_at) as newest
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    """)
    
    print("📄 Document Status Distribution:")
    total_docs = sum(row['count'] for row in doc_stats)
    for row in doc_stats:
        percentage = (row['count'] / total_docs * 100) if total_docs > 0 else 0
        print(f"   {row['status']}: {row['count']} ({percentage:.1f}%)")
        if row['status'] == 'pending':
            print(f"      Oldest pending: {row['oldest']}")
    
    # Check processing jobs
    job_stats = await conn.fetch("""
        SELECT 
            job_type,
            status, 
            COUNT(*) as count,
            AVG(retry_count) as avg_retries
        FROM processing_jobs 
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY job_type, status
        ORDER BY job_type, status
    """)
    
    print("\n📋 Processing Jobs (24h):")
    if job_stats:
        for row in job_stats:
            print(f"   {row['job_type']} → {row['status']}: {row['count']} (avg retries: {row['avg_retries']:.1f})")
    else:
        print("   No processing jobs found in last 24 hours")
    
    # Check for stuck jobs
    stuck_jobs = await conn.fetch("""
        SELECT 
            pj.id, d.original_filename, pj.job_type, pj.status,
            EXTRACT(EPOCH FROM (NOW() - pj.created_at)) / 60 as age_minutes
        FROM processing_jobs pj
        JOIN documents d ON pj.document_id = d.id
        WHERE pj.status = 'running' AND pj.created_at < NOW() - INTERVAL '30 minutes'
        ORDER BY pj.created_at
    """)
    
    if stuck_jobs:
        print(f"\n⚠️  Stuck Jobs ({len(stuck_jobs)}):")
        for job in stuck_jobs:
            print(f"   {job['job_type']} for {job['original_filename']} (running {job['age_minutes']:.1f}m)")
    else:
        print("\n✅ No stuck jobs found")

async def validate_queue_management(conn):
    """Validate queue management functions and triggers"""
    print("\n🔧 Step 2: Queue Management Validation")
    print("-" * 40)
    
    # Check if required functions exist
    functions_to_check = [
        'get_pending_jobs',
        'create_processing_job',
        'start_processing_job',
        'complete_processing_job',
        'fail_processing_job'
    ]
    
    for func_name in functions_to_check:
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_proc 
                    WHERE proname = $1
                )
            """, func_name)
            
            status = "✅" if exists else "❌"
            print(f"   {status} Function: {func_name}")
            
        except Exception as e:
            print(f"   ❌ Error checking {func_name}: {e}")
    
    # Test get_pending_jobs function
    try:
        pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(5)')
        print(f"\n📥 Pending Jobs: {len(pending_jobs)} ready for processing")
        
        if pending_jobs:
            for i, job in enumerate(pending_jobs[:3]):  # Show first 3
                print(f"   Job {i+1}: {job['job_type']} for document {job['document_id']}")
        
    except Exception as e:
        print(f"   ❌ Error getting pending jobs: {e}")

async def check_processing_functions(conn):
    """Check processing functions and edge functions"""
    print("\n⚙️  Step 3: Processing Functions Check")
    print("-" * 40)
    
    # Check if we have the required environment in edge functions
    edge_functions = [
        'doc-parser',
        'job-processor', 
        'link-assigner',
        'upload-handler'
    ]
    
    print("📡 Edge Functions Status:")
    for func in edge_functions:
        print(f"   {func}: Should be deployed")
    
    # Check database triggers
    triggers = await conn.fetch("""
        SELECT 
            trigger_name, 
            event_object_table,
            action_timing,
            event_manipulation
        FROM information_schema.triggers 
        WHERE trigger_schema = 'public'
        AND trigger_name LIKE '%document%' OR trigger_name LIKE '%job%'
    """)
    
    print(f"\n🔗 Database Triggers ({len(triggers)}):")
    for trigger in triggers:
        print(f"   {trigger['trigger_name']} on {trigger['event_object_table']}")

async def test_job_processor():
    """Test the job processor edge function"""
    print("\n🎯 Step 4: Testing Job Processor")
    print("-" * 40)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'apikey': SERVICE_ROLE_KEY
    }
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            job_processor_url = f"{SUPABASE_URL}/functions/v1/job-processor"
            
            async with session.post(job_processor_url, headers=headers, json={}) as response:
                status = response.status
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                print(f"📞 Job Processor Response:")
                print(f"   Status: {status}")
                print(f"   Response: {response_data}")
                
                if status == 200:
                    print("   ✅ Job processor is accessible")
                else:
                    print("   ⚠️  Job processor may have issues")
                    
    except Exception as e:
        print(f"   ❌ Job processor test failed: {e}")

async def test_manual_job_creation(conn):
    """Test manual job creation for pending documents"""
    print("\n🔨 Step 5: Testing Manual Job Creation")
    print("-" * 40)
    
    # Find a pending document without jobs
    pending_doc = await conn.fetchrow("""
        SELECT d.id, d.original_filename
        FROM documents d
        LEFT JOIN processing_jobs pj ON d.id = pj.document_id
        WHERE d.status = 'pending' 
        AND pj.id IS NULL
        LIMIT 1
    """)
    
    if pending_doc:
        doc_id = pending_doc['id']
        filename = pending_doc['original_filename']
        
        print(f"📄 Found pending document: {filename}")
        print(f"   Creating manual processing job...")
        
        try:
            # Create a manual job
            job_id = await conn.fetchval("""
                SELECT create_processing_job(
                    $1::UUID,     -- document_id
                    'parse',      -- job_type
                    '{}'::JSONB,  -- payload
                    5,            -- priority
                    3,            -- max_retries
                    5             -- schedule_delay_seconds
                )
            """, doc_id)
            
            print(f"   ✅ Created job: {job_id}")
            
            # Verify job was created
            job_info = await conn.fetchrow("""
                SELECT status, created_at, scheduled_at
                FROM processing_jobs
                WHERE id = $1
            """, job_id)
            
            if job_info:
                print(f"   Status: {job_info['status']}")
                print(f"   Scheduled for: {job_info['scheduled_at']}")
            
        except Exception as e:
            print(f"   ❌ Manual job creation failed: {e}")
    else:
        print("📄 No pending documents found without jobs")

async def monitor_queue_activity(conn):
    """Monitor queue activity for a short period"""
    print("\n📊 Step 6: Queue Activity Monitoring")
    print("-" * 40)
    
    print("🔍 Monitoring for 30 seconds...")
    
    initial_stats = await get_queue_stats(conn)
    print(f"Initial state: {initial_stats}")
    
    # Wait and check again
    await asyncio.sleep(30)
    
    final_stats = await get_queue_stats(conn)
    print(f"After 30s: {final_stats}")
    
    # Calculate changes
    changes = {}
    for status in ['pending', 'running', 'completed', 'failed']:
        initial = initial_stats.get(status, 0)
        final = final_stats.get(status, 0)
        change = final - initial
        if change != 0:
            changes[status] = change
    
    if changes:
        print("\n📈 Changes detected:")
        for status, change in changes.items():
            direction = "+" if change > 0 else ""
            print(f"   {status}: {direction}{change}")
    else:
        print("\n📊 No queue activity detected")

async def get_queue_stats(conn):
    """Get current queue statistics"""
    stats = await conn.fetch("""
        SELECT status, COUNT(*) as count
        FROM processing_jobs
        WHERE created_at > NOW() - INTERVAL '1 hour'
        GROUP BY status
    """)
    
    return {row['status']: row['count'] for row in stats}

if __name__ == "__main__":