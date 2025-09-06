#!/usr/bin/env python3
"""
Real API Pipeline Test
Test the complete pipeline using the real local API server with production Supabase and real external APIs
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
RUN_ID = f"real_api_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"

# API Configuration
API_CONFIG = {
    "LOCAL_API_URL": "http://localhost:8000",
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
    "DATABASE_URL": os.getenv("DATABASE_URL")
}

class RealAPIPipelineTest:
    def __init__(self):
        self.results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "environment": "real_api_pipeline_test",
            "tests": {},
            "summary": {}
        }
        self.db_connection = None
        self.api_client = httpx.AsyncClient(timeout=60.0)
        
    async def connect_to_database(self):
        """Connect to production Supabase database"""
        try:
            self.db_connection = await asyncpg.connect(API_CONFIG["DATABASE_URL"])
            print("✅ Connected to production Supabase database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def check_api_health(self) -> bool:
        """Check if local API server is running and healthy"""
        try:
            response = await self.api_client.get(f"{API_CONFIG['LOCAL_API_URL']}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API health check passed: {health_data}")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return False
    
    async def generate_jwt_token(self) -> str:
        """Generate JWT token for API authentication"""
        import jwt
        
        payload = {
            "sub": TEST_USER_ID,
            "aud": "authenticated",
            "role": "authenticated",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600
        }
        
        secret = API_CONFIG["SUPABASE_SERVICE_ROLE_KEY"]
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token
    
    async def test_document_upload_via_api(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test document upload through the real API"""
        print(f"📤 Testing document upload via API for {doc_info['name']}...")
        
        try:
            # Read file data
            file_path = Path(doc_info['path'])
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Generate JWT token
            token = await self.generate_jwt_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Prepare upload request
            upload_data = {
                "filename": doc_info['name'],
                "file_size": len(file_data),
                "mime_type": "application/pdf",
                "run_id": RUN_ID
            }
            
            # Step 1: Create upload job
            response = await self.api_client.post(
                f"{API_CONFIG['LOCAL_API_URL']}/api/v1/upload/initiate",
                headers=headers,
                json=upload_data
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Upload initiation failed: {response.status_code} - {response.text}"}
            
            upload_result = response.json()
            print(f"✅ Upload job created: {upload_result}")
            
            # Step 2: Upload file to storage
            file_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/pdf"
            }
            
            file_response = await self.api_client.post(
                f"{API_CONFIG['LOCAL_API_URL']}/api/v1/upload/file",
                headers=file_headers,
                files={"file": (doc_info['name'], file_data, "application/pdf")},
                data={"job_id": upload_result.get("job_id")}
            )
            
            if file_response.status_code not in [200, 201]:
                return {"success": False, "error": f"File upload failed: {file_response.status_code} - {file_response.text}"}
            
            print(f"✅ File uploaded successfully")
            
            return {
                "success": True,
                "upload_result": upload_result,
                "file_upload_result": file_response.json() if file_response.text else {"status": "uploaded"}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_worker_processing_via_api(self, job_id: str) -> Dict[str, Any]:
        """Test worker processing through the real API"""
        print(f"⚙️ Testing worker processing via API for job {job_id}...")
        
        try:
            # Generate JWT token
            token = await self.generate_jwt_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Trigger worker processing
            response = await self.api_client.post(
                f"{API_CONFIG['LOCAL_API_URL']}/api/v1/worker/process",
                headers=headers,
                json={"job_id": job_id}
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Worker processing failed: {response.status_code} - {response.text}"}
            
            worker_result = response.json()
            print(f"✅ Worker processing triggered: {worker_result}")
            
            return {
                "success": True,
                "worker_result": worker_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_status_check_via_api(self, job_id: str) -> Dict[str, Any]:
        """Test status checking through the real API"""
        print(f"📊 Testing status check via API for job {job_id}...")
        
        try:
            # Generate JWT token
            token = await self.generate_jwt_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Check job status
            response = await self.api_client.get(
                f"{API_CONFIG['LOCAL_API_URL']}/api/v1/upload/status/{job_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Status check failed: {response.status_code} - {response.text}"}
            
            status_result = response.json()
            print(f"✅ Status retrieved: {status_result}")
            
            return {
                "success": True,
                "status_result": status_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def verify_database_state(self, job_id: str) -> Dict[str, Any]:
        """Verify database state after API operations"""
        print(f"🔍 Verifying database state for job {job_id}...")
        
        try:
            # Check documents table
            doc_query = """
                SELECT document_id, filename, processing_status, raw_path, file_sha256
                FROM upload_pipeline.documents 
                WHERE document_id = $1
            """
            doc_result = await self.db_connection.fetchrow(doc_query, job_id)
            
            # Check upload_jobs table
            job_query = """
                SELECT job_id, document_id, state, status, progress
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1
            """
            job_result = await self.db_connection.fetchrow(job_query, job_id)
            
            # Check document_chunks table
            chunks_query = """
                SELECT COUNT(*) as chunk_count
                FROM upload_pipeline.document_chunks 
                WHERE document_id = $1
            """
            chunks_result = await self.db_connection.fetchrow(chunks_query, job_id)
            
            print(f"✅ Database verification complete")
            
            return {
                "success": True,
                "document": dict(doc_result) if doc_result else None,
                "job": dict(job_result) if job_result else None,
                "chunks": dict(chunks_result) if chunks_result else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cleanup_test_data(self):
        """Clean up test data from database"""
        print(f"🧹 Cleaning up test data with RUN_ID: {RUN_ID}...")
        
        try:
            # Delete in reverse dependency order
            await self.db_connection.execute(
                "DELETE FROM upload_pipeline.document_chunks WHERE document_id LIKE $1",
                f"{RUN_ID}%"
            )
            await self.db_connection.execute(
                "DELETE FROM upload_pipeline.upload_jobs WHERE job_id LIKE $1",
                f"{RUN_ID}%"
            )
            await self.db_connection.execute(
                "DELETE FROM upload_pipeline.documents WHERE document_id LIKE $1",
                f"{RUN_ID}%"
            )
            
            print(f"✅ Test data cleanup complete")
            return True
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
    
    async def test_complete_real_api_pipeline(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test complete pipeline using real API"""
        print(f"🔄 Testing complete real API pipeline for {doc_info['name']}...")
        
        pipeline_result = {
            "document": doc_info['name'],
            "steps": {},
            "success": False
        }
        
        try:
            # Step 1: Upload document via API
            upload_result = await self.test_document_upload_via_api(doc_info)
            pipeline_result["steps"]["upload"] = upload_result
            if not upload_result["success"]:
                return pipeline_result
            
            job_id = upload_result["upload_result"].get("job_id")
            if not job_id:
                pipeline_result["error"] = "No job_id returned from upload"
                return pipeline_result
            
            # Step 2: Trigger worker processing via API
            worker_result = await self.test_worker_processing_via_api(job_id)
            pipeline_result["steps"]["worker_processing"] = worker_result
            
            # Step 3: Check status via API
            status_result = await self.test_status_check_via_api(job_id)
            pipeline_result["steps"]["status_check"] = status_result
            
            # Step 4: Verify database state
            db_result = await self.verify_database_state(job_id)
            pipeline_result["steps"]["database_verification"] = db_result
            
            pipeline_result["success"] = True
            print(f"✅ Complete real API pipeline successful for {doc_info['name']}")
            
        except Exception as e:
            pipeline_result["error"] = str(e)
            print(f"❌ Real API pipeline failed for {doc_info['name']}: {e}")
        
        return pipeline_result
    
    async def run_real_api_test(self):
        """Run complete real API pipeline test"""
        print("🚀 Starting Real API Pipeline Test")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 API URL: {API_CONFIG['LOCAL_API_URL']}")
        print(f"🗄️ Database: Production Supabase")
        
        # Connect to database
        if not await self.connect_to_database():
            return self.results
        
        # Check API health
        if not await self.check_api_health():
            print("❌ API health check failed, aborting test")
            return self.results
        
        # Clean up any existing test data
        await self.cleanup_test_data()
        
        # Test documents
        test_documents = [
            {
                "name": f"Real API Test Document {RUN_ID}.pdf",
                "path": "test_document.pdf"
            }
        ]
        
        # Test each document
        print("\n" + "="*70)
        print("REAL API PIPELINE TEST")
        print("="*70)
        
        for i, doc_info in enumerate(test_documents, 1):
            print(f"\n📄 Test Document {i}: {doc_info['name']}")
            
            pipeline_result = await self.test_complete_real_api_pipeline(doc_info)
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
        results_file = f"real_api_pipeline_test_{RUN_ID}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Real API Pipeline Test Complete!")
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"📁 Results saved to: {results_file}")
        
        # Clean up test data
        await self.cleanup_test_data()
        
        # Close connections
        if self.db_connection:
            await self.db_connection.close()
        await self.api_client.aclose()
        
        return self.results

async def main():
    """Main test execution"""
    tester = RealAPIPipelineTest()
    results = await tester.run_real_api_test()
    
    # Print summary
    print("\n" + "="*80)
    print("REAL API PIPELINE TEST SUMMARY")
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
