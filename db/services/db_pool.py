"""
Database connection pool and session management for Supabase PostgreSQL.
Provides async database operations with connection pooling and error handling.
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

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
    
    async def initialize(self) -> None:
        """Initialize database connection pool and SQLAlchemy engine."""
        if self._initialized:
            return
        
        try:
            # Extract connection parameters from DATABASE_URL
            db_url = config.database.url
            if not db_url:
                raise ValueError("DATABASE_URL not configured")
            
            # Create asyncpg connection pool
            self.pool = await asyncpg.create_pool(
                db_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'jit': 'off',  # Disable JIT for better compatibility
                    'application_name': 'insurance_navigator'
                }
            )
            
            # Create SQLAlchemy async engine
            # Convert postgresql:// to postgresql+asyncpg://
            if db_url.startswith('postgresql://'):
                sqlalchemy_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            else:
                sqlalchemy_url = db_url
                
            self.engine = create_async_engine(
                sqlalchemy_url,
                echo=False,  # Set to True for SQL debugging
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
            
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
                yield connection
            except Exception as e:
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
        """Test database connectivity."""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
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