#!/usr/bin/env python3
"""
Vercel CLI Component Tester
Test Vercel CLI local development functionality as part of Phase 2 component testing
"""

import asyncio
import json
import os
import sys
import subprocess
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vercel_cli_tester")

class VercelCLIComponentTester:
    """Test Vercel CLI component functionality."""
    
    def __init__(self):
        self.results = []
        self.ui_dir = Path("ui")
        self.vercel_process = None
        
    async def test_vercel_cli_installation(self) -> Dict[str, Any]:
        """Test Vercel CLI installation and version."""
        result = {
            "test_name": "vercel_cli_installation",
            "platform": "vercel",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            installation_tests = []
            
            # Check if Vercel CLI is installed
            try:
                vercel_version = subprocess.run(
                    ["vercel", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if vercel_version.returncode == 0:
                    installation_tests.append({
                        "test": "vercel_cli_installed",
                        "success": True,
                        "details": f"Vercel CLI installed: {vercel_version.stdout.strip()}"
                    })
                else:
                    installation_tests.append({
                        "test": "vercel_cli_installed",
                        "success": False,
                        "details": f"Vercel CLI not found: {vercel_version.stderr}"
                    })
            except FileNotFoundError:
                installation_tests.append({
                    "test": "vercel_cli_installed",
                    "success": False,
                    "details": "Vercel CLI not installed - need to install with 'npm install -g vercel'"
                })
            except subprocess.TimeoutExpired:
                installation_tests.append({
                    "test": "vercel_cli_installed",
                    "success": False,
                    "details": "Vercel CLI command timed out"
                })
            
            # Check if we're in a Vercel project
            if (self.ui_dir / ".vercel").exists():
                installation_tests.append({
                    "test": "vercel_project_initialized",
                    "success": True,
                    "details": "Vercel project is initialized (.vercel directory exists)"
                })
            else:
                installation_tests.append({
                    "test": "vercel_project_initialized",
                    "success": False,
                    "details": "Vercel project not initialized - need to run 'vercel' in ui directory"
                })
            
            passed_tests = sum(1 for test in installation_tests if test["success"])
            total_tests = len(installation_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel CLI installation: {passed_tests}/{total_tests} tests passed",
                "test_results": installation_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel CLI installation error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_vercel_local_development(self) -> Dict[str, Any]:
        """Test Vercel local development server."""
        result = {
            "test_name": "vercel_local_development",
            "platform": "vercel",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            dev_tests = []
            
            # Check if we can start Vercel dev server
            try:
                # Start Vercel dev server in background
                self.vercel_process = subprocess.Popen(
                    ["vercel", "dev", "--port", "3001"],  # Use port 3001 to avoid conflicts
                    cwd=self.ui_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for server to start
                max_wait = 60  # 1 minute
                server_started = False
                
                for i in range(max_wait):
                    try:
                        response = requests.get("http://localhost:3001", timeout=2)
                        if response.status_code == 200:
                            server_started = True
                            break
                    except:
                        pass
                    
                    if i % 10 == 0 and i > 0:
                        logger.info(f"Waiting for Vercel dev server... ({i}/{max_wait} seconds)")
                    time.sleep(1)
                
                if server_started:
                    dev_tests.append({
                        "test": "vercel_dev_server_start",
                        "success": True,
                        "details": "Vercel dev server started successfully on port 3001"
                    })
                    
                    # Test basic functionality
                    try:
                        # Test root endpoint
                        root_response = requests.get("http://localhost:3001", timeout=5)
                        dev_tests.append({
                            "test": "vercel_root_endpoint",
                            "success": root_response.status_code == 200,
                            "status_code": root_response.status_code,
                            "response_time_ms": root_response.elapsed.total_seconds() * 1000
                        })
                        
                        # Test API routes (if any)
                        api_response = requests.get("http://localhost:3001/api/health", timeout=5)
                        dev_tests.append({
                            "test": "vercel_api_routes",
                            "success": api_response.status_code in [200, 404],  # 404 is OK if no API routes
                            "status_code": api_response.status_code,
                            "response_time_ms": api_response.elapsed.total_seconds() * 1000
                        })
                        
                    except Exception as e:
                        dev_tests.append({
                            "test": "vercel_endpoint_testing",
                            "success": False,
                            "details": f"Failed to test endpoints: {str(e)}"
                        })
                else:
                    dev_tests.append({
                        "test": "vercel_dev_server_start",
                        "success": False,
                        "details": "Vercel dev server failed to start within 60 seconds"
                    })
                
            except Exception as e:
                dev_tests.append({
                    "test": "vercel_dev_server_start",
                    "success": False,
                    "details": f"Failed to start Vercel dev server: {str(e)}"
                })
            
            passed_tests = sum(1 for test in dev_tests if test["success"])
            total_tests = len(dev_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel local development: {passed_tests}/{total_tests} tests passed",
                "test_results": dev_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel local development error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_vercel_build_process(self) -> Dict[str, Any]:
        """Test Vercel build process."""
        result = {
            "test_name": "vercel_build_process",
            "platform": "vercel",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            build_tests = []
            
            # Test npm build process
            try:
                build_result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=self.ui_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes
                )
                
                if build_result.returncode == 0:
                    build_tests.append({
                        "test": "npm_build_success",
                        "success": True,
                        "details": "npm run build completed successfully"
                    })
                    
                    # Check if build output exists
                    if (self.ui_dir / ".next").exists():
                        build_tests.append({
                            "test": "build_output_exists",
                            "success": True,
                            "details": "Build output directory .next exists"
                        })
                    else:
                        build_tests.append({
                            "test": "build_output_exists",
                            "success": False,
                            "details": "Build output directory .next not found"
                        })
                else:
                    build_tests.append({
                        "test": "npm_build_success",
                        "success": False,
                        "details": f"npm run build failed: {build_result.stderr}"
                    })
                    
            except subprocess.TimeoutExpired:
                build_tests.append({
                    "test": "npm_build_success",
                    "success": False,
                    "details": "npm run build timed out after 5 minutes"
                })
            except Exception as e:
                build_tests.append({
                    "test": "npm_build_success",
                    "success": False,
                    "details": f"npm run build error: {str(e)}"
                })
            
            # Test Vercel build command
            try:
                vercel_build = subprocess.run(
                    ["vercel", "build"],
                    cwd=self.ui_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                build_tests.append({
                    "test": "vercel_build_command",
                    "success": vercel_build.returncode == 0,
                    "details": f"Vercel build command: {'success' if vercel_build.returncode == 0 else 'failed'}"
                })
                
            except Exception as e:
                build_tests.append({
                    "test": "vercel_build_command",
                    "success": False,
                    "details": f"Vercel build command error: {str(e)}"
                })
            
            passed_tests = sum(1 for test in build_tests if test["success"])
            total_tests = len(build_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel build process: {passed_tests}/{total_tests} tests passed",
                "test_results": build_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel build process error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_vercel_environment_configuration(self) -> Dict[str, Any]:
        """Test Vercel environment configuration."""
        result = {
            "test_name": "vercel_environment_configuration",
            "platform": "vercel",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            env_tests = []
            
            # Check environment files
            env_files = [".env.local", ".env.production", ".env.example"]
            for env_file in env_files:
                env_path = self.ui_dir / env_file
                if env_path.exists():
                    env_tests.append({
                        "test": f"env_file_{env_file.replace('.', '_')}",
                        "success": True,
                        "details": f"Environment file {env_file} exists"
                    })
                else:
                    env_tests.append({
                        "test": f"env_file_{env_file.replace('.', '_')}",
                        "success": False,
                        "details": f"Environment file {env_file} not found"
                    })
            
            # Check vercel.json configuration
            vercel_config_path = self.ui_dir / "vercel.json"
            if vercel_config_path.exists():
                env_tests.append({
                    "test": "vercel_config_exists",
                    "success": True,
                    "details": "vercel.json configuration file exists"
                })
                
                # Check vercel.json content
                try:
                    with open(vercel_config_path, 'r') as f:
                        vercel_config = json.load(f)
                    
                    # Check for required configuration
                    required_configs = ["buildCommand", "outputDirectory", "framework"]
                    for config in required_configs:
                        if config in vercel_config:
                            env_tests.append({
                                "test": f"vercel_config_{config}",
                                "success": True,
                                "details": f"vercel.json contains {config}"
                            })
                        else:
                            env_tests.append({
                                "test": f"vercel_config_{config}",
                                "success": False,
                                "details": f"vercel.json missing {config}"
                            })
                            
                except Exception as e:
                    env_tests.append({
                        "test": "vercel_config_parse",
                        "success": False,
                        "details": f"Failed to parse vercel.json: {str(e)}"
                    })
            else:
                env_tests.append({
                    "test": "vercel_config_exists",
                    "success": False,
                    "details": "vercel.json configuration file not found"
                })
            
            passed_tests = sum(1 for test in env_tests if test["success"])
            total_tests = len(env_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel environment configuration: {passed_tests}/{total_tests} tests passed",
                "test_results": env_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel environment configuration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_vercel_cli_commands(self) -> Dict[str, Any]:
        """Test various Vercel CLI commands."""
        result = {
            "test_name": "vercel_cli_commands",
            "platform": "vercel",
            "environment": "development",
            "start_time": datetime.now().isoformat()
        }
        
        try:
            command_tests = []
            
            # Test vercel --help
            try:
                help_result = subprocess.run(
                    ["vercel", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                command_tests.append({
                    "test": "vercel_help_command",
                    "success": help_result.returncode == 0,
                    "details": f"vercel --help: {'success' if help_result.returncode == 0 else 'failed'}"
                })
            except Exception as e:
                command_tests.append({
                    "test": "vercel_help_command",
                    "success": False,
                    "details": f"vercel --help error: {str(e)}"
                })
            
            # Test vercel whoami (if authenticated)
            try:
                whoami_result = subprocess.run(
                    ["vercel", "whoami"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                command_tests.append({
                    "test": "vercel_whoami_command",
                    "success": whoami_result.returncode == 0,
                    "details": f"vercel whoami: {'authenticated' if whoami_result.returncode == 0 else 'not authenticated'}"
                })
            except Exception as e:
                command_tests.append({
                    "test": "vercel_whoami_command",
                    "success": False,
                    "details": f"vercel whoami error: {str(e)}"
                })
            
            # Test vercel env ls (if in a project)
            try:
                env_ls_result = subprocess.run(
                    ["vercel", "env", "ls"],
                    cwd=self.ui_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                command_tests.append({
                    "test": "vercel_env_ls_command",
                    "success": env_ls_result.returncode == 0,
                    "details": f"vercel env ls: {'success' if env_ls_result.returncode == 0 else 'failed'}"
                })
            except Exception as e:
                command_tests.append({
                    "test": "vercel_env_ls_command",
                    "success": False,
                    "details": f"vercel env ls error: {str(e)}"
                })
            
            passed_tests = sum(1 for test in command_tests if test["success"])
            total_tests = len(command_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel CLI commands: {passed_tests}/{total_tests} tests passed",
                "test_results": command_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel CLI commands error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    def cleanup(self):
        """Clean up any running processes."""
        if self.vercel_process:
            try:
                self.vercel_process.terminate()
                self.vercel_process.wait(timeout=10)
            except:
                try:
                    self.vercel_process.kill()
                except:
                    pass
    
    async def run_all_tests(self):
        """Run all Vercel CLI component tests."""
        print("=" * 80)
        print("VERCEL CLI COMPONENT TESTING")
        print("=" * 80)
        print(f"UI Directory: {self.ui_dir}")
        print(f"Start Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        try:
            # Run all Vercel CLI tests
            await self.test_vercel_cli_installation()
            await self.test_vercel_environment_configuration()
            await self.test_vercel_build_process()
            await self.test_vercel_cli_commands()
            await self.test_vercel_local_development()
            
            # Generate report
            self._generate_report()
            
        finally:
            # Clean up
            self.cleanup()
    
    def _generate_report(self):
        """Generate Vercel CLI component test report."""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.get("status") == "passed"])
        partial_tests = len([r for r in self.results if r.get("status") == "partial"])
        error_tests = len([r for r in self.results if r.get("status") == "error"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": "vercel_cli_component_testing",
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
        report_path = "test-results/vercel_cli_component_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*80)
        print("VERCEL CLI COMPONENT TESTING SUMMARY")
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
    tester = VercelCLIComponentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
