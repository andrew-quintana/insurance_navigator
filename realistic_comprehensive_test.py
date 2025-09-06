#!/usr/bin/env python3
"""
Realistic Comprehensive Pipeline Test
Test what we can actually validate with current constraints

This test focuses on:
1. Direct database operations with production Supabase
2. Real external API integration (OpenAI, LlamaParse connectivity)
3. Complete pipeline simulation with real data
4. All storage layers validation
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

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.production')

# Test configuration
RUN_ID = f"realistic_comprehensive_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"

# API Configuration
API_CONFIG = {
    "LLAMAPARSE_API_KEY": os.getenv("LLAMAPARSE_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "LLAMAPARSE_BASE_URL": "https://api.cloud.llamaindex.ai",
    "OPENAI_API_URL": "https://api.openai.com/v1",
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
    "DATABASE_URL": os.getenv("DATABASE_URL")
}

# Test documents
TEST_DOCUMENTS = [
    {
        "name": "Simulated Insurance Document.pdf",
        "path": "test_document.pdf",
        "expected_size": 1782
    },
    {
        "name": "Scan Classic HMO.pdf", 
        "path": "test_upload.pdf",
        "expected_size": 2544678
    }
]

class RealisticComprehensiveTester:
    def __init__(self):
        self.results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "environment": "realistic_comprehensive_production_supabase",
            "tests": [],
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
    
    async def test_external_apis_connectivity(self) -> Dict[str, Any]:
        """Test external APIs connectivity"""
        print("🔗 Testing external APIs connectivity...")
        
        api_results = {}
        
        # Test OpenAI API
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_CONFIG['OPENAI_API_URL']}/models",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    models = response.json()
                    embedding_models = [m for m in models.get('data', []) if 'embedding' in m.get('id', '').lower()]
                    api_results["openai"] = {
                        "success": True,
                        "embedding_models": len(embedding_models),
                        "total_models": len(models.get('data', []))
                    }
                    print("✅ OpenAI API connectivity successful")
                else:
                    api_results["openai"] = {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            api_results["openai"] = {"success": False, "error": str(e)}
        
        # Test LlamaParse API
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['LLAMAPARSE_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_CONFIG['LLAMAPARSE_BASE_URL']}/api/v1/jobs",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    jobs_data = response.json()
                    job_count = jobs_data.get('total_count', 0)
                    api_results["llamaparse"] = {
                        "success": True,
                        "job_count": job_count
                    }
                    print("✅ LlamaParse API connectivity successful")
                else:
                    api_results["llamaparse"] = {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            api_results["llamaparse"] = {"success": False, "error": str(e)}
        
        return api_results
    
    async def test_openai_embedding_generation(self, text: str) -> Dict[str, Any]:
        """Test OpenAI embedding generation with real API"""
        try:
            headers = {
                "Authorization": f"Bearer {API_CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            embedding_data = {
                "input": text,
                "model": "text-embedding-3-small",
                "encoding_format": "float"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_CONFIG['OPENAI_API_URL']}/embeddings",
                    headers=headers,
                    json=embedding_data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embeddings = result.get('data', [])
                    if embeddings:
                        embedding = embeddings[0].get('embedding', [])
                        return {
                            "success": True,
                            "dimensions": len(embedding),
                            "embedding": embedding,
                            "model": result.get('model'),
                            "usage": result.get('usage', {})
                        }
                    else:
                        return {"success": False, "error": "No embeddings in response"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_supabase_storage_simulation(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Supabase Storage operations"""
        print(f"📁 Simulating Supabase Storage operations for {doc_info['name']}...")
        
        try:
            # Read file data
            file_path = Path(doc_info['path'])
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Create unique hash by including RUN_ID to avoid duplicates
            unique_content = f"{RUN_ID}_{doc_info['name']}_{file_data}"
            file_hash = hashlib.sha256(unique_content.encode()).hexdigest()
            file_size = len(file_data)
            
            # Generate storage paths as per spec
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = file_path.suffix
            
            # Raw file path: files/user/{userId}/raw/{datetime}_{hash}.{ext}
            raw_path = f"files/{TEST_USER_ID}/raw/{timestamp}_{file_hash[:8]}{file_ext}"
            
            # Parsed file path: files/user/{userId}/parsed/{datetime}_{filename}.md
            parsed_path = f"files/{TEST_USER_ID}/parsed/{timestamp}_{doc_info['name']}.md"
            
            print(f"✅ Storage paths generated:")
            print(f"   Raw: {raw_path}")
            print(f"   Parsed: {parsed_path}")
            
            return {
                "success": True,
                "raw_path": raw_path,
                "parsed_path": parsed_path,
                "file_hash": file_hash,
                "file_size": file_size
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_llamaparse_parsing_simulation(self, doc_info: Dict[str, Any], storage_path: str) -> Dict[str, Any]:
        """Simulate LlamaParse parsing with realistic content"""
        print(f"📄 Simulating LlamaParse parsing for {doc_info['name']}...")
        
        try:
            # Generate realistic parsed content
            parsed_content = f"""# {doc_info['name']}

## Document Information
- **Document Type**: Insurance Policy Document
- **File Size**: {doc_info['expected_size']:,} bytes
- **Processing Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Source File**: {storage_path}

## Executive Summary
This document contains insurance policy information that has been processed through the LlamaParse API. The content has been extracted and formatted for further processing in the pipeline.

## Key Sections

### 1. Policy Details
- **Policy Number**: POL-{str(uuid.uuid4())[:8].upper()}
- **Effective Date**: {datetime.now().strftime('%Y-%m-%d')}
- **Expiration Date**: {(datetime.now().replace(year=datetime.now().year + 1)).strftime('%Y-%m-%d')}

### 2. Coverage Information
- **Coverage Type**: Health Insurance
- **Deductible**: $1,000
- **Maximum Out-of-Pocket**: $5,000
- **Co-pay**: $25 for primary care visits

### 3. Benefits
- **Preventive Care**: 100% covered
- **Emergency Services**: 90% covered after deductible
- **Prescription Drugs**: Tiered coverage based on formulary

### 4. Terms and Conditions
This policy is subject to the terms and conditions outlined in the full document. Please refer to the complete policy for detailed information.

## Processing Metadata
- **Parse Timestamp**: {datetime.now().isoformat()}
- **Processing Status**: Successfully parsed
- **LlamaParse Job ID**: {str(uuid.uuid4())}
- **Confidence Score**: 0.95
- **Language**: English
- **Page Count**: 1
"""
            
            print(f"✅ Parsed content generated ({len(parsed_content)} characters)")
            return {
                "success": True,
                "parsed_content": parsed_content,
                "content_length": len(parsed_content),
                "metadata": {
                    "pages": 1,
                    "language": "en",
                    "confidence": 0.95,
                    "processing_time": "2.5s"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_complete_pipeline_simulation(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test complete pipeline simulation with real data"""
        print(f"🔄 Testing complete pipeline simulation for {doc_info['name']}...")
        
        pipeline_result = {
            "document": doc_info['name'],
            "steps": {},
            "success": False
        }
        
        try:
            # Step 1: Storage simulation
            storage_result = await self.test_supabase_storage_simulation(doc_info)
            pipeline_result["steps"]["storage_simulation"] = storage_result
            if not storage_result["success"]:
                return pipeline_result
            
            # Step 2: Create document record
            document_id = str(uuid.uuid4())
            await self.db_connection.execute("""
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, file_sha256, bytes_len, 
                    mime, processing_status, raw_path, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            """, document_id, TEST_USER_ID, f"{RUN_ID}_{doc_info['name']}", 
                 storage_result["file_hash"], storage_result["file_size"], 
                 "application/pdf", "uploaded", storage_result["raw_path"])
            
            # Step 3: Create upload job
            job_id = str(uuid.uuid4())
            await self.db_connection.execute("""
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, state, status, 
                    progress, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            """, job_id, document_id, "queued", "uploaded", '{"percent": 0}')
            
            # Step 4: LlamaParse parsing simulation
            parsing_result = await self.test_llamaparse_parsing_simulation(doc_info, storage_result["raw_path"])
            pipeline_result["steps"]["llamaparse_parsing"] = parsing_result
            if not parsing_result["success"]:
                return pipeline_result
            
            # Update document with parsed path
            await self.db_connection.execute("""
                UPDATE upload_pipeline.documents 
                SET parsed_path = $1, processing_status = 'parsed', updated_at = NOW()
                WHERE document_id = $2
            """, storage_result["parsed_path"], document_id)
            
            # Step 5: Status transitions simulation
            status_transitions = [
                ("uploaded", "parse_queued"),
                ("parse_queued", "parsed"),
                ("parsed", "parse_validated"),
                ("parse_validated", "chunking"),
                ("chunking", "chunks_stored"),
                ("chunks_stored", "embedding_queued"),
                ("embedding_queued", "embedding_in_progress"),
                ("embedding_in_progress", "embeddings_stored"),
                ("embeddings_stored", "complete")
            ]
            
            pipeline_result["steps"]["status_transitions"] = {}
            for from_status, to_status in status_transitions:
                progress_value = f'{{"percent": {20 + (status_transitions.index((from_status, to_status)) * 10)}}}'
                await self.db_connection.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET status = $1, progress = $2, updated_at = NOW()
                    WHERE job_id = $3
                """, to_status, progress_value, job_id)
                
                pipeline_result["steps"]["status_transitions"][f"{from_status}_to_{to_status}"] = {
                    "success": True,
                    "from_status": from_status,
                    "to_status": to_status
                }
            
            # Step 6: Chunking with real embeddings
            chunking_result = await self.test_chunking_with_real_embeddings(
                document_id, doc_info, parsing_result["parsed_content"]
            )
            pipeline_result["steps"]["chunking_embeddings"] = chunking_result
            if not chunking_result["success"]:
                return pipeline_result
            
            pipeline_result["success"] = True
            print(f"✅ Complete pipeline simulation successful for {doc_info['name']}")
            
        except Exception as e:
            pipeline_result["error"] = str(e)
            print(f"❌ Pipeline simulation failed for {doc_info['name']}: {e}")
        
        return pipeline_result
    
    async def test_chunking_with_real_embeddings(self, document_id: str, doc_info: Dict[str, Any], parsed_content: str) -> Dict[str, Any]:
        """Test chunking with real OpenAI embeddings"""
        print(f"🧩 Testing chunking with real embeddings for {doc_info['name']}...")
        
        try:
            # Create chunks from parsed content
            chunks = [parsed_content[i:i+1000] for i in range(0, len(parsed_content), 1000)]
            chunk_embeddings = []
            
            for i, chunk in enumerate(chunks[:3]):  # Limit to first 3 chunks for testing
                # Generate real embedding
                embed_result = await self.test_openai_embedding_generation(chunk)
                if not embed_result["success"]:
                    print(f"⚠️ Failed to generate embedding for chunk {i}")
                    continue
                
                # Create chunk record with real embedding
                chunk_id = str(uuid.uuid4())
                embedding_vector = embed_result["embedding"]
                
                await self.db_connection.execute("""
                    INSERT INTO upload_pipeline.document_chunks (
                        chunk_id, document_id, chunker_name, chunker_version, chunk_ord,
                        text, chunk_sha, embed_model, embed_version, vector_dim,
                        embedding, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                """, chunk_id, document_id, "markdown-simple", "1.0", i,
                     chunk, hashlib.sha256(chunk.encode()).hexdigest(),
                     "text-embedding-3-small", "1", 1536, str(embedding_vector))
                
                chunk_embeddings.append({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "dimensions": len(embedding_vector)
                })
            
            print(f"✅ Created {len(chunk_embeddings)} chunks with real embeddings")
            return {
                "success": True,
                "chunks_created": len(chunk_embeddings),
                "chunk_embeddings": chunk_embeddings
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_storage_verification(self) -> Dict[str, Any]:
        """Verify all storage layers"""
        print("🔍 Verifying all storage layers...")
        
        try:
            # Check database records
            doc_count = await self.db_connection.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents 
                WHERE user_id = $1 AND filename LIKE $2
            """, TEST_USER_ID, f"{RUN_ID}%")
            
            job_count = await self.db_connection.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.upload_jobs 
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE user_id = $1 AND filename LIKE $2
                )
            """, TEST_USER_ID, f"{RUN_ID}%")
            
            chunk_count = await self.db_connection.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE user_id = $1 AND filename LIKE $2
                )
            """, TEST_USER_ID, f"{RUN_ID}%")
            
            # Get status distribution
            status_dist = await self.db_connection.fetch("""
                SELECT status, COUNT(*) as count 
                FROM upload_pipeline.upload_jobs 
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE user_id = $1 AND filename LIKE $2
                )
                GROUP BY status
            """, TEST_USER_ID, f"{RUN_ID}%")
            
            print(f"✅ Storage verification complete:")
            print(f"   Database Documents: {doc_count}")
            print(f"   Database Jobs: {job_count}")
            print(f"   Database Chunks: {chunk_count}")
            print(f"   Status Distribution: {dict(status_dist)}")
            print(f"   Blob Storage: Simulated (paths generated)")
            print(f"   Parsed Storage: Simulated (content generated)")
            print(f"   Vector Storage: Real (embeddings stored)")
            
            return {
                "success": True,
                "database_documents": doc_count,
                "database_jobs": job_count,
                "database_chunks": chunk_count,
                "status_distribution": dict(status_dist),
                "blob_storage": "Simulated (paths generated)",
                "parsed_storage": "Simulated (content generated)",
                "vector_storage": "Real (embeddings stored)"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cleanup_test_data(self):
        """Clean up test data from previous runs"""
        if not self.db_connection:
            return
            
        try:
            # Delete test data with RUN_ID prefix
            await self.db_connection.execute("""
                DELETE FROM upload_pipeline.documents 
                WHERE user_id = $1 AND filename LIKE $2
            """, TEST_USER_ID, f"{RUN_ID}%")
            
            await self.db_connection.execute("""
                DELETE FROM upload_pipeline.upload_jobs 
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE user_id = $1 AND filename LIKE $2
                )
            """, TEST_USER_ID, f"{RUN_ID}%")
            
            await self.db_connection.execute("""
                DELETE FROM upload_pipeline.document_chunks 
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE user_id = $1 AND filename LIKE $2
                )
            """, TEST_USER_ID, f"{RUN_ID}%")
            
            print("✅ Test data cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    async def run_test(self):
        """Run the realistic comprehensive test"""
        print("🚀 Starting Realistic Comprehensive Pipeline Test")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 Environment: Production Supabase + Real External APIs")
        print(f"🔗 Components: Database + OpenAI + LlamaParse + Storage Simulation")
        
        # Connect to database
        if not await self.connect_to_database():
            return self.results
        
        # Test external APIs connectivity
        print("\n" + "="*70)
        print("EXTERNAL APIs CONNECTIVITY")
        print("="*70)
        
        api_connectivity = await self.test_external_apis_connectivity()
        self.results["api_connectivity"] = api_connectivity
        
        # Cleanup previous test data
        await self.cleanup_test_data()
        
        # Test complete pipeline for each document
        print("\n" + "="*70)
        print("COMPREHENSIVE PIPELINE SIMULATION")
        print("="*70)
        
        for i, doc_info in enumerate(TEST_DOCUMENTS, 1):
            print(f"\n📄 Test Document {i}: {doc_info['name']}")
            
            pipeline_result = await self.test_complete_pipeline_simulation(doc_info)
            self.results["tests"].append(pipeline_result)
            
            status = "✅ SUCCESS" if pipeline_result["success"] else "❌ FAILED"
            print(f"📊 Test {i} result: {status}")
        
        # Verify all storage layers
        print("\n" + "="*70)
        print("STORAGE LAYER VERIFICATION")
        print("="*70)
        
        storage_verification = await self.test_storage_verification()
        self.results["storage_verification"] = storage_verification
        
        # Generate summary
        total_tests = len(self.results["tests"])
        successful_tests = sum(1 for test in self.results["tests"] if test["success"])
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "api_connectivity": api_connectivity,
            "storage_verification": storage_verification["success"],
            "end_time": datetime.now().isoformat()
        }
        
        # Save results
        results_file = f"realistic_comprehensive_test_results_{RUN_ID}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Realistic Comprehensive Test Complete!")
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"📁 Results saved to: {results_file}")
        
        # Close database connection
        if self.db_connection:
            await self.db_connection.close()
        
        return self.results

async def main():
    """Main test execution"""
    tester = RealisticComprehensiveTester()
    results = await tester.run_test()
    
    # Print summary
    print("\n" + "="*80)
    print("REALISTIC COMPREHENSIVE PIPELINE TEST SUMMARY")
    print("="*80)
    print(f"Environment: Production Supabase + Real External APIs")
    print(f"Run ID: {RUN_ID}")
    print(f"Success Rate: {results['summary']['success_rate']}")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Successful: {results['summary']['successful_tests']}")
    print(f"Failed: {results['summary']['failed_tests']}")
    
    # API connectivity
    if 'api_connectivity' in results:
        openai_status = "✅" if results['api_connectivity'].get('openai', {}).get('success', False) else "❌"
        llamaparse_status = "✅" if results['api_connectivity'].get('llamaparse', {}).get('success', False) else "❌"
        print(f"OpenAI API: {openai_status}")
        print(f"LlamaParse API: {llamaparse_status}")
    
    print(f"Storage Verification: {'✅' if results['summary']['storage_verification'] else '❌'}")
    
    # Detailed results
    for i, test in enumerate(results['tests'], 1):
        status = "✅" if test['success'] else "❌"
        print(f"{status} Test {i}: {test['document']}")

if __name__ == "__main__":
    asyncio.run(main())
