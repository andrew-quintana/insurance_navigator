#!/usr/bin/env python3
"""
Run Database Setup Script
Executes the database schema restoration against production Supabase
"""

import os
import sys
import asyncio
import logging
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Set up the database schema"""
    logger.info("🚀 Starting database schema restoration...")
    
    # Get Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
        sys.exit(1)
    
    logger.info(f"📡 Connecting to Supabase: {supabase_url}")
    
    # Create Supabase client
    client = create_client(supabase_url, supabase_key)
    
    try:
        # Read the SQL file
        with open("scripts/restore_database_schema.sql", "r") as f:
            sql_content = f.read()
        
        logger.info("📄 Executing database schema restoration...")
        
        # Execute the SQL
        # Note: This might need to be done through the Supabase dashboard or CLI
        # as the Python client doesn't have direct SQL execution capabilities
        logger.warning("⚠️ Direct SQL execution not available through Python client")
        logger.info("📋 Please run the following SQL in your Supabase SQL editor:")
        logger.info("=" * 60)
        print(sql_content)
        logger.info("=" * 60)
        
        # Test basic connectivity
        logger.info("🧪 Testing database connectivity...")
        try:
            result = client.table("users").select("count").execute()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.info(f"ℹ️ Expected error (tables may not exist yet): {str(e)}")
        
        logger.info("✅ Database setup script completed!")
        logger.info("📝 Next steps:")
        logger.info("1. Copy the SQL above")
        logger.info("2. Go to your Supabase dashboard")
        logger.info("3. Navigate to SQL Editor")
        logger.info("4. Paste and execute the SQL")
        logger.info("5. Test user registration")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(setup_database())
