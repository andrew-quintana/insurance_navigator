#!/usr/bin/env python3
"""
Upload Pipeline Investigation Script

This script investigates why documents aren't being associated with the user
in the database, despite successful uploads from the frontend.
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

class UploadPipelineInvestigator:
    """Investigate upload pipeline issues."""
    
    def __init__(self):
        self.user_id = "e5167bd7-849e-4d04-bd74-eef7c60402ce"
        self.schema = os.getenv("DATABASE_SCHEMA", "upload_pipeline")
        self.conn = None
        
    async def run_investigation(self):
        """Run comprehensive upload pipeline investigation."""
        logger.info("🔍 Starting Upload Pipeline Investigation")
        logger.info(f"User ID: {self.user_id}")
        logger.info(f"Schema: {self.schema}")
        
        try:
            await self._connect_to_database()
            
            # 1. Check all users in the system
            await self._check_all_users()
            
            # 2. Check all documents
            await self._check_all_documents()
            
            # 3. Check upload jobs
            await self._check_upload_jobs()
            
            # 4. Check for recent activity
            await self._check_recent_activity()
            
            # 5. Check for duplicate user IDs
            await self._check_duplicate_users()
            
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
    
    async def _check_all_users(self):
        """Check all users in the system."""
        logger.info("\n👥 ALL USERS IN SYSTEM")
        logger.info("=" * 50)
        
        try:
            # Check documents table for all users
            users_query = f"""
                SELECT user_id, COUNT(*) as doc_count, 
                       MIN(created_at) as first_doc,
                       MAX(created_at) as last_doc
                FROM {self.schema}.documents
                GROUP BY user_id
                ORDER BY last_doc DESC
                LIMIT 20
            """
            users = await self.conn.fetch(users_query)
            
            logger.info(f"📊 Users with documents: {len(users)}")
            for user in users:
                logger.info(f"  - {user['user_id']}: {user['doc_count']} docs (first: {user['first_doc']}, last: {user['last_doc']})")
            
            # Check if our target user exists
            target_user_query = f"""
                SELECT user_id, COUNT(*) as doc_count
                FROM {self.schema}.documents
                WHERE user_id = $1
                GROUP BY user_id
            """
            target_user = await self.conn.fetch(target_user_query, self.user_id)
            
            if target_user:
                logger.info(f"✅ Target user {self.user_id} found with {target_user[0]['doc_count']} documents")
            else:
                logger.warning(f"⚠️  Target user {self.user_id} NOT found in documents table")
                
        except Exception as e:
            logger.error(f"❌ User check failed: {e}")
    
    async def _check_all_documents(self):
        """Check all documents in the system."""
        logger.info("\n📄 ALL DOCUMENTS IN SYSTEM")
        logger.info("=" * 50)
        
        try:
            # Get recent documents
            docs_query = f"""
                SELECT document_id, user_id, filename, created_at,
                       (SELECT COUNT(*) FROM {self.schema}.document_chunks dc 
                        WHERE dc.document_id = d.document_id) as chunk_count
                FROM {self.schema}.documents d
                ORDER BY created_at DESC
                LIMIT 20
            """
            docs = await self.conn.fetch(docs_query)
            
            logger.info(f"📊 Recent documents: {len(docs)}")
            for doc in docs:
                logger.info(f"  - {doc['document_id']}: {doc['filename']} (user: {doc['user_id']}, chunks: {doc['chunk_count']})")
            
            # Check for documents with similar user IDs
            similar_users_query = f"""
                SELECT user_id, COUNT(*) as doc_count
                FROM {self.schema}.documents
                WHERE user_id LIKE $1 OR user_id LIKE $2
                GROUP BY user_id
            """
            similar_users = await self.conn.fetch(similar_users_query, f"%{self.user_id[:8]}%", f"%{self.user_id[-8:]}%")
            
            if similar_users:
                logger.info(f"🔍 Similar user IDs found:")
                for user in similar_users:
                    logger.info(f"  - {user['user_id']}: {user['doc_count']} docs")
            else:
                logger.info("🔍 No similar user IDs found")
                
        except Exception as e:
            logger.error(f"❌ Document check failed: {e}")
    
    async def _check_upload_jobs(self):
        """Check upload jobs."""
        logger.info("\n📋 UPLOAD JOBS")
        logger.info("=" * 50)
        
        try:
            # Get recent upload jobs
            jobs_query = f"""
                SELECT job_id, user_id, document_id, status, created_at, error_message
                FROM {self.schema}.upload_jobs
                ORDER BY created_at DESC
                LIMIT 20
            """
            jobs = await self.conn.fetch(jobs_query)
            
            logger.info(f"📊 Recent upload jobs: {len(jobs)}")
            for job in jobs:
                logger.info(f"  - {job['job_id']}: {job['status']} (user: {job['user_id']}, doc: {job['document_id']})")
                if job['error_message']:
                    logger.info(f"    Error: {job['error_message']}")
            
            # Check for jobs with our target user
            target_jobs_query = f"""
                SELECT job_id, user_id, document_id, status, created_at, error_message
                FROM {self.schema}.upload_jobs
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 10
            """
            target_jobs = await self.conn.fetch(target_jobs_query, self.user_id)
            
            if target_jobs:
                logger.info(f"🎯 Upload jobs for target user {self.user_id}: {len(target_jobs)}")
                for job in target_jobs:
                    logger.info(f"  - {job['job_id']}: {job['status']} (doc: {job['document_id']})")
                    if job['error_message']:
                        logger.info(f"    Error: {job['error_message']}")
            else:
                logger.warning(f"⚠️  No upload jobs found for target user {self.user_id}")
                
        except Exception as e:
            logger.error(f"❌ Upload jobs check failed: {e}")
    
    async def _check_recent_activity(self):
        """Check for recent activity."""
        logger.info("\n⏰ RECENT ACTIVITY")
        logger.info("=" * 50)
        
        try:
            # Check recent documents (last 24 hours)
            recent_docs_query = f"""
                SELECT document_id, user_id, filename, created_at
                FROM {self.schema}.documents
                WHERE created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
            """
            recent_docs = await self.conn.fetch(recent_docs_query)
            
            logger.info(f"📊 Documents created in last 24 hours: {len(recent_docs)}")
            for doc in recent_docs:
                logger.info(f"  - {doc['document_id']}: {doc['filename']} (user: {doc['user_id']}, time: {doc['created_at']})")
            
            # Check recent upload jobs (last 24 hours)
            recent_jobs_query = f"""
                SELECT job_id, user_id, document_id, status, created_at
                FROM {self.schema}.upload_jobs
                WHERE created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
            """
            recent_jobs = await self.conn.fetch(recent_jobs_query)
            
            logger.info(f"📊 Upload jobs in last 24 hours: {len(recent_jobs)}")
            for job in recent_jobs:
                logger.info(f"  - {job['job_id']}: {job['status']} (user: {job['user_id']}, time: {job['created_at']})")
                
        except Exception as e:
            logger.error(f"❌ Recent activity check failed: {e}")
    
    async def _check_duplicate_users(self):
        """Check for duplicate user IDs or similar patterns."""
        logger.info("\n🔄 DUPLICATE USER INVESTIGATION")
        logger.info("=" * 50)
        
        try:
            # Check for users with similar UUIDs
            similar_patterns = [
                self.user_id,
                self.user_id.replace('-', ''),
                f"user_{self.user_id}",
                self.user_id.upper(),
                self.user_id.lower(),
            ]
            
            for pattern in similar_patterns:
                pattern_query = f"""
                    SELECT user_id, COUNT(*) as doc_count
                    FROM {self.schema}.documents
                    WHERE user_id = $1
                    GROUP BY user_id
                """
                pattern_result = await self.conn.fetch(pattern_query, pattern)
                
                if pattern_result:
                    logger.info(f"✅ Found documents for pattern '{pattern}': {pattern_result[0]['doc_count']} docs")
                else:
                    logger.info(f"❌ No documents for pattern '{pattern}'")
            
            # Check for any user IDs that contain parts of our target user ID
            partial_match_query = f"""
                SELECT user_id, COUNT(*) as doc_count
                FROM {self.schema}.documents
                WHERE user_id LIKE $1
                GROUP BY user_id
            """
            partial_matches = await self.conn.fetch(partial_match_query, f"%{self.user_id[:10]}%")
            
            if partial_matches:
                logger.info(f"🔍 Partial matches found:")
                for match in partial_matches:
                    logger.info(f"  - {match['user_id']}: {match['doc_count']} docs")
            else:
                logger.info("🔍 No partial matches found")
                
        except Exception as e:
            logger.error(f"❌ Duplicate user check failed: {e}")

async def main():
    """Main investigation execution."""
    investigator = UploadPipelineInvestigator()
    await investigator.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())

