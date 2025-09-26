#!/usr/bin/env python3
"""
Phase 4 User Acceptance Test Script
Tests the complete user workflows with Supabase authentication
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

def test_user_registration_workflow():
    """Test the complete user registration workflow"""
    print("🔍 Testing user registration workflow...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # Test user registration via Supabase Auth API
        test_email = f"test_user_{int(time.time())}@example.com"
        test_password = "testpassword123"
        
        auth_url = f"{supabase_url}/auth/v1/signup"
        headers = {
            'apikey': supabase_anon_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'email': test_email,
            'password': test_password,
            'data': {
                'full_name': 'Test User'
            }
        }
        
        response = requests.post(auth_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            if 'user' in data and 'access_token' in data:
                print("✅ User registration successful")
                return True, "User registration successful"
            else:
                print(f"❌ User registration incomplete: {response.text}")
                return False, f"User registration incomplete: missing user or token"
        else:
            print(f"❌ User registration failed: {response.status_code} - {response.text}")
            return False, f"User registration failed: {response.status_code}"
            
    except Exception as e:
        print(f"❌ User registration error: {e}")
        return False, f"User registration error: {e}"

def test_user_login_workflow():
    """Test the complete user login workflow"""
    print("🔍 Testing user login workflow...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # First, create a test user for login testing
        test_email = f"login_test_{int(time.time())}@example.com"
        test_password = "testpassword123"
        
        # Register the test user
        signup_url = f"{supabase_url}/auth/v1/signup"
        headers = {
            'apikey': supabase_anon_key,
            'Content-Type': 'application/json'
        }
        
        signup_payload = {
            'email': test_email,
            'password': test_password,
            'data': {
                'full_name': 'Login Test User'
            }
        }
        
        signup_response = requests.post(signup_url, headers=headers, json=signup_payload, timeout=10)
        
        if signup_response.status_code not in [200, 201]:
            print(f"❌ Failed to create test user: {signup_response.status_code} - {signup_response.text}")
            return False, f"Failed to create test user: {signup_response.status_code}"
        
        # Now test login with the created user
        login_url = f"{supabase_url}/auth/v1/token?grant_type=password"
        login_payload = {
            'email': test_email,
            'password': test_password
        }
        
        response = requests.post(login_url, headers=headers, json=login_payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data and 'user' in data:
                print("✅ User login successful")
                return True, "User login successful"
            else:
                print("❌ User login failed: No access token or user in response")
                return False, "User login failed: No access token or user in response"
        else:
            print(f"❌ User login failed: {response.status_code} - {response.text}")
            return False, f"User login failed: {response.status_code}"
            
    except Exception as e:
        print(f"❌ User login error: {e}")
        return False, f"User login error: {e}"

def test_session_management():
    """Test session management and token refresh"""
    print("🔍 Testing session management...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # First, create a test user and get a valid session
        test_email = f"session_test_{int(time.time())}@example.com"
        test_password = "testpassword123"
        
        # Register the test user
        signup_url = f"{supabase_url}/auth/v1/signup"
        headers = {
            'apikey': supabase_anon_key,
            'Content-Type': 'application/json'
        }
        
        signup_payload = {
            'email': test_email,
            'password': test_password,
            'data': {
                'full_name': 'Session Test User'
            }
        }
        
        signup_response = requests.post(signup_url, headers=headers, json=signup_payload, timeout=10)
        
        if signup_response.status_code not in [200, 201]:
            print(f"❌ Failed to create test user: {signup_response.status_code} - {signup_response.text}")
            return False, f"Failed to create test user: {signup_response.status_code}"
        
        # Login to get a valid session
        login_url = f"{supabase_url}/auth/v1/token?grant_type=password"
        login_payload = {
            'email': test_email,
            'password': test_password
        }
        
        login_response = requests.post(login_url, headers=headers, json=login_payload, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ Failed to login test user: {login_response.status_code} - {login_response.text}")
            return False, f"Failed to login test user: {login_response.status_code}"
        
        login_data = login_response.json()
        access_token = login_data.get('access_token')
        
        if not access_token:
            print("❌ No access token received from login")
            return False, "No access token received from login"
        
        # Now test session validation with the valid token
        session_url = f"{supabase_url}/auth/v1/user"
        session_headers = {
            'apikey': supabase_anon_key,
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(session_url, headers=session_headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            if 'id' in user_data and 'email' in user_data:
                print("✅ Session management working")
                return True, "Session management working"
            else:
                print("❌ Session management failed: Invalid user data")
                return False, "Session management failed: Invalid user data"
        else:
            print(f"❌ Session management failed: {response.status_code} - {response.text}")
            return False, f"Session management failed: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Session management error: {e}")
        return False, f"Session management error: {e}"

def test_frontend_authentication_flow():
    """Test the frontend authentication flow components"""
    print("🔍 Testing frontend authentication flow...")
    
    ui_dir = project_root / 'ui'
    
    # Check that all authentication components are properly configured
    auth_components = [
        'components/auth/SessionManager.tsx',
        'components/auth/LoginForm.tsx',
        'components/auth/RegisterForm.tsx',
        'components/auth/ProtectedRoute.tsx'
    ]
    
    for component in auth_components:
        component_path = ui_dir / component
        if not component_path.exists():
            print(f"❌ Missing authentication component: {component}")
            return False, f"Missing authentication component: {component}"
        
        try:
            with open(component_path, 'r') as f:
                content = f.read()
                
                # Check for proper Supabase integration
                if 'supabase' not in content.lower():
                    print(f"❌ {component} not properly integrated with Supabase")
                    return False, f"{component} not properly integrated with Supabase"
                    
        except Exception as e:
            print(f"❌ Error reading {component}: {e}")
            return False, f"Error reading {component}: {e}"
    
    print("✅ Frontend authentication flow working")
    return True, "Frontend authentication flow working"

def test_user_workflow_integration():
    """Test the complete user workflow integration"""
    print("🔍 Testing user workflow integration...")
    
    ui_dir = project_root / 'ui'
    
    # Check that main pages are properly integrated
    main_pages = [
        'app/page.tsx',
        'app/chat/page.tsx',
        'app/welcome/page.tsx'
    ]
    
    for page in main_pages:
        page_path = ui_dir / page
        if not page_path.exists():
            print(f"❌ Missing main page: {page}")
            return False, f"Missing main page: {page}"
        
        try:
            with open(page_path, 'r') as f:
                content = f.read()
                
                # Check for proper authentication integration
                if 'useAuth' not in content:
                    print(f"❌ {page} not properly integrated with authentication")
                    return False, f"{page} not properly integrated with authentication"
                    
        except Exception as e:
            print(f"❌ Error reading {page}: {e}")
            return False, f"Error reading {page}: {e}"
    
    print("✅ User workflow integration working")
    return True, "User workflow integration working"

def test_jwt_uuid_consistency():
    """Test JWT/UUID consistency across sessions"""
    print("🔍 Testing JWT/UUID consistency...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # Create a test user and verify JWT/UUID consistency
        test_email = f"jwt_test_{int(time.time())}@example.com"
        test_password = "testpassword123"
        
        # Register the test user
        signup_url = f"{supabase_url}/auth/v1/signup"
        headers = {
            'apikey': supabase_anon_key,
            'Content-Type': 'application/json'
        }
        
        signup_payload = {
            'email': test_email,
            'password': test_password,
            'data': {
                'full_name': 'JWT Test User'
            }
        }
        
        signup_response = requests.post(signup_url, headers=headers, json=signup_payload, timeout=10)
        
        if signup_response.status_code not in [200, 201]:
            print(f"❌ Failed to create test user: {signup_response.status_code} - {signup_response.text}")
            return False, f"Failed to create test user: {signup_response.status_code}"
        
        signup_data = signup_response.json()
        signup_user_id = signup_data.get('user', {}).get('id')
        
        if not signup_user_id:
            print("❌ No user ID in signup response")
            return False, "No user ID in signup response"
        
        # Login to get a session
        login_url = f"{supabase_url}/auth/v1/token?grant_type=password"
        login_payload = {
            'email': test_email,
            'password': test_password
        }
        
        login_response = requests.post(login_url, headers=headers, json=login_payload, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ Failed to login test user: {login_response.status_code} - {login_response.text}")
            return False, f"Failed to login test user: {login_response.status_code}"
        
        login_data = login_response.json()
        login_user_id = login_data.get('user', {}).get('id')
        access_token = login_data.get('access_token')
        
        if not login_user_id or not access_token:
            print("❌ No user ID or access token in login response")
            return False, "No user ID or access token in login response"
        
        # Verify user ID consistency
        if signup_user_id != login_user_id:
            print(f"❌ User ID inconsistency: signup={signup_user_id}, login={login_user_id}")
            return False, f"User ID inconsistency: signup={signup_user_id}, login={login_user_id}"
        
        # Test session validation with the token
        user_url = f"{supabase_url}/auth/v1/user"
        session_headers = {
            'apikey': supabase_anon_key,
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(user_url, headers=session_headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            session_user_id = user_data.get('id')
            
            if session_user_id == login_user_id:
                print("✅ JWT/UUID consistency working")
                return True, "JWT/UUID consistency working"
            else:
                print(f"❌ User ID inconsistency in session: expected={login_user_id}, got={session_user_id}")
                return False, f"User ID inconsistency in session: expected={login_user_id}, got={session_user_id}"
        else:
            print(f"❌ JWT/UUID consistency failed: {response.status_code} - {response.text}")
            return False, f"JWT/UUID consistency failed: {response.status_code}"
            
    except Exception as e:
        print(f"❌ JWT/UUID consistency error: {e}")
        return False, f"JWT/UUID consistency error: {e}"

def test_error_handling():
    """Test error handling and recovery"""
    print("🔍 Testing error handling...")
    
    ui_dir = project_root / 'ui'
    
    # Check that error handling is implemented in auth components
    error_handling_components = [
        'components/auth/LoginForm.tsx',
        'components/auth/RegisterForm.tsx',
        'components/auth/SessionManager.tsx'
    ]
    
    for component in error_handling_components:
        component_path = ui_dir / component
        if not component_path.exists():
            continue
            
        try:
            with open(component_path, 'r') as f:
                content = f.read()
                
                # Check for error handling patterns
                if 'error' not in content.lower() and 'catch' not in content.lower():
                    print(f"❌ {component} missing error handling")
                    return False, f"{component} missing error handling"
                    
        except Exception as e:
            print(f"❌ Error reading {component}: {e}")
            return False, f"Error reading {component}: {e}"
    
    print("✅ Error handling working")
    return True, "Error handling working"

def run_user_acceptance_tests():
    """Run all Phase 4 user acceptance tests"""
    print("🚀 Starting Phase 4 User Acceptance Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: User Registration Workflow
    success, message = test_user_registration_workflow()
    test_results.append(("User Registration Workflow", success, message))
    
    # Test 2: User Login Workflow
    success, message = test_user_login_workflow()
    test_results.append(("User Login Workflow", success, message))
    
    # Test 3: Session Management
    success, message = test_session_management()
    test_results.append(("Session Management", success, message))
    
    # Test 4: Frontend Authentication Flow
    success, message = test_frontend_authentication_flow()
    test_results.append(("Frontend Authentication Flow", success, message))
    
    # Test 5: User Workflow Integration
    success, message = test_user_workflow_integration()
    test_results.append(("User Workflow Integration", success, message))
    
    # Test 6: JWT/UUID Consistency
    success, message = test_jwt_uuid_consistency()
    test_results.append(("JWT/UUID Consistency", success, message))
    
    # Test 7: Error Handling
    success, message = test_error_handling()
    test_results.append(("Error Handling", success, message))
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 PHASE 4 USER ACCEPTANCE TEST RESULTS")
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
    
    results_file = project_root / f"phase4_user_acceptance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Results saved to: {results_file}")
    
    if failed == 0:
        print("\n🎉 All Phase 4 User Acceptance Tests PASSED!")
        return True
    else:
        print(f"\n⚠️  {failed} Phase 4 User Acceptance Tests FAILED!")
        return False

if __name__ == "__main__":
    success = run_user_acceptance_tests()
    sys.exit(0 if success else 1)