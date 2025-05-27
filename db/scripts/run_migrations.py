"""
Database migration runner for Supabase PostgreSQL.
Executes migration scripts in order and tracks migration state.
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import asyncpg

from ..config import config

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Handles database migration execution and tracking."""
    
    def __init__(self):
        self.db_url = config.database.url
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
        
    async def run_migrations(self) -> Dict[str, Any]:
        """Run all pending migrations."""
        if not self.db_url:
            raise ValueError("DATABASE_URL not configured")
        
        try:
            # Connect to database
            conn = await asyncpg.connect(self.db_url)
            
            # Ensure migration tracking table exists
            await self._create_migration_table(conn)
            
            # Get migration files
            migration_files = self._get_migration_files()
            
            # Track migration results
            results = {
                'executed': [],
                'skipped': [],
                'failed': [],
                'total': len(migration_files)
            }
            
            # Execute migrations in order
            for migration_file in migration_files:
                try:
                    migration_name = migration_file.stem
                    
                    # Check if migration already executed
                    if await self._is_migration_executed(conn, migration_name):
                        logger.info(f"Skipping migration {migration_name} - already executed")
                        results['skipped'].append(migration_name)
                        continue
                    
                    # Execute migration
                    logger.info(f"Executing migration: {migration_name}")
                    await self._execute_migration(conn, migration_file)
                    
                    # Record migration execution
                    await self._record_migration(conn, migration_name)
                    results['executed'].append(migration_name)
                    
                    logger.info(f"Successfully executed migration: {migration_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to execute migration {migration_file.stem}: {str(e)}")
                    results['failed'].append({
                        'name': migration_file.stem,
                        'error': str(e)
                    })
                    # Continue with other migrations
            
            await conn.close()
            
            # Log summary
            logger.info(f"Migration completed - Executed: {len(results['executed'])}, "
                       f"Skipped: {len(results['skipped'])}, "
                       f"Failed: {len(results['failed'])}")
            
            return results
            
        except Exception as e:
            logger.error(f"Migration runner failed: {str(e)}")
            raise
    
    async def _create_migration_table(self, conn: asyncpg.Connection) -> None:
        """Create migration tracking table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            migration_name TEXT NOT NULL UNIQUE,
            executed_at TIMESTAMPTZ DEFAULT NOW(),
            checksum TEXT,
            execution_time_ms INTEGER
        );
        """
        await conn.execute(create_table_sql)
    
    def _get_migration_files(self) -> List[Path]:
        """Get all migration files sorted by name."""
        if not self.migrations_dir.exists():
            raise FileNotFoundError(f"Migrations directory not found: {self.migrations_dir}")
        
        migration_files = []
        for file_path in self.migrations_dir.glob("*.sql"):
            migration_files.append(file_path)
        
        # Sort by filename to ensure correct order
        migration_files.sort(key=lambda x: x.name)
        return migration_files
    
    async def _is_migration_executed(self, conn: asyncpg.Connection, migration_name: str) -> bool:
        """Check if a migration has already been executed."""
        result = await conn.fetchval(
            "SELECT 1 FROM migration_history WHERE migration_name = $1",
            migration_name
        )
        return result is not None
    
    async def _execute_migration(self, conn: asyncpg.Connection, migration_file: Path) -> None:
        """Execute a single migration file."""
        start_time = datetime.now()
        
        # Read migration file
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Split into individual statements (basic implementation)
        statements = self._split_sql_statements(migration_sql)
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                await conn.execute(statement)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Migration {migration_file.stem} executed in {execution_time:.2f}ms")
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL content into individual statements."""
        # Simple implementation - split on semicolon
        # Note: This doesn't handle complex cases like functions or triggers
        statements = []
        current_statement = ""
        
        for line in sql.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue
            
            current_statement += line + '\n'
            
            # If line ends with semicolon, it's end of statement
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    async def _record_migration(self, conn: asyncpg.Connection, migration_name: str) -> None:
        """Record successful migration execution."""
        await conn.execute(
            """
            INSERT INTO migration_history (migration_name)
            VALUES ($1)
            """,
            migration_name
        )
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Check if migration table exists
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'migration_history'
                )
                """
            )
            
            if not table_exists:
                return {
                    'status': 'not_initialized',
                    'executed_migrations': [],
                    'pending_migrations': self._get_migration_files()
                }
            
            # Get executed migrations
            executed_migrations = await conn.fetch(
                "SELECT migration_name, executed_at FROM migration_history ORDER BY executed_at"
            )
            
            executed_names = [row['migration_name'] for row in executed_migrations]
            all_migrations = [f.stem for f in self._get_migration_files()]
            pending_migrations = [name for name in all_migrations if name not in executed_names]
            
            await conn.close()
            
            return {
                'status': 'initialized',
                'executed_migrations': executed_names,
                'pending_migrations': pending_migrations,
                'total_migrations': len(all_migrations)
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

async def run_migrations():
    """Convenience function to run migrations."""
    runner = MigrationRunner()
    return await runner.run_migrations()

async def get_migration_status():
    """Convenience function to get migration status."""
    runner = MigrationRunner()
    return await runner.get_migration_status()

if __name__ == "__main__":
    # Run migrations when script is executed directly
    async def main():
        logging.basicConfig(level=logging.INFO)
        runner = MigrationRunner()
        
        # Show current status
        status = await runner.get_migration_status()
        print(f"Migration Status: {status}")
        
        # Run migrations
        if status['pending_migrations']:
            print(f"Running {len(status['pending_migrations'])} pending migrations...")
            results = await runner.run_migrations()
            print(f"Migration Results: {results}")
        else:
            print("No pending migrations to run.")
    
    asyncio.run(main()) 