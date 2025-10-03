#!/usr/bin/env python3
"""
FM-033 Vercel Environment Variables Test Script

Tests Vercel environment variable configuration
to identify issues with Supabase authentication.

Usage:
    python test_vercel_env_vars.py
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

class VercelEnvVarTester:
    def __init__(self):
        self.results = []
        self.required_vars = [
            'NEXT_PUBLIC_SUPABASE_URL',
            'NEXT_PUBLIC_SUPABASE_ANON_KEY',
            'NEXT_PUBLIC_API_BASE_URL',
            'NEXT_PUBLIC_API_URL',
            'NODE_ENV'
        ]
        
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
        
    def test_required_variables_present(self) -> bool:
        """Test if all required environment variables are present"""
        missing_vars = []
        present_vars = []
        
        for var in self.required_vars:
            value = os.getenv(var)
            if value:
                present_vars.append(var)
            else:
                missing_vars.append(var)
        
        success = len(missing_vars) == 0
        self.log_result(
            'required_variables_present',
            success,
            {
                'message': 'Required environment variables test',
                'missing_vars': missing_vars,
                'present_vars': present_vars,
                'total_required': len(self.required_vars)
            }
        )
        return success
    
    def test_supabase_url_format(self) -> bool:
        """Test Supabase URL format"""
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        
        if not supabase_url:
            self.log_result(
                'supabase_url_format',
                False,
                {'message': 'NEXT_PUBLIC_SUPABASE_URL not set'}
            )
            return False
        
        # Check URL format
        is_https = supabase_url.startswith('https://')
        has_supabase_domain = 'supabase.co' in supabase_url
        has_project_id = len(supabase_url.split('//')[1].split('.')[0]) > 0
        
        success = is_https and has_supabase_domain and has_project_id
        self.log_result(
            'supabase_url_format',
            success,
            {
                'message': 'Supabase URL format test',
                'url': supabase_url,
                'is_https': is_https,
                'has_supabase_domain': has_supabase_domain,
                'has_project_id': has_project_id
            }
        )
        return success
    
    def test_supabase_anon_key_format(self) -> bool:
        """Test Supabase anon key format"""
        anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not anon_key:
            self.log_result(
                'supabase_anon_key_format',
                False,
                {'message': 'NEXT_PUBLIC_SUPABASE_ANON_KEY not set'}
            )
            return False
        
        # Check JWT format (should start with eyJ)
        is_jwt_format = anon_key.startswith('eyJ')
        has_three_parts = len(anon_key.split('.')) == 3
        reasonable_length = 100 < len(anon_key) < 1000
        
        success = is_jwt_format and has_three_parts and reasonable_length
        self.log_result(
            'supabase_anon_key_format',
            success,
            {
                'message': 'Supabase anon key format test',
                'is_jwt_format': is_jwt_format,
                'has_three_parts': has_three_parts,
                'reasonable_length': reasonable_length,
                'key_length': len(anon_key)
            }
        )
        return success
    
    def test_api_url_consistency(self) -> bool:
        """Test API URL consistency"""
        api_base_url = os.getenv('NEXT_PUBLIC_API_BASE_URL')
        api_url = os.getenv('NEXT_PUBLIC_API_URL')
        
        if not api_base_url or not api_url:
            self.log_result(
                'api_url_consistency',
                False,
                {'message': 'API URLs not set'}
            )
            return False
        
        # Check if URLs are consistent
        urls_match = api_base_url == api_url
        both_https = api_base_url.startswith('https://') and api_url.startswith('https://')
        both_render = 'render.com' in api_base_url and 'render.com' in api_url
        
        success = urls_match and both_https and both_render
        self.log_result(
            'api_url_consistency',
            success,
            {
                'message': 'API URL consistency test',
                'api_base_url': api_base_url,
                'api_url': api_url,
                'urls_match': urls_match,
                'both_https': both_https,
                'both_render': both_render
            }
        )
        return success
    
    def test_node_env_value(self) -> bool:
        """Test NODE_ENV value"""
        node_env = os.getenv('NODE_ENV')
        
        if not node_env:
            self.log_result(
                'node_env_value',
                False,
                {'message': 'NODE_ENV not set'}
            )
            return False
        
        # Check if NODE_ENV is valid
        valid_values = ['development', 'staging', 'production']
        is_valid = node_env.lower() in valid_values
        
        success = is_valid
        self.log_result(
            'node_env_value',
            success,
            {
                'message': 'NODE_ENV value test',
                'node_env': node_env,
                'is_valid': is_valid,
                'valid_values': valid_values
            }
        )
        return success
    
    def test_environment_variable_scope(self) -> bool:
        """Test environment variable scope"""
        # Check if variables are available in different contexts
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        # Test if variables are accessible
        url_accessible = bool(supabase_url)
        key_accessible = bool(anon_key)
        
        success = url_accessible and key_accessible
        self.log_result(
            'environment_variable_scope',
            success,
            {
                'message': 'Environment variable scope test',
                'url_accessible': url_accessible,
                'key_accessible': key_accessible,
                'url_value': supabase_url[:20] + '...' if supabase_url else None,
                'key_value': anon_key[:20] + '...' if anon_key else None
            }
        )
        return success
    
    def test_supabase_connectivity_with_env_vars(self) -> bool:
        """Test Supabase connectivity using environment variables"""
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not anon_key:
            self.log_result(
                'supabase_connectivity_with_env_vars',
                False,
                {'message': 'Required environment variables not set'}
            )
            return False
        
        try:
            response = requests.get(
                f"{supabase_url}/rest/v1/",
                headers={'apikey': anon_key},
                timeout=10
            )
            
            success = response.status_code == 200
            self.log_result(
                'supabase_connectivity_with_env_vars',
                success,
                {
                    'message': 'Supabase connectivity test using env vars',
                    'status_code': response.status_code,
                    'response_headers': dict(response.headers)
                }
            )
            return success
        except Exception as e:
            self.log_result(
                'supabase_connectivity_with_env_vars',
                False,
                {'message': f'Connectivity error: {str(e)}'}
            )
            return False
    
    def test_vercel_build_env_vars(self) -> bool:
        """Test Vercel build environment variables"""
        # Check if variables are available during build
        build_vars = [
            'NEXT_PUBLIC_SUPABASE_URL',
            'NEXT_PUBLIC_SUPABASE_ANON_KEY',
            'NEXT_PUBLIC_API_BASE_URL',
            'NEXT_PUBLIC_API_URL',
            'NODE_ENV'
        ]
        
        build_vars_present = []
        build_vars_missing = []
        
        for var in build_vars:
            if os.getenv(var):
                build_vars_present.append(var)
            else:
                build_vars_missing.append(var)
        
        success = len(build_vars_missing) == 0
        self.log_result(
            'vercel_build_env_vars',
            success,
            {
                'message': 'Vercel build environment variables test',
                'present_vars': build_vars_present,
                'missing_vars': build_vars_missing,
                'total_vars': len(build_vars)
            }
        )
        return success
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all environment variable tests"""
        print("🔍 Running FM-033 Vercel Environment Variables Tests...")
        print("-" * 50)
        
        tests = [
            self.test_required_variables_present,
            self.test_supabase_url_format,
            self.test_supabase_anon_key_format,
            self.test_api_url_consistency,
            self.test_node_env_value,
            self.test_environment_variable_scope,
            self.test_supabase_connectivity_with_env_vars,
            self.test_vercel_build_env_vars
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
            return "All tests passed - Environment variables configuration appears correct"
        
        summary = "Failed tests identified:\n"
        for test in failed_tests:
            summary += f"- {test['test_name']}: {test['details'].get('message', 'Unknown error')}\n"
        
        return summary

def main():
    """Main test execution"""
    tester = VercelEnvVarTester()
    results = tester.run_all_tests()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"fm033_vercel_env_vars_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Results saved to: {filename}")
    
    # Print summary
    print("\n📋 Test Summary:")
    print(results['summary'])
    
    return results

if __name__ == "__main__":
    main()
