"""
Unit tests for core database module.

Tests the DatabaseManager class and related functionality including:
- Connection establishment and pooling
- Query execution methods
- Transaction handling
- Error handling and recovery
- Health checks
- Configuration management
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from contextlib import asynccontextmanager

from core.database import (
    DatabaseManager,
    DatabaseConfig,
    create_database_config,
    initialize_database,
    close_database,
    get_database_manager,
    get_db_connection
)


class TestDatabaseConfig:
    """Test DatabaseConfig class."""
    
    def test_database_config_creation(self):
        """Test basic database config creation."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.user == "test_user"
        assert config.password == "test_pass"
        assert config.min_connections == 5  # default
        assert config.max_connections == 20  # default
        assert config.command_timeout == 60  # default
        assert config.ssl_mode == "prefer"  # default
    
    def test_connection_string_generation(self):
        """Test connection string generation."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass",
            ssl_mode="require"
        )
        
        expected = "postgresql://test_user:test_pass@localhost:5432/test_db?sslmode=require"
        assert config.connection_string == expected
    
    def test_connection_string_with_special_chars(self):
        """Test connection string with special characters in password."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test@pass#word",
            ssl_mode="require"
        )
        
        # Should handle URL encoding
        connection_string = config.connection_string
        assert "test@pass#word" in connection_string or "%40" in connection_string


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock database configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass",
            min_connections=1,
            max_connections=5
        )
    
    @pytest.fixture
    def db_manager(self, mock_config):
        """Create a DatabaseManager instance."""
        return DatabaseManager(mock_config)
    
    def test_database_manager_initialization(self, db_manager, mock_config):
        """Test database manager initialization."""
        assert db_manager.config == mock_config
        assert db_manager.pool is None
        assert db_manager._health_check_task is None
        assert db_manager._is_initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, db_manager):
        """Test successful database initialization."""
        with patch('core.database.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            await db_manager.initialize()
            
            assert db_manager._is_initialized is True
            assert db_manager.pool == mock_pool
            mock_create_pool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, db_manager):
        """Test initialization when already initialized."""
        db_manager._is_initialized = True
        
        with patch('core.database.create_pool') as mock_create_pool:
            await db_manager.initialize()
            mock_create_pool.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, db_manager):
        """Test initialization failure handling."""
        with patch('core.database.create_pool') as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                await db_manager.initialize()
            
            assert db_manager._is_initialized is False
            assert db_manager.pool is None
    
    @pytest.mark.asyncio
    async def test_close_success(self, db_manager):
        """Test successful database closure."""
        # Mock pool and health check task
        mock_pool = AsyncMock()
        mock_task = AsyncMock()
        db_manager.pool = mock_pool
        db_manager._health_check_task = mock_task
        db_manager._is_initialized = True
        
        await db_manager.close()
        
        mock_task.cancel.assert_called_once()
        mock_pool.close.assert_called_once()
        assert db_manager._is_initialized is False
    
    @pytest.mark.asyncio
    async def test_close_no_pool(self, db_manager):
        """Test closure when no pool exists."""
        await db_manager.close()  # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_get_connection_not_initialized(self, db_manager):
        """Test getting connection when not initialized."""
        with pytest.raises(RuntimeError, match="Database manager not initialized"):
            async with db_manager.get_connection():
                pass
    
    @pytest.mark.asyncio
    async def test_get_connection_success(self, db_manager):
        """Test successful connection acquisition."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        async with db_manager.get_connection() as conn:
            assert conn == mock_conn
            mock_conn.execute.assert_called_with('SET search_path TO upload_pipeline, public')
    
    @pytest.mark.asyncio
    async def test_execute_query(self, db_manager):
        """Test query execution."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "EXECUTED"
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        result = await db_manager.execute("SELECT 1", "arg1", key="value")
        
        assert result == "EXECUTED"
        mock_conn.execute.assert_called_with("SELECT 1", "arg1", key="value")
    
    @pytest.mark.asyncio
    async def test_fetch_query(self, db_manager):
        """Test fetch query execution."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_records = [Mock(), Mock()]
        mock_conn.fetch.return_value = mock_records
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        result = await db_manager.fetch("SELECT * FROM test")
        
        assert result == mock_records
        mock_conn.fetch.assert_called_with("SELECT * FROM test")
    
    @pytest.mark.asyncio
    async def test_fetchrow_query(self, db_manager):
        """Test fetchrow query execution."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_record = Mock()
        mock_conn.fetchrow.return_value = mock_record
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        result = await db_manager.fetchrow("SELECT * FROM test WHERE id = $1", 1)
        
        assert result == mock_record
        mock_conn.fetchrow.assert_called_with("SELECT * FROM test WHERE id = $1", 1)
    
    @pytest.mark.asyncio
    async def test_fetchval_query(self, db_manager):
        """Test fetchval query execution."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = "test_value"
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        result = await db_manager.fetchval("SELECT COUNT(*) FROM test")
        
        assert result == "test_value"
        mock_conn.fetchval.assert_called_with("SELECT COUNT(*) FROM test")
    
    @pytest.mark.asyncio
    async def test_executemany_query(self, db_manager):
        """Test executemany query execution."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.executemany.return_value = "EXECUTED"
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        args_list = [("arg1",), ("arg2",)]
        result = await db_manager.executemany("INSERT INTO test VALUES ($1)", args_list)
        
        assert result == "EXECUTED"
        mock_conn.executemany.assert_called_with("INSERT INTO test VALUES ($1)", args_list)
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, db_manager):
        """Test health check when database is healthy."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 1
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.get_size.return_value = 5
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        result = await db_manager.health_check()
        
        assert result["status"] == "healthy"
        assert result["pool_size"] == 5
        assert result["free_size"] == 5
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_not_initialized(self, db_manager):
        """Test health check when not initialized."""
        result = await db_manager.health_check()
        
        assert result["status"] == "unhealthy"
        assert "Pool not initialized" in result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_query_fails(self, db_manager):
        """Test health check when query fails."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 0  # Not 1, so query "fails"
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        result = await db_manager.health_check()
        
        assert result["status"] == "unhealthy"
        assert "Basic query failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_exception(self, db_manager):
        """Test health check when exception occurs."""
        mock_pool = AsyncMock()
        mock_pool.acquire.side_effect = Exception("Connection failed")
        db_manager.pool = mock_pool
        db_manager._is_initialized = True
        
        result = await db_manager.health_check()
        
        assert result["status"] == "unhealthy"
        assert "Connection failed" in result["error"]
    
    def test_is_supabase_connection_true(self, db_manager):
        """Test Supabase connection detection."""
        db_manager.config.host = "znvwzkdblknkkztqyfnu.supabase.com"
        assert db_manager._is_supabase_connection() is True
        
        db_manager.config.host = "project.supabase.co"
        assert db_manager._is_supabase_connection() is True
    
    def test_is_supabase_connection_false(self, db_manager):
        """Test non-Supabase connection detection."""
        db_manager.config.host = "localhost"
        assert db_manager._is_supabase_connection() is False
        
        db_manager.config.host = "postgres.example.com"
        assert db_manager._is_supabase_connection() is False
    
    @pytest.mark.asyncio
    async def test_setup_connection(self, db_manager):
        """Test connection setup."""
        mock_conn = AsyncMock()
        
        await db_manager._setup_connection(mock_conn)
        
        # Verify all setup commands were called
        assert mock_conn.execute.call_count == 4
        calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        assert "SET timezone = 'UTC'" in calls
        assert "SET application_name = 'insurance_navigator'" in calls
        assert "SET statement_timeout = '60s'" in calls
        assert "SET idle_in_transaction_session_timeout = '30s'" in calls


