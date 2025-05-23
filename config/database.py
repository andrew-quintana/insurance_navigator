"""
Database configuration for the insurance navigator application.

This module provides database connection settings and utilities for
connecting to PostgreSQL with pgvector support.
"""

import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dictionary with database connection parameters
    """
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'insurance_navigator')
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