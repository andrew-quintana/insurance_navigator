#!/usr/bin/env python3
"""
Phase 1 Import Resolution Test Script

This script tests the import management resolution implemented in Phase 1
of the Agent Integration Infrastructure Refactor.

Usage:
    python test_phase1_imports.py [--verbose] [--test-specific TEST_NAME]
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class Phase1ImportTester:
    """Tests Phase 1 import management resolution."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.errors: List[str] = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 1 import tests."""
        logger.info("Starting Phase 1 import resolution tests")
        
        # Test 1: Core module imports
        await self._test_core_imports()
        
        # Test 2: Database manager initialization
        await self._test_database_manager()
        
        # Test 3: Agent integration manager
        await self._test_agent_integration()
        
        # Test 4: System initialization
        await self._test_system_initialization()
        
        # Test 5: Import validation script
        await self._test_import_validation()
        
        # Test 6: Agent migration script
        await self._test_agent_migration()
        
        return {
            "test_results": self.test_results,
            "errors": self.errors,
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results.values() if r.get("passed", False)]),
            "failed_tests": len([r for r in self.test_results.values() if not r.get("passed", False)])
        }
    
    async def _test_core_imports(self) -> None:
        """Test that core modules can be imported without errors."""
        test_name = "core_imports"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test core module imports
            from core import initialize_system, close_system, get_database, get_agents
            from core.database import DatabaseManager, create_database_config
            from core.agent_integration import AgentIntegrationManager, initialize_agent_integration
            
            self.test_results[test_name] = {
                "passed": True,
                "message": "All core modules imported successfully"
            }
            
        except ImportError as e:
            error_msg = f"Core import test failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.test_results[test_name] = {
                "passed": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Core import test failed with unexpected error: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.test_results[test_name] = {
                "passed": False,
                "error": error_msg
            }
    
    async def _test_database_manager(self) -> None:
        """Test database manager initialization and functionality."""
        test_name = "database_manager"
        logger.info(f"Running test: {test_name}")
        
        try:
            from core.database import DatabaseManager, create_database_config
            
            # Create database configuration
            config = create_database_config()
            
            # Test database manager creation
            db_manager = DatabaseManager(config)
            
            # Test configuration properties
            assert hasattr(config, 'connection_string')
            assert hasattr(config, 'host')
            assert hasattr(config, 'port')
            
            self.test_results[test_name] = {
                "passed": True,
                "message": "Database manager created successfully",
                "config": {
                    "host": config.host,
                    "port": config.port,
                    "database": config.database
                }
            }
            
        except Exception as e:
            error_msg = f"Database manager test failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.test_results[test_name] = {
                "passed": False,
                "error": error_msg
            }
    
    async def _test_agent_integration(self) -> None:
        """Test agent integration manager functionality."""
        test_name = "agent_integration"
        logger.info(f"Running test: {test_name}")
        
        try:
            from core.agent_integration import AgentIntegrationManager, AgentConfig
            from core.database import DatabaseManager, create_database_config
            
            # Create test configuration
            config = create_database_config()
            db_manager = DatabaseManager(config)
            agent_config = AgentConfig(use_mock=True)
            
            # Test agent integration manager creation
            agent_manager = AgentIntegrationManager(db_manager, agent_config)
            
            # Test configuration properties
            assert hasattr(agent_manager, 'db_manager')
            assert hasattr(agent_manager, 'config')
            assert hasattr(agent_manager, '_agents')
            
            self.test_results[test_name] = {
                "passed": True,
                "message": "Agent integration manager created successfully",
                "config": {
                    "use_mock": agent_config.use_mock,
                    "timeout_seconds": agent_config.timeout_seconds
                }
            }
            
        except Exception as e:
            error_msg = f"Agent integration test failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.test_results[test_name] = {
                "passed": False,
                "error": error_msg
            }
    
    async def _test_system_initialization(self) -> None:
        """Test system initialization and shutdown."""
        test_name = "system_initialization"
        logger.info(f"Running test: {test_name}")
        
        try:
            from core import SystemManager
            
            # Test system manager creation
            system_manager = SystemManager()
            
            # Test initialization order
            assert hasattr(system_manager, '_initialization_order')
            assert 'database' in system_manager._initialization_order
            assert 'agent_integration' in system_manager._initialization_order
            
            # Test health check method exists
            assert hasattr(system_manager, 'health_check')
            assert callable(system_manager.health_check)
            
            self.test_results[test_name] = {
                "passed": True,
                "message": "System manager created successfully",
                "initialization_order": system_manager._initialization_order
            }
            
        except Exception as e:
            error_msg = f"System initialization test failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.test_results[test_name] = {
                "passed": False,
                "error": error_msg
            }
    
    async def _test_import_validation(self) -> None:
        """Test the import validation script."""
        test_name = "import_validation_script"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test that the validation script can be imported
            import scripts.validate_imports as validate_imports
            
            # Test that the ImportValidator class exists
            assert hasattr(validate_imports, 'ImportValidator')
            
            # Test that the main function exists
            assert hasattr(validate_imports, 'main')
            
            self.test_results[test_name] = {
                "passed": True,
                "message": "Import validation script imported successfully"
            }
            
        except Exception as e:
            error_msg = f"Import validation script test failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.test_results[test_name] = {
                "passed": False,
                "error": error_msg
            }
    
    async def _test_agent_migration(self) -> None:
        """Test the agent migration script."""
        test_name = "agent_migration_script"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test that the migration script can be imported
            import scripts.migrate_agents_to_di as migrate_agents
            
            # Test that the AgentMigrator class exists
            assert hasattr(migrate_agents, 'AgentMigrator')
            
            # Test that the main function exists
            assert hasattr(migrate_agents, 'main')
            
            self.test_results[test_name] = {
                "passed": True,
                "message": "Agent migration script imported successfully"
            }
            
        except Exception as e:
            error_msg = f"Agent migration script test failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.test_results[test_name] = {
                "passed": False,
                "error": error_msg
            }
    
    async def test_specific(self, test_name: str) -> Dict[str, Any]:
        """Run a specific test."""
        if test_name == "core_imports":
            await self._test_core_imports()
        elif test_name == "database_manager":
            await self._test_database_manager()
        elif test_name == "agent_integration":
            await self._test_agent_integration()
        elif test_name == "system_initialization":
            await self._test_system_initialization()
        elif test_name == "import_validation_script":
            await self._test_import_validation()
        elif test_name == "agent_migration_script":
            await self._test_agent_migration()
        else:
            raise ValueError(f"Unknown test: {test_name}")
        
        return self.test_results.get(test_name, {})


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Phase 1 import resolution")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--test-specific", type=str, help="Run specific test")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create tester
    tester = Phase1ImportTester()
    
    try:
        if args.test_specific:
            result = await tester.test_specific(args.test_specific)
            print(f"\nTest Result: {result}")
            return 0 if result.get("passed", False) else 1
        else:
            result = await tester.run_all_tests()
            
            # Print results
            print(f"\n{'='*60}")
            print(f"Phase 1 Import Resolution Test Results")
            print(f"{'='*60}")
            print(f"Total tests: {result['total_tests']}")
            print(f"Passed tests: {result['passed_tests']}")
            print(f"Failed tests: {result['failed_tests']}")
            print(f"Errors: {len(result['errors'])}")
            
            if result['test_results']:
                print(f"\nTest Details:")
                for test_name, test_result in result['test_results'].items():
                    status = "✅ PASS" if test_result.get("passed", False) else "❌ FAIL"
                    message = test_result.get("message", test_result.get("error", "Unknown"))
                    print(f"  {status} {test_name}: {message}")
            
            if result['errors']:
                print(f"\nErrors:")
                for error in result['errors']:
                    print(f"  ❌ {error}")
            
            print(f"\n{'='*60}")
            
            return 0 if result['failed_tests'] == 0 else 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
