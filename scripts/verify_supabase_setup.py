#!/usr/bin/env python3
"""
Verification script for Supabase setup and authentication.
Tests database connection, authentication, and basic operations.
"""

import os
import sys
import logging
from pathlib import Path
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.services.user_service import get_user_service
from db.services.db_pool import get_db_pool, close_db_pool, get_connection_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test data
TEST_USER_EMAIL = f"verify_setup_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "VerifySetup123!"
TEST_USER_NAME = "Verify Setup User"

def verify_environment() -> bool:
    """Verify required environment variables."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_ANON_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
        
    logger.info("✅ Environment variables verified")
    return True

def verify_database_connection() -> bool:
    """Verify database connection and pool management."""
    try:
        # Get initial connection status
        status = get_connection_status()
        logger.info(f"Initial connection status: {status}")
        
        # Get database pool
        db = get_db_pool()
        if not db:
            logger.error("❌ Failed to create database pool")
            return False
            
        # Verify connection status
        status = get_connection_status()
        if not status["is_connected"]:
            logger.error("❌ Database not connected after pool creation")
            return False
            
        # Test simple query
        response = db.table("users").select("id").limit(1).execute()
        if not response:
            logger.error("❌ Failed to execute test query")
            return False
            
        logger.info("✅ Database connection verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection error: {str(e)}")
        return False

def verify_user_service() -> bool:
    """Verify user service operations."""
    try:
        # Get user service
        user_service = get_user_service()
        if not user_service:
            logger.error("❌ Failed to create user service")
            return False
            
        # Create test user
        user_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_NAME
        }
        
        user = user_service.create_user(user_data)
        if not user:
            logger.error("❌ Failed to create test user")
            return False
            
        logger.info(f"✅ Created test user: {user['id']}")
        
        # Test authentication
        auth_data, error = user_service.authenticate_user(
            TEST_USER_EMAIL,
            TEST_USER_PASSWORD
        )
        
        if error or not auth_data:
            logger.error(f"❌ Authentication failed: {error}")
            return False
            
        logger.info("✅ Authentication successful")
        
        # Cleanup test user
        user_service.db.delete().eq("id", user["id"]).execute()
        logger.info("✅ Test user cleaned up")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ User service error: {str(e)}")
        return False

def verify_setup() -> bool:
    """Run all verification checks."""
    try:
        logger.info("🔄 Starting Supabase setup verification...")
        
        # Check environment
        if not verify_environment():
            return False
            
        # Check database connection
        if not verify_database_connection():
            return False
            
        # Check user service
        if not verify_user_service():
            return False
            
        # Close connections
        close_db_pool()
        logger.info("✅ Database connections closed")
        
        logger.info("🎉 All verification checks passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main entry point."""
    try:
        success = verify_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Verification interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 