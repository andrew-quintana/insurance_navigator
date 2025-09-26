#!/usr/bin/env python3
"""
Script to run Phase 1 migration - removing public.users table and using auth.users directly.
This script applies the migration and verifies it works correctly.
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.development'))

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_supabase_service_client
from scripts.test_phase1_migration import Phase1MigrationTester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase1MigrationRunner:
    """Run the Phase 1 migration."""
    
    def __init__(self):
        self.migration_file = "supabase/migrations/20250925200000_phase1_remove_public_users_table.sql"
    
    async def check_prerequisites(self):
        """Check that prerequisites are met before running migration."""
        logger.info("🔍 Checking prerequisites...")
        
        try:
            # Check that migration file exists
            if not os.path.exists(self.migration_file):
                logger.error(f"❌ Migration file not found: {self.migration_file}")
                return False
            
            # Check that we can connect to Supabase
            service_client = await get_supabase_service_client()
            logger.info("✅ Supabase connection successful")
            
            # Check that public.users table exists (should exist before migration)
            try:
                result = service_client.table("users").select("*").limit(1).execute()
                logger.info("✅ public.users table exists (ready for migration)")
            except Exception as e:
                if "relation \"public.users\" does not exist" in str(e):
                    logger.warning("⚠️ public.users table already removed - migration may have been run")
                else:
                    logger.error(f"❌ Error checking public.users table: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Prerequisites check failed: {e}")
            return False
    
    async def run_migration(self):
        """Run the database migration."""
        logger.info("🚀 Running Phase 1 migration...")
        
        try:
            # Read migration file
            with open(self.migration_file, 'r') as f:
                migration_sql = f.read()
            
            logger.info(f"📄 Migration file loaded: {self.migration_file}")
            
            # Get service client
            service_client = await get_supabase_service_client()
            
            # Execute migration
            logger.info("⚡ Executing migration SQL...")
            result = service_client.rpc('exec_sql', {'sql': migration_sql}).execute()
            
            logger.info("✅ Migration executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    async def verify_migration(self):
        """Verify that the migration was successful."""
        logger.info("🔍 Verifying migration...")
        
        try:
            # Run the migration tests
            tester = Phase1MigrationTester()
            success = await tester.run_all_tests()
            
            if success:
                logger.info("✅ Migration verification successful")
                return True
            else:
                logger.error("❌ Migration verification failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration verification error: {e}")
            return False
    
    async def run_full_migration(self):
        """Run the complete Phase 1 migration process."""
        logger.info("🚀 Starting Phase 1 Migration Process")
        logger.info("=" * 60)
        
        # Step 1: Check prerequisites
        logger.info("\n📋 Step 1: Checking prerequisites...")
        if not await self.check_prerequisites():
            logger.error("❌ Prerequisites check failed - aborting migration")
            return False
        
        # Step 2: Run migration
        logger.info("\n⚡ Step 2: Running database migration...")
        if not await self.run_migration():
            logger.error("❌ Migration failed - aborting")
            return False
        
        # Step 3: Verify migration
        logger.info("\n🔍 Step 3: Verifying migration...")
        if not await self.verify_migration():
            logger.error("❌ Migration verification failed")
            return False
        
        # Success
        logger.info("\n🎉 Phase 1 Migration Completed Successfully!")
        logger.info("=" * 60)
        logger.info("✅ public.users table removed")
        logger.info("✅ RLS policies updated to use auth.uid()")
        logger.info("✅ Authentication service simplified")
        logger.info("✅ System now uses auth.users as single source of truth")
        logger.info("=" * 60)
        
        return True

async def main():
    """Main migration function."""
    runner = Phase1MigrationRunner()
    
    try:
        success = await runner.run_full_migration()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"💥 Migration process failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
