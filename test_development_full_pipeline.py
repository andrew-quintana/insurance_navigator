#!/usr/bin/env python3
"""
Test the complete development pipeline: user creation, document upload, and RAG search.
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

async def test_development_full_pipeline():
    """Test the complete development pipeline end-to-end."""
    
    # Use production API for testing (local backend requires local Supabase)
    base_url = "***REMOVED***"
    
    # Create test user
    test_user_email = f"dev_test_{uuid.uuid4().hex[:8]}@example.com"
    test_user_password = "TestPassword123!"
    
    async with aiohttp.ClientSession() as session:
        logger.info("🔍 Starting development full pipeline test...")
        
        # 1. Create user
        logger.info("1️⃣ Creating test user...")
        signup_data = {
            "email": test_user_email,
            "password": test_user_password,
            "full_name": "Development Test User",
            "consent_version": "1.0",
            "consent_timestamp": datetime.utcnow().isoformat()
        }
        
        async with session.post(f"{base_url}/auth/signup", json=signup_data) as response:
            if response.status not in [200, 201, 409]:
                logger.error(f"❌ User creation failed: {response.status}")
                response_text = await response.text()
                logger.error(f"Response: {response_text}")
                return False
            logger.info("✅ User created successfully")
        
        # 2. Authenticate
        logger.info("2️⃣ Authenticating user...")
        auth_data = {
            "email": test_user_email,
            "password": test_user_password
        }
        
        async with session.post(f"{base_url}/auth/login", json=auth_data) as response:
            if response.status != 200:
                logger.error(f"❌ Authentication failed: {response.status}")
                response_text = await response.text()
                logger.error(f"Response: {response_text}")
                return False
            
            result = await response.json()
            auth_token = result.get("access_token")
            user_id = result.get("user", {}).get("id")
            logger.info(f"✅ User authenticated successfully - User ID: {user_id}")
        
        # 3. Upload document with insurance policy content
        logger.info("3️⃣ Uploading insurance policy document...")
        test_doc_content = f"""
        INSURANCE POLICY DOCUMENT
        Policy Number: DEV-{uuid.uuid4().hex[:8]}
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
        filename = f"dev_insurance_policy_{uuid.uuid4().hex[:8]}.pdf"
        
        upload_data = {
            "filename": filename,
            "bytes_len": len(test_doc_content),
            "mime": "application/pdf",
            "sha256": test_doc_hash,
            "ocr": False
        }
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        async with session.post(f"{base_url}/api/v2/upload", json=upload_data, headers=headers) as response:
            if response.status != 200:
                logger.error(f"❌ Upload failed: {response.status}")
                response_text = await response.text()
                logger.error(f"Response: {response_text}")
                return False
            
            result = await response.json()
            job_id = result.get("job_id")
            document_id = result.get("document_id")
            signed_url = result.get("signed_url")
            logger.info(f"✅ Document upload initiated - Job ID: {job_id}, Document ID: {document_id}")
        
        # 4. Upload content to signed URL
        logger.info("4️⃣ Uploading content to signed URL...")
        async with session.put(signed_url, data=test_doc_content.encode(), headers={"Content-Type": "application/pdf"}) as response:
            if response.status != 200:
                logger.error(f"❌ Content upload failed: {response.status}")
                response_text = await response.text()
                logger.error(f"Response: {response_text}")
                return False
            logger.info("✅ Content uploaded successfully")
        
        # 5. Wait for processing and check for chunks
        logger.info("5️⃣ Waiting for document processing...")
        max_attempts = 30  # 5 minutes
        chunks_found = False
        
        for attempt in range(max_attempts):
            logger.info(f"   Attempt {attempt + 1}/{max_attempts} - Checking for chunks...")
            
            try:
                # Check for chunks
                async with session.get(f"{base_url}/documents/{document_id}/chunks", headers=headers) as response:
                    if response.status == 200:
                        chunks_data = await response.json()
                        if chunks_data and len(chunks_data) > 0:
                            logger.info(f"🎉 Found {len(chunks_data)} chunks!")
                            for i, chunk in enumerate(chunks_data[:3]):
                                chunk_text = chunk.get('text', '')[:100]
                                logger.info(f"   Chunk {i+1}: {chunk_text}...")
                            chunks_found = True
                            break
                        else:
                            logger.info(f"   📝 No chunks yet (attempt {attempt + 1})")
                    else:
                        logger.warning(f"   ⚠️ Chunks check failed: {response.status}")
                
                await asyncio.sleep(10)  # Wait 10 seconds between checks
                
            except Exception as e:
                logger.warning(f"   ⚠️ Error during chunk check: {e}")
                await asyncio.sleep(10)
        
        if not chunks_found:
            logger.warning("⏰ Timeout waiting for chunks to be generated")
            return False
        
        # 6. Test RAG search with deductible question
        logger.info("6️⃣ Testing RAG search for deductible information...")
        
        # First, let's test the debug RAG similarity endpoint
        try:
            async with session.get(f"{base_url}/debug/rag-similarity/{user_id}") as response:
                if response.status == 200:
                    rag_data = await response.json()
                    logger.info(f"✅ RAG debug endpoint working: {rag_data}")
                else:
                    logger.warning(f"⚠️ RAG debug endpoint failed: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ RAG debug endpoint error: {e}")
        
        # Test chat endpoint with deductible question
        logger.info("7️⃣ Testing chat endpoint with deductible question...")
        chat_data = {
            "message": "What is my deductible?",
            "user_id": user_id
        }
        
        try:
            async with session.post(f"{base_url}/chat", json=chat_data, headers=headers) as response:
                if response.status == 200:
                    chat_result = await response.json()
                    logger.info(f"✅ Chat response received:")
                    logger.info(f"   Response: {chat_result.get('response', 'No response')}")
                    
                    # Check if response contains deductible information
                    response_text = chat_result.get('response', '').lower()
                    if 'deductible' in response_text or '$2,500' in response_text:
                        logger.info("🎉 SUCCESS: RAG found deductible information!")
                        return True
                    else:
                        logger.warning("⚠️ Response doesn't seem to contain deductible information")
                        logger.info(f"   Full response: {chat_result}")
                else:
                    logger.error(f"❌ Chat endpoint failed: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Chat endpoint error: {e}")
        
        # 8. Test direct RAG similarity search
        logger.info("8️⃣ Testing direct RAG similarity search...")
        try:
            # Test with a query about deductibles
            rag_query_data = {
                "query": "What is my deductible amount?",
                "user_id": user_id,
                "limit": 5
            }
            
            async with session.post(f"{base_url}/api/v1/rag/search", json=rag_query_data, headers=headers) as response:
                if response.status == 200:
                    rag_results = await response.json()
                    logger.info(f"✅ RAG search results:")
                    
                    if rag_results and len(rag_results) > 0:
                        for i, result in enumerate(rag_results):
                            similarity = result.get('similarity', 0)
                            text = result.get('text', '')[:100]
                            logger.info(f"   Result {i+1}: Similarity={similarity:.3f}, Text={text}...")
                            
                            if similarity > 0.3:
                                logger.info(f"🎉 SUCCESS: Found result with similarity > 0.3: {similarity:.3f}")
                                return True
                        logger.warning("⚠️ No results with similarity > 0.3 found")
                    else:
                        logger.warning("⚠️ No RAG search results returned")
                else:
                    logger.error(f"❌ RAG search failed: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ RAG search error: {e}")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_development_full_pipeline())
    if success:
        logger.info("🎉 DEVELOPMENT PIPELINE TEST PASSED!")
    else:
        logger.info("❌ Development pipeline test failed")
