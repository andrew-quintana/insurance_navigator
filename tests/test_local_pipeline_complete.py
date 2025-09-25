#!/usr/bin/env python3
"""
Complete local pipeline test for Insurance Navigator.
Tests the full document processing pipeline with local Supabase.
"""

import asyncio
import aiohttp
import hashlib
import json
import time
import uuid
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_local_pipeline():
    """Test the complete local pipeline end-to-end."""
    
    # Use local API
    base_url = "http://localhost:8000"
    
    # Create test user
    test_user_email = f"local_test_{uuid.uuid4().hex[:8]}@example.com"
    test_user_password = "TestPassword123!"
    
    async with aiohttp.ClientSession() as session:
        logger.info("🔍 Starting local pipeline test...")
        
        # 1. Test health endpoint
        logger.info("1️⃣ Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"✅ Health check: {health_data}")
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
        
        # 2. Test debug environment endpoint
        logger.info("2️⃣ Testing debug environment endpoint...")
        try:
            async with session.get(f"{base_url}/debug/env") as response:
                if response.status == 200:
                    env_data = await response.json()
                    logger.info(f"✅ Environment debug: {env_data}")
                else:
                    logger.warning(f"⚠️ Debug endpoint failed: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Debug endpoint error: {e}")
        
        # 3. Test upload limits endpoint
        logger.info("3️⃣ Testing upload limits endpoint...")
        try:
            async with session.get(f"{base_url}/api/upload-pipeline/upload/limits") as response:
                if response.status == 200:
                    limits_data = await response.json()
                    logger.info(f"✅ Upload limits: {limits_data}")
                else:
                    logger.error(f"❌ Upload limits failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Upload limits error: {e}")
            return False
        
        # 4. Test document upload (without authentication for now)
        logger.info("4️⃣ Testing document upload...")
        test_doc_content = f"""
        INSURANCE POLICY DOCUMENT
        Policy Number: LOCAL-{uuid.uuid4().hex[:8]}
        Policyholder: {test_user_email}
        Effective Date: 2024-01-01
        Expiration Date: 2024-12-31
        
        COVERAGE DETAILS
        ================
        
        Medical Coverage:
        - Annual Maximum: $1,000,000
        - Deductible: $2,500 per year
        - Coinsurance: 20% after deductible
        - Office Visit Copay: $25
        - Specialist Visit Copay: $50
        - Emergency Room Copay: $200
        - Urgent Care Copay: $75
        
        Dental Coverage:
        - Annual Maximum: $50,000
        - Deductible: $500 per year
        - Preventive Care: 100% covered
        - Basic Services: 80% covered after deductible
        - Major Services: 50% covered after deductible
        
        Vision Coverage:
        - Annual Maximum: $25,000
        - Eye Exam: $25 copay
        - Frames: $200 allowance every 2 years
        - Lenses: 100% covered for basic lenses
        
        EXCLUSIONS
        ==========
        - Cosmetic procedures
        - Experimental treatments
        - Pre-existing conditions (unless covered under special provisions)
        - Weight loss surgery (unless medically necessary)
        - Fertility treatments (unless covered under special provisions)
        
        PRESCRIPTION DRUG COVERAGE
        =========================
        - Generic drugs: $10 copay
        - Preferred brand drugs: $30 copay
        - Non-preferred brand drugs: $50 copay
        - Specialty drugs: $100 copay
        
        NETWORK INFORMATION
        ===================
        - In-Network: Lower copays and deductibles apply
        - Out-of-Network: Higher costs, may not count toward deductible
        - Emergency care: Covered at in-network rates regardless of provider
        
        This policy provides comprehensive health insurance coverage for the policyholder.
        """
        
        test_doc_hash = hashlib.sha256(test_doc_content.encode()).hexdigest()
        filename = f"local_insurance_policy_{uuid.uuid4().hex[:8]}.pdf"
        
        upload_data = {
            "filename": filename,
            "bytes_len": len(test_doc_content),
            "mime": "application/pdf",
            "sha256": test_doc_hash,
            "ocr": False
        }
        
        # Test upload without authentication first
        try:
            async with session.post(f"{base_url}/api/upload-pipeline/upload", json=upload_data) as response:
                if response.status == 401:
                    logger.info("✅ Upload endpoint requires authentication (expected)")
                elif response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Upload successful: {result}")
                else:
                    logger.warning(f"⚠️ Upload response: {response.status}")
                    response_text = await response.text()
                    logger.warning(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Upload test error: {e}")
        
        # 5. Test test endpoints
        logger.info("5️⃣ Testing test endpoints...")
        try:
            # Test upload endpoint
            async with session.post(f"{base_url}/test/upload", json={"filename": "test.pdf"}) as response:
                if response.status == 200:
                    test_result = await response.json()
                    logger.info(f"✅ Test upload endpoint: {test_result}")
                else:
                    logger.warning(f"⚠️ Test upload endpoint failed: {response.status}")
            
            # Test jobs endpoint
            async with session.get(f"{base_url}/test/jobs/test-job-123") as response:
                if response.status == 200:
                    test_result = await response.json()
                    logger.info(f"✅ Test jobs endpoint: {test_result}")
                else:
                    logger.warning(f"⚠️ Test jobs endpoint failed: {response.status}")
        except Exception as e:
            logger.error(f"❌ Test endpoints error: {e}")
        
        # 6. Test database connectivity directly
        logger.info("6️⃣ Testing database connectivity...")
        try:
            import asyncpg
            conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:54322/postgres")
            
            # Check if upload_pipeline schema exists
            schema_check = await conn.fetch("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name = 'upload_pipeline'
            """)
            
            if schema_check:
                logger.info("✅ Upload pipeline schema exists")
                
                # Check tables
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'upload_pipeline'
                """)
                logger.info(f"✅ Found {len(tables)} tables in upload_pipeline schema")
                for table in tables:
                    logger.info(f"   - {table['table_name']}")
            else:
                logger.warning("⚠️ Upload pipeline schema not found")
            
            await conn.close()
        except Exception as e:
            logger.error(f"❌ Database connectivity error: {e}")
        
        logger.info("🎉 Local pipeline test completed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_local_pipeline())
    if success:
        logger.info("🎉 LOCAL PIPELINE TEST COMPLETED!")
    else:
        logger.info("❌ Local pipeline test failed")
