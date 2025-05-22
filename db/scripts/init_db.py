#!/usr/bin/env python3
"""
Database initialization script.
Sets up the initial database structure and required extensions.
"""

import asyncio
import os
from pathlib import Path
import logging
from typing import List, Optional
import asyncpg
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'insurance_navigator')
}

async def create_database() -> None:
    """Create the database if it doesn't exist."""
    # Connect to default postgres database
    conn = await asyncpg.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database='postgres'
    )
    
    try:
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            DB_CONFIG['database']
        )
        
        if not exists:
            logger.info(f"Creating database {DB_CONFIG['database']}")
            await conn.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        else:
            logger.info(f"Database {DB_CONFIG['database']} already exists")
    finally:
        await conn.close()

async def setup_extensions(conn: asyncpg.Connection) -> None:
    """Setup required PostgreSQL extensions."""
    extensions = ['uuid-ossp', 'pgcrypto']
    for ext in extensions:
        logger.info(f"Enabling extension: {ext}")
        await conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')

async def run_migrations(conn: asyncpg.Connection) -> None:
    """Run database migrations."""
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    migration_files = sorted([f for f in migrations_dir.glob('*.sql') if not f.name.endswith('_rollback.sql')])
    
    # Create migrations table if it doesn't exist
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    
    # Get applied migrations
    applied = await conn.fetch('SELECT version FROM schema_migrations')
    applied_versions = {row['version'] for row in applied}
    
    for migration_file in migration_files:
        version = migration_file.stem
        if version not in applied_versions:
            logger.info(f"Applying migration: {version}")
            
            # Read and execute migration
            sql = migration_file.read_text()
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    'INSERT INTO schema_migrations (version) VALUES ($1)',
                    version
                )
            logger.info(f"Migration {version} applied successfully")
        else:
            logger.info(f"Migration {version} already applied")

async def setup_database() -> None:
    """Main function to setup the database."""
    try:
        # Create database if it doesn't exist
        await create_database()
        
        # Connect to the database
        conn = await asyncpg.connect(**DB_CONFIG)
        try:
            # Setup extensions
            await setup_extensions(conn)
            
            # Run migrations
            await run_migrations(conn)
            
            logger.info("Database setup completed successfully")
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise

def main():
    """Script entry point."""
    asyncio.run(setup_database())

if __name__ == '__main__':
    main() 