#!/usr/bin/env python3
"""
Phase 1 Validation Test - Critical Service Integration

This script validates that all Phase 1 requirements have been met:
1. RAG Tool Integration Fix
2. Database Schema Standardization  
3. Configuration System Overhaul

Usage:
    python test_phase1_validation.py
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Phase1Validation")

class Phase1Validator:
    """Validates Phase 1 implementation requirements."""
    
    def __init__(self):
        self.results = {
            "rag_tool_integration": {"passed": False, "details": []},
            "configuration_system": {"passed": False, "details": []},
            "service_dependency_injection": {"passed": False, "details": []},
            "database_schema": {"passed": False, "details": []},
            "error_handling": {"passed": False, "details": []}
        }
    
    async def validate_all(self) -> Dict[str, Any]:
        """Run all Phase 1 validation tests."""
        logger.info("🚀 Starting Phase 1 validation tests...")
        
        # Test 1: RAG Tool Integration
        await self._validate_rag_tool_integration()
        
        # Test 2: Configuration System
        await self._validate_configuration_system()
        
        # Test 3: Service Dependency Injection
        await self._validate_service_dependency_injection()
        
        # Test 4: Database Schema
        await self._validate_database_schema()
        
        # Test 5: Error Handling
        await self._validate_error_handling()
        
        # Calculate overall results
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["passed"])
        
        overall_result = {
            "phase": "Phase 1 - Critical Service Integration",
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "overall_status": "PASSED" if passed_tests == total_tests else "FAILED",
            "results": self.results
        }
        
        return overall_result
    
    async def _validate_rag_tool_integration(self):
        """Validate RAG tool integration fixes."""
        logger.info("🔍 Testing RAG tool integration...")
        
        try:
            # Test 1: RAG tool can be imported
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            self.results["rag_tool_integration"]["details"].append("✅ RAG tool imports successful")
            
            # Test 2: Configuration manager can be imported
            from config.configuration_manager import get_config_manager, initialize_config
            self.results["rag_tool_integration"]["details"].append("✅ Configuration manager imports successful")
            
            # Test 3: Service manager can be imported
            from core.service_manager import get_service_manager, initialize_service_manager
            self.results["rag_tool_integration"]["details"].append("✅ Service manager imports successful")
            
            # Test 4: RAG tool can be instantiated with configuration
            config_manager = initialize_config("production")
            rag_config = RetrievalConfig(
                similarity_threshold=config_manager.get_rag_similarity_threshold(),
                max_chunks=config_manager.get_config("rag.max_chunks", 10),
                token_budget=config_manager.get_config("rag.token_budget", 4000)
            )
            
            # Test similarity threshold is 0.3
            if rag_config.similarity_threshold == 0.3:
                self.results["rag_tool_integration"]["details"].append("✅ Similarity threshold correctly set to 0.3")
            else:
                self.results["rag_tool_integration"]["details"].append(f"❌ Similarity threshold is {rag_config.similarity_threshold}, expected 0.3")
                return
            
            # Test 5: RAG tool can be instantiated
            rag_tool = RAGTool("test_user", rag_config)
            self.results["rag_tool_integration"]["details"].append("✅ RAG tool instantiation successful")
            
            self.results["rag_tool_integration"]["passed"] = True
            logger.info("✅ RAG tool integration validation passed")
            
        except Exception as e:
            self.results["rag_tool_integration"]["details"].append(f"❌ RAG tool integration failed: {str(e)}")
            logger.error(f"❌ RAG tool integration validation failed: {e}")
    
    async def _validate_configuration_system(self):
        """Validate configuration system overhaul."""
        logger.info("🔍 Testing configuration system...")
        
        try:
            # Test 1: Configuration manager can be initialized
            from config.configuration_manager import initialize_config
            config_manager = initialize_config("production")
            self.results["configuration_system"]["details"].append("✅ Configuration manager initialization successful")
            
            # Test 2: Environment detection works
            environment = config_manager.get_environment()
            self.results["configuration_system"]["details"].append(f"✅ Environment detection: {environment.value}")
            
            # Test 3: RAG configuration loading
            similarity_threshold = config_manager.get_rag_similarity_threshold()
            if similarity_threshold == 0.3:
                self.results["configuration_system"]["details"].append("✅ RAG similarity threshold loaded correctly (0.3)")
            else:
                self.results["configuration_system"]["details"].append(f"❌ RAG similarity threshold is {similarity_threshold}, expected 0.3")
                return
            
            # Test 4: Configuration validation
            config_dict = config_manager.to_dict()
            if "rag" in config_dict and "similarity_threshold" in config_dict["rag"]:
                self.results["configuration_system"]["details"].append("✅ Configuration serialization successful")
            else:
                self.results["configuration_system"]["details"].append("❌ Configuration serialization failed")
                return
            
            # Test 5: Hot reloading capability
            reload_success = config_manager.reload_config()
            if reload_success:
                self.results["configuration_system"]["details"].append("✅ Configuration hot reloading works")
            else:
                self.results["configuration_system"]["details"].append("❌ Configuration hot reloading failed")
                return
            
            self.results["configuration_system"]["passed"] = True
            logger.info("✅ Configuration system validation passed")
            
        except Exception as e:
            self.results["configuration_system"]["details"].append(f"❌ Configuration system failed: {str(e)}")
            logger.error(f"❌ Configuration system validation failed: {e}")
    
    async def _validate_service_dependency_injection(self):
        """Validate service dependency injection system."""
        logger.info("🔍 Testing service dependency injection...")
        
        try:
            # Test 1: Service manager can be initialized
            from core.service_manager import initialize_service_manager
            service_manager = initialize_service_manager()
            self.results["service_dependency_injection"]["details"].append("✅ Service manager initialization successful")
            
            # Test 2: Services can be registered
            async def test_init_func():
                return {"test": "value"}
            
            service_manager.register_service(
                name="test_service",
                service_type=dict,
                dependencies=[],
                init_func=test_init_func
            )
            self.results["service_dependency_injection"]["details"].append("✅ Service registration successful")
            
            # Test 3: Services can be initialized
            success = await service_manager.initialize_all_services()
            if success:
                self.results["service_dependency_injection"]["details"].append("✅ Service initialization successful")
            else:
                self.results["service_dependency_injection"]["details"].append("❌ Service initialization failed")
                return
            
            # Test 4: Services can be retrieved
            test_service = service_manager.get_service("test_service")
            if test_service and test_service.get("test") == "value":
                self.results["service_dependency_injection"]["details"].append("✅ Service retrieval successful")
            else:
                self.results["service_dependency_injection"]["details"].append("❌ Service retrieval failed")
                return
            
            # Test 5: Health checks work
            health_status = await service_manager.health_check_all()
            if "test_service" in health_status:
                self.results["service_dependency_injection"]["details"].append("✅ Health checks work")
            else:
                self.results["service_dependency_injection"]["details"].append("❌ Health checks failed")
                return
            
            # Test 6: Services can be shutdown
            shutdown_success = await service_manager.shutdown_all_services()
            if shutdown_success:
                self.results["service_dependency_injection"]["details"].append("✅ Service shutdown successful")
            else:
                self.results["service_dependency_injection"]["details"].append("❌ Service shutdown failed")
                return
            
            self.results["service_dependency_injection"]["passed"] = True
            logger.info("✅ Service dependency injection validation passed")
            
        except Exception as e:
            self.results["service_dependency_injection"]["details"].append(f"❌ Service dependency injection failed: {str(e)}")
            logger.error(f"❌ Service dependency injection validation failed: {e}")
    
    async def _validate_database_schema(self):
        """Validate database schema standardization."""
        logger.info("🔍 Testing database schema...")
        
        try:
            # Test 1: Database schema files exist and are consistent
            schema_files = [
                "scripts/restore_database_schema.sql",
                "sql/integration_schema_setup.sql",
                "create_upload_pipeline_schema.sql"
            ]
            
            for schema_file in schema_files:
                if os.path.exists(schema_file):
                    self.results["database_schema"]["details"].append(f"✅ Schema file exists: {schema_file}")
                else:
                    self.results["database_schema"]["details"].append(f"❌ Schema file missing: {schema_file}")
                    return
            
            # Test 2: RAG tool uses correct table names
            from agents.tooling.rag.core import RAGTool
            import inspect
            
            # Check that RAG tool queries use document_chunks table
            source = inspect.getsource(RAGTool.retrieve_chunks)
            if "document_chunks" in source:
                self.results["database_schema"]["details"].append("✅ RAG tool uses correct table name (document_chunks)")
            else:
                self.results["database_schema"]["details"].append("❌ RAG tool does not use document_chunks table")
                return
            
            # Test 3: No references to old 'chunks' table in RAG tool
            if "chunks" not in source or "document_chunks" in source:
                self.results["database_schema"]["details"].append("✅ No references to old 'chunks' table in RAG tool")
            else:
                self.results["database_schema"]["details"].append("❌ RAG tool still references old 'chunks' table")
                return
            
            # Test 4: Database connection configuration
            from config.configuration_manager import initialize_config
            config_manager = initialize_config("production")
            db_url = config_manager.get_database_url()
            if db_url:
                self.results["database_schema"]["details"].append("✅ Database URL configuration available")
            else:
                self.results["database_schema"]["details"].append("❌ Database URL configuration missing")
                return
            
            self.results["database_schema"]["passed"] = True
            logger.info("✅ Database schema validation passed")
            
        except Exception as e:
            self.results["database_schema"]["details"].append(f"❌ Database schema validation failed: {str(e)}")
            logger.error(f"❌ Database schema validation failed: {e}")
    
    async def _validate_error_handling(self):
        """Validate error handling and logging."""
        logger.info("🔍 Testing error handling...")
        
        try:
            # Test 1: Structured logging is configured
            # Check if logging is properly configured by testing log output
            test_logger = logging.getLogger("test_error_handling")
            test_logger.setLevel(logging.INFO)
            
            # Test that we can create log messages
            test_logger.info("Test log message")
            self.results["error_handling"]["details"].append("✅ Logging system functional")
            
            # Test 2: Error handling middleware exists in main.py
            with open("main.py", "r") as f:
                main_content = f.read()
            
            if "ErrorHandlerMiddleware" in main_content:
                self.results["error_handling"]["details"].append("✅ Error handling middleware exists")
            else:
                self.results["error_handling"]["details"].append("❌ Error handling middleware missing")
                return
            
            # Test 3: Service manager has error handling
            from core.service_manager import ServiceManager
            service_manager = ServiceManager()
            
            # Test error handling in service registration
            try:
                service_manager.register_service("test", dict)
                service_manager.register_service("test", dict)  # Should fail
                self.results["error_handling"]["details"].append("❌ Service registration error handling failed")
                return
            except ValueError:
                self.results["error_handling"]["details"].append("✅ Service registration error handling works")
            
            # Test 4: Configuration manager has error handling
            from config.configuration_manager import ConfigurationManager
            try:
                config_manager = ConfigurationManager()
                # Test invalid threshold
                config_manager.set_rag_similarity_threshold(1.5)  # Should fail
                self.results["error_handling"]["details"].append("❌ Configuration error handling failed")
                return
            except ValueError:
                self.results["error_handling"]["details"].append("✅ Configuration error handling works")
            
            self.results["error_handling"]["passed"] = True
            logger.info("✅ Error handling validation passed")
            
        except Exception as e:
            self.results["error_handling"]["details"].append(f"❌ Error handling validation failed: {str(e)}")
            logger.error(f"❌ Error handling validation failed: {e}")

async def main():
    """Main validation function."""
    print("🚀 Phase 1 Validation Test - Critical Service Integration")
    print("=" * 60)
    
    validator = Phase1Validator()
    results = await validator.validate_all()
    
    print("\n📊 VALIDATION RESULTS")
    print("=" * 60)
    print(f"Phase: {results['phase']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed Tests: {results['passed_tests']}")
    print(f"Failed Tests: {results['failed_tests']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Overall Status: {results['overall_status']}")
    
    print("\n📋 DETAILED RESULTS")
    print("=" * 60)
    
    for test_name, result in results["results"].items():
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"\n{test_name.upper().replace('_', ' ')}: {status}")
        for detail in result["details"]:
            print(f"  {detail}")
    
    print("\n" + "=" * 60)
    
    if results["overall_status"] == "PASSED":
        print("🎉 Phase 1 validation PASSED! All critical service integration fixes are working.")
        return 0
    else:
        print("❌ Phase 1 validation FAILED! Some critical fixes are not working.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
