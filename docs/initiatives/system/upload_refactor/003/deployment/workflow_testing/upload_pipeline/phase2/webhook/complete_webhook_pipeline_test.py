#!/usr/bin/env python3
"""
Complete Webhook Pipeline Test
Test the complete pipeline with LlamaParse webhook integration
"""

import asyncio
import json
import time
import uuid
import hashlib
import httpx
import asyncpg
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv

load_dotenv('.env.production')

# Test configuration
RUN_ID = f"complete_webhook_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"
WEBHOOK_URL = "http://localhost:8001/webhook/llamaparse"

# API Configuration
API_CONFIG = {
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
    "DATABASE_URL": os.getenv("DATABASE_URL"),
    "LLAMAPARSE_API_KEY": os.getenv("LLAMAPARSE_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "LLAMAPARSE_BASE_URL": "https://api.cloud.llamaindex.ai",
    "OPENAI_API_URL": "https://api.openai.com/v1"
}

class CompleteWebhookPipelineTest:
    def __init__(self):
        self.results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "environment": "complete_webhook_pipeline_test",
            "tests": {},
            "summary": {}
        }
        self.db_connection = None
        
    async def connect_to_database(self):
        """Connect to production Supabase database"""
        try:
            self.db_connection = await asyncpg.connect(API_CONFIG["DATABASE_URL"])
            print("✅ Connected to production Supabase database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def test_webhook_server_health(self) -> bool:
        """Test if webhook server is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/webhook/status", timeout=5)
                if response.status_code == 200:
                    print("✅ Webhook server is running")
                    return True
                else:
                    print(f"❌ Webhook server health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Webhook server not accessible: {e}")
            return False
    
    async def test_supabase_storage_upload(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test real Supabase Storage upload"""
        print(f"📁 Testing Supabase Storage upload for {doc_info['name']}...")
        
        try:
            # Read file data
            file_path = Path(doc_info['path'])
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Make file hash unique by including RUN_ID
            unique_content = file_data + RUN_ID.encode()
            file_hash = hashlib.sha256(unique_content).hexdigest()
            
            # Generate storage path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = file_path.suffix
            storage_path = f"files/{TEST_USER_ID}/raw/{timestamp}_{file_hash[:8]}{file_ext}"
            
            # Upload to Supabase Storage
            headers = {
                "Authorization": f"Bearer {API_CONFIG['SUPABASE_SERVICE_ROLE_KEY']}",
                "Content-Type": "application/pdf"
            }
            
            storage_url = f"{API_CONFIG['SUPABASE_URL']}/storage/v1/object/files/{storage_path}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    storage_url,
                    headers=headers,
                    content=file_data,
                    timeout=60
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ File uploaded to storage: {storage_path}")
                    return {
                        "success": True,
                        "storage_path": storage_path,
                        "file_hash": file_hash,
                        "file_size": len(file_data),
                        "storage_url": storage_url
                    }
                else:
                    return {"success": False, "error": f"Storage upload failed: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_llamaparse_with_webhook(self, doc_info: Dict[str, Any], storage_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test LlamaParse with webhook configuration"""
        print(f"📄 Testing LlamaParse with webhook for {doc_info['name']}...")
        
        try:
            # Read file data
            file_path = Path(doc_info['path'])
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Prepare LlamaParse request with webhook
            headers = {
                "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
            }
            
            files = {
                "upload_file": (doc_info['name'], file_data, "application/pdf")
            }
            
            data = {
                "language": "en",
                "parsing_instruction": "Extract all text content from this document, preserving structure and formatting.",
                "webhook_url": WEBHOOK_URL,  # Add webhook URL
                "webhook_events": ["completed", "failed"]  # Events to trigger webhook
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_CONFIG['LLAMAPARSE_BASE_URL']}/api/v1/files",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"✅ LlamaParse upload with webhook successful: {result}")
                    return {
                        "success": True,
                        "llamaparse_result": result,
                        "job_id": result.get('id', str(uuid.uuid4())),
                        "status": "uploaded",
                        "webhook_configured": True
                    }
                else:
                    return {"success": False, "error": f"LlamaParse upload failed: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_database_job_creation(self, doc_info: Dict[str, Any], storage_result: Dict[str, Any], llamaparse_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test database job creation for webhook processing"""
        print(f"🗄️ Testing database job creation for {doc_info['name']}...")
        
        try:
            # Create document record
            document_id = str(uuid.uuid4())
            doc_query = """
                INSERT INTO upload_pipeline.documents 
                (document_id, filename, file_sha256, bytes_len, mime, processing_status, raw_path, user_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            
            await self.db_connection.execute(
                doc_query,
                document_id,
                doc_info['name'],
                storage_result['file_hash'],
                storage_result['file_size'],
                'application/pdf',
                'uploaded',
                storage_result['storage_path'],
                TEST_USER_ID,
                datetime.now(),
                datetime.now()
            )
            
            # Create upload job record for webhook processing
            job_id = str(uuid.uuid4())
            job_query = """
                INSERT INTO upload_pipeline.upload_jobs 
                (job_id, document_id, state, status, progress, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            
            await self.db_connection.execute(
                job_query,
                job_id,
                document_id,
                'queued',
                'parse_queued',
                '0.0',
                datetime.now(),
                datetime.now()
            )
            
            print(f"✅ Database job created for webhook processing: {job_id}")
            
            return {
                "success": True,
                "document_id": document_id,
                "job_id": job_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_webhook_processing(self, job_id: str) -> Dict[str, Any]:
        """Test webhook processing by simulating LlamaParse callback"""
        print(f"📥 Testing webhook processing for job {job_id}...")
        
        try:
            # Simulate LlamaParse webhook callback
            webhook_payload = {
                "job_id": job_id,
                "status": "completed",
                "result_url": f"https://example.com/parsed_{job_id}.md",
                "timestamp": datetime.now().isoformat(),
                "file_size": 1024,
                "processing_time": 5.2
            }
            
            # Send webhook to our server
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    WEBHOOK_URL,
                    json=webhook_payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Webhook processed successfully: {result}")
                    
                    # Verify database update
                    query = """
                        SELECT job_id, status, progress, updated_at
                        FROM upload_pipeline.upload_jobs 
                        WHERE job_id = $1
                    """
                    
                    db_result = await self.db_connection.fetchrow(query, job_id)
                    
                    if db_result and db_result['status'] == 'parsed':
                        print(f"✅ Database updated to parsed status: {dict(db_result)}")
                        return {
                            "success": True,
                            "webhook_response": result,
                            "database_update": dict(db_result),
                            "status_updated": True
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Database not updated correctly: {db_result}",
                            "webhook_response": result
                        }
                else:
                    return {"success": False, "error": f"Webhook processing failed: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_complete_webhook_pipeline(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test complete pipeline with webhook integration"""
        print(f"🔄 Testing complete webhook pipeline for {doc_info['name']}...")
        
        pipeline_result = {
            "document": doc_info['name'],
            "steps": {},
            "success": False
        }
        
        try:
            # Step 1: Real Supabase Storage upload
            storage_result = await self.test_supabase_storage_upload(doc_info)
            pipeline_result["steps"]["supabase_storage"] = storage_result
            if not storage_result["success"]:
                return pipeline_result
            
            # Step 2: LlamaParse with webhook configuration
            llamaparse_result = await self.test_llamaparse_with_webhook(doc_info, storage_result)
            pipeline_result["steps"]["llamaparse_webhook"] = llamaparse_result
            if not llamaparse_result["success"]:
                return pipeline_result
            
            # Step 3: Database job creation
            db_result = await self.test_database_job_creation(doc_info, storage_result, llamaparse_result)
            pipeline_result["steps"]["database_job_creation"] = db_result
            if not db_result["success"]:
                return pipeline_result
            
            # Step 4: Webhook processing simulation
            webhook_result = await self.test_webhook_processing(db_result["job_id"])
            pipeline_result["steps"]["webhook_processing"] = webhook_result
            if not webhook_result["success"]:
                return pipeline_result
            
            pipeline_result["success"] = True
            print(f"✅ Complete webhook pipeline successful for {doc_info['name']}")
            
        except Exception as e:
            pipeline_result["error"] = str(e)
            print(f"❌ Webhook pipeline failed for {doc_info['name']}: {e}")
        
        return pipeline_result
    
    async def cleanup_test_data(self):
        """Clean up test data from database"""
        print(f"🧹 Cleaning up test data with RUN_ID: {RUN_ID}...")
        
        try:
            # Delete in reverse dependency order
            await self.db_connection.execute(
                "DELETE FROM upload_pipeline.document_chunks WHERE text LIKE $1",
                f"%{RUN_ID}%"
            )
            await self.db_connection.execute(
                "DELETE FROM upload_pipeline.upload_jobs WHERE job_id::text LIKE $1",
                f"%{RUN_ID}%"
            )
            await self.db_connection.execute(
                "DELETE FROM upload_pipeline.documents WHERE filename LIKE $1",
                f"%{RUN_ID}%"
            )
            
            print(f"✅ Test data cleanup complete")
            return True
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
    
    async def run_complete_webhook_test(self):
        """Run complete webhook pipeline test"""
        print("🚀 Starting Complete Webhook Pipeline Test")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 Webhook URL: {WEBHOOK_URL}")
        print(f"🗄️ Database: Production Supabase")
        
        # Connect to database
        if not await self.connect_to_database():
            return self.results
        
        # Check webhook server health
        if not await self.test_webhook_server_health():
            print("❌ Webhook server not running, please start it first:")
            print("   python webhook_test_server.py")
            return self.results
        
        # Clean up any existing test data
        await self.cleanup_test_data()
        
        # Test documents
        test_documents = [
            {
                "name": f"Complete Webhook Test Document {RUN_ID}.pdf",
                "path": "test_document.pdf"
            }
        ]
        
        # Test each document
        print("\n" + "="*70)
        print("COMPLETE WEBHOOK PIPELINE TEST")
        print("="*70)
        
        for i, doc_info in enumerate(test_documents, 1):
            print(f"\n📄 Test Document {i}: {doc_info['name']}")
            
            pipeline_result = await self.test_complete_webhook_pipeline(doc_info)
            self.results["tests"][f"test_{i}"] = pipeline_result
            
            status = "✅ SUCCESS" if pipeline_result["success"] else "❌ FAILED"
            print(f"📊 Test {i} result: {status}")
        
        # Generate summary
        total_tests = len(self.results["tests"])
        successful_tests = sum(1 for test in self.results["tests"].values() if test["success"])
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "end_time": datetime.now().isoformat()
        }
        
        # Save results
        results_file = f"complete_webhook_pipeline_test_{RUN_ID}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Complete Webhook Pipeline Test Complete!")
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"📁 Results saved to: {results_file}")
        
        # Clean up test data
        await self.cleanup_test_data()
        
        # Close database connection
        if self.db_connection:
            await self.db_connection.close()
        
        return self.results

async def main():
    """Main test execution"""
    tester = CompleteWebhookPipelineTest()
    results = await tester.run_complete_webhook_test()
    
    # Print summary
    print("\n" + "="*80)
    print("COMPLETE WEBHOOK PIPELINE TEST SUMMARY")
    print("="*80)
    print(f"Success Rate: {results['summary']['success_rate']}")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Successful: {results['summary']['successful_tests']}")
    print(f"Failed: {results['summary']['failed_tests']}")
    
    # Detailed results
    for test_name, test_result in results['tests'].items():
        status = "✅" if test_result['success'] else "❌"
        print(f"{status} {test_name}: {test_result['document']}")

if __name__ == "__main__":
    asyncio.run(main())
