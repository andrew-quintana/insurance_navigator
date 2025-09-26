"""
Consolidated Database Management System

This module provides a unified database management interface that consolidates
all database operations across the application, implementing the dependency
injection pattern for Phase 1 of the Agent Integration Infrastructure Refactor.

Key Features:
- Single source of truth for database connections
- Async/await support with connection pooling
- Health monitoring and error handling
- Environment-specific configuration
- Graceful degradation and retry logic
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from contextlib import asynccontextmanager
from dataclasses import dataclass

import asyncpg
from asyncpg import Pool, Connection
from asyncpg.pool import create_pool

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60
    ssl_mode: str = "prefer"
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"


class DatabaseManager:
    """
    Centralized database manager implementing dependency injection pattern.
    
    This class provides a single interface for all database operations across
    the application, eliminating the need for multiple database managers and
    resolving import management issues.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[Pool] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_initialized = False
        
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if self._is_initialized:
            logger.warning("Database manager already initialized")
            return
            
        try:
            logger.info(f"Initializing database pool: {self.config.host}:{self.config.port}")
            
            # Create connection pool with SSL configuration for Supabase
            # For local development, disable SSL; for production, require SSL
            if self._is_supabase_connection():
                ssl_config = "disable" if any(host in self.config.host for host in ["127.0.0.1", "localhost", "supabase_db_insurance_navigator"]) else "require"
                logger.info(f"Supabase connection detected, using SSL config: {ssl_config}")
            else:
                ssl_config = self.config.ssl_mode
                logger.info(f"Non-Supabase connection, using SSL config: {ssl_config}")
            
            logger.info(f"Connection string: {self.config.connection_string[:50]}...")
            logger.info(f"Host: {self.config.host}, Port: {self.config.port}")
            
            # Use the standard connection string approach for all connections
            # This avoids the complex pooler logic that was causing SCRAM authentication issues
            self.pool = await create_pool(
                self.config.connection_string,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                statement_cache_size=0,  # Fix pgbouncer prepared statement issue
                ssl=ssl_config,
                setup=self._setup_connection
            )
            
            self._is_initialized = True
            logger.info(f"Database pool initialized with {self.config.min_connections}-{self.config.max_connections} connections")
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close the database connection pool and cleanup resources."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
        
        self._is_initialized = False
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection from the pool."""
        if not self._is_initialized or not self.pool:
            raise RuntimeError("Database manager not initialized")
        
        async with self.pool.acquire() as conn:
            # Set search path to include upload_pipeline schema
            await conn.execute('SET search_path TO upload_pipeline, public')
            yield conn
    
    async def execute(self, query: str, *args, **kwargs) -> str:
        """Execute a database query."""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    async def fetch(self, query: str, *args, **kwargs) -> List[asyncpg.Record]:
        """Fetch rows from a database query."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args, **kwargs)
    
    async def fetchrow(self, query: str, *args, **kwargs) -> Optional[asyncpg.Record]:
        """Fetch a single row from a database query."""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args, **kwargs)
    
    async def fetchval(self, query: str, *args, **kwargs) -> Any:
        """Fetch a single value from a database query."""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args, **kwargs)
    
    async def executemany(self, query: str, args_list: List[tuple]) -> str:
        """Execute a query multiple times with different parameters."""
        async with self.get_connection() as conn:
            return await conn.executemany(query, args_list)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database."""
        try:
            if not self._is_initialized or not self.pool:
                return {"status": "unhealthy", "error": "Pool not initialized"}
            
            # Test connection and basic query
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    return {
                        "status": "healthy",
                        "pool_size": self.pool.get_size(),
                        "free_size": self.pool.get_size()  # asyncpg.Pool doesn't have get_free_size
                    }
                else:
                    return {"status": "unhealthy", "error": "Basic query failed"}
                    
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def _is_supabase_connection(self) -> bool:
        """Check if this is a Supabase connection."""
        return (
            "supabase.com" in self.config.host or 
            "supabase.co" in self.config.host or
            "znvwzkdblknkkztqyfnu" in self.config.host or
            "supabase_db_insurance_navigator" in self.config.host or
            "pooler.supabase.com" in self.config.host or
            "dfgzeastcxnoqshgyotp" in self.config.host  # Supabase project ID pattern
        )
    
    async def _setup_connection(self, conn: Connection) -> None:
        """Set up a new database connection."""
        # Set timezone
        await conn.execute("SET timezone = 'UTC'")
        
        # Set application name for monitoring
        await conn.execute("SET application_name = 'insurance_navigator'")
        
        # Set statement timeout
        await conn.execute("SET statement_timeout = '60s'")
        
        # Set idle session timeout
        await conn.execute("SET idle_in_transaction_session_timeout = '30s'")
    
    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                health = await self.health_check()
                if health["status"] != "healthy":
                    logger.warning(f"Database health check failed: {health}")
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(30)


def create_database_config() -> DatabaseConfig:
    """Create database configuration from environment variables."""
    # For cloud deployments, try to use pooler URL to avoid IPv6 issues
    # For local development, use DATABASE_URL directly
    is_cloud_deployment = any(os.getenv(var) for var in ['RENDER', 'VERCEL', 'HEROKU_APP_NAME', 'AWS_LAMBDA_FUNCTION_NAME', 'K_SERVICE'])
    
    logger.info(f"Database config creation - Cloud deployment: {is_cloud_deployment}")
    
    if is_cloud_deployment:
        # For cloud deployments, try pooler URL first to avoid IPv6 connectivity issues
        pooler_url = os.getenv("SUPABASE_SESSION_POOLER_URL") or os.getenv("SUPABASE_POOLER_URL")
        if pooler_url:
            logger.info(f"Using Supabase pooler URL for cloud deployment: {pooler_url[:50]}...")
            db_url = pooler_url
        else:
            # Fallback to direct DATABASE_URL if no pooler available
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                logger.warning("No pooler URL found, using direct DATABASE_URL")
    else:
        # Local development: use DATABASE_URL directly
        db_url = os.getenv("DATABASE_URL")
        logger.info("Using direct DATABASE_URL for local development")
    
    if db_url:
        # Parse DATABASE_URL if available
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        return DatabaseConfig(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/') or "postgres",
            user=parsed.username or "postgres",
            password=parsed.password or "",
            ssl_mode="disable" if any(host in db_url for host in ["127.0.0.1", "localhost", "supabase_db_insurance_navigator"]) else "require"
        )
    
    # Fallback to individual environment variables
    return DatabaseConfig(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "54322")),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        ssl_mode="require" if os.getenv("SUPABASE_URL") else "prefer"
    )


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized. Call initialize_database() first.")
    return _db_manager


async def initialize_database() -> DatabaseManager:
    """Initialize the global database manager."""
    global _db_manager
    if _db_manager is not None:
        logger.warning("Database manager already initialized")
        return _db_manager
    
    config = create_database_config()
    _db_manager = DatabaseManager(config)
    await _db_manager.initialize()
    return _db_manager


async def close_database() -> None:
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None


# Convenience function for getting connections
@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[Connection, None]:
    """Get a database connection from the global manager."""
    manager = await get_database_manager()
    async with manager.get_connection() as conn:
        yield conn
