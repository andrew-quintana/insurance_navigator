#!/usr/bin/env python3
"""
Execute the vector architecture fix migration.
This script runs the schema migration and then optionally the encryption migration.
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

async def run_sql_migration(migration_file: str) -> bool:
    """Run a SQL migration file against the database."""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        logger.info(f"Running migration: {migration_file}")
        
        # Use subprocess to run psql
        result = subprocess.run([
            'psql', database_url, '-f', migration_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Migration {migration_file} completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"Migration {migration_file} failed")
            logger.error(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running migration {migration_file}: {str(e)}")
        return False

async def main():
    """Main execution function."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info("=" * 70)
    logger.info("VECTOR ARCHITECTURE FIX MIGRATION")
    logger.info("=" * 70)
    
    # Check if we're in the right directory
    if not Path("db/migrations").exists():
        logger.error("Must run from project root directory")
        return 1
    
    # Step 1: Run schema migration
    logger.info("Step 1: Running schema migration...")
    schema_success = await run_sql_migration("db/migrations/010_fix_vector_architecture.sql")
    
    if not schema_success:
        logger.error("Schema migration failed. Stopping.")
        return 1
    
    logger.info("✅ Schema migration completed successfully")
    
    # Step 2: Ask if user wants to run encryption migration
    print("\n" + "="*50)
    print("SCHEMA MIGRATION COMPLETED SUCCESSFULLY")
    print("="*50)
    print("\nThe vector architecture has been fixed:")
    print("✅ Encryption columns added to vector tables")
    print("✅ RLS policies updated to use user_policy_links properly")
    print("✅ user_id denormalization prepared for removal")
    print("✅ Encryption constraints and indexes added")
    
    print("\nNext step: Encrypt existing data and remove deprecated columns")
    
    # For now, let's not run the encryption migration automatically
    # as it requires careful handling of the existing data
    print("\nTo complete the migration:")
    print("1. Test the current schema changes")
    print("2. Run: python db/scripts/encrypt_existing_vectors.py")
    print("3. Verify encryption is working correctly")
    
    logger.info("Architecture fix migration completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 