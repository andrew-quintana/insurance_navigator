#!/usr/bin/env python3
"""
Direct unit test execution for Insurance Navigator core modules.

This script runs unit tests directly without pytest to avoid import issues.
"""

import sys
import os
import asyncio
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core modules
from core.database import DatabaseConfig, DatabaseManager, create_database_config
from core.service_manager import ServiceManager, ServiceInfo, ServiceStatus
from core.agent_integration import AgentIntegrationManager, AgentConfig

class TestDatabaseConfig(unittest.TestCase):
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
        
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.database, "test_db")
        self.assertEqual(config.user, "test_user")
        self.assertEqual(config.password, "test_pass")
        self.assertEqual(config.min_connections, 5)  # default
        self.assertEqual(config.max_connections, 20)  # default
        self.assertEqual(config.command_timeout, 60)  # default
        self.assertEqual(config.ssl_mode, "prefer")  # default
    
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
        self.assertEqual(config.connection_string, expected)

class TestDatabaseManager(unittest.TestCase):
    """Test DatabaseManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass",
            min_connections=1,
            max_connections=5
        )
        self.db_manager = DatabaseManager(self.config)
    
    def test_database_manager_initialization(self):
        """Test database manager initialization."""
        self.assertEqual(self.db_manager.config, self.config)
        self.assertIsNone(self.db_manager.pool)
        self.assertIsNone(self.db_manager._health_check_task)
        self.assertFalse(self.db_manager._is_initialized)
    
    def test_is_supabase_connection_true(self):
        """Test Supabase connection detection."""
        self.db_manager.config.host = "your-project.supabase.com"
        self.assertTrue(self.db_manager._is_supabase_connection())
        
        self.db_manager.config.host = "project.supabase.co"
        self.assertTrue(self.db_manager._is_supabase_connection())
    
    def test_is_supabase_connection_false(self):
        """Test non-Supabase connection detection."""
        self.db_manager.config.host = "localhost"
        self.assertFalse(self.db_manager._is_supabase_connection())
        
        self.db_manager.config.host = "postgres.example.com"
        self.assertFalse(self.db_manager._is_supabase_connection())

class TestServiceManager(unittest.TestCase):
    """Test ServiceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service_manager = ServiceManager()
    
    def test_service_manager_initialization(self):
        """Test service manager initialization."""
        self.assertEqual(self.service_manager._services, {})
        self.assertEqual(self.service_manager._initialization_order, [])
        self.assertFalse(self.service_manager._is_initialized)
        self.assertFalse(self.service_manager._is_shutting_down)
    
    def test_register_service_success(self):
        """Test successful service registration."""
        self.service_manager.register_service(
            name="test_service",
            service_type=Mock,
            dependencies=["dep1"],
            health_check=lambda x: True
        )
        
        self.assertIn("test_service", self.service_manager._services)
        service_info = self.service_manager._services["test_service"]
        self.assertEqual(service_info.name, "test_service")
        self.assertEqual(service_info.service_type, Mock)
        self.assertEqual(service_info.dependencies, ["dep1"])
        self.assertIsNotNone(service_info.health_check)
    
    def test_register_service_duplicate(self):
        """Test registering duplicate service."""
        self.service_manager.register_service("test_service", Mock)
        
        with self.assertRaises(ValueError):
            self.service_manager.register_service("test_service", Mock)
    
    def test_get_service_not_found(self):
        """Test getting non-existent service."""
        result = self.service_manager.get_service("nonexistent")
        self.assertIsNone(result)
    
    def test_get_service_status_not_found(self):
        """Test getting status of non-existent service."""
        result = self.service_manager.get_service_status("nonexistent")
        self.assertIsNone(result)

class TestAgentConfig(unittest.TestCase):
    """Test AgentConfig class."""
    
    def test_agent_config_creation(self):
        """Test basic agent config creation."""
        config = AgentConfig()
        
        self.assertFalse(config.use_mock)
        self.assertEqual(config.timeout_seconds, 30)
        self.assertEqual(config.retry_attempts, 3)
        self.assertTrue(config.enable_health_checks)
    
    def test_agent_config_custom_values(self):
        """Test agent config with custom values."""
        config = AgentConfig(
            use_mock=True,
            timeout_seconds=60,
            retry_attempts=5,
            enable_health_checks=False
        )
        
        self.assertTrue(config.use_mock)
        self.assertEqual(config.timeout_seconds, 60)
        self.assertEqual(config.retry_attempts, 5)
        self.assertFalse(config.enable_health_checks)

class TestAgentIntegrationManager(unittest.TestCase):
    """Test AgentIntegrationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db_manager = AsyncMock()
        self.mock_db_manager.health_check.return_value = {"status": "healthy"}
        self.agent_config = AgentConfig()
        self.agent_manager = AgentIntegrationManager(self.mock_db_manager, self.agent_config)
    
    def test_agent_manager_initialization(self):
        """Test agent manager initialization."""
        self.assertEqual(self.agent_manager.db_manager, self.mock_db_manager)
        self.assertEqual(self.agent_manager.config, self.agent_config)
        self.assertEqual(self.agent_manager._agents, {})
        self.assertFalse(self.agent_manager._initialized)

def run_tests():
    """Run all unit tests."""
    print("=" * 80)
    print("INSURANCE NAVIGATOR - DIRECT UNIT TESTING")
    print("=" * 80)
    print(f"Project Root: {project_root}")
    print(f"Python Path: {sys.path[0]}")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestDatabaseConfig,
        TestDatabaseManager,
        TestServiceManager,
        TestAgentConfig,
        TestAgentIntegrationManager
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 80)
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
