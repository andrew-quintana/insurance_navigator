import asyncio
import asyncpg
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager with connection pooling and health monitoring"""
    
    def __init__(self, database_url: str, min_size: int = 5, max_size: int = 20):
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )
            logger.info(f"Database pool initialized with {self.min_size}-{self.max_size} connections")
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close the connection pool and cleanup"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def get_connection(self):
        """Get a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return await self.pool.acquire()
    
    async def release_connection(self, connection):
        """Release a database connection back to the pool"""
        if self.pool:
            await self.pool.release(connection)
    
    @asynccontextmanager
    async def get_db_connection(self):
        """Context manager for database connections"""
        connection = await self.get_connection()
        try:
            yield connection
        finally:
            await self.release_connection(connection)
    
    async def execute(self, query: str, *args, **kwargs):
        """Execute a query using the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return await self.pool.execute(query, *args, **kwargs)
    
    async def fetch(self, query: str, *args, **kwargs):
        """Fetch rows using the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return await self.pool.fetch(query, *args, **kwargs)
    
    async def fetchrow(self, query: str, *args, **kwargs):
        """Fetch a single row using the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return await self.pool.fetchrow(query, *args, **kwargs)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database"""
        try:
            if not self.pool:
                return {"status": "unhealthy", "error": "Pool not initialized"}
            
            # Test connection and basic query
            async with self.get_db_connection() as conn:
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
    
    async def _health_check_loop(self):
        """Background health check loop"""
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

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

async def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return _db_manager

async def initialize_database(database_url: str):
    """Initialize the global database manager"""
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    await _db_manager.initialize()

async def close_database():
    """Close the global database manager"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None

# Convenience function for getting connections
async def get_db_connection():
    """Get a database connection from the global manager"""
    manager = await get_db_manager()
    return await manager.get_db_connection()
