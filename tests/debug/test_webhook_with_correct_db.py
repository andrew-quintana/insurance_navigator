#!/usr/bin/env python3
"""
Webhook Test with Correct Database Configuration

This script tests the webhook functionality using the correct production database URLs
to validate the complete webhook flow.
"""

import asyncio
import json
import httpx
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Production API configuration
PRODUCTION_API_URL = "https://insurance-navigator-api.onrender.com"
WEBHOOK_ENDPOINT = f"{PRODUCTION_API_URL}/api/upload-pipeline/webhook/llamaparse"

# Production database configuration (from user's environment)
PRODUCTION_DATABASE_URL = "postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres"
PRODUCTION_POOLER_URL = "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
PRODUCTION_SESSION_POOLER_URL = "postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:5432/postgres"

async def test_database_connection():
    """Test database connection with production URLs."""
    print("🔍 TESTING DATABASE CONNECTION WITH PRODUCTION URLS")
    print("-" * 60)
    
    # Test different database URLs
    db_urls = {
        "DATABASE_URL": PRODUCTION_DATABASE_URL,
        "POOLER_URL": PRODUCTION_POOLER_URL,
        "SESSION_POOLER_URL": PRODUCTION_SESSION_POOLER_URL
    }
    
    for name, db_url in db_urls.items():
        print(f"\nTesting {name}:")
        print(f"URL: {db_url[:50]}...")
        
        try:
            import asyncpg
            
            # Test connection
            conn = await asyncpg.connect(
                db_url,
                ssl="require"
            )
            
            # Test simple query
            result = await conn.fetchval("SELECT 1")
            print(f"✅ {name}: Connection successful (result: {result})")
            
            # Test upload_pipeline schema
            try:
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'upload_pipeline'
                """)
                print(f"✅ {name}: Found {len(tables)} tables in upload_pipeline schema")
                for table in tables:
                    print(f"   - {table['table_name']}")
            except Exception as e:
                print(f"⚠️  {name}: Could not query upload_pipeline schema: {e}")
            
            await conn.close()
            
        except Exception as e:
            print(f"❌ {name}: Connection failed: {e}")

async def create_test_job_in_production_db():
    """Create a test job in the production database."""
    print("\n🔍 CREATING TEST JOB IN PRODUCTION DATABASE")
    print("-" * 60)
    
    try:
        import asyncpg
        
        # Use the pooler URL for better performance, disable prepared statements for PgBouncer
        conn = await asyncpg.connect(
            PRODUCTION_POOLER_URL,
            ssl="require",
            statement_cache_size=0
        )
        
        # Generate test data with proper UUIDs
        job_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        webhook_secret = f"secret-{uuid.uuid4().hex[:16]}"
        
        print(f"Job ID: {job_id}")
        print(f"Document ID: {document_id}")
        print(f"User ID: {user_id}")
        print(f"Webhook Secret: {webhook_secret}")
        
        # Create test document first (required for foreign key)
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (document_id) DO UPDATE SET
                processing_status = EXCLUDED.processing_status,
                updated_at = NOW()
        """, document_id, user_id, "test-insurance-policy.pdf", "application/pdf", 1024000, "test-sha256-hash", "test/path/file.pdf", "uploaded", datetime.now())
        
        print("✅ Test document created in upload_pipeline.documents")
        
        # Create test job in upload_pipeline.upload_jobs
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (job_id, document_id, state, status, webhook_secret, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (job_id) DO UPDATE SET
                state = EXCLUDED.state,
                status = EXCLUDED.status,
                webhook_secret = EXCLUDED.webhook_secret,
                updated_at = NOW()
        """, job_id, document_id, "working", "parse_queued", webhook_secret, datetime.now())
        
        print("✅ Test job created in upload_pipeline.upload_jobs")
        
        await conn.close()
        return job_id
        
    except Exception as e:
        print(f"❌ Failed to create test job: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_webhook_with_real_job(job_id: str):
    """Test webhook with a real job that exists in the database."""
    print(f"\n🔍 TESTING WEBHOOK WITH REAL JOB: {job_id}")
    print("-" * 60)
    
    webhook_url = f"{WEBHOOK_ENDPOINT}/{job_id}"
    
    # Realistic LlamaParse webhook payload
    webhook_payload = {
        "status": "completed",
        "result": {
            "md": """# Insurance Policy Document

## Policy Information
**Policy Number:** 12345-67890
**Policy Holder:** John Doe
**Coverage Type:** Health Insurance
**Effective Date:** January 1, 2024
**Expiration Date:** December 31, 2024

## Coverage Details
This policy provides comprehensive health insurance coverage including:

### Inpatient Services
- Hospital stays
- Surgical procedures
- Emergency room visits
- Intensive care unit stays

### Outpatient Services
- Doctor visits
- Specialist consultations
- Laboratory tests
- Diagnostic imaging

### Prescription Drugs
- Generic medications (80% coverage)
- Brand name medications (60% coverage)
- Specialty medications (50% coverage)

## Deductibles and Copayments
- Annual deductible: $1,500 per individual, $3,000 per family
- Office visit copay: $25
- Specialist copay: $50
- Emergency room copay: $150

## Network Information
- In-network providers: Full coverage after deductible
- Out-of-network providers: 70% coverage after deductible
- Preferred provider network available

## Exclusions
- Cosmetic procedures
- Experimental treatments
- Pre-existing conditions (first 12 months)
- Dental and vision (separate coverage required)

## Contact Information
- Customer Service: 1-800-555-0123
- Claims Department: 1-800-555-0124
- Website: www.exampleinsurance.com

## Important Notes
- Prior authorization required for certain procedures
- Referrals needed for specialist visits
- Prescription formulary available online
- 24/7 nurse hotline available""",
            "txt": """Insurance Policy Document

Policy Information
Policy Number: 12345-67890
Policy Holder: John Doe
Coverage Type: Health Insurance
Effective Date: January 1, 2024
Expiration Date: December 31, 2024

Coverage Details
This policy provides comprehensive health insurance coverage including:

Inpatient Services
- Hospital stays
- Surgical procedures
- Emergency room visits
- Intensive care unit stays

Outpatient Services
- Doctor visits
- Specialist consultations
- Laboratory tests
- Diagnostic imaging

Prescription Drugs
- Generic medications (80% coverage)
- Brand name medications (60% coverage)
- Specialty medications (50% coverage)

Deductibles and Copayments
- Annual deductible: $1,500 per individual, $3,000 per family
- Office visit copay: $25
- Specialist copay: $50
- Emergency room copay: $150

Network Information
- In-network providers: Full coverage after deductible
- Out-of-network providers: 70% coverage after deductible
- Preferred provider network available

Exclusions
- Cosmetic procedures
- Experimental treatments
- Pre-existing conditions (first 12 months)
- Dental and vision (separate coverage required)

Contact Information
- Customer Service: 1-800-555-0123
- Claims Department: 1-800-555-0124
- Website: www.exampleinsurance.com

Important Notes
- Prior authorization required for certain procedures
- Referrals needed for specialist visits
- Prescription formulary available online
- 24/7 nurse hotline available"""
        },
        "metadata": {
            "processing_time": 15.2,
            "confidence": 0.94,
            "pages_processed": 8,
            "model_version": "llamaparse-v1.2.0",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print(f"Webhook URL: {webhook_url}")
    print(f"Payload size: {len(json.dumps(webhook_payload))} bytes")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("Sending webhook request...")
            response = await client.post(
                webhook_url,
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "LlamaParse-Webhook/1.0",
                    "X-Webhook-Source": "llamaparse"
                }
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Webhook request successful")
                try:
                    response_data = response.json()
                    print(f"Response Data: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"Response Text: {response.text}")
                return True
            else:
                print(f"❌ Webhook request failed: {response.status_code}")
                print(f"Error Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Webhook request timed out (60s)")
        return False
    except Exception as e:
        print(f"❌ Webhook request failed: {e}")
        return False

async def verify_job_status_update(job_id: str):
    """Verify that the job status was updated in the database."""
    print(f"\n🔍 VERIFYING JOB STATUS UPDATE FOR: {job_id}")
    print("-" * 60)
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            PRODUCTION_POOLER_URL,
            ssl="require",
            statement_cache_size=0
        )
        
        # Check job status
        job = await conn.fetchrow("""
            SELECT uj.status, uj.updated_at, uj.progress, d.processing_status as doc_status
            FROM upload_pipeline.upload_jobs uj
            JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
            WHERE uj.job_id = $1
        """, job_id)
        
        if job:
            print(f"Job Status: {job['status']}")
            print(f"Document Status: {job['doc_status']}")
            print(f"Updated At: {job['updated_at']}")
            print(f"Progress Data: {job['progress'] is not None}")
            
            if job['status'] in ['parsed', 'complete']:
                print(f"✅ Job status updated to {job['status']}")
                return True
            else:
                print(f"⚠️  Job status is {job['status']}, expected 'parsed' or 'complete'")
                return False
        else:
            print("❌ Job not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Failed to verify job status: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 WEBHOOK TEST WITH CORRECT DATABASE CONFIGURATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Production API: {PRODUCTION_API_URL}")
    print()
    
    # Step 1: Test database connections
    await test_database_connection()
    
    # Step 2: Create test job in production database
    job_id = await create_test_job_in_production_db()
    if not job_id:
        print("\n❌ Failed to create test job. Cannot proceed with webhook test.")
        return
    
    # Step 3: Test webhook with real job
    webhook_success = await test_webhook_with_real_job(job_id)
    
    if webhook_success:
        # Step 4: Verify job status update
        status_updated = await verify_job_status_update(job_id)
        
        if status_updated:
            print("\n🎉 COMPLETE WEBHOOK FLOW TEST PASSED!")
            print("✅ Webhook processing is working correctly")
            print("✅ Job status was updated in database")
            print("✅ Document processing completed")
        else:
            print("\n⚠️  WEBHOOK FLOW TEST PARTIALLY PASSED")
            print("✅ Webhook was received")
            print("❌ Job status not updated in database")
    else:
        print("\n❌ WEBHOOK FLOW TEST FAILED!")
        print("❌ Webhook was not processed successfully")
    
    print(f"\n🏁 Test completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())
