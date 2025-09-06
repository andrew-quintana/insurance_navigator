#!/usr/bin/env python3
"""
Simplified Real API Test
Test the pipeline using direct API calls with production Supabase and real external APIs
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
RUN_ID = f"simplified_real_api_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"

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

class SimplifiedRealAPITest:
    def __init__(self):
        self.results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "environment": "simplified_real_api_test",
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
    
    async def test_supabase_storage_upload(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test real Supabase Storage upload via REST API"""
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
            
            # Generate storage path as per spec: files/user/{userId}/raw/{datetime}_{hash}.{ext}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = file_path.suffix
            storage_path = f"files/{TEST_USER_ID}/raw/{timestamp}_{file_hash[:8]}{file_ext}"
            
            # Upload to Supabase Storage using REST API
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
    
    async def test_llamaparse_real_parsing(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test real LlamaParse API parsing"""
        print(f"📄 Testing LlamaParse real API parsing for {doc_info['name']}...")
        
        try:
            # Read file data
            file_path = Path(doc_info['path'])
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Use the discovered endpoint: /api/v1/files with upload_file parameter
            headers = {
                "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
            }
            
            # Prepare file upload
            files = {
                "upload_file": (doc_info['name'], file_data, "application/pdf")
            }
            
            data = {
                "language": "en",
                "parsing_instruction": "Extract all text content from this document, preserving structure and formatting."
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
                    print(f"✅ LlamaParse upload successful: {result}")
                    return {
                        "success": True,
                        "llamaparse_result": result,
                        "job_id": result.get('id', str(uuid.uuid4())),
                        "status": "uploaded"
                    }
                else:
                    return {"success": False, "error": f"LlamaParse upload failed: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_openai_embeddings(self, text: str) -> Dict[str, Any]:
        """Test real OpenAI embeddings generation"""
        print(f"🧠 Testing OpenAI embeddings for text: {text[:50]}...")
        
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "input": text,
                "model": "text-embedding-3-small"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_CONFIG['OPENAI_API_URL']}/embeddings",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result['data'][0]['embedding']
                    print(f"✅ OpenAI embeddings generated: {len(embedding)} dimensions")
                    return {
                        "success": True,
                        "embedding": embedding,
                        "model": result['model'],
                        "usage": result['usage']
                    }
                else:
                    return {"success": False, "error": f"OpenAI embeddings failed: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_database_operations(self, doc_info: Dict[str, Any], storage_result: Dict[str, Any], llamaparse_result: Dict[str, Any], embedding_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test database operations with real data"""
        print(f"🗄️ Testing database operations for {doc_info['name']}...")
        
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
            
            # Create upload job record
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
                'uploaded',
                '0.0',
                datetime.now(),
                datetime.now()
            )
            
            # Create document chunks with real embeddings
            chunk_id = str(uuid.uuid4())
            chunk_text = f"Test chunk for {doc_info['name']} - {RUN_ID}"
            
            chunk_query = """
                INSERT INTO upload_pipeline.document_chunks 
                (chunk_id, document_id, chunker_name, chunker_version, chunk_ord, text, chunk_sha, embed_model, embed_version, vector_dim, embedding, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """
            
            await self.db_connection.execute(
                chunk_query,
                chunk_id,
                document_id,
                'test_chunker',
                '1.0.0',
                1,
                chunk_text,
                hashlib.sha256(chunk_text.encode()).hexdigest(),
                embedding_result['model'],
                '1.0.0',
                len(embedding_result['embedding']),
                str(embedding_result['embedding']),
                datetime.now(),
                datetime.now()
            )
            
            print(f"✅ Database operations completed for {doc_info['name']}")
            
            return {
                "success": True,
                "document_id": document_id,
                "job_id": job_id,
                "chunk_id": chunk_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_complete_real_api_pipeline(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test complete pipeline using real APIs"""
        print(f"🔄 Testing complete real API pipeline for {doc_info['name']}...")
        
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
            
            # Step 2: Real LlamaParse parsing
            llamaparse_result = await self.test_llamaparse_real_parsing(doc_info)
            pipeline_result["steps"]["llamaparse_parsing"] = llamaparse_result
            if not llamaparse_result["success"]:
                return pipeline_result
            
            # Step 3: Real OpenAI embeddings
            embedding_result = await self.test_openai_embeddings(f"Test content for {doc_info['name']}")
            pipeline_result["steps"]["openai_embeddings"] = embedding_result
            if not embedding_result["success"]:
                return pipeline_result
            
            # Step 4: Database operations with real data
            db_result = await self.test_database_operations(doc_info, storage_result, llamaparse_result, embedding_result)
            pipeline_result["steps"]["database_operations"] = db_result
            if not db_result["success"]:
                return pipeline_result
            
            pipeline_result["success"] = True
            print(f"✅ Complete real API pipeline successful for {doc_info['name']}")
            
        except Exception as e:
            pipeline_result["error"] = str(e)
            print(f"❌ Real API pipeline failed for {doc_info['name']}: {e}")
        
        return pipeline_result
    
    async def cleanup_test_data(self):
        """Clean up test data from database"""
        print(f"🧹 Cleaning up test data with RUN_ID: {RUN_ID}...")
        
        try:
            # Delete in reverse dependency order (chunks first, then jobs, then documents)
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
    
    async def run_real_api_test(self):
        """Run complete real API pipeline test"""
        print("🚀 Starting Simplified Real API Pipeline Test")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 External APIs: Real LlamaParse + OpenAI")
        print(f"🗄️ Database: Production Supabase")
        print(f"📁 Storage: Real Supabase Storage")
        
        # Connect to database
        if not await self.connect_to_database():
            return self.results
        
        # Clean up any existing test data
        await self.cleanup_test_data()
        
        # Test documents
        test_documents = [
            {
                "name": f"Simplified Real API Test Document {RUN_ID}.pdf",
                "path": "test_document.pdf"
            }
        ]
        
        # Test each document
        print("\n" + "="*70)
        print("SIMPLIFIED REAL API PIPELINE TEST")
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
        results_file = f"simplified_real_api_test_{RUN_ID}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Simplified Real API Pipeline Test Complete!")
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
    tester = SimplifiedRealAPITest()
    results = await tester.run_real_api_test()
    
    # Print summary
    print("\n" + "="*80)
    print("SIMPLIFIED REAL API PIPELINE TEST SUMMARY")
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
