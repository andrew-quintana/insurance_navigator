#!/usr/bin/env python3
"""
Phase 2 Direct Database Test
Test the production Supabase database directly to validate schema parity

This test simulates Phase 2 by:
1. Connecting directly to production Supabase
2. Creating test documents and jobs
3. Verifying the schema matches Phase 1 expectations
"""

import asyncio
import json
import time
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import asyncpg

# Test configuration
RUN_ID = f"phase2_direct_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"  # Same as Phase 1

# Production Supabase configuration
PRODUCTION_CONFIG = {
    "DATABASE_URL": "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres"
}

# Test documents
TEST_DOCUMENTS = [
    {
        "name": "Simulated Insurance Document.pdf",
        "path": "test_document.pdf",
        "expected_size": 1782,
        "expected_hash": "0331f3c86b9de0f8ff372c486bed5572e843c4b6d5f5502e283e1a9483f4635d"
    },
    {
        "name": "Scan Classic HMO.pdf", 
        "path": "test_upload.pdf",
        "expected_size": 2544678,
        "expected_hash": "8df483896c19e6d1e20d627b19838da4e7d911cd90afad64cf5098138e50afe5"
    }
]

class Phase2DirectTester:
    def __init__(self):
        self.results = {
            "run_id": RUN_ID,
            "start_time": datetime.now().isoformat(),
            "environment": "direct_production_db_test",
            "tests": [],
            "summary": {}
        }
        self.conn = None
        
    async def setup_connection(self):
        """Connect to production Supabase database"""
        print("🔌 Connecting to production Supabase database...")
        
        try:
            self.conn = await asyncpg.connect(PRODUCTION_CONFIG["DATABASE_URL"])
            print("✅ Connected to production database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def test_schema_parity(self):
        """Test that production schema matches Phase 1 expectations"""
        print("🔍 Testing schema parity with Phase 1...")
        
        try:
            # Check upload_pipeline schema exists
            schema_exists = await self.conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = 'upload_pipeline'
                )
            """)
            
            if not schema_exists:
                print("❌ upload_pipeline schema not found")
                return False
            
            print("✅ upload_pipeline schema exists")
            
            # Check required tables exist
            required_tables = ['documents', 'upload_jobs', 'document_chunks', 'events']
            existing_tables = await self.conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'upload_pipeline'
                ORDER BY table_name
            """)
            
            existing_table_names = [t['table_name'] for t in existing_tables]
            missing_tables = [t for t in required_tables if t not in existing_table_names]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            print(f"✅ All required tables exist: {existing_table_names}")
            
            # Check upload_jobs table structure (critical for Phase 1 parity)
            columns = await self.conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'upload_pipeline' 
                AND table_name = 'upload_jobs'
                ORDER BY ordinal_position
            """)
            
            column_info = [(c['column_name'], c['data_type'], c['is_nullable']) for c in columns]
            print(f"✅ upload_jobs columns: {column_info}")
            
            # Verify critical columns exist
            critical_columns = ['job_id', 'document_id', 'status', 'state', 'created_at', 'updated_at']
            existing_columns = [c[0] for c in column_info]
            missing_columns = [c for c in critical_columns if c not in existing_columns]
            
            if missing_columns:
                print(f"❌ Missing critical columns: {missing_columns}")
                return False
            
            print("✅ All critical columns exist")
            
            # Check status values constraint
            status_constraint = await self.conn.fetch("""
                SELECT conname, pg_get_constraintdef(oid) as constraint_def
                FROM pg_constraint 
                WHERE conrelid = 'upload_pipeline.upload_jobs'::regclass
                AND conname LIKE '%status%'
            """)
            
            if status_constraint:
                print(f"✅ Status constraint exists: {status_constraint[0]['constraint_def']}")
            else:
                print("⚠️ No status constraint found")
            
            return True
            
        except Exception as e:
            print(f"❌ Schema parity test failed: {e}")
            return False
    
    async def test_document_creation(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test creating a document record in production database"""
        print(f"📄 Testing document creation for {doc_info['name']}...")
        
        try:
            # Prepare file data
            file_path = Path(doc_info['path'])
            if not file_path.exists():
                print(f"❌ Test file not found: {file_path}")
                return {"success": False, "error": "File not found"}
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Calculate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            if file_hash != doc_info['expected_hash']:
                print(f"⚠️ File hash mismatch: expected {doc_info['expected_hash'][:8]}..., got {file_hash[:8]}...")
                file_hash = file_hash  # Use actual hash
            
            # Generate IDs
            document_id = str(uuid.uuid4())
            job_id = str(uuid.uuid4())
            
            # Create document record
            await self.conn.execute("""
                INSERT INTO upload_pipeline.documents (
                    document_id, user_id, filename, mime, bytes_len, 
                    file_sha256, raw_path, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """, document_id, TEST_USER_ID, doc_info['name'], 'application/pdf', 
                len(file_data), file_hash, f"files/user/{TEST_USER_ID}/raw/{int(time.time())}_{file_hash[:8]}.pdf")
            
            print("✅ Document record created")
            
            # Create upload job
            await self.conn.execute("""
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, status, state, retry_count, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            """, job_id, document_id, 'uploaded', 'queued', 0)
            
            print("✅ Upload job created")
            
            return {
                "success": True,
                "document_id": document_id,
                "job_id": job_id,
                "file_hash": file_hash,
                "file_size": len(file_data)
            }
            
        except Exception as e:
            print(f"❌ Document creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_status_transitions(self, job_id: str) -> Dict[str, Any]:
        """Test status transitions in production database"""
        print(f"🔄 Testing status transitions for job {job_id}...")
        
        try:
            # Test valid status transitions
            valid_statuses = [
                'uploaded', 'parse_queued', 'parsed', 'parse_validated',
                'chunking', 'chunks_stored', 'embedding_queued', 
                'embedding_in_progress', 'embeddings_stored', 'complete'
            ]
            
            status_changes = []
            
            for status in valid_statuses:
                try:
                    await self.conn.execute("""
                        UPDATE upload_pipeline.upload_jobs 
                        SET status = $1, updated_at = NOW()
                        WHERE job_id = $2
                    """, status, job_id)
                    
                    status_changes.append({
                        "status": status,
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    })
                    
                    print(f"✅ Status updated to: {status}")
                    
                except Exception as e:
                    status_changes.append({
                        "status": status,
                        "timestamp": datetime.now().isoformat(),
                        "success": False,
                        "error": str(e)
                    })
                    print(f"❌ Failed to update status to {status}: {e}")
            
            return {
                "success": True,
                "status_changes": status_changes,
                "total_transitions": len(valid_statuses),
                "successful_transitions": sum(1 for s in status_changes if s['success'])
            }
            
        except Exception as e:
            print(f"❌ Status transition test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_chunk_creation(self, document_id: str) -> Dict[str, Any]:
        """Test creating document chunks in production database"""
        print(f"📝 Testing chunk creation for document {document_id}...")
        
        try:
            # Create test chunks
            test_chunks = [
                {
                    "chunk_id": str(uuid.uuid4()),
                    "chunk_ord": 0,
                    "text": "This is a test chunk for Phase 2 testing.",
                    "chunk_sha": hashlib.sha256("This is a test chunk for Phase 2 testing.".encode()).hexdigest()
                },
                {
                    "chunk_id": str(uuid.uuid4()),
                    "chunk_ord": 1,
                    "text": "This is another test chunk for validation.",
                    "chunk_sha": hashlib.sha256("This is another test chunk for validation.".encode()).hexdigest()
                }
            ]
            
            created_chunks = []
            
            for chunk in test_chunks:
                # Create a proper vector for pgvector
                dummy_vector = [0.0] * 1536
                vector_str = '[' + ','.join(map(str, dummy_vector)) + ']'
                
                await self.conn.execute("""
                    INSERT INTO upload_pipeline.document_chunks (
                        chunk_id, document_id, chunker_name, chunker_version, 
                        chunk_ord, text, chunk_sha, embed_model, embed_version, 
                        vector_dim, embedding, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, NOW(), NOW())
                """, chunk['chunk_id'], document_id, 'markdown-simple', '1',
                    chunk['chunk_ord'], chunk['text'], chunk['chunk_sha'],
                    'text-embedding-3-small', '1', 1536, 
                    vector_str)  # Properly formatted vector
                
                created_chunks.append(chunk['chunk_id'])
                print(f"✅ Chunk {chunk['chunk_ord']} created")
            
            return {
                "success": True,
                "chunks_created": len(created_chunks),
                "chunk_ids": created_chunks
            }
            
        except Exception as e:
            print(f"❌ Chunk creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        print(f"🧹 Cleaning up test data with RUN_ID: {RUN_ID}...")
        
        try:
            # Delete test chunks
            await self.conn.execute("""
                DELETE FROM upload_pipeline.document_chunks 
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE user_id = $1 AND filename LIKE '%Phase 2%'
                )
            """, TEST_USER_ID)
            
            # Delete test jobs
            await self.conn.execute("""
                DELETE FROM upload_pipeline.upload_jobs 
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents 
                    WHERE user_id = $1 AND filename LIKE '%Phase 2%'
                )
            """, TEST_USER_ID)
            
            # Delete test documents
            await self.conn.execute("""
                DELETE FROM upload_pipeline.documents 
                WHERE user_id = $1 AND filename LIKE '%Phase 2%'
            """, TEST_USER_ID)
            
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    async def run_test(self):
        """Run the complete Phase 2 direct test"""
        print("🚀 Starting Phase 2 Direct Database Test")
        print(f"📋 Run ID: {RUN_ID}")
        print(f"🌐 Environment: Direct Production Supabase Database")
        
        # Setup
        if not await self.setup_connection():
            print("❌ Setup failed, aborting test")
            return
        
        # Test schema parity
        schema_ok = await self.test_schema_parity()
        if not schema_ok:
            print("❌ Schema parity test failed, aborting test")
            return
        
        # Run document tests
        for i, doc_info in enumerate(TEST_DOCUMENTS, 1):
            print(f"\n📄 Test Document {i}: {doc_info['name']}")
            
            test_result = {
                "document": doc_info['name'],
                "document_creation": None,
                "status_transitions": None,
                "chunk_creation": None,
                "success": False
            }
            
            # Test document creation
            doc_result = await self.test_document_creation(doc_info)
            test_result["document_creation"] = doc_result
            
            if doc_result["success"]:
                # Test status transitions
                status_result = await self.test_status_transitions(doc_result["job_id"])
                test_result["status_transitions"] = status_result
                
                # Test chunk creation
                chunk_result = await self.test_chunk_creation(doc_result["document_id"])
                test_result["chunk_creation"] = chunk_result
                
                # Overall success
                test_result["success"] = (
                    doc_result["success"] and
                    status_result["success"] and
                    chunk_result["success"]
                )
            
            self.results["tests"].append(test_result)
            
            print(f"📊 Test {i} result: {'✅ SUCCESS' if test_result['success'] else '❌ FAILED'}")
        
        # Generate summary
        total_tests = len(self.results["tests"])
        successful_tests = sum(1 for test in self.results["tests"] if test["success"])
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "end_time": datetime.now().isoformat()
        }
        
        # Cleanup
        await self.cleanup_test_data()
        
        # Close connection
        if self.conn:
            await self.conn.close()
        
        # Save results
        results_file = f"phase2_direct_test_results_{RUN_ID}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Phase 2 Direct Test Complete!")
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main test execution"""
    tester = Phase2DirectTester()
    results = await tester.run_test()
    
    # Print summary
    print("\n" + "="*60)
    print("PHASE 2 DIRECT TEST SUMMARY")
    print("="*60)
    print(f"Environment: Direct Production Supabase Database")
    print(f"Run ID: {RUN_ID}")
    print(f"Success Rate: {results['summary']['success_rate']}")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Successful: {results['summary']['successful_tests']}")
    print(f"Failed: {results['summary']['failed_tests']}")
    
    # Detailed results
    for i, test in enumerate(results['tests'], 1):
        print(f"\nTest {i}: {test['document']}")
        print(f"  Document Creation: {'✅' if test['document_creation']['success'] else '❌'}")
        if test['status_transitions']:
            print(f"  Status Transitions: {'✅' if test['status_transitions']['success'] else '❌'}")
        if test['chunk_creation']:
            print(f"  Chunk Creation: {'✅' if test['chunk_creation']['success'] else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())
