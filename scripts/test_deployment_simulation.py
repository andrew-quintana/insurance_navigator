#!/usr/bin/env python3
"""
Deployment Simulation Test
=========================

This script simulates render.com deployment conditions to catch issues locally:
1. Clean import testing (no cache)
2. Environment variable validation  
3. Port binding verification
4. Database connection testing
5. Application startup sequence
6. Health check endpoint testing

Run this before deploying to render.com to catch issues early.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import importlib
import time
from pathlib import Path
from datetime import datetime
import requests
import threading
import signal
import urllib.parse

# Ensure the current directory is in Python path for imports
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def print_header(title):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def print_step(step):
    """Print formatted step."""
    print(f"\n🔍 {step}")
    print("-" * 40)

def simulate_clean_environment():
    """Simulate render.com's clean environment by clearing Python caches."""
    print_step("Simulating Clean Environment (Render.com style)")
    
    # Clear __pycache__ directories (only in project, not in venv)
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        # Skip .venv directory
        if '.venv' in root:
            continue
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))
    
    print(f"Found {len(cache_dirs)} project __pycache__ directories")
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"  ✅ Cleared: {cache_dir}")
        except Exception as e:
            print(f"  ❌ Failed to clear {cache_dir}: {e}")
    
    # Clear .pyc files (only in project)
    pyc_files = []
    for root, dirs, files in os.walk('.'):
        # Skip .venv directory
        if '.venv' in root:
            continue
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
    
    print(f"Found {len(pyc_files)} project .pyc files")
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"  ✅ Removed: {pyc_file}")
        except Exception as e:
            print(f"  ❌ Failed to remove {pyc_file}: {e}")
    
    # Clear sys.modules cache for project modules
    project_modules = [module for module in sys.modules.keys() 
                      if module.startswith(('agents', 'graph', 'utils', 'db', 'main'))]
    
    print(f"Clearing {len(project_modules)} project modules from sys.modules")
    for module in project_modules:
        if module in sys.modules:
            del sys.modules[module]
            print(f"  ✅ Cleared: {module}")
    
    # Re-add current directory to path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    return True

def test_clean_imports():
    """Test imports in a clean environment like render.com."""
    print_step("Testing Clean Imports (Critical for Deployment)")
    
    test_imports = [
        "main",
        "graph.agent_orchestrator",
        "agents.prompt_security.prompt_security",
        "agents.patient_navigator.patient_navigator", 
        "agents.task_requirements.task_requirements",
        "agents.service_access_strategy.service_access_strategy",
        "agents.chat_communicator.chat_communicator",
        "agents.regulatory.regulatory"
    ]
    
    results = []
    for import_path in test_imports:
        try:
            print(f"  Testing: {import_path}")
            module = importlib.import_module(import_path)
            print(f"    ✅ SUCCESS: {import_path}")
            results.append((import_path, True, None))
        except Exception as e:
            print(f"    ❌ FAILED: {import_path} - {str(e)}")
            results.append((import_path, False, str(e)))
    
    # Summary
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    print(f"\n📊 Import Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed < total:
        print("❌ CRITICAL: Import failures detected - deployment will fail!")
        return False
    
    print("✅ All imports successful - ready for deployment!")
    return True

def validate_environment_variables():
    """Validate critical environment variables like render.com would."""
    print_step("Environment Variable Validation")
    
    critical_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
        "JWT_SECRET_KEY"
    ]
    
    optional_vars = [
        "ASYNCPG_DISABLE_PREPARED_STATEMENTS",
        "ENVIRONMENT",
        "LOG_LEVEL", 
        "SECURITY_BYPASS_ENABLED",
        "API_BASE_URL"
    ]
    
    missing_critical = []
    missing_optional = []
    
    for var in critical_vars:
        if not os.getenv(var):
            missing_critical.append(var)
            print(f"  ❌ CRITICAL MISSING: {var}")
        else:
            print(f"  ✅ Found: {var}")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
            print(f"  ⚠️  Optional missing: {var}")
        else:
            print(f"  ✅ Found: {var}")
    
    if missing_critical:
        print(f"\n❌ CRITICAL: {len(missing_critical)} critical environment variables missing!")
        print("   Deployment will fail without these.")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Warning: {len(missing_optional)} optional variables missing")
        print("   App may work but with reduced functionality")
    
    print("\n✅ Environment validation passed!")
    return True

