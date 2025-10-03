#!/usr/bin/env python3
"""
LlamaParse Webhook Flow Test

This script simulates the complete LlamaParse webhook flow:
1. Creates a job in the database (simulating upload pipeline)
2. Simulates LlamaParse processing the document
3. Sends webhook callback to production API
4. Validates the webhook processing and database updates
"""

import asyncio
import json
import httpx
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Production API configuration
PRODUCTION_API_URL = "https://insurance-navigator-api.onrender.com"
WEBHOOK_ENDPOINT = f"{PRODUCTION_API_URL}/api/upload-pipeline/webhook/llamaparse"

async def create_test_job_in_database() -> Optional[str]:
    """Create a test job in the database to simulate upload pipeline."""
    print("🔍 CREATING TEST JOB IN DATABASE")
    print("-" * 50)
    
    try:
        # Import database modules
        from api.upload_pipeline.database import get_database
        from core.database import initialize_database
        
        # Generate test data
        job_id = f"test-webhook-{uuid.uuid4().hex[:8]}"
        document_id = f"doc-{uuid.uuid4().hex[:8]}"
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        webhook_secret = f"secret-{uuid.uuid4().hex[:16]}"
        
        print(f"Job ID: {job_id}")
        print(f"Document ID: {document_id}")
        print(f"User ID: {user_id}")
        print(f"Webhook Secret: {webhook_secret}")
        
        # Get database connections
        upload_db = get_database()
        
        # Initialize databases if needed
        if not upload_db.pool:
            print("Initializing upload pipeline database...")
            await upload_db.initialize()
        
        print("Initializing main database...")
        main_db = await initialize_database()
        
        # Create test job in upload pipeline database
        async with upload_db.get_connection() as conn:
            print("Creating test job in upload_pipeline.upload_jobs...")
            
            # Insert test document
            await conn.execute("""
                INSERT INTO upload_pipeline.documents (document_id, user_id, filename, status, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (document_id) DO NOTHING
            """, document_id, user_id, "test-insurance-policy.pdf", "uploaded", datetime.now())
            
            # Insert test job
            await conn.execute("""
                INSERT INTO upload_pipeline.upload_jobs (job_id, document_id, status, webhook_secret, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (job_id) DO NOTHING
            """, job_id, document_id, "processing", webhook_secret, datetime.now())
            
            print("✅ Test job created successfully")
        
        # Create test user in main database
        async with main_db.get_connection() as conn:
            print("Creating test user in main database...")
            
            await conn.execute("""
                INSERT INTO users (user_id, email, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id, f"test-{user_id}@example.com", datetime.now())
            
            print("✅ Test user created successfully")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Failed to create test job: {e}")
        import traceback
        traceback.print_exc()
        return None

async def simulate_llamaparse_processing(job_id: str) -> Dict[str, Any]:
    """Simulate LlamaParse processing a document and generating results."""
    print(f"\n🔍 SIMULATING LLAMAPARSE PROCESSING FOR JOB: {job_id}")
    print("-" * 50)
    
    # Simulate realistic LlamaParse response
    llamaparse_result = {
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
    
    print("✅ LlamaParse processing simulation completed")
    print(f"Processing time: {llamaparse_result['metadata']['processing_time']}s")
    print(f"Confidence: {llamaparse_result['metadata']['confidence']}")
    print(f"Pages processed: {llamaparse_result['metadata']['pages_processed']}")
    
    return llamaparse_result

async def send_webhook_to_production(job_id: str, webhook_data: Dict[str, Any]) -> bool:
    """Send webhook to production API service."""
    print(f"\n🔍 SENDING WEBHOOK TO PRODUCTION API")
    print("-" * 50)
    
    webhook_url = f"{WEBHOOK_ENDPOINT}/{job_id}"
    print(f"Webhook URL: {webhook_url}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("Sending webhook request...")
            print(f"Payload size: {len(json.dumps(webhook_data))} bytes")
            
            response = await client.post(
                webhook_url,
                json=webhook_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "LlamaParse-Webhook/1.0",
                    "X-Webhook-Source": "llamaparse"
                }
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Webhook sent successfully")
                try:
                    response_data = response.json()
                    print(f"Response Data: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"Response Text: {response.text}")
                return True
            else:
                print(f"❌ Webhook failed: {response.status_code}")
                print(f"Error Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Webhook request timed out (60s)")
        print("This suggests the webhook handler is hanging")
        return False
    except Exception as e:
        print(f"❌ Webhook request failed: {e}")
        return False

async def verify_job_status_in_database(job_id: str) -> bool:
    """Verify that the job status was updated in the database."""
    print(f"\n🔍 VERIFYING JOB STATUS IN DATABASE")
    print("-" * 50)
    
    try:
        from api.upload_pipeline.database import get_database
        
        db = get_database()
        if not db.pool:
            await db.initialize()
        
        async with db.get_connection() as conn:
            # Check job status
            job = await conn.fetchrow("""
                SELECT uj.status, uj.updated_at, uj.result_data, d.status as doc_status
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.job_id = $1
            """, job_id)
            
            if job:
                print(f"Job Status: {job['status']}")
                print(f"Document Status: {job['doc_status']}")
                print(f"Updated At: {job['updated_at']}")
                print(f"Result Data: {job['result_data'] is not None}")
                
                if job['status'] == 'completed':
                    print("✅ Job status updated to completed")
                    return True
                else:
                    print(f"⚠️  Job status is {job['status']}, expected 'completed'")
                    return False
            else:
                print("❌ Job not found in database")
                return False
                
    except Exception as e:
        print(f"❌ Failed to verify job status: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_production_api_health() -> bool:
    """Test if production API is accessible."""
    print("🔍 TESTING PRODUCTION API HEALTH")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try different endpoints
            endpoints = ["/", "/health", "/docs", "/api/health"]
            
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{PRODUCTION_API_URL}{endpoint}")
                    print(f"{endpoint}: {response.status_code}")
                    if response.status_code != 404:
                        print(f"✅ Production API is accessible at {endpoint}")
                        return True
                except Exception as e:
                    print(f"{endpoint}: Error - {e}")
            
            print("❌ Production API is not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Production API health check failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 LLAMAPARSE WEBHOOK FLOW TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Production API: {PRODUCTION_API_URL}")
    print()
    
    # Step 1: Test production API health
    api_healthy = await test_production_api_health()
    if not api_healthy:
        print("\n❌ Production API is not accessible. Cannot proceed with webhook test.")
        print("Please check:")
        print("1. Production API deployment status on Render")
        print("2. Environment variables are set correctly")
        print("3. Database connectivity in production")
        return
    
    # Step 2: Create test job in database
    job_id = await create_test_job_in_database()
    if not job_id:
        print("\n❌ Failed to create test job. Cannot proceed with webhook test.")
        return
    
    # Step 3: Simulate LlamaParse processing
    webhook_data = await simulate_llamaparse_processing(job_id)
    
    # Step 4: Send webhook to production
    webhook_success = await send_webhook_to_production(job_id, webhook_data)
    
    if webhook_success:
        # Step 5: Verify job status in database
        status_updated = await verify_job_status_in_database(job_id)
        
        if status_updated:
            print("\n🎉 LLAMAPARSE WEBHOOK FLOW TEST PASSED!")
            print("✅ Complete webhook flow is working correctly")
        else:
            print("\n⚠️  LLAMAPARSE WEBHOOK FLOW TEST PARTIALLY PASSED")
            print("✅ Webhook was received but job status not updated")
    else:
        print("\n❌ LLAMAPARSE WEBHOOK FLOW TEST FAILED!")
        print("❌ Webhook was not processed successfully")
    
    print(f"\n🏁 Test completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())
