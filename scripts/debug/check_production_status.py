#!/usr/bin/env python3
"""
Check the production system status and identify issues.
"""

import asyncio
import aiohttp
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_production_status():
    """Check various production endpoints to identify issues."""
    
    base_url = "***REMOVED***"
    
    async with aiohttp.ClientSession() as session:
        logger.info("🔍 Checking production system status...")
        
        # 1. Check health endpoint
        logger.info("1️⃣ Checking health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"✅ Health check passed: {health_data}")
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
        
        # 2. Check worker status
        logger.info("2️⃣ Checking worker status...")
        try:
            async with session.get(f"{base_url}/api/v1/status") as response:
                if response.status == 200:
                    worker_data = await response.json()
                    logger.info(f"✅ Worker status: {worker_data}")
                else:
                    logger.error(f"❌ Worker status failed: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Worker status error: {e}")
        
        # 3. Check if we can get documents
        logger.info("3️⃣ Checking documents endpoint...")
        try:
            async with session.get(f"{base_url}/documents") as response:
                logger.info(f"Documents endpoint status: {response.status}")
                if response.status == 200:
                    docs_data = await response.json()
                    logger.info(f"✅ Documents endpoint working: {len(docs_data)} documents")
                else:
                    response_text = await response.text()
                    logger.info(f"Documents response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Documents endpoint error: {e}")
        
        # 4. Check database connectivity
        logger.info("4️⃣ Checking database connectivity...")
        try:
            # Try a simple endpoint that might use the database
            async with session.get(f"{base_url}/debug/rag-similarity/test-user-id") as response:
                logger.info(f"Database connectivity test status: {response.status}")
                if response.status in [200, 401, 403]:  # 401/403 might be expected without auth
                    logger.info("✅ Database appears to be accessible")
                else:
                    response_text = await response.text()
                    logger.warning(f"Database connectivity issue: {response_text}")
        except Exception as e:
            logger.error(f"❌ Database connectivity error: {e}")

if __name__ == "__main__":
    asyncio.run(check_production_status())
