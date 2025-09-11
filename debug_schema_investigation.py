#!/usr/bin/env python3
"""
Schema Investigation Script

This script investigates the database schema to understand the table structures
and identify why the user's documents aren't being found.
"""

import asyncio
import os
import sys
import logging
from typing import List, Dict, Any
import asyncpg
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SchemaInvestigator:
    """Investigate database schema and table structures."""
    
    def __init__(self):
        self.user_id = "e5167bd7-849e-4d04-bd74-eef7c60402ce"
        self.schema = os.getenv("DATABASE_SCHEMA", "upload_pipeline")
        self.conn = None
        
    async def run_investigation(self):
        """Run comprehensive schema investigation."""
        logger.info("🔍 Starting Schema Investigation")
        logger.info(f"User ID: {self.user_id}")
        logger.info(f"Schema: {self.schema}")
        
        try:
            await self._connect_to_database()
            
            # 1. Check upload_jobs table schema
            await self._check_upload_jobs_schema()
            
            # 2. Check upload_jobs data
            await self._check_upload_jobs_data()
            
            # 3. Check for our user in upload_jobs
            await self._check_user_in_upload_jobs()
            
            # 4. Check recent upload activity
            await self._check_recent_upload_activity()
            
        except Exception as e:
            logger.error(f"Investigation failed: {e}")
            raise
        finally:
            if self.conn:
                await self.conn.close()
    
    async def _connect_to_database(self):
        """Connect to the production database."""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            self.conn = await asyncpg.connect(database_url)
            logger.info("✅ Connected to production database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    async def _check_upload_jobs_schema(self):
        """Check upload_jobs table schema."""
        logger.info("\n📋 UPLOAD_JOBS TABLE SCHEMA")
        logger.info("=" * 50)
        
        try:
            # Get table schema
            schema_query = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1 
                  AND table_name = 'upload_jobs'
                ORDER BY ordinal_position
            """
            columns = await self.conn.fetch(schema_query, self.schema)
            
            logger.info(f"📊 Upload jobs table columns: {len(columns)}")
            for col in columns:
                logger.info(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
                
        except Exception as e:
            logger.error(f"❌ Schema check failed: {e}")
    
    async def _check_upload_jobs_data(self):
        """Check upload_jobs table data."""
        logger.info("\n📊 UPLOAD_JOBS DATA")
        logger.info("=" * 50)
        
        try:
            # Get recent upload jobs
            jobs_query = f"""
                SELECT *
                FROM {self.schema}.upload_jobs
                ORDER BY created_at DESC
                LIMIT 10
            """
            jobs = await self.conn.fetch(jobs_query)
            
            logger.info(f"📊 Recent upload jobs: {len(jobs)}")
            for job in jobs:
                logger.info(f"  Job: {dict(job)}")
                
        except Exception as e:
            logger.error(f"❌ Upload jobs data check failed: {e}")
    
    async def _check_user_in_upload_jobs(self):
        """Check if our user exists in upload_jobs."""
        logger.info("\n👤 USER IN UPLOAD_JOBS")
        logger.info("=" * 50)
        
        try:
            # Check for our user in upload_jobs
            user_jobs_query = f"""
                SELECT *
                FROM {self.schema}.upload_jobs
                WHERE user_id = $1
                ORDER BY created_at DESC
            """
            user_jobs = await self.conn.fetch(user_jobs_query, self.user_id)
            
            if user_jobs:
                logger.info(f"✅ Found {len(user_jobs)} upload jobs for user {self.user_id}")
                for job in user_jobs:
                    logger.info(f"  Job: {dict(job)}")
            else:
                logger.warning(f"⚠️  No upload jobs found for user {self.user_id}")
                
                # Check for similar user IDs
                similar_query = f"""
                    SELECT DISTINCT user_id, COUNT(*) as job_count
                    FROM {self.schema}.upload_jobs
                    WHERE user_id LIKE $1 OR user_id LIKE $2
                    GROUP BY user_id
                    ORDER BY job_count DESC
                """
                similar_users = await self.conn.fetch(similar_query, f"%{self.user_id[:8]}%", f"%{self.user_id[-8:]}%")
                
                if similar_users:
                    logger.info(f"🔍 Similar user IDs found:")
                    for user in similar_users:
                        logger.info(f"  - {user['user_id']}: {user['job_count']} jobs")
                else:
                    logger.info("🔍 No similar user IDs found")
                    
        except Exception as e:
            logger.error(f"❌ User in upload jobs check failed: {e}")
    
    async def _check_recent_upload_activity(self):
        """Check recent upload activity."""
        logger.info("\n⏰ RECENT UPLOAD ACTIVITY")
        logger.info("=" * 50)
        
        try:
            # Get recent upload jobs (last 24 hours)
            recent_jobs_query = f"""
                SELECT *
                FROM {self.schema}.upload_jobs
                WHERE created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
            """
            recent_jobs = await self.conn.fetch(recent_jobs_query)
            
            logger.info(f"📊 Upload jobs in last 24 hours: {len(recent_jobs)}")
            for job in recent_jobs:
                logger.info(f"  Job: {dict(job)}")
                
        except Exception as e:
            logger.error(f"❌ Recent upload activity check failed: {e}")

async def main():
    """Main investigation execution."""
    investigator = SchemaInvestigator()
    await investigator.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())
