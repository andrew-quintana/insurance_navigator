#!/usr/bin/env python3
"""
Phase 4 Performance Test Script
Tests the performance and reliability of the Supabase authentication system
"""

import os
import sys
import json
import time
import requests
import statistics
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def test_registration_performance():
    """Test user registration performance"""
    print("🔍 Testing user registration performance...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # Test multiple registrations to measure performance
        num_tests = 5
        response_times = []
        success_count = 0
        
        for i in range(num_tests):
            test_email = f"perf_test_{int(time.time())}_{i}@example.com"
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
                    'full_name': f'Performance Test User {i}'
                }
            }
            
            start_time = time.time()
            response = requests.post(auth_url, headers=headers, json=payload, timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code in [200, 201]:
                success_count += 1
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        success_rate = (success_count / num_tests) * 100
        
        print(f"✅ Registration performance: avg={avg_response_time:.2f}s, max={max_response_time:.2f}s, min={min_response_time:.2f}s, success={success_rate:.1f}%")
        
        if success_rate >= 80 and avg_response_time <= 2.0:
            return True, f"Registration performance good: {success_rate:.1f}% success, {avg_response_time:.2f}s avg"
        else:
            return False, f"Registration performance poor: {success_rate:.1f}% success, {avg_response_time:.2f}s avg"
            
    except Exception as e:
        print(f"❌ Registration performance error: {e}")
        return False, f"Registration performance error: {e}"

def test_login_performance():
    """Test user login performance"""
    print("🔍 Testing user login performance...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # First create a test user
        test_email = f"login_perf_{int(time.time())}@example.com"
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
                'full_name': 'Login Performance Test User'
            }
        }
        
        signup_response = requests.post(signup_url, headers=headers, json=signup_payload, timeout=10)
        
        if signup_response.status_code not in [200, 201]:
            return False, f"Failed to create test user: {signup_response.status_code}"
        
        # Test multiple logins to measure performance
        num_tests = 5
        response_times = []
        success_count = 0
        
        for i in range(num_tests):
            login_url = f"{supabase_url}/auth/v1/token?grant_type=password"
            login_payload = {
                'email': test_email,
                'password': test_password
            }
            
            start_time = time.time()
            response = requests.post(login_url, headers=headers, json=login_payload, timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code == 200:
                success_count += 1
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        success_rate = (success_count / num_tests) * 100
        
        print(f"✅ Login performance: avg={avg_response_time:.2f}s, max={max_response_time:.2f}s, min={min_response_time:.2f}s, success={success_rate:.1f}%")
        
        if success_rate >= 80 and avg_response_time <= 1.0:
            return True, f"Login performance good: {success_rate:.1f}% success, {avg_response_time:.2f}s avg"
        else:
            return False, f"Login performance poor: {success_rate:.1f}% success, {avg_response_time:.2f}s avg"
            
    except Exception as e:
        print(f"❌ Login performance error: {e}")
        return False, f"Login performance error: {e}"

def test_concurrent_requests():
    """Test concurrent request handling"""
    print("🔍 Testing concurrent request handling...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    def make_registration_request(i):
        """Make a single registration request"""
        test_email = f"concurrent_test_{int(time.time())}_{i}@example.com"
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
                'full_name': f'Concurrent Test User {i}'
            }
        }
        
        start_time = time.time()
        try:
            response = requests.post(auth_url, headers=headers, json=payload, timeout=10)
            end_time = time.time()
            
            return {
                'success': response.status_code in [200, 201],
                'response_time': end_time - start_time,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'response_time': 0,
                'error': str(e)
            }
    
    try:
        # Test with 10 concurrent requests
        num_concurrent = 10
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_registration_request, i) for i in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        
        success_count = sum(1 for r in results if r['success'])
        response_times = [r['response_time'] for r in results if r['response_time'] > 0]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        success_rate = (success_count / num_concurrent) * 100
        
        print(f"✅ Concurrent performance: {success_count}/{num_concurrent} successful, avg={avg_response_time:.2f}s, max={max_response_time:.2f}s")
        
        if success_rate >= 70 and avg_response_time <= 3.0:
            return True, f"Concurrent performance good: {success_rate:.1f}% success, {avg_response_time:.2f}s avg"
        else:
            return False, f"Concurrent performance poor: {success_rate:.1f}% success, {avg_response_time:.2f}s avg"
            
    except Exception as e:
        print(f"❌ Concurrent performance error: {e}")
        return False, f"Concurrent performance error: {e}"

