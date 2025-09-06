#!/usr/bin/env python3
"""
Simple Webhook Test
Test webhook functionality with a simple job creation and webhook call
"""

import asyncio
import json
import time
import uuid
import hashlib
import httpx
import asyncpg
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env.production')

# Test configuration
RUN_ID = f"simple_webhook_{int(time.time())}"
TEST_USER_ID = "766e8693-7fd5-465e-9ee4-4a9b3a696480"
WEBHOOK_URL = "http://localhost:8001/webhook/llamaparse"

# API Configuration
API_CONFIG = {
    "DATABASE_URL": os.getenv("DATABASE_URL"),
}

async def test_webhook_integration():
    """Test complete webhook integration"""
    print("🚀 Starting Simple Webhook Integration Test")
    print(f"📋 Run ID: {RUN_ID}")
    print(f"🌐 Webhook URL: {WEBHOOK_URL}")
    
    # Connect to database
    try:
        db_connection = await asyncpg.connect(API_CONFIG["DATABASE_URL"])
        print("✅ Connected to production Supabase database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    try:
        # Step 1: Create test job in database
        print("\n📄 Creating test job...")
        job_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        filename = f"webhook_test_{RUN_ID}.pdf"
        
        # Generate unique file hash
        unique_content = f"{filename}_{RUN_ID}".encode()
        file_hash = hashlib.sha256(unique_content).hexdigest()
        
        # Insert document
        doc_query = """
            INSERT INTO upload_pipeline.documents 
            (document_id, filename, file_sha256, bytes_len, mime, processing_status, raw_path, user_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        
        await db_connection.execute(
            doc_query,
            document_id,
            filename,
            file_hash,
            1000,
            'application/pdf',
            'uploaded',
            f"files/{TEST_USER_ID}/raw/{filename}",
            TEST_USER_ID,
            datetime.now(),
            datetime.now()
        )
        
        # Insert job
        job_query = """
            INSERT INTO upload_pipeline.upload_jobs 
            (job_id, document_id, state, status, progress, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        await db_connection.execute(
            job_query,
            job_id,
            document_id,
            'queued',
            'parse_queued',
            '0.0',
            datetime.now(),
            datetime.now()
        )
        
        print(f"✅ Test job created: {job_id}")
        
        # Step 2: Test webhook call
        print("\n📥 Testing webhook call...")
        webhook_payload = {
            "job_id": job_id,
            "status": "completed",
            "result_url": f"https://example.com/parsed_{job_id}.md",
            "timestamp": datetime.now().isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WEBHOOK_URL,
                json=webhook_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Webhook call successful: {result}")
            else:
                print(f"❌ Webhook call failed: {response.status_code} - {response.text}")
                return False
        
        # Step 3: Verify database update
        print("\n🔍 Verifying database update...")
        query = """
            SELECT job_id, status, progress, updated_at
            FROM upload_pipeline.upload_jobs 
            WHERE job_id = $1
        """
        
        db_result = await db_connection.fetchrow(query, job_id)
        
        if db_result and db_result['status'] == 'parsed':
            print(f"✅ Database updated successfully: {dict(db_result)}")
            success = True
        else:
            print(f"❌ Database update failed: {db_result}")
            success = False
        
        # Step 4: Cleanup
        print("\n🧹 Cleaning up test data...")
        try:
            await db_connection.execute(
                "DELETE FROM upload_pipeline.upload_jobs WHERE job_id = $1",
                job_id
            )
            await db_connection.execute(
                "DELETE FROM upload_pipeline.documents WHERE document_id = $1",
                document_id
            )
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        await db_connection.close()

async def main():
    """Main test execution"""
    success = await test_webhook_integration()
    
    print("\n" + "="*60)
    print("SIMPLE WEBHOOK INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("🎉 Webhook integration is working correctly!")
        print("✅ Job creation: Working")
        print("✅ Webhook processing: Working") 
        print("✅ Database updates: Working")
        print("✅ Status transitions: Working")
    else:
        print("❌ Webhook integration needs fixes")

if __name__ == "__main__":
    asyncio.run(main())
