#!/usr/bin/env python3
"""
Test RAG functionality with existing data to verify chunk generation and search.
"""

import asyncio
import aiohttp
import logging
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_rag_functionality():
    """Test RAG functionality with existing data."""
    
    base_url = "https://insurance-navigator-api.onrender.com"
    
    # Create test user
    test_user_email = f"rag_test_{uuid.uuid4().hex[:8]}@example.com"
    test_user_password = "TestPassword123!"
    
    async with aiohttp.ClientSession() as session:
        logger.info("🔍 Testing RAG functionality...")
        
        # 1. Create user
        logger.info("1️⃣ Creating test user...")
        signup_data = {
            "email": test_user_email,
            "password": test_user_password,
            "full_name": "RAG Test User",
            "consent_version": "1.0",
            "consent_timestamp": datetime.utcnow().isoformat()
        }
        
        async with session.post(f"{base_url}/auth/signup", json=signup_data) as response:
            if response.status not in [200, 201, 409]:
                logger.error(f"❌ User creation failed: {response.status}")
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
                return False
            
            result = await response.json()
            auth_token = result.get("access_token")
            user_id = result.get("user", {}).get("id")
            logger.info(f"✅ User authenticated successfully - User ID: {user_id}")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 3. Test debug RAG similarity endpoint
        logger.info("3️⃣ Testing debug RAG similarity endpoint...")
        try:
            async with session.get(f"{base_url}/debug/rag-similarity/{user_id}", headers=headers) as response:
                if response.status == 200:
                    rag_data = await response.json()
                    logger.info(f"✅ RAG debug endpoint working: {rag_data}")
                else:
                    logger.warning(f"⚠️ RAG debug endpoint failed: {response.status}")
                    response_text = await response.text()
                    logger.warning(f"Response: {response_text}")
        except Exception as e:
            logger.warning(f"⚠️ RAG debug endpoint error: {e}")
        
        # 4. Test chat endpoint with deductible question
        logger.info("4️⃣ Testing chat endpoint with deductible question...")
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
        
        # 5. Test document status endpoint
        logger.info("5️⃣ Testing document status endpoint...")
        try:
            # We'll use a dummy document ID to test the endpoint
            dummy_doc_id = "00000000-0000-0000-0000-000000000000"
            async with session.get(f"{base_url}/documents/{dummy_doc_id}/status", headers=headers) as response:
                if response.status == 200:
                    doc_status = await response.json()
                    logger.info(f"✅ Document status endpoint working: {doc_status}")
                elif response.status == 404:
                    logger.info("✅ Document status endpoint working (404 expected for dummy ID)")
                else:
                    logger.warning(f"⚠️ Document status endpoint failed: {response.status}")
                    response_text = await response.text()
                    logger.warning(f"Response: {response_text}")
        except Exception as e:
            logger.warning(f"⚠️ Document status endpoint error: {e}")
        
        # 6. Test worker status
        logger.info("6️⃣ Testing worker status...")
        try:
            async with session.get(f"{base_url}/api/v1/status") as response:
                if response.status == 200:
                    worker_status = await response.json()
                    logger.info(f"✅ Worker status: {worker_status}")
                else:
                    logger.warning(f"⚠️ Worker status failed: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Worker status error: {e}")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rag_functionality())
    if success:
        logger.info("🎉 RAG FUNCTIONALITY TEST PASSED!")
    else:
        logger.info("❌ RAG functionality test failed")
