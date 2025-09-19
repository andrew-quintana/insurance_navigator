"""
Database pool module for managing database connections.
"""
import os
from typing import Optional, Dict, Any
import logging
import backoff
from supabase import create_client, Client as SupabaseClient
from db.config import SupabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
_client: Optional[SupabaseClient] = None

# Connection status tracking
_connection_status = {
    'is_connected': False,
    'last_error': None,
    'retry_count': 0,
    'max_retries': 3
}

def _should_retry(error: Exception) -> bool:
    """Determine if we should retry on this error."""
    retryable_errors = [
        "connection refused",
        "timeout occurred",
        "network unreachable",
        "connection reset",
        "too many connections"
    ]
    error_str = str(error).lower()
    return any(msg in error_str for msg in retryable_errors)


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3,
    giveup=lambda e: not _should_retry(e)
)
def _create_client() -> Optional[SupabaseClient]:
    """Create a new Supabase client with retries."""
    try:
        # Use environment-based configuration
        config = SupabaseConfig.from_env()
        
        # Create client using proper configuration
        client = create_client(config.url, config.service_role_key)
        
        # Configure client
        client.postgrest.schema('public')
        
        logger.info(f"Successfully created Supabase client for URL: {config.url}")
        _connection_status['is_connected'] = True
        _connection_status['last_error'] = None
        _connection_status['retry_count'] = 0
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        _connection_status['is_connected'] = False
        _connection_status['last_error'] = str(e)
        _connection_status['retry_count'] += 1
        raise

def get_db_pool() -> Optional[SupabaseClient]:
    """Get the database pool instance."""
    global _client
    try:
        if _client is None:
            _client = _create_client()
        return _client
    except Exception as e:
        logger.error(f"Error getting database pool: {str(e)}")
        return None

def close_db_pool() -> None:
    """Close the database pool."""
    global _client
    try:
        _client = None
        _connection_status['is_connected'] = False
        _connection_status['last_error'] = None
        _connection_status['retry_count'] = 0
        logger.info("Database pool closed successfully")
    except Exception as e:
        logger.error(f"Error closing database pool: {str(e)}")

def get_connection_status() -> Dict[str, Any]:
    """Get the current connection status."""
    return _connection_status.copy() 