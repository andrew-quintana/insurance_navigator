"""
Database connection management for the upload pipeline.
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import os

import asyncpg
from asyncpg import Pool, Connection
from asyncpg.pool import create_pool

from .config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and provides database operations."""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.config = get_config()
    
    async def initialize(self):
        """Initialize the database connection pool."""
        try:
            # Parse connection string from Supabase URL
            db_url = self._parse_supabase_url()
            
            # Create connection pool
            self.pool = await create_pool(
                db_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                statement_cache_size=0,
                max_cached_statement_lifetime=0,
                max_cached_statement_size=0,
                setup=self._setup_connection
            )
            
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database connection pool", exc_info=True)
            raise
    
    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("Database health check failed", exc_info=True)
            return False
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            # Set schema for this connection
            await conn.execute(f'SET search_path TO {self.config.database_schema}, public')
            yield conn
    
    async def execute(self, query: str, *args, **kwargs):
        """Execute a database query."""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    async def fetch(self, query: str, *args, **kwargs):
        """Fetch rows from a database query."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args, **kwargs)
    
    async def fetchrow(self, query: str, *args, **kwargs):
        """Fetch a single row from a database query."""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args, **kwargs)
    
    async def fetchval(self, query: str, *args, **kwargs):
        """Fetch a single value from a database query."""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args, **kwargs)
    
    async def executemany(self, query: str, args_list):
        """Execute a query multiple times with different parameters."""
        async with self.get_connection() as conn:
            return await conn.executemany(query, args_list)
    
    def _parse_supabase_url(self) -> str:
        """Parse Supabase URL to extract database connection details."""
        # Extract database connection string from environment
        # This would typically be set as SUPABASE_DB_URL or similar
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            # Fallback: construct from Supabase URL and service role key
            supabase_url = self.config.supabase_url
            service_key = self.config.supabase_service_role_key
            
            # Extract host from Supabase URL
            if supabase_url.startswith("https://"):
                host = supabase_url[8:]  # Remove https://
            else:
                host = supabase_url
            
            # Construct PostgreSQL connection string
            db_url = f"postgresql://postgres:{service_key}@{host}:5432/postgres"
        
        return db_url
    
    async def _setup_connection(self, conn: Connection):
        """Set up a new database connection."""
        # Set timezone
        await conn.execute("SET timezone = 'UTC'")
        
        # Set application name for monitoring
        await conn.execute("SET application_name = 'upload_pipeline_api'")
        
        # Set statement timeout
        await conn.execute("SET statement_timeout = '60s'")
        
        # Set idle session timeout
        await conn.execute("SET idle_in_transaction_session_timeout = '30s'")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def close_database():
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
