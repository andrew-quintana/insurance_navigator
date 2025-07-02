"""
Database pool module for managing database connections.
"""
import os
import jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
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

def _generate_jwt_token() -> str:
    """Generate a JWT token for authentication."""
    jwt_secret = "zNfav2GWycDdZIsQxJ5UogupJmcKHUkt3pV/LC87Dkk="
    payload = {
        "role": "service_role",
        "iss": "supabase",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")

@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3,
    giveup=lambda e: not _should_retry(e)
)
def _create_client() -> Optional[SupabaseClient]:
    """Create a new Supabase client with retries."""
    try:
        # Use local Supabase instance
        url = "http://127.0.0.1:54321"
        token = _generate_jwt_token()
            
        # Create client
        client = create_client(url, token)
        
        # Configure client
        client.postgrest.schema('public')
        
        logger.info("Successfully created Supabase client")
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