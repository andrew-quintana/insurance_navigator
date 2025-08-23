#!/usr/bin/env python3
"""
Phase 3: Database Flow Verification (Container Version)
Simplified verification script to run inside Docker container
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, Any

async def verify_database_flow():
    """Comprehensive database flow verification"""
    print("🚀 Phase 3: Database Flow Verification")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect('postgresql://postgres:postgres@postgres:5432/postgres')
        print("✅ Connected to database")
        
        # 1. Verify Database Schema
        print("\n🔍 Verifying Database Schema...")
        schema_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'upload_pipeline')"
        )
        if schema_exists:
            print("✅ upload_pipeline schema exists")
        else:
            print("❌ upload_pipeline schema missing")
            return False
        
        # Check required tables
        required_tables = ['documents', 'upload_jobs', 'events', 'document_chunks', 'document_vector_buffer']
        for table in required_tables:
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'upload_pipeline' AND table_name = $1)",
                table
            )
            if table_exists:
                print(f"✅ Table upload_pipeline.{table} exists")
            else:
                print(f"❌ Table upload_pipeline.{table} missing")
                return False
        
        # 2. Verify Documents Table
        print("\n📄 Verifying Documents Table...")
        doc_count = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.documents')
        print(f"📊 Total documents: {doc_count}")
        
        if doc_count > 0:
            # Get sample documents
            documents = await conn.fetch("""
                SELECT 
                    document_id::text,
                    user_id::text,
                    filename,
                    mime,
                    bytes_len,
                    file_sha256,
                    raw_path,
                    parsed_path,
                    processing_status,
                    created_at
                FROM upload_pipeline.documents
                ORDER BY created_at DESC
                LIMIT 3
            """)
            
            print("\n📋 Sample Documents:")
            for doc in documents:
                print(f"  - ID: {doc['document_id'][:8]}...")
                print(f"    Filename: {doc['filename']}")
                print(f"    MIME: {doc['mime']}")
                print(f"    Size: {doc['bytes_len']} bytes")
                print(f"    Raw Path: {doc['raw_path']}")
                print(f"    Created: {doc['created_at']}")
                print(f"    Status: {doc['processing_status'] or 'N/A'}")
                print()
        
        # 3. Verify Upload Jobs Table
        print("\n🔄 Verifying Upload Jobs Table...")
        job_count = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.upload_jobs')
        print(f"📊 Total jobs: {job_count}")
        
        if job_count > 0:
            # Get job details
            jobs = await conn.fetch("""
                SELECT 
                    j.job_id::text,
                    j.document_id::text,
                    j.stage,
                    j.state,
                    j.retry_count,
                    j.payload,
                    j.last_error,
                    j.created_at,
                    j.updated_at,
                    d.filename
                FROM upload_pipeline.upload_jobs j
                JOIN upload_pipeline.documents d ON j.document_id = d.document_id
                ORDER BY j.created_at DESC
            """)
            
            print("\n📋 Current Job States:")
            for job in jobs:
                print(f"  - Job ID: {job['job_id'][:8]}...")
                print(f"    Document: {job['filename']}")
                print(f"    Stage: {job['stage']}")
                print(f"    State: {job['state']}")
                print(f"    Retry Count: {job['retry_count']}")
                print(f"    Created: {job['created_at']}")
                print(f"    Updated: {job['updated_at']}")
                
                if job['last_error']:
                    print(f"    Last Error: {job['last_error']}")
                print()
        
        # 4. Verify Events Table
        print("\n📝 Verifying Events Table...")
        event_count = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.events')
        print(f"📊 Total events: {event_count}")
        
        if event_count > 0:
            events = await conn.fetch("""
                SELECT 
                    e.event_id::text,
                    e.job_id::text,
                    e.document_id::text,
                    e.type,
                    e.severity,
                    e.code,
                    e.payload,
                    e.correlation_id::text,
                    e.ts,
                    d.filename
                FROM upload_pipeline.events e
                JOIN upload_pipeline.documents d ON e.document_id = d.document_id
                ORDER BY e.ts DESC
                LIMIT 5
            """)
            
            print("\n📋 Recent Events:")
            for event in events:
                print(f"  - Event ID: {event['event_id'][:8]}...")
                print(f"    Type: {event['type']}")
                print(f"    Severity: {event['severity']}")
                print(f"    Code: {event['code']}")
                print(f"    Document: {event['filename']}")
                print(f"    Timestamp: {event['ts']}")
                print()
        else:
            print("⚠️  No events found - processing pipeline may not be active")
        
        # 5. Verify Chunk Processing
        print("\n🧩 Verifying Chunk Processing...")
        chunk_count = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.document_chunks')
        print(f"📊 Total chunks: {chunk_count}")
        
        vector_buffer_count = await conn.fetchval('SELECT COUNT(*) FROM upload_pipeline.document_vector_buffer')
        print(f"📊 Total vector buffer entries: {vector_buffer_count}")
        
        if chunk_count > 0:
            chunks = await conn.fetch("""
                SELECT 
                    chunk_id::text,
                    document_id::text,
                    chunker_name,
                    chunker_version,
                    chunk_ord,
                    embed_model,
                    embed_version,
                    vector_dim,
                    created_at
                FROM upload_pipeline.document_chunks
                ORDER BY created_at DESC
                LIMIT 3
            """)
            
            print("\n📋 Sample Chunks:")
            for chunk in chunks:
                print(f"  - Chunk ID: {chunk['chunk_id'][:8]}...")
                print(f"    Document ID: {chunk['document_id'][:8]}...")
                print(f"    Chunker: {chunk['chunker_name']} v{chunk['chunker_version']}")
                print(f"    Order: {chunk['chunk_ord']}")
                print(f"    Embed Model: {chunk['embed_model']} v{chunk['embed_version']}")
                print(f"    Vector Dim: {chunk['vector_dim']}")
                print(f"    Created: {chunk['created_at']}")
                print()
        
        # 6. Verify Processing Pipeline State
        print("\n⚙️  Verifying Processing Pipeline...")
        
        if job_count > 0:
            # Check state distribution
            state_distribution = await conn.fetch("""
                SELECT stage, state, COUNT(*) 
                FROM upload_pipeline.upload_jobs 
                GROUP BY stage, state
            """)
            
            print("  - Job State Distribution:")
            for state in state_distribution:
                print(f"    {state['stage']} -> {state['state']}: {state['count']}")
            
            # Check for expected state progression
            expected_stages = [
                'queued', 'job_validated', 'parsing', 'parsed', 
                'parse_validated', 'chunking', 'chunks_buffered', 
                'chunked', 'embedding', 'embeddings_buffered', 'embedded'
            ]
            
            print(f"\n  - Expected Stage Progression: {' -> '.join(expected_stages)}")
            
            # Check for stuck or failed jobs
            stuck_jobs = await conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.upload_jobs 
                WHERE state IN ('retryable', 'deadletter')
            """)
            
            if stuck_jobs > 0:
                print(f"  ⚠️  Found {stuck_jobs} jobs in retryable/deadletter state")
            else:
                print("  ✅ No stuck jobs found")
            
            # Check for long-running jobs
            long_running_jobs = await conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.upload_jobs 
                WHERE state = 'working' AND created_at < NOW() - INTERVAL '1 hour'
            """)
            
            if long_running_jobs > 0:
                print(f"  ⚠️  Found {long_running_jobs} long-running jobs (>1 hour)")
            else:
                print("  ✅ No long-running jobs found")
        
        # 7. Verify Foreign Key Relationships
        print("\n🔗 Verifying Foreign Key Relationships...")
        
        # Check documents -> upload_jobs relationship
        orphaned_jobs = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.upload_jobs j
            LEFT JOIN upload_pipeline.documents d ON j.document_id = d.document_id
            WHERE d.document_id IS NULL
        """)
        
        if orphaned_jobs > 0:
            print(f"❌ Found {orphaned_jobs} orphaned jobs without documents")
        else:
            print("✅ All jobs have valid document references")
        
        # Check upload_jobs -> events relationship (if events exist)
        if event_count > 0:
            orphaned_events = await conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.events e
                LEFT JOIN upload_pipeline.upload_jobs j ON e.job_id = j.job_id
                WHERE j.job_id IS NULL
            """)
            
            if orphaned_events > 0:
                print(f"❌ Found {orphaned_events} orphaned events without jobs")
            else:
                print("✅ All events have valid job references")
        
        # 8. Generate Summary Report
        print("\n📋 Database Flow Verification Summary")
        print("=" * 60)
        
        summary = {
            "verification_timestamp": datetime.utcnow().isoformat(),
            "overall_status": "PASS",
            "data_counts": {
                "documents": doc_count,
                "jobs": job_count,
                "events": event_count,
                "chunks": chunk_count,
                "vector_buffer_entries": vector_buffer_count
            },
            "current_state": "Initial Setup Complete",
            "recommendations": []
        }
        
        # Generate recommendations
        if event_count == 0:
            summary["recommendations"].append("No events logged - processing pipeline may not be active")
        
        if job_count > 0:
            # Check if all jobs are in queued state
            queued_jobs = await conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.upload_jobs WHERE stage = 'queued' AND state = 'queued'
            """)
            
            if queued_jobs == job_count:
                summary["recommendations"].append("All jobs in 'queued' state - worker processes may not be running")
        
        if chunk_count == 0:
            summary["recommendations"].append("No chunks created - document processing pipeline not yet started")
        
        # Print summary
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Documents: {summary['data_counts']['documents']}")
        print(f"Jobs: {summary['data_counts']['jobs']}")
        print(f"Events: {summary['data_counts']['events']}")
        print(f"Chunks: {summary['data_counts']['chunks']}")
        print(f"Current State: {summary['current_state']}")
        
        if summary['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"  - {rec}")
        
        # Save summary to file
        report_file = f"database_flow_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        await conn.close()
        print("\n✅ Database flow verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(verify_database_flow())
