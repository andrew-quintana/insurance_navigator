#!/usr/bin/env python3
"""
Component Validation Tester
Test component functionality without requiring running services
"""

import asyncio
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("component_validation")

class ComponentValidationTester:
    """Test component functionality without requiring running services."""
    
    def __init__(self):
        self.results = []
        
    async def test_fastapi_application_structure(self) -> Dict[str, Any]:
        """Test FastAPI application structure and imports."""
        result = {
            "test_name": "fastapi_application_structure",
            "platform": "render",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            structure_tests = []
            
            # Test main.py exists and is importable
            if os.path.exists("main.py"):
                structure_tests.append({
                    "test": "main_py_exists",
                    "success": True,
                    "details": "main.py file exists"
                })
                
                # Try to import main.py
                try:
                    import main
                    structure_tests.append({
                        "test": "main_py_importable",
                        "success": True,
                        "details": "main.py can be imported successfully"
                    })
                    
                    # Check if FastAPI app is defined
                    if hasattr(main, 'app'):
                        structure_tests.append({
                            "test": "fastapi_app_defined",
                            "success": True,
                            "details": "FastAPI app is defined in main.py"
                        })
                    else:
                        structure_tests.append({
                            "test": "fastapi_app_defined",
                            "success": False,
                            "details": "FastAPI app not found in main.py"
                        })
                except Exception as e:
                    structure_tests.append({
                        "test": "main_py_importable",
                        "success": False,
                        "details": f"Failed to import main.py: {str(e)}"
                    })
            else:
                structure_tests.append({
                    "test": "main_py_exists",
                    "success": False,
                    "details": "main.py file does not exist"
                })
            
            # Test requirements.txt exists
            if os.path.exists("requirements.txt"):
                structure_tests.append({
                    "test": "requirements_txt_exists",
                    "success": True,
                    "details": "requirements.txt file exists"
                })
            else:
                structure_tests.append({
                    "test": "requirements_txt_exists",
                    "success": False,
                    "details": "requirements.txt file does not exist"
                })
            
            # Test core modules exist
            core_modules = ["core/database.py", "core/service_manager.py", "core/agent_integration.py"]
            for module in core_modules:
                if os.path.exists(module):
                    structure_tests.append({
                        "test": f"core_module_{module.replace('/', '_').replace('.', '_')}",
                        "success": True,
                        "details": f"Core module {module} exists"
                    })
                else:
                    structure_tests.append({
                        "test": f"core_module_{module.replace('/', '_').replace('.', '_')}",
                        "success": False,
                        "details": f"Core module {module} does not exist"
                    })
            
            passed_tests = sum(1 for test in structure_tests if test["success"])
            total_tests = len(structure_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"FastAPI application structure: {passed_tests}/{total_tests} tests passed",
                "test_results": structure_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"FastAPI application structure error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_vercel_frontend_structure(self) -> Dict[str, Any]:
        """Test Vercel frontend structure and configuration."""
        result = {
            "test_name": "vercel_frontend_structure",
            "platform": "vercel",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            frontend_tests = []
            
            # Test package.json exists
            if os.path.exists("package.json"):
                frontend_tests.append({
                    "test": "package_json_exists",
                    "success": True,
                    "details": "package.json file exists"
                })
                
                # Check package.json content
                try:
                    with open("package.json", "r") as f:
                        package_data = json.load(f)
                    
                    # Check for required scripts
                    scripts = package_data.get("scripts", {})
                    required_scripts = ["dev", "build", "start"]
                    for script in required_scripts:
                        if script in scripts:
                            frontend_tests.append({
                                "test": f"script_{script}",
                                "success": True,
                                "details": f"Script '{script}' is defined"
                            })
                        else:
                            frontend_tests.append({
                                "test": f"script_{script}",
                                "success": False,
                                "details": f"Script '{script}' is not defined"
                            })
                    
                    # Check for Next.js
                    dependencies = package_data.get("dependencies", {})
                    if "next" in dependencies:
                        frontend_tests.append({
                            "test": "nextjs_dependency",
                            "success": True,
                            "details": "Next.js is included in dependencies"
                        })
                    else:
                        frontend_tests.append({
                            "test": "nextjs_dependency",
                            "success": False,
                            "details": "Next.js is not included in dependencies"
                        })
                        
                except Exception as e:
                    frontend_tests.append({
                        "test": "package_json_parse",
                        "success": False,
                        "details": f"Failed to parse package.json: {str(e)}"
                    })
            else:
                frontend_tests.append({
                    "test": "package_json_exists",
                    "success": False,
                    "details": "package.json file does not exist"
                })
            
            # Test Vercel configuration
            vercel_config_files = ["vercel.json", ".vercelignore"]
            for config_file in vercel_config_files:
                if os.path.exists(config_file):
                    frontend_tests.append({
                        "test": f"vercel_config_{config_file.replace('.', '_')}",
                        "success": True,
                        "details": f"Vercel config file {config_file} exists"
                    })
                else:
                    frontend_tests.append({
                        "test": f"vercel_config_{config_file.replace('.', '_')}",
                        "success": False,
                        "details": f"Vercel config file {config_file} does not exist"
                    })
            
            # Test UI directory structure
            ui_dirs = ["ui", "frontend", "src", "app", "pages"]
            ui_dir_found = False
            for ui_dir in ui_dirs:
                if os.path.exists(ui_dir) and os.path.isdir(ui_dir):
                    ui_dir_found = True
                    frontend_tests.append({
                        "test": f"ui_directory_{ui_dir}",
                        "success": True,
                        "details": f"UI directory {ui_dir} exists"
                    })
                    break
            
            if not ui_dir_found:
                frontend_tests.append({
                    "test": "ui_directory",
                    "success": False,
                    "details": "No UI directory found (ui, frontend, src, app, pages)"
                })
            
            passed_tests = sum(1 for test in frontend_tests if test["success"])
            total_tests = len(frontend_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel frontend structure: {passed_tests}/{total_tests} tests passed",
                "test_results": frontend_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel frontend structure error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_database_integration_structure(self) -> Dict[str, Any]:
        """Test database integration structure and configuration."""
        result = {
            "test_name": "database_integration_structure",
            "platform": "render",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            db_tests = []
            
            # Test Supabase configuration
            supabase_files = ["supabase/config.toml", "supabase/migrations", "supabase/seed.sql"]
            for file_path in supabase_files:
                if os.path.exists(file_path):
                    db_tests.append({
                        "test": f"supabase_{file_path.replace('/', '_').replace('.', '_')}",
                        "success": True,
                        "details": f"Supabase file {file_path} exists"
                    })
                else:
                    db_tests.append({
                        "test": f"supabase_{file_path.replace('/', '_').replace('.', '_')}",
                        "success": False,
                        "details": f"Supabase file {file_path} does not exist"
                    })
            
            # Test environment files
            env_files = [".env.development", ".env.staging", ".env.production", ".env.local"]
            for env_file in env_files:
                if os.path.exists(env_file):
                    db_tests.append({
                        "test": f"env_file_{env_file.replace('.', '_')}",
                        "success": True,
                        "details": f"Environment file {env_file} exists"
                    })
                else:
                    db_tests.append({
                        "test": f"env_file_{env_file.replace('.', '_')}",
                        "success": False,
                        "details": f"Environment file {env_file} does not exist"
                    })
            
            # Test database connection modules
            db_modules = ["core/database.py", "db/config.py", "db/services"]
            for module in db_modules:
                if os.path.exists(module):
                    db_tests.append({
                        "test": f"db_module_{module.replace('/', '_').replace('.', '_')}",
                        "success": True,
                        "details": f"Database module {module} exists"
                    })
                else:
                    db_tests.append({
                        "test": f"db_module_{module.replace('/', '_').replace('.', '_')}",
                        "success": False,
                        "details": f"Database module {module} does not exist"
                    })
            
            passed_tests = sum(1 for test in db_tests if test["success"])
            total_tests = len(db_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Database integration structure: {passed_tests}/{total_tests} tests passed",
                "test_results": db_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Database integration structure error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_worker_components_structure(self) -> Dict[str, Any]:
        """Test worker components structure."""
        result = {
            "test_name": "worker_components_structure",
            "platform": "render",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            worker_tests = []
            
            # Test worker directory structure
            worker_dirs = ["backend/workers", "workers", "jobs"]
            worker_dir_found = False
            for worker_dir in worker_dirs:
                if os.path.exists(worker_dir) and os.path.isdir(worker_dir):
                    worker_dir_found = True
                    worker_tests.append({
                        "test": f"worker_directory_{worker_dir.replace('/', '_')}",
                        "success": True,
                        "details": f"Worker directory {worker_dir} exists"
                    })
                    break
            
            if not worker_dir_found:
                worker_tests.append({
                    "test": "worker_directory",
                    "success": False,
                    "details": "No worker directory found"
                })
            
            # Test worker configuration files
            worker_configs = ["requirements-worker.txt", "render-upload-pipeline-worker.yaml"]
            for config_file in worker_configs:
                if os.path.exists(config_file):
                    worker_tests.append({
                        "test": f"worker_config_{config_file.replace('.', '_').replace('-', '_')}",
                        "success": True,
                        "details": f"Worker config file {config_file} exists"
                    })
                else:
                    worker_tests.append({
                        "test": f"worker_config_{config_file.replace('.', '_').replace('-', '_')}",
                        "success": False,
                        "details": f"Worker config file {config_file} does not exist"
                    })
            
            passed_tests = sum(1 for test in worker_tests if test["success"])
            total_tests = len(worker_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Worker components structure: {passed_tests}/{total_tests} tests passed",
                "test_results": worker_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Worker components structure error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_security_components_structure(self) -> Dict[str, Any]:
        """Test security components structure."""
        result = {
            "test_name": "security_components_structure",
            "platform": "both",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            security_tests = []
            
            # Test authentication modules
            auth_modules = ["backend/shared/auth.py", "core/auth.py", "auth/"]
            for module in auth_modules:
                if os.path.exists(module):
                    security_tests.append({
                        "test": f"auth_module_{module.replace('/', '_').replace('.', '_')}",
                        "success": True,
                        "details": f"Authentication module {module} exists"
                    })
                else:
                    security_tests.append({
                        "test": f"auth_module_{module.replace('/', '_').replace('.', '_')}",
                        "success": False,
                        "details": f"Authentication module {module} does not exist"
                    })
            
            # Test security configuration files
            security_configs = [".env.production.example", "config/auth_config.py"]
            for config_file in security_configs:
                if os.path.exists(config_file):
                    security_tests.append({
                        "test": f"security_config_{config_file.replace('/', '_').replace('.', '_')}",
                        "success": True,
                        "details": f"Security config file {config_file} exists"
                    })
                else:
                    security_tests.append({
                        "test": f"security_config_{config_file.replace('/', '_').replace('.', '_')}",
                        "success": False,
                        "details": f"Security config file {config_file} does not exist"
                    })
            
            passed_tests = sum(1 for test in security_tests if test["success"])
            total_tests = len(security_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Security components structure: {passed_tests}/{total_tests} tests passed",
                "test_results": security_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Security components structure error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_deployment_configurations(self) -> Dict[str, Any]:
        """Test deployment configurations for both platforms."""
        result = {
            "test_name": "deployment_configurations",
            "platform": "both",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            deployment_tests = []
            
            # Test Render configuration files
            render_configs = ["render.yaml", "render-upload-pipeline.yaml", "render-upload-pipeline-worker.yaml"]
            for config_file in render_configs:
                if os.path.exists(config_file):
                    deployment_tests.append({
                        "test": f"render_config_{config_file.replace('.', '_').replace('-', '_')}",
                        "success": True,
                        "details": f"Render config file {config_file} exists"
                    })
                else:
                    deployment_tests.append({
                        "test": f"render_config_{config_file.replace('.', '_').replace('-', '_')}",
                        "success": False,
                        "details": f"Render config file {config_file} does not exist"
                    })
            
            # Test Docker configuration
            docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yml"]
            for docker_file in docker_files:
                if os.path.exists(docker_file):
                    deployment_tests.append({
                        "test": f"docker_{docker_file.replace('.', '_').replace('-', '_')}",
                        "success": True,
                        "details": f"Docker file {docker_file} exists"
                    })
                else:
                    deployment_tests.append({
                        "test": f"docker_{docker_file.replace('.', '_').replace('-', '_')}",
                        "success": False,
                        "details": f"Docker file {docker_file} does not exist"
                    })
            
            # Test Vercel configuration
            vercel_configs = ["vercel.json", ".vercelignore"]
            for config_file in vercel_configs:
                if os.path.exists(config_file):
                    deployment_tests.append({
                        "test": f"vercel_config_{config_file.replace('.', '_')}",
                        "success": True,
                        "details": f"Vercel config file {config_file} exists"
                    })
                else:
                    deployment_tests.append({
                        "test": f"vercel_config_{config_file.replace('.', '_')}",
                        "success": False,
                        "details": f"Vercel config file {config_file} does not exist"
                    })
            
            passed_tests = sum(1 for test in deployment_tests if test["success"])
            total_tests = len(deployment_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Deployment configurations: {passed_tests}/{total_tests} tests passed",
                "test_results": deployment_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Deployment configurations error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def run_all_tests(self):
        """Run all component validation tests."""
        print("=" * 80)
        print("COMPONENT VALIDATION TESTING")
        print("=" * 80)
        print(f"Project Root: {project_root}")
        print(f"Start Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all validation tests
        await self.test_fastapi_application_structure()
        await self.test_vercel_frontend_structure()
        await self.test_database_integration_structure()
        await self.test_worker_components_structure()
        await self.test_security_components_structure()
        await self.test_deployment_configurations()
        
        # Generate report
        self._generate_report()
    
    def _generate_report(self):
        """Generate component validation test report."""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.get("status") == "passed"])
        partial_tests = len([r for r in self.results if r.get("status") == "partial"])
        error_tests = len([r for r in self.results if r.get("status") == "error"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": "component_validation",
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "partial_tests": partial_tests,
                "error_tests": error_tests,
                "success_rate": success_rate
            },
            "test_results": self.results
        }
        
        # Save report
        os.makedirs("test-results", exist_ok=True)
        report_path = "test-results/component_validation_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*80)
        print("COMPONENT VALIDATION TESTING SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Partial: {partial_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Report saved to: {report_path}")
        print("="*80)
        
        return report

async def main():
    """Main execution function."""
    tester = ComponentValidationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
