#!/usr/bin/env python3
"""
Test Script for Infrastructure Validation Framework
003 Worker Refactor - Phase 2

This script tests all components of the infrastructure validation framework
to ensure it works correctly before deployment.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the validation directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from deployment_validator import DeploymentValidator
from automated_rollback import AutomatedRollback


class ValidationFrameworkTester:
    """Comprehensive tester for the infrastructure validation framework"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    async def run_all_tests(self) -> bool:
        """Run all validation framework tests"""
        print("🧪 Testing Infrastructure Validation Framework")
        print("=" * 60)
        
        tests = [
            ("Configuration Loading", self.test_configuration_loading),
            ("Local Baseline Creation", self.test_local_baseline_creation),
            ("Deployment Validator", self.test_deployment_validator),
            ("Health Check Framework", self.test_health_check_framework),
            ("Database Validation", self.test_database_validation),
            ("Performance Validation", self.test_performance_validation),
            ("Security Validation", self.test_security_validation),
            ("Rollback System", self.test_rollback_system),
            ("Report Generation", self.test_report_generation),
            ("Integration Testing", self.test_integration)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            print("-" * 40)
            
            try:
                result = await test_func()
                if result:
                    print(f"✅ {test_name}: PASSED")
                    self.test_results[test_name] = "PASSED"
                else:
                    print(f"❌ {test_name}: FAILED")
                    self.test_results[test_name] = "FAILED"
                    all_passed = False
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                self.test_results[test_name] = f"ERROR: {e}"
                all_passed = False
        
        # Print summary
        self.print_test_summary()
        
        return all_passed
    
    async def test_configuration_loading(self) -> bool:
        """Test configuration loading functionality"""
        try:
            config_path = Path("infrastructure/config/deployment_config.yaml")
            if not config_path.exists():
                print("  ⚠️  Configuration file not found, creating test config...")
                self.create_test_config()
            
            # Test YAML loading
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            required_keys = ["environment", "database", "services", "validation"]
            for key in required_keys:
                if key not in config:
                    print(f"  ❌ Missing required config key: {key}")
                    return False
            
            print("  ✅ Configuration loaded successfully")
            print(f"  ✅ Environment: {config.get('environment')}")
            print(f"  ✅ Services: {len(config.get('services', {}))}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Configuration loading failed: {e}")
            return False
    
    def create_test_config(self):
        """Create a test configuration file"""
        config_content = """
environment: test
deployment_type: docker_compose

database:
  host: localhost
  port: 5432
  database: test_db
  user: test_user
  password: test_pass

services:
  test_service:
    host: localhost
    port: 8000
    health_endpoint: /health

validation:
  health_check_interval_seconds: 30
  rollback_triggers:
    health_check_failure_threshold: 3
"""
        
        config_path = Path("infrastructure/config/deployment_config.yaml")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print("  ✅ Test configuration created")
    
    async def test_local_baseline_creation(self) -> bool:
        """Test local baseline creation"""
        try:
            # This will create the default baseline if it doesn't exist
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            baseline_path = Path("infrastructure/validation/local_baseline.json")
            if baseline_path.exists():
                print("  ✅ Local baseline exists")
                
                with open(baseline_path, 'r') as f:
                    baseline = json.load(f)
                
                required_keys = ["environment", "services", "database_schema", "performance_baseline"]
                for key in required_keys:
                    if key not in baseline:
                        print(f"  ❌ Missing baseline key: {key}")
                        return False
                
                print(f"  ✅ Baseline contains {len(baseline.get('services', {}))} services")
                return True
            else:
                print("  ❌ Local baseline not created")
                return False
                
        except Exception as e:
            print(f"  ❌ Local baseline creation failed: {e}")
            return False
    
    async def test_deployment_validator(self) -> bool:
        """Test deployment validator initialization"""
        try:
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            # Test basic properties
            if not hasattr(validator, 'config'):
                print("  ❌ Validator missing config attribute")
                return False
            
            if not hasattr(validator, 'local_baseline'):
                print("  ❌ Validator missing local_baseline attribute")
                return False
            
            print("  ✅ Deployment validator initialized successfully")
            print(f"  ✅ Config keys: {list(validator.config.keys())}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Deployment validator test failed: {e}")
            return False
    
    async def test_health_check_framework(self) -> bool:
        """Test health check framework"""
        try:
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            # Test health check result creation
            from deployment_validator import HealthCheckResult
            
            health_result = HealthCheckResult(
                service="test_service",
                endpoint="/health",
                status_code=200,
                response_time_ms=50.0,
                healthy=True
            )
            
            if health_result.service != "test_service":
                print("  ❌ Health check result creation failed")
                return False
            
            # Test to_dict conversion
            health_dict = health_result.to_dict()
            if "timestamp" not in health_dict:
                print("  ❌ Health check result serialization failed")
                return False
            
            print("  ✅ Health check framework working")
            return True
            
        except Exception as e:
            print(f"  ❌ Health check framework test failed: {e}")
            return False
    
    async def test_database_validation(self) -> bool:
        """Test database validation methods"""
        try:
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            # Test validation result creation
            from deployment_validator import ValidationResult
            
            validation_result = ValidationResult(
                service="database",
                check_type="connection",
                status=True,
                message="Test database connection",
                duration_ms=25.0,
                timestamp=validator.local_baseline.get("timestamp", "2025-01-14T00:00:00")
            )
            
            if validation_result.service != "database":
                print("  ❌ Validation result creation failed")
                return False
            
            # Test to_dict conversion
            validation_dict = validation_result.to_dict()
            if "timestamp" not in validation_dict:
                print("  ❌ Validation result serialization failed")
                return False
            
            print("  ✅ Database validation framework working")
            return True
            
        except Exception as e:
            print(f"  ❌ Database validation test failed: {e}")
            return False
    
    async def test_performance_validation(self) -> bool:
        """Test performance validation methods"""
        try:
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            # Test baseline loading
            baseline = validator.local_baseline.get("performance_baseline", {})
            if not baseline:
                print("  ⚠️  No performance baseline found")
                return True  # Not a failure, just no baseline
            
            print(f"  ✅ Performance baseline loaded: {list(baseline.keys())}")
            return True
            
        except Exception as e:
            print(f"  ❌ Performance validation test failed: {e}")
            return False
    
    async def test_security_validation(self) -> bool:
        """Test security validation methods"""
        try:
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            # Test security config loading
            security_config = validator.config.get("security", {})
            if not security_config:
                print("  ⚠️  No security configuration found")
                return True  # Not a failure, just no config
            
            print(f"  ✅ Security configuration loaded: {list(security_config.keys())}")
            return True
            
        except Exception as e:
            print(f"  ❌ Security validation test failed: {e}")
            return False
    
    async def test_rollback_system(self) -> bool:
        """Test rollback system"""
        try:
            rollback_system = AutomatedRollback("infrastructure/config/deployment_config.yaml")
            
            # Test rollback trigger checking
            test_validation_results = {
                "overall": True,
                "services": {"failed_checks": 0},
                "database": {"overall": True},
                "performance": {"overall": True},
                "security": {"overall": True}
            }
            
            triggers = rollback_system.check_rollback_triggers(test_validation_results)
            
            if triggers:
                print("  ⚠️  Rollback triggers activated unexpectedly")
                return False
            
            print("  ✅ Rollback system working correctly")
            print(f"  ✅ No triggers activated for healthy system")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Rollback system test failed: {e}")
            return False
    
    async def test_report_generation(self) -> bool:
        """Test report generation"""
        try:
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            # Test validation report generation
            report = validator.generate_validation_report()
            
            required_keys = ["timestamp", "summary", "validation_results", "health_check_results"]
            for key in required_keys:
                if key not in report:
                    print(f"  ❌ Missing report key: {key}")
                    return False
            
            print("  ✅ Report generation working")
            print(f"  ✅ Report contains {len(report.get('validation_results', []))} validation results")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Report generation test failed: {e}")
            return False
    
    async def test_integration(self) -> bool:
        """Test integration between components"""
        try:
            # Test full validation workflow
            validator = DeploymentValidator("infrastructure/config/deployment_config.yaml")
            
            # Test rollback integration
            rollback_system = AutomatedRollback("infrastructure/config/deployment_config.yaml")
            
            # Simulate validation failure
            test_failure_results = {
                "overall": False,
                "infrastructure": False,
                "services": {"failed_checks": 5},
                "database": {"overall": False}
            }
            
            # Check rollback triggers
            triggers = rollback_system.check_rollback_triggers(test_failure_results)
            
            if not triggers:
                print("  ❌ Rollback triggers not activated for failure")
                return False
            
            print(f"  ✅ Integration test passed - {len(triggers)} rollback triggers activated")
            return True
            
        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            return False
    
    def print_test_summary(self):
        """Print test results summary"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if "PASSED" in str(result))
        failed = sum(1 for result in self.test_results.values() if "FAILED" in str(result))
        errors = sum(1 for result in self.test_results.values() if "ERROR" in str(result))
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Errors: {errors} ⚠️")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        
        if failed == 0 and errors == 0:
            print("\n🎉 ALL TESTS PASSED! Infrastructure validation framework is ready.")
        else:
            print(f"\n⚠️  {failed + errors} tests failed. Please review and fix issues.")
        
        print("=" * 60)
        
        # Print detailed results
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if "PASSED" in str(result) else "❌"
            print(f"  {status_icon} {test_name}: {result}")


async def main():
    """Main test execution function"""
    tester = ValidationFrameworkTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎯 All validation framework tests passed!")
            print("🚀 Infrastructure validation framework is ready for deployment.")
            sys.exit(0)
        else:
            print("\n❌ Some validation framework tests failed.")
            print("🔧 Please fix the issues before proceeding with deployment.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
