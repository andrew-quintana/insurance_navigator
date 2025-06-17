"""
Database connection pool and session management for Supabase PostgreSQL.
Provides async database operations with connection pooling and error handling.
"""

import asyncio
import os
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, event

from ..config import config

logger = logging.getLogger(__name__)

Base = declarative_base()
metadata = MetaData()

class DatabasePool:
    """Manages PostgreSQL connection pool for Supabase database."""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.engine = None
        self.session_maker = None
        self._initialized = False
        self._transaction_pooler_mode = False
    
    async def initialize(self) -> None:
        """Initialize database connection pool and SQLAlchemy engine."""
        if self._initialized:
            return
        
        try:
            # Extract connection parameters from DATABASE_URL
            db_url = config.database.url
            if not db_url:
                raise ValueError("DATABASE_URL not configured")
            
            # Log masked database URL for debugging (hide password)
            if db_url:
                masked_url = db_url.split('@')[0].split(':')[:-1]
                masked_url = ':'.join(masked_url) + ':***@' + db_url.split('@')[1] if '@' in db_url else "Invalid URL format"
                logger.info(f"🌐 Using database: {masked_url}")
            
            # Check if using transaction pooler (Supavisor/pgbouncer)
            self._transaction_pooler_mode = (
                os.getenv('ASYNCPG_DISABLE_PREPARED_STATEMENTS') == '1' or
                'pooler.supabase.com' in db_url
            )
            
            # Prepare asyncpg connection pool kwargs with shorter timeouts for faster startup
            pool_kwargs = {
                'min_size': 2,  # Reduced for faster startup
                'max_size': 10,  # Reduced for resource efficiency
                'command_timeout': 30,  # Reduced timeout
                'timeout': 10,  # Connection timeout
                'server_settings': {
                    'jit': 'off',  # Disable JIT for better compatibility
                    'application_name': 'insurance_navigator'
                }
            }
            
            # Critical fix for Supabase transaction pooler (render.com deployment)
            # Disable prepared statements when using transaction poolers like Supavisor
            if self._transaction_pooler_mode:
                pool_kwargs['statement_cache_size'] = 0
                logger.info("🔧 Prepared statements DISABLED for transaction pooler compatibility")
            else:
                logger.info("🔧 Prepared statements ENABLED for direct connections")
            
            # Log environment for debugging
            logger.info(f"🔧 Transaction pooler mode: {self._transaction_pooler_mode}")
            logger.info(f"🔧 Pool config: min_size={pool_kwargs['min_size']}, max_size={pool_kwargs['max_size']}")
            
            # Create asyncpg connection pool with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"📡 Creating database pool (attempt {attempt + 1}/{max_retries})...")
                    self.pool = await asyncpg.create_pool(db_url, **pool_kwargs)
                    logger.info("✅ Database pool created successfully")
                    break
                except Exception as e:
                    logger.error(f"❌ Pool creation failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        logger.error("🚨 All database pool creation attempts failed")
                        raise
                    await asyncio.sleep(2)  # Wait before retry
            
            # Prepare SQLAlchemy engine kwargs
            sqlalchemy_kwargs = {
                'echo': False,  # Set to True for SQL debugging
                'pool_size': 10,
                'max_overflow': 20,
                'pool_pre_ping': True,
                'pool_recycle': 3600,  # Recycle connections after 1 hour
            }
            
            # Apply prepared statement settings to SQLAlchemy as well
            connect_args = {}
            if self._transaction_pooler_mode:
                connect_args['statement_cache_size'] = 0
                logger.info("🔧 SQLAlchemy prepared statements DISABLED for transaction pooler")
            
            # Create SQLAlchemy async engine
            # Convert postgresql:// to postgresql+asyncpg://
            if db_url.startswith('postgresql://'):
                sqlalchemy_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            else:
                sqlalchemy_url = db_url
                
            self.engine = create_async_engine(
                sqlalchemy_url,
                connect_args=connect_args,
                **sqlalchemy_kwargs
            )
            
            # CRITICAL FIX: Add event handler to clear prepared statements for transaction poolers
            # This is the key solution from SQLAlchemy issue #6467
            if self._transaction_pooler_mode:
                @event.listens_for(self.engine.sync_engine, "begin")
                def clear_prepared_statements_on_begin(conn):
                    """Clear prepared statements at transaction start for pooler compatibility."""
                    try:
                        conn.exec_driver_sql("DEALLOCATE ALL")
                        logger.debug("🔧 Cleared prepared statements for transaction pooler")
                    except Exception as e:
                        # Ignore errors if no statements exist to deallocate
                        if "does not exist" not in str(e).lower():
                            logger.warning(f"DEALLOCATE ALL failed: {e}")
                
                logger.info("🔧 SQLAlchemy event handler added: DEALLOCATE ALL on transaction begin")
            
            # Create session maker
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("Database pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close database connections and clean up resources."""
        if self.pool:
            await self.pool.close()
            logger.info("AsyncPG pool closed")
        
        if self.engine:
            await self.engine.dispose()
            logger.info("SQLAlchemy engine disposed")
        
        self._initialized = False
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a raw asyncpg connection from the pool."""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            try:
                # For transaction poolers, clear any existing prepared statements
                if self._transaction_pooler_mode:
                    try:
                        await connection.execute("DEALLOCATE ALL")
                        logger.debug("🔧 Cleared prepared statements for raw connection")
                    except Exception:
                        # Ignore errors if no statements exist
                        pass
                
                yield connection
            except Exception as e:
                error_msg = str(e).lower()
                if 'prepared statement' in error_msg and 'does not exist' in error_msg:
                    logger.error(f"�� CRITICAL: Prepared statement error detected: {e}")
                    logger.error(f"   This indicates transaction pooler compatibility issue")
                    logger.error(f"   Environment: ASYNCPG_DISABLE_PREPARED_STATEMENTS={os.getenv('ASYNCPG_DISABLE_PREPARED_STATEMENTS')}")
                    logger.error(f"   Transaction pooler mode: {self._transaction_pooler_mode}")
                else:
                    logger.error(f"Database connection error: {str(e)}")
                raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a SQLAlchemy async session."""
        if not self._initialized:
            await self.initialize()
        
        if not self.session_maker:
            raise RuntimeError("Session maker not initialized")
        
        async with self.session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                await session.close()
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results."""
        async with self.get_connection() as conn:
            if params:
                result = await conn.fetch(query, *params.values())
            else:
                result = await conn.fetch(query)
            
            return [dict(row) for row in result]
    
    async def execute_command(
        self, 
        command: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a SQL command (INSERT, UPDATE, DELETE) and return status."""
        async with self.get_connection() as conn:
            if params:
                result = await conn.execute(command, *params.values())
            else:
                result = await conn.execute(command)
            
            return result
    
    async def test_connection(self) -> bool:
        """Test database connectivity with transaction pooler compatibility and retry logic."""
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                async with self.get_connection() as conn:
                    # Use simple execute() instead of fetchval() to avoid prepared statements
                    # This is recommended for transaction poolers
                    await conn.execute("SELECT 1")
                    return True
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                if 'prepared statement' in error_msg:
                    logger.error(f"🚨 CRITICAL: Prepared statement error in health check: {e}")
                    logger.error(f"   This will cause render.com deployment to fail")
                    logger.error(f"   Transaction pooler mode: {self._transaction_pooler_mode}")
                elif 'connection was closed' in error_msg or 'connection lost' in error_msg:
                    logger.warning(f"⚠️ Connection dropped (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                else:
                    logger.error(f"Database connection test failed: {str(e)}")
                
                # If this is the last attempt, return False
                if attempt == max_retries - 1:
                    return False
                    
        return False

# Global database pool instance
db_pool = DatabasePool()

async def get_db_pool() -> DatabasePool:
    """Get the global database pool instance."""
    if not db_pool._initialized:
        await db_pool.initialize()
    return db_pool

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function for getting database sessions."""
    pool = await get_db_pool()
    async with pool.get_session() as session:
        yield session

async def get_db_connection() -> AsyncGenerator[Connection, None]:
    """Dependency function for getting raw database connections."""
    pool = await get_db_pool()
    async with pool.get_connection() as conn:
        yield conn

# Cleanup function for application shutdown
async def close_db_pool():
    """Close the global database pool."""
    await db_pool.close() 