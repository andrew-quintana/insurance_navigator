# Database Connection Pool Manager
# Addresses: FM-043 - Implement connection pooling to prevent database connection exhaustion

import os
import logging
import asyncpg
from typing import Optional
from asyncpg import Pool


class DatabasePoolManager:
    """
    Centralized database connection pool manager for RAG operations.
    Implements bounded connection pooling to prevent resource exhaustion.
    """

    def __init__(self, min_size: int = 5, max_size: int = 20):
        """
        Initialize the database pool manager.
        
        Args:
            min_size: Minimum connections to maintain in pool
            max_size: Maximum connections allowed in pool
        """
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[Pool] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self.pool is not None:
            self.logger.warning("Connection pool already initialized")
            return

        try:
            # Try to use DATABASE_URL first, then fall back to individual parameters
            database_url = os.getenv("DATABASE_URL")
            
            if database_url:
                self.pool = await asyncpg.create_pool(
                    database_url,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    statement_cache_size=0
                )
                self.logger.info(f"Database pool initialized with DATABASE_URL (min: {self.min_size}, max: {self.max_size})")
            else:
                # Fallback to individual environment variables
                host = os.getenv("SUPABASE_DB_HOST", "127.0.0.1")
                port = int(os.getenv("SUPABASE_DB_PORT", "5432"))
                user = os.getenv("SUPABASE_DB_USER", "postgres")
                password = os.getenv("SUPABASE_DB_PASSWORD", "postgres")
                database = os.getenv("SUPABASE_DB_NAME", "postgres")
                
                self.pool = await asyncpg.create_pool(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    statement_cache_size=0
                )
                self.logger.info(f"Database pool initialized with individual params (min: {self.min_size}, max: {self.max_size})")

        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def acquire_connection(self):
        """
        Acquire a connection from the pool.
        
        Returns:
            asyncpg.Connection from the pool
        """
        if self.pool is None:
            await self.initialize()
        
        try:
            return await self.pool.acquire()
        except Exception as e:
            self.logger.error(f"Failed to acquire connection from pool: {e}")
            raise

    async def release_connection(self, conn) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            conn: Connection to release
        """
        if self.pool is not None and conn is not None:
            try:
                await self.pool.release(conn)
            except Exception as e:
                self.logger.error(f"Failed to release connection to pool: {e}")

    async def close_pool(self) -> None:
        """Close the connection pool and all connections."""
        if self.pool is not None:
            try:
                await self.pool.close()
                self.pool = None
                self.logger.info("Database connection pool closed")
            except Exception as e:
                self.logger.error(f"Error closing connection pool: {e}")

    async def get_pool_status(self) -> dict:
        """
        Get current pool status for monitoring.
        
        Returns:
            Dictionary with pool status information
        """
        if self.pool is None:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "size": self.pool.get_size(),
            "min_size": self.pool.get_min_size(),
            "max_size": self.pool.get_max_size(),
            "idle_size": self.pool.get_idle_size()
        }


# Global pool manager instance
_pool_manager: Optional[DatabasePoolManager] = None


async def get_pool_manager() -> DatabasePoolManager:
    """
    Get the global database pool manager instance.
    Initializes it if it doesn't exist.
    
    Returns:
        DatabasePoolManager instance
    """
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = DatabasePoolManager()
        await _pool_manager.initialize()
    return _pool_manager


async def get_db_connection():
    """
    Convenience function to get a database connection from the pool.
    
    Returns:
        asyncpg.Connection from the pool
    """
    pool_manager = await get_pool_manager()
    return await pool_manager.acquire_connection()


async def release_db_connection(conn) -> None:
    """
    Convenience function to release a database connection back to the pool.
    
    Args:
        conn: Connection to release
    """
    pool_manager = await get_pool_manager()
    await pool_manager.release_connection(conn)