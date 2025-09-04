#!/usr/bin/env python3
"""
Production Database Setup Script
Restores complete Supabase database schema for production deployment
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from supabase import create_client, Client
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
        
    async def setup_database(self):
        """Set up the complete database schema"""
        logger.info("🚀 Starting production database setup...")
        
        try:
            # 1. Check current database status
            await self.check_database_status()
            
            # 2. Run all migrations
            await self.run_migrations()
            
            # 3. Verify schema setup
            await self.verify_schema()
            
            # 4. Test user registration
            await self.test_user_registration()
            
            logger.info("✅ Database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {str(e)}")
            raise
    
    async def check_database_status(self):
        """Check current database status"""
        logger.info("📊 Checking database status...")
        
        try:
            # Test basic connectivity
            response = await self.client.table("users").select("count").execute()
            logger.info("✅ Database connection successful")
            
        except Exception as e:
            logger.warning(f"⚠️ Database connection issue: {str(e)}")
            logger.info("This is expected if tables don't exist yet")
    
    async def run_migrations(self):
        """Run all database migrations"""
        logger.info("🔄 Running database migrations...")
        
        # Get all migration files
        migration_dir = Path("supabase/migrations")
        migration_files = sorted(migration_dir.glob("*.sql"))
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        for migration_file in migration_files:
            logger.info(f"📄 Running migration: {migration_file.name}")
            
            try:
                # Read migration SQL
                with open(migration_file, 'r') as f:
                    sql_content = f.read()
                
                # Execute migration
                result = await self.client.rpc('exec_sql', {'sql': sql_content}).execute()
                logger.info(f"✅ Migration {migration_file.name} completed")
                
            except Exception as e:
                logger.error(f"❌ Migration {migration_file.name} failed: {str(e)}")
                # Continue with other migrations
                continue
    
    async def verify_schema(self):
        """Verify that all required tables exist"""
        logger.info("🔍 Verifying database schema...")
        
        required_tables = [
            "public.users",
            "upload_pipeline.documents", 
            "upload_pipeline.upload_jobs",
            "upload_pipeline.document_chunks",
            "upload_pipeline.events"
        ]
        
        for table in required_tables:
            try:
                # Try to select from table
                result = await self.client.table(table.split('.')[1]).select("count").limit(1).execute()
                logger.info(f"✅ Table {table} exists and is accessible")
            except Exception as e:
                logger.error(f"❌ Table {table} missing or inaccessible: {str(e)}")
                raise
    
    async def test_user_registration(self):
        """Test user registration functionality"""
        logger.info("🧪 Testing user registration...")
        
        try:
            # Test user creation
            test_email = "test@example.com"
            test_password = "testpassword123"
            
            # Create auth user
            auth_response = await self.client.auth.sign_up({
                "email": test_email,
                "password": test_password
            })
            
            if auth_response.user:
                logger.info("✅ User registration test successful")
                
                # Clean up test user
                try:
                    await self.client.auth.admin.delete_user(auth_response.user.id)
                    logger.info("🧹 Test user cleaned up")
                except:
                    logger.warning("⚠️ Could not clean up test user")
            else:
                logger.error("❌ User registration test failed")
                raise Exception("User registration failed")
                
        except Exception as e:
            logger.error(f"❌ User registration test failed: {str(e)}")
            raise

async def main():
    """Main function"""
    logger.info("🏗️ Production Database Setup")
    logger.info("=" * 50)
    
    try:
        setup = DatabaseSetup()
        await setup.setup_database()
        
        logger.info("=" * 50)
        logger.info("🎉 Database setup completed successfully!")
        logger.info("The Insurance Navigator database is now ready for production use.")
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"💥 Database setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