class TestDatabaseConfigCreation:
    """Test database configuration creation from environment."""
    
    def test_create_config_from_database_url(self):
        """Test config creation from DATABASE_URL."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@host:5432/db?sslmode=require'
        }):
            config = create_database_config()
            
            assert config.host == "host"
            assert config.port == 5432
            assert config.database == "db"
            assert config.user == "user"
            assert config.password == "pass"
            assert config.ssl_mode == "require"
    
    def test_create_config_from_individual_vars(self):
        """Test config creation from individual environment variables."""
        with patch.dict(os.environ, {
            'DB_HOST': 'testhost',
            'DB_PORT': '5433',
            'DB_NAME': 'testdb',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'SUPABASE_URL': 'https://test.supabase.co'
        }, clear=True):
            config = create_database_config()
            
            assert config.host == "testhost"
            assert config.port == 5433
            assert config.database == "testdb"
            assert config.user == "testuser"
            assert config.password == "testpass"
            assert config.ssl_mode == "require"  # Because SUPABASE_URL is set
    
    def test_create_config_defaults(self):
        """Test config creation with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = create_database_config()
            
            assert config.host == "127.0.0.1"
            assert config.port == 54322
            assert config.database == "postgres"
            assert config.user == "postgres"
            assert config.password == "postgres"
            assert config.ssl_mode == "prefer"


