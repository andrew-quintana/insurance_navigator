from typing import Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta
import json

from asyncpg.pool import Pool
import asyncpg
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class DatabasePool:
    """
    Manages database connections with connection pooling, monitoring, and retry logic.
    """
    def __init__(
        self,
        dsn: str,
        min_size: int = 10,
        max_size: int = 50,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: float = 300.0,
        setup_queries: Optional[list[str]] = None
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.max_queries = max_queries
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self.setup_queries = setup_queries or []
        self._pool: Optional[Pool] = None
        self._stats: Dict[str, Any] = {
            'created_at': datetime.utcnow().isoformat(),
            'total_connections': 0,
            'active_connections': 0,
            'queries_executed': 0,
            'last_error': None,
            'error_count': 0
        }

    async def initialize(self):
        """Initialize the connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                max_queries=self.max_queries,
                max_inactive_connection_lifetime=self.max_inactive_connection_lifetime,
                setup=self._connection_setup
            )
            logger.info(f"Database pool initialized with {self.min_size} to {self.max_size} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            self._update_error_stats(e)
            raise

    async def _connection_setup(self, connection: asyncpg.Connection):
        """Setup a new database connection with initial queries."""
        try:
            # Set session parameters
            await connection.execute("SET application_name = 'insurance_navigator'")
            await connection.execute("SET timezone = 'UTC'")
            
            # Execute any additional setup queries
            for query in self.setup_queries:
                await connection.execute(query)
            
            self._stats['total_connections'] += 1
        except Exception as e:
            logger.error(f"Failed to setup database connection: {str(e)}")
            self._update_error_stats(e)
            raise

    def _update_error_stats(self, error: Exception):
        """Update error statistics."""
        self._stats['last_error'] = {
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(error),
            'type': error.__class__.__name__
        }
        self._stats['error_count'] += 1

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a database connection from the pool.
        
        Usage:
            async with pool.acquire() as connection:
                await connection.execute(query)
        """
        if not self._pool:
            raise RuntimeError("Database pool not initialized")

        try:
            self._stats['active_connections'] += 1
            async with self._pool.acquire() as connection:
                yield connection
        except Exception as e:
            self._update_error_stats(e)
            raise
        finally:
            self._stats['active_connections'] -= 1

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def execute_with_retry(self, query: str, *args, timeout: Optional[float] = None):
        """Execute a query with retry logic."""
        try:
            async with self.acquire() as connection:
                result = await connection.execute(query, *args, timeout=timeout)
                self._stats['queries_executed'] += 1
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            self._update_error_stats(e)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def fetch_with_retry(self, query: str, *args, timeout: Optional[float] = None):
        """Fetch results with retry logic."""
        try:
            async with self.acquire() as connection:
                result = await connection.fetch(query, *args, timeout=timeout)
                self._stats['queries_executed'] += 1
                return result
        except Exception as e:
            logger.error(f"Query fetch failed: {str(e)}")
            self._update_error_stats(e)
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get current pool statistics."""
        if not self._pool:
            return self._stats

        pool_stats = {
            'pool_size': len(self._pool._holders),
            'free_size': len(self._pool._free),
            'max_size': self._pool._max_size,
        }
        
        return {**self._stats, **pool_stats}

    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database pool closed")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.
        Returns:
            Dict containing health status and metrics.
        """
        try:
            start_time = datetime.utcnow()
            async with self.acquire() as connection:
                await connection.execute('SELECT 1')
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            stats = await self.get_stats()
            return {
                'status': 'healthy',
                'response_time_seconds': response_time,
                'last_checked': datetime.utcnow().isoformat(),
                'pool_stats': stats
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            self._update_error_stats(e)
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_checked': datetime.utcnow().isoformat(),
                'pool_stats': await self.get_stats()
            } 