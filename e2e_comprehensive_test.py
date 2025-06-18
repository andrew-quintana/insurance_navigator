#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Insurance Navigator
====================================================
"""

import asyncio
import asyncpg
import aiohttp
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class E2ETestFramework:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        self.test_results = []
        self.test_user_id = f"test-user-{uuid.uuid4().hex[:8]}"
        
    async def run_comprehensive_test(self):
        """Run all end-to-end tests"""
        print("🚀 Insurance Navigator - Comprehensive E2E Test")
        print("=" * 60)
        print(f"🆔 Test User ID: {self.test_user_id}")
        
        conn = None
        try:
            # Connect to database
            conn = await asyncpg.connect(
                self.database_url, 
                statement_cache_size=0,
                server_settings={'jit': 'off'}
            )
            
            # Test 1: System Health Check
            await self.test_system_health(conn)
            
            # Test 2: Database Operations
            await self.test_database_operations(conn)
            
            # Test 3: Document Processing
            await self.test_document_processing(conn)
            
            # Test 4: Queue Processing
            await self.test_queue_processing(conn)
            
            # Test 5: Agent Workflow
            await self.test_agent_workflow(conn)
            
            # Generate Report
            self.generate_test_report()
            
        except Exception as e:
            print(f"❌ Critical test failure: {e}")
        finally:
            if conn:
                await conn.close()
    
    async def test_system_health(self, conn):
        """Test 1: System Health Check"""
        print("\n🔍 Test 1: System Health Check")
        print("-" * 40)
        
        try:
            # Check database connection
            db_version = await conn.fetchval('SELECT version()')
            print(f"✅ Database connected: {db_version[:50]}...")
            
            # Check document stats
            doc_stats = await conn.fetch("""
                SELECT status, COUNT(*) as count 
                FROM documents 
                GROUP BY status 
                ORDER BY count DESC
            """)
            
            print("📄 Document Status:")
            for stat in doc_stats:
                print(f"   {stat['status']}: {stat['count']}")
            
            self.test_results.append({
                "test": "System Health",
                "status": "PASSED",
                "details": f"DB connected, {len(doc_stats)} status types"
            })
            
        except Exception as e:
            print(f"❌ System health check failed: {e}")
            self.test_results.append({
                "test": "System Health",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_database_operations(self, conn):
        """Test 2: Database Operations"""
        print("\n🗄️ Test 2: Database Operations")
        print("-" * 40)
        
        try:
            # Test creating a document record
            test_doc_id = await conn.fetchval("""
                INSERT INTO documents (
                    original_filename, 
                    content_type, 
                    file_size, 
                    user_id, 
                    status,
                    storage_path
                ) VALUES ($1, $2, $3, $4, $5, $6) 
                RETURNING id
            """, 
            f"test_e2e_{uuid.uuid4().hex[:8]}.txt",
            "text/plain",
            500,
            self.test_user_id,
            "pending",
            f"test_path_{uuid.uuid4().hex[:8]}.txt"
            )
            
            print(f"✅ Created test document: {test_doc_id}")
            
            # Clean up
            await conn.execute("DELETE FROM documents WHERE id = $1", test_doc_id)
            
            self.test_results.append({
                "test": "Database Operations",
                "status": "PASSED",
                "details": f"Document {test_doc_id}"
            })
            
        except Exception as e:
            print(f"❌ Database operations failed: {e}")
            self.test_results.append({
                "test": "Database Operations",
                "status": "FAILED", 
                "error": str(e)
            })
    
    async def test_document_processing(self, conn):
        """Test 3: Document Processing"""
        print("\n📄 Test 3: Document Processing")
        print("-" * 40)
        
        try:
            # Test direct storage upload
            test_content = f"""
            End-to-End Test Document
            Generated: {datetime.now().isoformat()}
            Test User: {self.test_user_id}
            """.strip()
            
            filename = f"e2e_test_{uuid.uuid4().hex[:8]}.txt"
            storage_path = f"documents/{self.test_user_id}/{filename}"
            
            # Upload to storage
            storage_url = f"{self.supabase_url}/storage/v1/object/documents/{storage_path}"
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': 'text/plain',
                'apikey': self.service_role_key
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(storage_url, data=test_content.encode(), headers=headers) as response:
                    if response.status in [200, 201]:
                        print(f"✅ File uploaded to storage: {storage_path}")
                        
                        self.test_results.append({
                            "test": "Document Processing",
                            "status": "PASSED",
                            "details": f"Uploaded {filename}"
                        })
                        
                    else:
                        raise Exception(f"Storage upload failed: {response.status}")
            
        except Exception as e:
            print(f"❌ Document processing test failed: {e}")
            self.test_results.append({
                "test": "Document Processing",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_queue_processing(self, conn):
        """Test 4: Queue Processing"""
        print("\n⚙️ Test 4: Queue Processing")
        print("-" * 40)
        
        try:
            # Test job processor
            processor_url = f"{self.supabase_url}/functions/v1/job-processor"
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': 'application/json',
                'apikey': self.service_role_key
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(processor_url, headers=headers, json={}) as response:
                    status = response.status
                    
                    if status == 200:
                        print("✅ Job processor is accessible")
                        self.test_results.append({
                            "test": "Queue Processing",
                            "status": "PASSED",
                            "details": "Job processor responsive"
                        })
                    else:
                        raise Exception(f"Job processor returned {status}")
            
        except Exception as e:
            print(f"❌ Queue processing test failed: {e}")
            self.test_results.append({
                "test": "Queue Processing", 
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_agent_workflow(self, conn):
        """Test 5: Agent Workflow"""
        print("\n🤖 Test 5: Agent Workflow")
        print("-" * 40)
        
        try:
            # Test agent imports
            import sys
            from pathlib import Path
            project_root = Path.cwd()
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
            
            print("✅ Agent imports successful")
            
            # Test creating agent instance
            navigator = PatientNavigatorAgent(use_mock=True)
            print("✅ Agent instance created")
            
            self.test_results.append({
                "test": "Agent Workflow",
                "status": "PASSED",
                "details": "Navigator agent functional"
            })
                
        except Exception as e:
            print(f"❌ Agent workflow test failed: {e}")
            self.test_results.append({
                "test": "Agent Workflow",
                "status": "FAILED",
                "error": str(e)
            })
    
    def generate_test_report(self):
        """Generate test report"""
        print("\n📊 End-to-End Test Report")
        print("=" * 50)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed = len([r for r in self.test_results if r['status'] == 'FAILED'])
        
        print(f"📈 Summary: {passed} passed, {failed} failed")
        print(f"🆔 Test User: {self.test_user_id}")
        
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"   {status_emoji} {result['test']}: {result['status']}")
            
            if 'details' in result:
                print(f"      Details: {result['details']}")
            if 'error' in result:
                print(f"      Error: {result['error']}")

async def main():
    """Run the comprehensive E2E test"""
    test_framework = E2ETestFramework()
    await test_framework.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 