class TestGlobalDatabaseManager:
    """Test global database manager functions."""
    
    @pytest.mark.asyncio
    async def test_initialize_database_success(self):
        """Test successful database initialization."""
        with patch('core.database.DatabaseManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            result = await initialize_database()
            
            assert result == mock_manager
            mock_manager.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_database_already_initialized(self):
        """Test database initialization when already initialized."""
        with patch('core.database._db_manager', mock_manager := AsyncMock()):
            result = await initialize_database()
            
            assert result == mock_manager
    
    @pytest.mark.asyncio
    async def test_get_database_manager_not_initialized(self):
        """Test getting database manager when not initialized."""
        with patch('core.database._db_manager', None):
            with pytest.raises(RuntimeError, match="Database manager not initialized"):
                await get_database_manager()
    
    @pytest.mark.asyncio
    async def test_get_database_manager_success(self):
        """Test getting initialized database manager."""
        mock_manager = AsyncMock()
        with patch('core.database._db_manager', mock_manager):
            result = await get_database_manager()
            
            assert result == mock_manager
    
    @pytest.mark.asyncio
    async def test_close_database(self):
        """Test closing database manager."""
        mock_manager = AsyncMock()
        with patch('core.database._db_manager', mock_manager):
            await close_database()
            
            mock_manager.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_database_none(self):
        """Test closing database when manager is None."""
        with patch('core.database._db_manager', None):
            await close_database()  # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_get_db_connection(self):
        """Test getting database connection from global manager."""
        mock_manager = AsyncMock()
        mock_conn = AsyncMock()
        mock_manager.get_connection.return_value.__aenter__.return_value = mock_conn
        
        with patch('core.database.get_database_manager', return_value=mock_manager):
            async with get_db_connection() as conn:
                assert conn == mock_conn


class TestDatabaseManagerIntegration:
    """Integration tests for DatabaseManager."""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Test complete database manager lifecycle."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass",
            min_connections=1,
            max_connections=2
        )
        
        with patch('core.database.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.fetchval.return_value = 1
            mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
            mock_pool.get_size.return_value = 2
            mock_create_pool.return_value = mock_pool
            
            # Initialize
            manager = DatabaseManager(config)
            await manager.initialize()
            
            # Test operations
            result = await manager.fetchval("SELECT 1")
            assert result == 1
            
            # Test health check
            health = await manager.health_check()
            assert health["status"] == "healthy"
            
            # Close
            await manager.close()
            mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_pool_management(self):
        """Test connection pool management."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass",
            min_connections=2,
            max_connections=5
        )
        
        with patch('core.database.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            manager = DatabaseManager(config)
            await manager.initialize()
            
            # Verify pool was created with correct parameters
            mock_create_pool.assert_called_once()
            call_args = mock_create_pool.call_args
            assert call_args[1]['min_size'] == 2
            assert call_args[1]['max_size'] == 5
            assert call_args[1]['command_timeout'] == 60
            assert call_args[1]['statement_cache_size'] == 0
            
            await manager.close()


if __name__ == "__main__":
    pytest.main([__file__])
