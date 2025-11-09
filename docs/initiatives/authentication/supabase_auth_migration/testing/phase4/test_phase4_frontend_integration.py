#!/usr/bin/env python3
"""
Phase 4 Frontend Integration Test Script
Tests the frontend Supabase authentication integration
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_environment_config():
    """Load environment configuration based on the current environment"""
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'development':
        env_file = project_root / '.env.development'
    elif env == 'staging':
        env_file = project_root / '.env.staging'
    elif env == 'production':
        env_file = project_root / '.env.production'
    else:
        raise ValueError(f"Unknown environment: {env}")
    
    if not env_file.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file}")
    
    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value
    
    return config

def test_supabase_connection():
    """Test Supabase connection and authentication"""
    print("🔍 Testing Supabase connection...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # Test Supabase health endpoint
        health_url = f"{supabase_url}/rest/v1/"
        headers = {
            'apikey': supabase_anon_key,
            'Authorization': f'Bearer {supabase_anon_key}'
        }
        
        response = requests.get(health_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Supabase connection successful")
            return True, "Supabase connection successful"
        else:
            print(f"❌ Supabase connection failed: {response.status_code}")
            return False, f"Supabase connection failed: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False, f"Supabase connection error: {e}"

def test_frontend_build():
    """Test if the frontend builds successfully"""
    print("🔍 Testing frontend build...")
    
    ui_dir = project_root / 'ui'
    if not ui_dir.exists():
        return False, "UI directory not found"
    
    try:
        import subprocess
        import os
        
        # Change to UI directory
        original_cwd = os.getcwd()
        os.chdir(ui_dir)
        
        # Run build command
        result = subprocess.run(
            ['npm', 'run', 'build'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        # Restore original directory
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            print("✅ Frontend build successful")
            return True, "Frontend build successful"
        else:
            print(f"❌ Frontend build failed: {result.stderr}")
            return False, f"Frontend build failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        print("❌ Frontend build timed out")
        return False, "Frontend build timed out"
    except Exception as e:
        print(f"❌ Frontend build error: {e}")
        return False, f"Frontend build error: {e}"

def test_environment_variables():
    """Test that all required environment variables are present"""
    print("🔍 Testing environment variables...")
    
    config = load_environment_config()
    
    required_vars = [
        'NEXT_PUBLIC_SUPABASE_URL',
        'NEXT_PUBLIC_SUPABASE_ANON_KEY',
        'NEXT_PUBLIC_API_BASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not config.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False, f"Missing environment variables: {missing_vars}"
    
    print("✅ All required environment variables present")
    return True, "All required environment variables present"

def test_auth_components():
    """Test that authentication components are properly configured"""
    print("🔍 Testing authentication components...")
    
    ui_dir = project_root / 'ui'
    
    # Check if required files exist
    required_files = [
        'components/auth/SessionManager.tsx',
        'components/auth/LoginForm.tsx',
        'components/auth/RegisterForm.tsx',
        'components/auth/ProtectedRoute.tsx',
        'lib/supabase-client.ts'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = ui_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing authentication files: {missing_files}")
        return False, f"Missing authentication files: {missing_files}"
    
    # Check if files contain Supabase imports
    supabase_files = [
        'components/auth/SessionManager.tsx',
        'components/auth/LoginForm.tsx',
        'components/auth/RegisterForm.tsx',
        'lib/supabase-client.ts'
    ]
    
    for file_path in supabase_files:
        full_path = ui_dir / file_path
        try:
            with open(full_path, 'r') as f:
                content = f.read()
                if 'supabase' not in content.lower():
                    print(f"❌ {file_path} does not contain Supabase references")
                    return False, f"{file_path} does not contain Supabase references"
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return False, f"Error reading {file_path}: {e}"
    
    print("✅ Authentication components properly configured")
    return True, "Authentication components properly configured"

def test_page_integration():
    """Test that pages are properly integrated with Supabase auth"""
    print("🔍 Testing page integration...")
    
    ui_dir = project_root / 'ui'
    
    # Check main pages for Supabase auth integration
    pages_to_check = [
        ('app/page.tsx', ['useAuth']),
        ('app/chat/page.tsx', ['useAuth']),
        ('app/welcome/page.tsx', ['useAuth']),
        ('app/login/page.tsx', ['LoginForm']),  # Uses LoginForm component
        ('app/register/page.tsx', ['RegisterForm'])  # Uses RegisterForm component
    ]
    
    for page_path, required_imports in pages_to_check:
        full_path = ui_dir / page_path
        if not full_path.exists():
            print(f"❌ Page not found: {page_path}")
            return False, f"Page not found: {page_path}"
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
                
                # Check for required imports
                found_imports = []
                for required_import in required_imports:
                    if required_import in content:
                        found_imports.append(required_import)
                
                if not found_imports:
                    print(f"❌ {page_path} not properly integrated with Supabase auth (missing: {required_imports})")
                    return False, f"{page_path} not properly integrated with Supabase auth (missing: {required_imports})"
                    
        except Exception as e:
            print(f"❌ Error reading {page_path}: {e}")
            return False, f"Error reading {page_path}: {e}"
    
    print("✅ Page integration successful")
    return True, "Page integration successful"

def run_comprehensive_test():
    """Run all Phase 4 frontend integration tests"""
    print("🚀 Starting Phase 4 Frontend Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Environment Variables
    success, message = test_environment_variables()
    test_results.append(("Environment Variables", success, message))
    
    # Test 2: Supabase Connection
    success, message = test_supabase_connection()
    test_results.append(("Supabase Connection", success, message))
    
    # Test 3: Authentication Components
    success, message = test_auth_components()
    test_results.append(("Authentication Components", success, message))
    
    # Test 4: Page Integration
    success, message = test_page_integration()
    test_results.append(("Page Integration", success, message))
    
    # Test 5: Frontend Build
    success, message = test_frontend_build()
    test_results.append(("Frontend Build", success, message))
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 PHASE 4 FRONTEND INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success, message in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Summary: {passed} passed, {failed} failed")
    
    # Save results to file
    results = {
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "tests": [
            {
                "name": test_name,
                "passed": success,
                "message": message
            }
            for test_name, success, message in test_results
        ],
        "summary": {
            "total": len(test_results),
            "passed": passed,
            "failed": failed
        }
    }
    
    results_file = project_root / f"phase4_frontend_integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Results saved to: {results_file}")
    
    if failed == 0:
        print("\n🎉 All Phase 4 Frontend Integration Tests PASSED!")
        return True
    else:
        print(f"\n⚠️  {failed} Phase 4 Frontend Integration Tests FAILED!")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
