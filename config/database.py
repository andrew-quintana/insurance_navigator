"""
Database configuration for the insurance navigator application.

This module provides database connection settings and utilities for
connecting to PostgreSQL with pgvector support and Supabase.
"""

import os
from typing import Dict, Any, Optional, AsyncGenerator
import logging
from supabase import create_client, Client
import httpx
from contextlib import asynccontextmanager
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv('DB_HOST', '127.0.0.1')
        self.port = int(os.getenv('DB_PORT', '54322'))
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        self.database = os.getenv('DB_NAME', 'postgres')
        
        # Disable audit logging for MVP
        self.audit_logging_enabled = False
        
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

db_config = DatabaseConfig()


def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dictionary with database connection parameters
    """
    config = {
        'host': db_config.host,
        'port': db_config.port,
        'user': db_config.user,
        'password': db_config.password,
        'database': db_config.database,
        'schema': os.getenv('DB_SCHEMA', 'public')
    }
    
    # Validate required fields
    if not config['password']:
        logger.warning("DB_PASSWORD not set - database connection may fail")
    
    return config


def get_database_url() -> str:
    """
    Get PostgreSQL database URL for SQLAlchemy connections.
    
    Returns:
        Database URL string
    """
    config = get_db_config()
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"


def get_async_database_url() -> str:
    """
    Get async PostgreSQL database URL for async SQLAlchemy connections.
    
    Returns:
        Async database URL string
    """
    config = get_db_config()
    return f"postgresql+asyncpg://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"


def get_pgvector_config() -> Dict[str, Any]:
    """
    Get configuration for PGVector connections.
    
    Returns:
        Configuration dictionary for PGVector
    """
    config = get_db_config()
    
    return {
        'connection_string': get_database_url(),
        'collection_name': 'regulatory_documents',
        'embedding_function': None,  # Will be set by caller
        'distance_strategy': 'cosine'
    }


class DatabasePool:
    def __init__(self):
        self._client: Optional[Client] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database pool if not already initialized"""
        if not self._initialized:
            self._client = await get_supabase_client()
            self._initialized = True

    async def get_client(self) -> Client:
        """Get the database client, initializing if necessary"""
        if not self._initialized:
            await self.initialize()
        return self._client

    async def cleanup(self) -> None:
        """Cleanup resources - for Supabase client we just need to remove references"""
        self._client = None
        self._initialized = False
        logger.info("Database pool cleaned up")

# Global pool instance
db_pool = DatabasePool()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_supabase_client() -> Client:
    """Get a Supabase client with retry logic"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY (or ANON_KEY) environment variables must be set")
    
    try:
        # Create client with upload_pipeline schema
        from supabase._sync.client import ClientOptions
        options = ClientOptions()
        options.schema = "upload_pipeline"
        
        client = create_client(
            supabase_url,
            supabase_key,
            options=options
        )
        return client
    except Exception as e:
        logger.warning(f"Database connection error: {str(e)}")
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_supabase_service_client() -> Client:
    """Get a Supabase client with service role privileges"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set")
    
    try:
        # Create client with service role key for admin operations
        from supabase._sync.client import ClientOptions
        options = ClientOptions()
        options.schema = "upload_pipeline"
        
        client = create_client(
            supabase_url,
            supabase_service_key,
            options=options
        )
        return client
    except Exception as e:
        logger.warning(f"Service role database connection error: {str(e)}")
        raise

@asynccontextmanager
async def get_db() -> AsyncGenerator[Client, None]:
    """Async context manager for database access"""
    try:
        client = await db_pool.get_client()
        yield client
    except Exception as e:
        logger.error(f"Database access error: {str(e)}")
        raise 