#!/usr/bin/env python3
"""
Database and Storage Reset Script

Completely clears all data from Supabase database and storage
to start with a clean slate for production deployment.
"""

import asyncio
import os
import sys
import logging
from typing import List
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from db.services.db_pool import get_db_pool
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseResetter:
    """Complete database and storage reset utility."""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
        
    async def reset_database_tables(self):
        """Drop all tables and recreate schema from consolidated migration."""
        logger.info("🔥 Resetting database tables...")
        
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                
                # Get list of all tables first
                tables_result = await conn.fetch("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename NOT LIKE 'pg_%'
                    AND tablename NOT LIKE '_realtime%'
                """)
                
                table_names = [row['tablename'] for row in tables_result]
                logger.info(f"📋 Found {len(table_names)} tables to drop")
                
                if table_names:
                    # Drop all tables
                    for table_name in table_names:
                        try:
                            await conn.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
                            logger.info(f"✅ Dropped table: {table_name}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not drop {table_name}: {e}")
                
                # Drop all functions
                functions_result = await conn.fetch("""
                    SELECT proname, oidvectortypes(proargtypes) as args
                    FROM pg_proc 
                    WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                    AND proname NOT LIKE 'pg_%'
                """)
                
                for func in functions_result:
                    try:
                        await conn.execute(f'DROP FUNCTION IF EXISTS "{func["proname"]}"({func["args"]}) CASCADE')
                        logger.info(f"✅ Dropped function: {func['proname']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not drop function {func['proname']}: {e}")
                
                # Drop all views
                views_result = await conn.fetch("""
                    SELECT viewname FROM pg_views 
                    WHERE schemaname = 'public'
                """)
                
                for view in views_result:
                    try:
                        await conn.execute(f'DROP VIEW IF EXISTS "{view["viewname"]}" CASCADE')
                        logger.info(f"✅ Dropped view: {view['viewname']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not drop view {view['viewname']}: {e}")
                
                logger.info("✅ Database tables reset complete")
                
        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            raise
    
    async def run_consolidated_migration(self):
        """Apply the consolidated migration to recreate clean schema."""
        logger.info("🏗️ Running consolidated migration...")
        
        try:
            # Read the consolidated migration file
            migration_path = Path(__file__).parent.parent / "db" / "migrations" / "V2.0.0__consolidated_production_schema.sql"
            
            if not migration_path.exists():
                raise FileNotFoundError(f"Migration file not found: {migration_path}")
            
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Execute the migration
                await conn.execute(migration_sql)
                logger.info("✅ Consolidated migration applied successfully")
                
                # Verify tables were created
                tables_result = await conn.fetch("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY tablename
                """)
                
                table_names = [row['tablename'] for row in tables_result]
                logger.info(f"✅ Created {len(table_names)} tables:")
                for table_name in table_names:
                    logger.info(f"   📋 {table_name}")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    def clear_storage_buckets(self):
        """Clear all files from Supabase storage buckets."""
        logger.info("🗂️ Clearing storage buckets...")
        
        try:
            # List all buckets
            buckets_response = self.supabase.storage.list_buckets()
            
            if hasattr(buckets_response, 'data') and buckets_response.data:
                buckets = buckets_response.data
            else:
                buckets = buckets_response if isinstance(buckets_response, list) else []
            
            logger.info(f"📦 Found {len(buckets)} storage buckets")
            
            for bucket in buckets:
                bucket_name = bucket.get('name') or bucket.get('id')
                if not bucket_name:
                    continue
                    
                logger.info(f"🧹 Clearing bucket: {bucket_name}")
                
                try:
                    # List all files in bucket
                    files_response = self.supabase.storage.from_(bucket_name).list()
                    
                    if hasattr(files_response, 'data') and files_response.data:
                        files = files_response.data
                    else:
                        files = files_response if isinstance(files_response, list) else []
                    
                    if files:
                        # Delete all files
                        file_paths = [f.get('name') for f in files if f.get('name')]
                        if file_paths:
                            delete_response = self.supabase.storage.from_(bucket_name).remove(file_paths)
                            logger.info(f"✅ Deleted {len(file_paths)} files from {bucket_name}")
                        else:
                            logger.info(f"📭 No files to delete in {bucket_name}")
                    else:
                        logger.info(f"📭 Bucket {bucket_name} is already empty")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not clear bucket {bucket_name}: {e}")
            
            logger.info("✅ Storage clearing complete")
            
        except Exception as e:
            logger.warning(f"⚠️ Storage clearing failed: {e}")
            # Don't raise - storage clearing is not critical
    
    async def reset_complete_system(self):
        """Perform complete system reset."""
        logger.info("🚀 " + "="*60)
        logger.info("🚀 COMPLETE SYSTEM RESET - INSURANCE NAVIGATOR")
        logger.info("🚀 " + "="*60)
        
        try:
            # Step 1: Clear storage
            self.clear_storage_buckets()
            
            # Step 2: Reset database
            await self.reset_database_tables()
            
            # Step 3: Apply clean migration
            await self.run_consolidated_migration()
            
            logger.info("\n🎉 " + "="*60)
            logger.info("🎉 SYSTEM RESET COMPLETE!")
            logger.info("🎉 " + "="*60)
            logger.info("✅ Database: Clean schema applied")
            logger.info("✅ Storage: All files cleared")
            logger.info("✅ Ready for fresh deployment!")
            
        except Exception as e:
            logger.error(f"\n❌ SYSTEM RESET FAILED: {e}")
            raise

async def main():
    """Main reset function."""
    # Confirmation prompt
    print("\n" + "="*70)
    print("🚨 DESTRUCTIVE OPERATION WARNING 🚨")
    print("="*70)
    print("This will PERMANENTLY DELETE:")
    print("• All database tables and data")
    print("• All uploaded files in Supabase storage")
    print("• All user accounts and conversations")
    print("• All regulatory documents and vectors")
    print("="*70)
    
    confirm = input("\nType 'RESET' to confirm complete system reset: ")
    
    if confirm != 'RESET':
        print("❌ Reset cancelled")
        return
    
    resetter = DatabaseResetter()
    await resetter.reset_complete_system()

if __name__ == "__main__":
    asyncio.run(main()) 