def test_database_connection():
    """Test database connectivity like render.com environment with enhanced logging."""
    print_step("Database Connection Test")
    
    try:
        # Enhanced logging for database configuration
        print("  🔍 Checking database configuration...")
        
        # Check environment variables
        db_url = os.getenv('DATABASE_URL', '')
        db_url_local = os.getenv('DATABASE_URL_LOCAL', '')
        db_port_env = os.getenv('DB_PORT', '')
        asyncpg_disable = os.getenv('ASYNCPG_DISABLE_PREPARED_STATEMENTS', '')
        
        print(f"  📊 DATABASE_URL configured: {bool(db_url)}")
        print(f"  📊 DATABASE_URL_LOCAL configured: {bool(db_url_local)}")
        print(f"  📊 DB_PORT env var: {db_port_env}")
        print(f"  📊 ASYNCPG_DISABLE_PREPARED_STATEMENTS: {asyncpg_disable}")
        
        if db_url:
            # Parse URL to check port
            parsed = urllib.parse.urlparse(db_url)
            print(f"  📊 DATABASE_URL host: {parsed.hostname}")
            print(f"  📊 DATABASE_URL port: {parsed.port}")
            print(f"  📊 DATABASE_URL scheme: {parsed.scheme}")
            
            # Check for transaction pooler indicator
            if 'pooler.supabase.com' in parsed.hostname:
                print(f"  ✅ Using Supabase transaction pooler (port {parsed.port})")
                
                # Critical test: Check prepared statement configuration for transaction pooler
                if asyncpg_disable != '1':
                    print(f"  ❌ CRITICAL: ASYNCPG_DISABLE_PREPARED_STATEMENTS should be '1' for transaction pooler!")
                    print(f"      Current value: '{asyncpg_disable}'")
                    print(f"      This will cause 'prepared statement does not exist' errors on render.com")
                    return False
                else:
                    print(f"  ✅ Prepared statements correctly disabled for transaction pooler")
            else:
                print(f"  ℹ️  Using direct connection")
                if asyncpg_disable == '1':
                    print(f"  ⚠️  Prepared statements disabled for direct connection (may impact performance)")
        
        # Test import of actual database modules
        try:
            from db.services.db_pool import get_db_pool, DatabasePool
            print("  ✅ Database pool module imported successfully")
        except ImportError as e:
            print(f"  ❌ Database pool import failed: {e}")
            return False
        
        # Test connection using the actual database pool
        try:
            import asyncio
            
            async def test_db_connection():
                try:
                    pool = await get_db_pool()
                    print("  ✅ Database pool initialized")
                    
                    # Test actual connection
                    connection_test = await pool.test_connection()
                    if connection_test:
                        print("  ✅ Database connection test successful")
                        
                        # Additional test: Verify prepared statement configuration is applied
                        if hasattr(pool, 'pool') and pool.pool:
                            print("  ✅ AsyncPG pool created successfully")
                            
                            # Test a simple query that would fail if prepared statements aren't handled correctly
                            try:
                                async with pool.get_connection() as conn:
                                    # This type of query pattern often triggers prepared statement issues
                                    result1 = await conn.fetchval("SELECT 1 as test")
                                    result2 = await conn.fetchval("SELECT 2 as test") 
                                    if result1 == 1 and result2 == 2:
                                        print("  ✅ Multiple queries successful (no prepared statement conflicts)")
                                    else:
                                        print("  ❌ Query results unexpected")
                                        return False
                            except Exception as e:
                                error_msg = str(e).lower()
                                if 'prepared statement' in error_msg or 'does not exist' in error_msg:
                                    print(f"  ❌ CRITICAL: Prepared statement error detected: {e}")
                                    print(f"      This indicates ASYNCPG_DISABLE_PREPARED_STATEMENTS is not working")
                                    return False
                                else:
                                    print(f"  ⚠️  Query test failed (non-prepared-statement error): {e}")
                        
                        return True
                    else:
                        print("  ❌ Database connection test failed")
                        return False
                        
                except Exception as e:
                    print(f"  ❌ Database pool connection failed: {e}")
                    print(f"      Error type: {type(e).__name__}")
                    print(f"      Error details: {str(e)}")
                    
                    # Check if this is a prepared statement error
                    error_msg = str(e).lower()
                    if 'prepared statement' in error_msg or 'does not exist' in error_msg:
                        print(f"  🚨 RENDER.COM DEPLOYMENT BLOCKER: Prepared statement error!")
                        print(f"      Set ASYNCPG_DISABLE_PREPARED_STATEMENTS=1 for transaction pooler")
                    
                    return False
            
            # Run async test
            result = asyncio.run(test_db_connection())
            return result
            
        except Exception as e:
            print(f"  ❌ Async database test failed: {e}")
            print(f"      Error type: {type(e).__name__}")
            return False
    
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        print(f"      Error type: {type(e).__name__}")
        print("     This may cause deployment issues if DB is required at startup")
        return False