def test_error_handling_performance():
    """Test error handling performance"""
    print("🔍 Testing error handling performance...")
    
    config = load_environment_config()
    supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        return False, "Missing Supabase configuration"
    
    try:
        # Test various error scenarios
        error_scenarios = [
            {
                'name': 'Invalid email format',
                'payload': {'email': 'invalid-email', 'password': 'testpassword123'},
                'expected_status': [400, 422]  # Accept both 400 and 422
            },
            {
                'name': 'Weak password',
                'payload': {'email': 'test@example.com', 'password': '123'},
                'expected_status': [400, 422]  # Accept both 400 and 422
            },
            {
                'name': 'Missing email',
                'payload': {'password': 'testpassword123'},
                'expected_status': [400, 422]  # Accept both 400 and 422
            },
            {
                'name': 'Missing password',
                'payload': {'email': 'test@example.com'},
                'expected_status': [400, 422]  # Accept both 400 and 422
            }
        ]
        
        response_times = []
        correct_error_handling = 0
        
        for scenario in error_scenarios:
            auth_url = f"{supabase_url}/auth/v1/signup"
            headers = {
                'apikey': supabase_anon_key,
                'Content-Type': 'application/json'
            }
            
            start_time = time.time()
            response = requests.post(auth_url, headers=headers, json=scenario['payload'], timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code in scenario['expected_status']:
                correct_error_handling += 1
                print(f"  ✅ {scenario['name']}: {response.status_code} ({response_time:.2f}s)")
            else:
                print(f"  ❌ {scenario['name']}: expected {scenario['expected_status']}, got {response.status_code}")
        
        avg_response_time = statistics.mean(response_times)
        error_handling_rate = (correct_error_handling / len(error_scenarios)) * 100
        
        print(f"✅ Error handling performance: {correct_error_handling}/{len(error_scenarios)} correct, avg={avg_response_time:.2f}s")
        
        if error_handling_rate >= 75 and avg_response_time <= 1.0:
            return True, f"Error handling performance good: {error_handling_rate:.1f}% correct, {avg_response_time:.2f}s avg"
        else:
            return False, f"Error handling performance poor: {error_handling_rate:.1f}% correct, {avg_response_time:.2f}s avg"
            
    except Exception as e:
        print(f"❌ Error handling performance error: {e}")
        return False, f"Error handling performance error: {e}"

def test_memory_usage():
    """Test memory usage during operations"""
    print("🔍 Testing memory usage...")
    
    try:
        import psutil
        process = psutil.Process()
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform some operations
        config = load_environment_config()
        supabase_url = config.get('NEXT_PUBLIC_SUPABASE_URL')
        supabase_anon_key = config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_anon_key:
            return False, "Missing Supabase configuration"
        
        # Make several requests
        for i in range(10):
            test_email = f"memory_test_{int(time.time())}_{i}@example.com"
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
                    'full_name': f'Memory Test User {i}'
                }
            }
            
            try:
                requests.post(auth_url, headers=headers, json=payload, timeout=5)
            except:
                pass  # Ignore errors for memory test
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"✅ Memory usage: initial={initial_memory:.1f}MB, final={final_memory:.1f}MB, increase={memory_increase:.1f}MB")
        
        if memory_increase <= 50:  # Less than 50MB increase
            return True, f"Memory usage good: {memory_increase:.1f}MB increase"
        else:
            return False, f"Memory usage high: {memory_increase:.1f}MB increase"
            
    except ImportError:
        print("⚠️ psutil not available, skipping memory test")
        return True, "Memory test skipped (psutil not available)"
    except Exception as e:
        print(f"❌ Memory usage error: {e}")
        return False, f"Memory usage error: {e}"

def run_performance_tests():
    """Run all Phase 4 performance tests"""
    print("🚀 Starting Phase 4 Performance Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Registration Performance
    success, message = test_registration_performance()
    test_results.append(("Registration Performance", success, message))
    
    # Test 2: Login Performance
    success, message = test_login_performance()
    test_results.append(("Login Performance", success, message))
    
    # Test 3: Concurrent Requests
    success, message = test_concurrent_requests()
    test_results.append(("Concurrent Requests", success, message))
    
    # Test 4: Error Handling Performance
    success, message = test_error_handling_performance()
    test_results.append(("Error Handling Performance", success, message))
    
    # Test 5: Memory Usage
    success, message = test_memory_usage()
    test_results.append(("Memory Usage", success, message))
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 PHASE 4 PERFORMANCE TEST RESULTS")
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
    
    results_file = project_root / f"phase4_performance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Results saved to: {results_file}")
    
    if failed == 0:
        print("\n🎉 All Phase 4 Performance Tests PASSED!")
        return True
    else:
        print(f"\n⚠️  {failed} Phase 4 Performance Tests FAILED!")
        return False

if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)