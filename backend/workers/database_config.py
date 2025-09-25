"""
Database configuration for worker service with pooler URL support.
This is a local copy to work around the build filter limitation.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl_mode: str = "prefer"
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"


def create_database_config() -> DatabaseConfig:
    """Create database configuration from environment variables."""
    # For cloud deployments (Render, Vercel, etc.), prefer pooler URL to avoid IPv6 issues
    # For local development, use DATABASE_URL directly
    is_cloud_deployment = any(os.getenv(var) for var in ['RENDER', 'VERCEL', 'HEROKU_APP_NAME', 'AWS_LAMBDA_FUNCTION_NAME', 'K_SERVICE'])
    
    logger.info(f"Database config creation - Cloud deployment: {is_cloud_deployment}")
    logger.info(f"RENDER env var: {os.getenv('RENDER')}")
    logger.info(f"SUPABASE_SESSION_POOLER_URL available: {bool(os.getenv('SUPABASE_SESSION_POOLER_URL'))}")
    logger.info(f"SUPABASE_POOLER_URL available: {bool(os.getenv('SUPABASE_POOLER_URL'))}")
    logger.info(f"DEBUG: Using worker-specific database config with pooler URL support")
    
    if is_cloud_deployment:
        # Use pooler URL for IPv4 connectivity in cloud deployments
        # Direct DATABASE_URL has IPv6 connectivity issues from Render
        pooler_url = os.getenv("SUPABASE_SESSION_POOLER_URL") or os.getenv("SUPABASE_POOLER_URL")
        if pooler_url:
            logger.info(f"Using Supabase pooler URL for IPv4 connectivity: {pooler_url[:50]}...")
            db_url = pooler_url
        else:
            # Fallback to direct DATABASE_URL if no pooler available
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                logger.warning("No pooler URL found, using direct DATABASE_URL (may have IPv6 connectivity issues)")
            else:
                logger.warning("No database URL found")
    else:
        # Local development: use DATABASE_URL directly
        db_url = os.getenv("DATABASE_URL")
        logger.info("Using direct DATABASE_URL for local development")
    
    if db_url:
        # Parse DATABASE_URL if available
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        # Determine SSL mode based on connection type
        if any(host in db_url for host in ["127.0.0.1", "localhost", "supabase_db_insurance_navigator"]):
            ssl_mode = "disable"
        elif "pooler.supabase.com" in db_url or "dfgzeastcxnoqshgyotp" in db_url:
            # Supabase pooler URLs need require SSL
            ssl_mode = "require"
        else:
            ssl_mode = "require"
        
        # For pooler URLs, add connection parameters to avoid SCRAM authentication issues
        if "pooler.supabase.com" in db_url:
            # Add connection parameters to avoid SCRAM authentication
            if "?" in db_url:
                db_url += "&sslmode=require&application_name=insurance_navigator_worker"
            else:
                db_url += "?sslmode=require&application_name=insurance_navigator_worker"
            logger.info("Added connection parameters to pooler URL to avoid SCRAM authentication issues")
        
        logger.info(f"Database connection SSL mode: {ssl_mode}")
        logger.info(f"Database host: {parsed.hostname}")
        
        return DatabaseConfig(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/') or "postgres",
            user=parsed.username or "postgres",
            password=parsed.password or "",
            ssl_mode=ssl_mode
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
