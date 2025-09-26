#!/usr/bin/env python3
"""
Debug script to test Supabase connection and identify issues.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.development'))

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_supabase_connection():
    """Debug Supabase connection issues."""
    logger.info("🔍 Debugging Supabase connection...")
    
    # Check environment variables
    logger.info("📋 Checking environment variables...")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    logger.info(f"SUPABASE_URL: {supabase_url}")
    logger.info(f"SUPABASE_ANON_KEY: {supabase_anon_key[:20]}..." if supabase_anon_key else "None")
    logger.info(f"SUPABASE_SERVICE_ROLE_KEY: {supabase_service_key[:20]}..." if supabase_service_key else "None")
    
    if not supabase_url or not supabase_anon_key:
        logger.error("❌ Missing required environment variables")
        return False
    
    # Test basic Supabase client creation
    try:
        logger.info("🔧 Testing basic Supabase client creation...")
        from supabase import create_client
        
        client = create_client(supabase_url, supabase_anon_key)
        logger.info("✅ Basic Supabase client created successfully")
        
        # Test a simple query
        logger.info("🔍 Testing simple query...")
        result = client.table("user_info").select("*").limit(1).execute()
        logger.info(f"✅ Query successful: {len(result.data)} rows returned")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase client creation failed: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def debug_database_connection():
    """Debug database connection issues."""
    logger.info("🔍 Debugging database connection...")
    
    try:
        from config.database import get_supabase_client, get_supabase_service_client
        
        logger.info("🔧 Testing get_supabase_client...")
        client = await get_supabase_client()
        logger.info("✅ get_supabase_client successful")
        
        logger.info("🔧 Testing get_supabase_service_client...")
        service_client = await get_supabase_service_client()
        logger.info("✅ get_supabase_service_client successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main debug function."""
    logger.info("🚀 Starting Supabase connection debug...")
    
    # Test 1: Environment variables
    logger.info("\n" + "="*50)
    logger.info("Test 1: Environment Variables")
    logger.info("="*50)
    await debug_supabase_connection()
    
    # Test 2: Database connection functions
    logger.info("\n" + "="*50)
    logger.info("Test 2: Database Connection Functions")
    logger.info("="*50)
    await debug_database_connection()
    
    logger.info("\n🎯 Debug complete!")

if __name__ == "__main__":
    asyncio.run(main())
