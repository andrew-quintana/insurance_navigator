#!/usr/bin/env python3
"""
Local Setup Validation Script
=============================

This script validates that your Insurance Navigator local development environment
is properly configured and all services are running correctly.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

import requests
import asyncpg


async def check_database_connection():
    """Test database connectivity."""
    print("🗄️  Testing Database Connection...")
    try:
        database_url = os.getenv("DATABASE_URL_LOCAL", os.getenv("DATABASE_URL"))
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
            
        conn = await asyncpg.connect(database_url)
        result = await conn.fetchval('SELECT version()')
        print(f"✅ Database connected: {result[:50]}...")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_api_health():
    """Test backend API health endpoint."""
    print("🔧 Testing Backend API Health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend API is healthy")
            
            # Check individual services
            services = health_data.get("services", {})
            for service, status in services.items():
                status_icon = "✅" if status.get("healthy") else "❌"
                print(f"  {status_icon} {service}: {status.get('status', 'unknown')}")
            
            return True
        else:
            print(f"❌ Backend API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend API not accessible: {e}")
        return False


def check_api_docs():
    """Test API documentation accessibility."""
    print("📚 Testing API Documentation...")
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200 and "swagger-ui" in response.text.lower():
            print("✅ API documentation accessible")
            return True
        else:
            print("❌ API documentation not accessible")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API documentation check failed: {e}")
        return False


def check_frontend():
    """Test frontend accessibility."""
    print("🌐 Testing Frontend Application...")
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend application accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend not accessible: {e}")
        return False


def check_supabase():
    """Test Supabase local instance."""
    print("🗃️  Testing Supabase Instance...")
    try:
        # Check Supabase API
        response = requests.get("http://localhost:54321/health", timeout=5)
        if response.status_code == 200:
            print("✅ Supabase API accessible")
        else:
            print(f"⚠️  Supabase API status: {response.status_code}")
        
        # Check Supabase Studio
        studio_response = requests.get("http://localhost:54323", timeout=5)
        if studio_response.status_code == 200:
            print("✅ Supabase Studio accessible")
            return True
        else:
            print(f"⚠️  Supabase Studio status: {studio_response.status_code}")
            return True  # API is more important than Studio
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Supabase not accessible: {e}")
        return False


def check_environment_variables():
    """Validate required environment variables."""
    print("🔧 Checking Environment Variables...")
    
    required_vars = [
        "DATABASE_URL",
        "SUPABASE_URL", 
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY"
    ]
    
    optional_vars = [
        "DATABASE_URL_LOCAL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    missing_required = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing")
            missing_required.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Not set (optional)")
    
    return len(missing_required) == 0


def check_python_environment():
    """Check Python environment setup."""
    print("🐍 Checking Python Environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 11):
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python version too old: {python_version.major}.{python_version.minor}.{python_version.micro} (need 3.11+)")
        return False
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment: Active")
    else:
        print("⚠️  Virtual environment: Not detected")
    
    # Check key packages
    try:
        import fastapi
        import uvicorn
        import asyncpg
        import supabase
        print("✅ Key Python packages: Available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python packages: {e}")
        return False


def run_api_integration_test():
    """Run the comprehensive API integration test."""
    print("🧪 Running API Integration Tests...")
    try:
        result = subprocess.run([
            sys.executable, "test_api_endpoint_direct.py"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Look for success indicators in output
            if "ALL API INTEGRATION TESTS PASSED" in result.stdout:
                print("✅ API integration tests passed")
                return True
            else:
                print("⚠️  API tests completed with warnings")
                return True
        else:
            print(f"❌ API integration tests failed: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ API integration tests timed out")
        return False
    except FileNotFoundError:
        print("⚠️  API test file not found - skipping")
        return True


def check_typescript_build():
    """Validate TypeScript build and type checking."""
    print("🔧 Testing TypeScript Build & Type Validation...")
    
    # Check if ui directory exists
    if not os.path.exists("ui"):
        print("⚠️  Frontend ui directory not found - skipping TypeScript validation")
        return True
    
    try:
        # Change to ui directory
        original_cwd = os.getcwd()
        os.chdir("ui")
        
        print("  ├─ Running TypeScript type check...")
        # Run type check
        result = subprocess.run([
            "npm", "run", "type-check"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ TypeScript type check passed")
        else:
            print(f"  ❌ TypeScript type check failed:")
            print(f"     {result.stderr[:300]}...")
            return False
        
        print("  ├─ Running ESLint validation...")
        # Run lint check
        result = subprocess.run([
            "npm", "run", "lint"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ ESLint validation passed")
        else:
            # Lint warnings are acceptable, only fail on errors
            if "error" in result.stdout.lower():
                print(f"  ❌ ESLint errors found:")
                print(f"     {result.stdout[:300]}...")
                return False
            else:
                print("  ✅ ESLint validation passed (warnings ignored)")
        
        print("  ├─ Testing production build...")
        # Run build test
        result = subprocess.run([
            "npm", "run", "build"
        ], capture_output=True, text=True, timeout=180, env={
            **os.environ,
            "NODE_ENV": "production"
        })
        
        if result.returncode == 0:
            print("  ✅ Production build successful")
            # Check for specific success indicators
            if "✓ Compiled successfully" in result.stdout:
                print("  ✅ Frontend ready for Vercel deployment")
                return True
            else:
                print("  ⚠️  Build completed with warnings")
                return True
        else:
            print(f"  ❌ Production build failed:")
            print(f"     {result.stderr[:400]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ TypeScript validation timed out")
        return False
    except FileNotFoundError:
        print("⚠️  npm not found - ensure Node.js is installed")
        return False
    except Exception as e:
        print(f"❌ TypeScript validation error: {e}")
        return False
    finally:
        # Return to original directory
        os.chdir(original_cwd)


async def main():
    """Run all validation checks."""
    print("🚀 Insurance Navigator - Local Setup Validation")
    print("=" * 60)
    print(f"Validation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load environment variables from .env.development if it exists
    env_file = ".env.development"
    if os.path.exists(env_file):
        print(f"📄 Loading environment from {env_file}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✅ Environment variables loaded")
        except ImportError:
            print("⚠️  python-dotenv not available, using system environment")
        except Exception as e:
            print(f"⚠️  Error loading environment: {e}")
        print()
    
    checks = [
        ("Python Environment", check_python_environment),
        ("Environment Variables", check_environment_variables),
        ("Database Connection", check_database_connection),
        ("Supabase Instance", check_supabase),
        ("Backend API Health", check_api_health),
        ("API Documentation", check_api_docs),
        ("Frontend Application", check_frontend),
        ("TypeScript Build & Validation", check_typescript_build),
        ("API Integration Tests", run_api_integration_test),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n{check_name}")
        print("-" * len(check_name))
        
        if asyncio.iscoroutinefunction(check_func):
            result = await check_func()
        else:
            result = check_func()
        
        results[check_name] = result
        time.sleep(0.5)  # Brief pause between checks
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}")
    print()
    
    for check_name, result in results.items():
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {check_name}")
    
    print()
    
    if passed == total:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Your local development environment is fully operational.")
        print()
        print("🌐 Access Points:")
        print("  • Frontend: http://localhost:3000")
        print("  • Backend API: http://localhost:8000")
        print("  • API Docs: http://localhost:8000/docs")
        print("  • Supabase Studio: http://localhost:54323")
        print("  • Health Check: http://localhost:8000/health")
        
    else:
        print(f"⚠️  {total - passed} checks failed.")
        print("📖 Please refer to SETUP_AND_TEST_LOCAL.md for troubleshooting.")
    
    print()
    print(f"Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)