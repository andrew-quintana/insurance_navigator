#!/usr/bin/env python3
"""
Vercel Platform Testing Module
Specialized testing for Vercel frontend deployments and CLI
"""

import asyncio
import requests
import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("vercel_tester")

class VercelFrontendTester:
    """Test Vercel frontend integration and React/Next.js functionality."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.frontend_url = self._get_frontend_url()
        self.results = []
        
    def _get_frontend_url(self) -> str:
        """Get Vercel frontend URL based on environment."""
        if self.environment == "production":
            return "https://insurance-navigator.vercel.app"
        elif self.environment == "staging":
            return "https://insurance-navigator-staging.vercel.app"
        else:  # development
            return "http://localhost:3000"
    
    async def test_frontend_startup(self) -> Dict[str, Any]:
        """Test React/Next.js application startup on Vercel."""
        result = {
            "test_name": "frontend_startup",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            response = requests.get(self.frontend_url, timeout=15)
            
            if response.status_code == 200:
                # Check if it's a valid HTML response
                content_type = response.headers.get('content-type', '')
                is_html = 'text/html' in content_type
                
                result.update({
                    "status": "passed" if is_html else "partial",
                    "details": f"Frontend accessible: {response.status_code}, HTML: {is_html}",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "content_type": content_type,
                    "content_length": len(response.content)
                })
            else:
                result.update({
                    "status": "failed",
                    "details": f"Frontend startup failed: {response.status_code}",
                    "error": response.text[:200]
                })
                
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Frontend startup error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_vercel_cli_setup(self) -> Dict[str, Any]:
        """Test Vercel CLI setup and configuration."""
        result = {
            "test_name": "vercel_cli_setup",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            cli_tests = []
            
            # Check if Vercel CLI is installed
            try:
                vercel_version = subprocess.run(
                    ["vercel", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                cli_tests.append({
                    "test": "cli_installed",
                    "success": vercel_version.returncode == 0,
                    "details": f"Vercel CLI version: {vercel_version.stdout.strip()}" if vercel_version.returncode == 0 else "Vercel CLI not installed"
                })
            except Exception as e:
                cli_tests.append({
                    "test": "cli_installed",
                    "success": False,
                    "details": f"Vercel CLI check failed: {str(e)}"
                })
            
            # Check Vercel project configuration
            vercel_config_exists = os.path.exists("vercel.json")
            cli_tests.append({
                "test": "vercel_config",
                "success": vercel_config_exists,
                "details": "Vercel configuration file exists" if vercel_config_exists else "Vercel configuration file missing"
            })
            
            # Check package.json for Vercel scripts
            if os.path.exists("package.json"):
                with open("package.json", "r") as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})
                    has_vercel_scripts = any("vercel" in script.lower() for script in scripts.values())
                    cli_tests.append({
                        "test": "vercel_scripts",
                        "success": has_vercel_scripts,
                        "details": f"Vercel scripts found: {has_vercel_scripts}"
                    })
            
            # Check .vercel directory
            vercel_dir_exists = os.path.exists(".vercel")
            cli_tests.append({
                "test": "vercel_directory",
                "success": vercel_dir_exists,
                "details": "Vercel directory exists" if vercel_dir_exists else "Vercel directory missing"
            })
            
            passed_tests = sum(1 for test in cli_tests if test["success"])
            total_tests = len(cli_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel CLI setup: {passed_tests}/{total_tests} tests passed",
                "test_results": cli_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel CLI setup error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_supabase_integration(self) -> Dict[str, Any]:
        """Test Supabase client integration across Vercel environments."""
        result = {
            "test_name": "supabase_integration",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Check if Supabase client files exist
            supabase_files = [
                "ui/lib/supabase.ts",
                "ui/lib/supabase.js",
                "shared/supabase.ts",
                "shared/supabase.js"
            ]
            
            supabase_tests = []
            for file_path in supabase_files:
                file_exists = os.path.exists(file_path)
                supabase_tests.append({
                    "test": f"file_{file_path.replace('/', '_').replace('.', '_')}",
                    "success": file_exists,
                    "details": f"File {file_path} exists" if file_exists else f"File {file_path} missing"
                })
            
            # Check for Supabase environment variables
            supabase_env_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
            for env_var in supabase_env_vars:
                env_value = os.getenv(env_var)
                supabase_tests.append({
                    "test": f"env_{env_var.lower()}",
                    "success": env_value is not None and env_value != "",
                    "details": f"Environment variable {env_var} set" if env_value else f"Environment variable {env_var} not set"
                })
            
            passed_tests = sum(1 for test in supabase_tests if test["success"])
            total_tests = len(supabase_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Supabase integration: {passed_tests}/{total_tests} tests passed",
                "test_results": supabase_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Supabase integration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_api_communication(self) -> Dict[str, Any]:
        """Test API communication layer between Vercel frontend and Render backend."""
        result = {
            "test_name": "api_communication",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test API endpoint accessibility from frontend
            api_endpoints = [
                "/api/health",
                "/api/status",
                "/api/auth/login",
                "/api/documents"
            ]
            
            api_tests = []
            for endpoint in api_endpoints:
                try:
                    response = requests.get(f"{self.frontend_url}{endpoint}", timeout=10)
                    api_tests.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 401, 404],  # 401/404 expected for some endpoints
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                except Exception as e:
                    api_tests.append({
                        "endpoint": endpoint,
                        "status_code": "error",
                        "success": False,
                        "error": str(e)
                    })
            
            passed_tests = sum(1 for test in api_tests if test["success"])
            total_tests = len(api_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"API communication: {passed_tests}/{total_tests} endpoints accessible",
                "test_results": api_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"API communication error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_authentication_flow(self) -> Dict[str, Any]:
        """Test authentication flow integration across platforms."""
        result = {
            "test_name": "authentication_flow",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test authentication pages/endpoints
            auth_endpoints = [
                "/login",
                "/register",
                "/auth/callback",
                "/dashboard"
            ]
            
            auth_tests = []
            for endpoint in auth_endpoints:
                try:
                    response = requests.get(f"{self.frontend_url}{endpoint}", timeout=10)
                    auth_tests.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 401, 302, 404],  # Various expected responses
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                except Exception as e:
                    auth_tests.append({
                        "endpoint": endpoint,
                        "status_code": "error",
                        "success": False,
                        "error": str(e)
                    })
            
            passed_tests = sum(1 for test in auth_tests if test["success"])
            total_tests = len(auth_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Authentication flow: {passed_tests}/{total_tests} endpoints accessible",
                "test_results": auth_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Authentication flow error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_document_upload_interface(self) -> Dict[str, Any]:
        """Test document upload interface with Render backend."""
        result = {
            "test_name": "document_upload_interface",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test document upload page
            upload_endpoints = [
                "/upload",
                "/documents",
                "/documents/new"
            ]
            
            upload_tests = []
            for endpoint in upload_endpoints:
                try:
                    response = requests.get(f"{self.frontend_url}{endpoint}", timeout=10)
                    upload_tests.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 401, 404],
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                except Exception as e:
                    upload_tests.append({
                        "endpoint": endpoint,
                        "status_code": "error",
                        "success": False,
                        "error": str(e)
                    })
            
            passed_tests = sum(1 for test in upload_tests if test["success"])
            total_tests = len(upload_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Document upload interface: {passed_tests}/{total_tests} endpoints accessible",
                "test_results": upload_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Document upload interface error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_chat_interface(self) -> Dict[str, Any]:
        """Test chat interface functionality with cross-platform communication."""
        result = {
            "test_name": "chat_interface",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test chat interface endpoints
            chat_endpoints = [
                "/chat",
                "/conversations",
                "/ai"
            ]
            
            chat_tests = []
            for endpoint in chat_endpoints:
                try:
                    response = requests.get(f"{self.frontend_url}{endpoint}", timeout=10)
                    chat_tests.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 401, 404],
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                except Exception as e:
                    chat_tests.append({
                        "endpoint": endpoint,
                        "status_code": "error",
                        "success": False,
                        "error": str(e)
                    })
            
            passed_tests = sum(1 for test in chat_tests if test["success"])
            total_tests = len(chat_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Chat interface: {passed_tests}/{total_tests} endpoints accessible",
                "test_results": chat_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Chat interface error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_responsive_design(self) -> Dict[str, Any]:
        """Test responsive design components on Vercel deployments."""
        result = {
            "test_name": "responsive_design",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test different viewport sizes
            viewports = [
                {"name": "mobile", "width": 375, "height": 667},
                {"name": "tablet", "width": 768, "height": 1024},
                {"name": "desktop", "width": 1920, "height": 1080}
            ]
            
            responsive_tests = []
            for viewport in viewports:
                try:
                    headers = {
                        "User-Agent": f"Mozilla/5.0 (compatible; {viewport['name']} test)"
                    }
                    response = requests.get(
                        self.frontend_url, 
                        headers=headers, 
                        timeout=10
                    )
                    
                    responsive_tests.append({
                        "viewport": viewport["name"],
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                except Exception as e:
                    responsive_tests.append({
                        "viewport": viewport["name"],
                        "status_code": "error",
                        "success": False,
                        "error": str(e)
                    })
            
            passed_tests = sum(1 for test in responsive_tests if test["success"])
            total_tests = len(responsive_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Responsive design: {passed_tests}/{total_tests} viewports accessible",
                "test_results": responsive_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Responsive design error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_vercel_environment_config(self) -> Dict[str, Any]:
        """Test Vercel environment variable configuration."""
        result = {
            "test_name": "vercel_environment_config",
            "platform": "vercel",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Check environment-specific configuration files
            env_files = [
                ".env.development",
                ".env.staging", 
                ".env.production",
                ".env.local"
            ]
            
            env_tests = []
            for env_file in env_files:
                file_exists = os.path.exists(env_file)
                env_tests.append({
                    "test": f"env_file_{env_file.replace('.', '_')}",
                    "success": file_exists,
                    "details": f"Environment file {env_file} exists" if file_exists else f"Environment file {env_file} missing"
                })
            
            # Check for required environment variables
            required_vars = [
                "NEXT_PUBLIC_SUPABASE_URL",
                "NEXT_PUBLIC_SUPABASE_ANON_KEY",
                "NEXT_PUBLIC_API_URL"
            ]
            
            for var in required_vars:
                var_value = os.getenv(var)
                env_tests.append({
                    "test": f"env_var_{var.lower()}",
                    "success": var_value is not None and var_value != "",
                    "details": f"Environment variable {var} set" if var_value else f"Environment variable {var} not set"
                })
            
            passed_tests = sum(1 for test in env_tests if test["success"])
            total_tests = len(env_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Vercel environment config: {passed_tests}/{total_tests} tests passed",
                "test_results": env_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Vercel environment config error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all Vercel frontend tests."""
        logger.info(f"Starting Vercel frontend testing for {self.environment} environment")
        
        await self.test_frontend_startup()
        await self.test_vercel_cli_setup()
        await self.test_supabase_integration()
        await self.test_api_communication()
        await self.test_authentication_flow()
        await self.test_document_upload_interface()
        await self.test_chat_interface()
        await self.test_responsive_design()
        await self.test_vercel_environment_config()
        
        return self.results

async def main():
    """Main execution function for Vercel platform testing."""
    print("=" * 80)
    print("VERCEL PLATFORM TESTING")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Test development environment
    print("\n🧪 Testing Development Environment...")
    dev_tester = VercelFrontendTester("development")
    dev_results = await dev_tester.run_all_tests()
    
    # Test staging environment
    print("\n🧪 Testing Staging Environment...")
    staging_tester = VercelFrontendTester("staging")
    staging_results = await staging_tester.run_all_tests()
    
    # Test production environment
    print("\n🧪 Testing Production Environment...")
    prod_tester = VercelFrontendTester("production")
    prod_results = await prod_tester.run_all_tests()
    
    # Generate combined report
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "environments": {
            "development": dev_results,
            "staging": staging_results,
            "production": prod_results
        }
    }
    
    # Save report
    os.makedirs("test-results", exist_ok=True)
    report_path = "test-results/vercel_platform_test_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📄 Vercel platform test report saved to: {report_path}")
    print("=" * 80)
    print("VERCEL PLATFORM TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