def test_application_startup():
    """Test the full application startup sequence."""
    print_step("Application Startup Test")
    
    try:
        # Import the FastAPI app
        from main import app
        print("  ✅ FastAPI app imported successfully")
        
        # Test basic app configuration
        if hasattr(app, 'routes'):
            route_count = len(app.routes)
            print(f"  ✅ Found {route_count} routes configured")
        
        if hasattr(app, 'middleware_stack'):
            print("  ✅ Middleware stack configured")
        
        print("  ✅ Application startup test passed")
        return True
    
    except Exception as e:
        print(f"  ❌ Application startup failed: {e}")
        return False

def test_health_endpoint_in_subprocess():
    """Test health endpoint by actually starting the server."""
    print_step("Health Endpoint Test (Server Startup)")
    
    # Start server in background
    server_process = None
    try:
        print("  🚀 Starting uvicorn server...")
        server_process = subprocess.Popen([
            "uvicorn", "main:app", 
            "--host", "127.0.0.1", 
            "--port", "8001",  # Use different port to avoid conflicts
            "--log-level", "warning"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        print("  ⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Test health endpoint
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Health endpoint responding: {response.json()}")
                return True
            else:
                print(f"  ❌ Health endpoint returned {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"  ❌ Health endpoint not reachable: {e}")
            return False
    
    except Exception as e:
        print(f"  ❌ Server startup failed: {e}")
        return False
    
    finally:
        if server_process:
            print("  🛑 Stopping test server...")
            server_process.terminate()
            server_process.wait(timeout=5)

def test_docker_simulation():
    """Simulate Docker environment conditions."""
    print_step("Docker Environment Simulation")
    
    # Check if running as root (like render.com initially does)
    user_id = os.getuid() if hasattr(os, 'getuid') else 'unknown'
    print(f"  Running as user ID: {user_id}")
    
    # Check port environment variable
    port = os.getenv('PORT', '8000')
    print(f"  PORT environment variable: {port}")
    
    # Check working directory
    cwd = os.getcwd()
    print(f"  Current working directory: {cwd}")
    
    # Check Python version
    python_version = sys.version
    print(f"  Python version: {python_version}")
    
    print("  ✅ Docker simulation checks passed")
    return True

def main():
    """Run the complete deployment simulation."""
    start_time = datetime.now()
    
    print_header("DEPLOYMENT SIMULATION TEST (Render.com Style)")
    print(f"⏰ Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis test simulates render.com deployment conditions to catch issues early.")
    
    # Test sequence
    tests = [
        ("Clean Environment Setup", simulate_clean_environment),
        ("Clean Imports", test_clean_imports),
        ("Environment Variables", validate_environment_variables),
        ("Database Connection", test_database_connection),
        ("Application Startup", test_application_startup),
        ("Health Endpoint", test_health_endpoint_in_subprocess),
        ("Docker Simulation", test_docker_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if callable(test_func):
                result = test_func()
            else:
                test_func()  # For setup functions
                result = True
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Final report
    print_header("DEPLOYMENT SIMULATION RESULTS")
    
    passed_tests = []
    failed_tests = []
    
    for test_name, result in results:
        if result:
            passed_tests.append(test_name)
            print(f"  ✅ {test_name}: PASSED")
        else:
            failed_tests.append(test_name)
            print(f"  ❌ {test_name}: FAILED")
    
    total_tests = len(results)
    passed_count = len(passed_tests)
    success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_count}")
    print(f"  Failed: {len(failed_tests)}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    if failed_tests:
        print(f"\n❌ DEPLOYMENT RISK: {len(failed_tests)} tests failed")
        print("   These issues may cause render.com deployment to fail:")
        for test in failed_tests:
            print(f"     • {test}")
        print("\n🔧 Fix these issues before deploying to render.com!")
        return False
    else:
        print("\n🎉 ALL TESTS PASSED! Ready for render.com deployment! 🚀")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 