#!/usr/bin/env python3
"""
FM-033 Supabase Authentication Test Script

Tests Supabase authentication endpoints and configuration
to identify root cause of 400 Bad Request errors.

Usage:
    python test_supabase_auth.py
"""

import os
import json
import requests
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, Optional

class SupabaseAuthTester:
    def __init__(self):
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL', 'https://dfgzeastcxnoqshgyotp.supabase.co')
        self.supabase_anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.results.append(result)
        print(f"{'✅' if success else '❌'} {test_name}: {details.get('message', '')}")
        
    def test_supabase_connectivity(self) -> bool:
        """Test basic Supabase connectivity"""
        try:
            response = requests.get(f"{self.supabase_url}/rest/v1/", 
                                  headers={'apikey': self.supabase_anon_key},
                                  timeout=10)
            
            success = response.status_code == 200
            self.log_result(
                'supabase_connectivity',
                success,
                {
                    'status_code': response.status_code,
                    'message': 'Supabase connectivity test',
                    'response_headers': dict(response.headers)
                }
            )
            return success
        except Exception as e:
            self.log_result(
                'supabase_connectivity',
                False,
                {'message': f'Connection error: {str(e)}'}
            )
            return False
    
    def test_auth_token_endpoint(self) -> bool:
        """Test authentication token endpoint"""
        try:
            # Test with invalid credentials to see if endpoint responds
            auth_data = {
                'email': 'test@example.com',
                'password': 'invalidpassword'
            }
            
            response = requests.post(
                f"{self.supabase_url}/auth/v1/token?grant_type=password",
                headers={
                    'apikey': self.supabase_anon_key,
                    'Content-Type': 'application/json'
                },
                json=auth_data,
                timeout=10
            )
            
            # We expect 400 for invalid credentials, but endpoint should respond
            success = response.status_code in [200, 400, 401]
            self.log_result(
                'auth_token_endpoint',
                success,
                {
                    'status_code': response.status_code,
                    'message': 'Auth token endpoint test',
                    'response_body': response.text[:200] if response.text else 'No response body'
                }
            )
            return success
        except Exception as e:
            self.log_result(
                'auth_token_endpoint',
                False,
                {'message': f'Token endpoint error: {str(e)}'}
            )
            return False
    
    def test_api_key_permissions(self) -> bool:
        """Test API key permissions"""
        try:
            # Test if API key can access auth endpoints
            response = requests.get(
                f"{self.supabase_url}/auth/v1/settings",
                headers={'apikey': self.supabase_anon_key},
                timeout=10
            )
            
            success = response.status_code in [200, 401, 403]
            self.log_result(
                'api_key_permissions',
                success,
                {
                    'status_code': response.status_code,
                    'message': 'API key permissions test',
                    'response_body': response.text[:200] if response.text else 'No response body'
                }
            )
            return success
        except Exception as e:
            self.log_result(
                'api_key_permissions',
                False,
                {'message': f'API key permissions error: {str(e)}'}
            )
            return False
    
    def test_environment_variables(self) -> bool:
        """Test environment variable configuration"""
        required_vars = [
            'NEXT_PUBLIC_SUPABASE_URL',
            'NEXT_PUBLIC_SUPABASE_ANON_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        success = len(missing_vars) == 0
        self.log_result(
            'environment_variables',
            success,
            {
                'message': 'Environment variables test',
                'missing_vars': missing_vars,
                'supabase_url': self.supabase_url,
                'has_anon_key': bool(self.supabase_anon_key)
            }
        )
        return success
    
    def test_cors_configuration(self) -> bool:
        """Test CORS configuration"""
        try:
            # Test preflight request
            response = requests.options(
                f"{self.supabase_url}/auth/v1/token",
                headers={
                    'Origin': 'https://insurance-navigator-preview.vercel.app',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'apikey,content-type'
                },
                timeout=10
            )
            
            success = response.status_code in [200, 204]
            self.log_result(
                'cors_configuration',
                success,
                {
                    'status_code': response.status_code,
                    'message': 'CORS configuration test',
                    'cors_headers': {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
                }
            )
            return success
        except Exception as e:
            self.log_result(
                'cors_configuration',
                False,
                {'message': f'CORS configuration error: {str(e)}'}
            )
            return False
    
    def test_authentication_flow_simulation(self) -> bool:
        """Simulate the authentication flow that's failing"""
        try:
            # Simulate the exact flow from the error
            # Auth state changes to "INITIAL_SESSION" then fails
            
            # Step 1: Check if we can get initial session
            response = requests.get(
                f"{self.supabase_url}/auth/v1/user",
                headers={'apikey': self.supabase_anon_key},
                timeout=10
            )
            
            # Step 2: Test token refresh if needed
            if response.status_code == 401:
                # Try to get new session
                refresh_response = requests.post(
                    f"{self.supabase_url}/auth/v1/token?grant_type=refresh_token",
                    headers={
                        'apikey': self.supabase_anon_key,
                        'Content-Type': 'application/json'
                    },
                    json={'refresh_token': 'invalid_token'},
                    timeout=10
                )
                
                success = refresh_response.status_code in [200, 400, 401]
                self.log_result(
                    'authentication_flow_simulation',
                    success,
                    {
                        'status_code': refresh_response.status_code,
                        'message': 'Authentication flow simulation',
                        'response_body': refresh_response.text[:200] if refresh_response.text else 'No response body'
                    }
                )
                return success
            else:
                success = response.status_code in [200, 401]
                self.log_result(
                    'authentication_flow_simulation',
                    success,
                    {
                        'status_code': response.status_code,
                        'message': 'Authentication flow simulation',
                        'response_body': response.text[:200] if response.text else 'No response body'
                    }
                )
                return success
                
        except Exception as e:
            self.log_result(
                'authentication_flow_simulation',
                False,
                {'message': f'Authentication flow simulation error: {str(e)}'}
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all authentication tests"""
        print("🔍 Running FM-033 Supabase Authentication Tests...")
        print(f"Supabase URL: {self.supabase_url}")
        print(f"Has API Key: {bool(self.supabase_anon_key)}")
        print("-" * 50)
        
        tests = [
            self.test_environment_variables,
            self.test_supabase_connectivity,
            self.test_api_key_permissions,
            self.test_auth_token_endpoint,
            self.test_cors_configuration,
            self.test_authentication_flow_simulation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        print("-" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'results': self.results,
            'summary': self.generate_summary()
        }
    
    def generate_summary(self) -> str:
        """Generate test summary"""
        failed_tests = [r for r in self.results if not r['success']]
        
        if not failed_tests:
            return "All tests passed - Supabase authentication configuration appears correct"
        
        summary = "Failed tests identified:\n"
        for test in failed_tests:
            summary += f"- {test['test_name']}: {test['details'].get('message', 'Unknown error')}\n"
        
        return summary

def main():
    """Main test execution"""
    tester = SupabaseAuthTester()
    results = tester.run_all_tests()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"fm033_supabase_auth_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Results saved to: {filename}")
    
    # Print summary
    print("\n📋 Test Summary:")
    print(results['summary'])
    
    return results

if __name__ == "__main__":
    main()
