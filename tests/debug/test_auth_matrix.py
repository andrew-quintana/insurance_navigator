#!/usr/bin/env python3
"""
FM-027 Auth Matrix Test Script

This script tests authentication across different contexts to identify
the root cause of 400 Bad Request errors in the Upload Pipeline Worker.

Tests:
1. Direct API calls with service role key
2. Worker simulation with same configuration
3. Different endpoint formats (old vs new)
4. Environment variable loading verification
5. JWT vs Service Role authentication methods
"""

import asyncio
import httpx
import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

class AuthMatrixTester:
    """Test authentication matrix across different contexts"""
    
    def __init__(self):
        self.base_url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        # Test file path (corrected from actual storage listing)
        self.test_file_path = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
        
        # Results storage
        self.results = []
        
        print(f"🔍 Auth Matrix Tester Initialized")
        print(f"   Base URL: {self.base_url}")
        print(f"   Service Role Key: {'✅ Present' if self.service_role_key else '❌ Missing'}")
        print(f"   Anon Key: {'✅ Present' if self.anon_key else '❌ Missing'}")
        print(f"   Test File: {self.test_file_path}")
        print()
    
    def log_result(self, test_name: str, context: str, endpoint: str, status_code: int, 
                   response_text: str = "", error: str = "", headers: Dict = None):
        """Log test result with sanitized information"""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_name": test_name,
            "context": context,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_text": response_text[:200] if response_text else "",
            "error": str(error)[:200] if error else "",
            "headers": self._sanitize_headers(headers) if headers else {}
        }
        self.results.append(result)
        
        # Print result
        status_emoji = "✅" if status_code == 200 else "❌" if status_code >= 400 else "⚠️"
        print(f"{status_emoji} {test_name} - {context} - {endpoint} - Status: {status_code}")
        if error:
            print(f"   Error: {error}")
        if response_text and status_code != 200:
            print(f"   Response: {response_text[:100]}...")
    
    def _sanitize_headers(self, headers: Dict) -> Dict:
        """Sanitize headers to remove sensitive information"""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in ['authorization', 'apikey', 'x-api-key']:
                if isinstance(value, str) and len(value) > 20:
                    sanitized[key] = f"{value[:10]}...{value[-10:]}"
                else:
                    sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
    
    def _decode_jwt_header(self, token: str) -> Dict:
        """Decode JWT header without verification (safe for logging)"""
        try:
            if not token:
                return {}
            
            # Split token into parts
            parts = token.split('.')
            if len(parts) != 3:
                return {"error": "Invalid JWT format"}
            
            # Decode header (base64url)
            header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
            header_bytes = base64.urlsafe_b64decode(header_padded)
            header = json.loads(header_bytes.decode('utf-8'))
            
            return {
                "alg": header.get("alg"),
                "typ": header.get("typ"),
                "kid": header.get("kid")
            }
        except Exception as e:
            return {"error": f"JWT decode failed: {str(e)}"}
    
    async def test_direct_api_calls(self):
        """Test direct API calls with service role key"""
        print("🧪 Testing Direct API Calls")
        
        # Test contexts
        contexts = [
            {
                "name": "Service Role Only",
                "headers": {
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            },
            {
                "name": "Service Role + Anon Key",
                "headers": {
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.anon_key
                }
            },
            {
                "name": "Anon Key Only",
                "headers": {
                    "Authorization": f"Bearer {self.anon_key}",
                    "apikey": self.anon_key
                }
            }
        ]
        
        # Test endpoints
        endpoints = [
            f"{self.base_url}/storage/v1/object/files/{self.test_file_path}",
            f"{self.base_url}/object/files/{self.test_file_path}",  # Old format
            f"{self.base_url}/storage/v1/object/files/{self.test_file_path}?download=true",
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for context in contexts:
                for endpoint in endpoints:
                    try:
                        response = await client.head(endpoint, headers=context["headers"])
                        self.log_result(
                            "Direct API Call",
                            context["name"],
                            endpoint,
                            response.status_code,
                            response.text,
                            headers=dict(response.headers)
                        )
                    except Exception as e:
                        self.log_result(
                            "Direct API Call",
                            context["name"],
                            endpoint,
                            0,
                            error=str(e)
                        )
    
    async def test_worker_simulation(self):
        """Simulate worker authentication method"""
        print("🤖 Testing Worker Simulation")
        
        # Simulate worker's StorageManager configuration
        storage_config = {
            "storage_url": self.base_url,
            "anon_key": self.anon_key,
            "service_role_key": self.service_role_key
        }
        
        # Test with worker's exact headers
        worker_headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        endpoints = [
            f"{self.base_url}/storage/v1/object/files/{self.test_file_path}",
            f"{self.base_url}/object/files/{self.test_file_path}",  # Old format
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for endpoint in endpoints:
                try:
                    response = await client.head(endpoint, headers=worker_headers)
                    self.log_result(
                        "Worker Simulation",
                        "StorageManager Headers",
                        endpoint,
                        response.status_code,
                        response.text,
                        headers=dict(response.headers)
                    )
                except Exception as e:
                    self.log_result(
                        "Worker Simulation",
                        "StorageManager Headers",
                        endpoint,
                        0,
                        error=str(e)
                    )
    
    async def test_environment_variable_loading(self):
        """Test environment variable loading and precedence"""
        print("🔧 Testing Environment Variable Loading")
        
        # Test different environment variable combinations
        env_tests = [
            {
                "name": "SUPABASE_SERVICE_ROLE_KEY only",
                "env_vars": {"SUPABASE_SERVICE_ROLE_KEY": self.service_role_key}
            },
            {
                "name": "SERVICE_ROLE_KEY only",
                "env_vars": {"SERVICE_ROLE_KEY": self.service_role_key}
            },
            {
                "name": "Both keys (precedence test)",
                "env_vars": {
                    "SUPABASE_SERVICE_ROLE_KEY": self.service_role_key,
                    "SERVICE_ROLE_KEY": "different_key_for_testing"
                }
            }
        ]
        
        for test in env_tests:
            # Simulate environment variable loading
            original_env = {}
            for key, value in test["env_vars"].items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value
            
            try:
                # Test the precedence logic from WorkerConfig
                service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
                
                # Test with the loaded key
                headers = {
                    "apikey": service_role_key,
                    "Authorization": f"Bearer {service_role_key}"
                }
                
                endpoint = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.head(endpoint, headers=headers)
                    self.log_result(
                        "Environment Loading",
                        test["name"],
                        endpoint,
                        response.status_code,
                        response.text,
                        headers=dict(response.headers)
                    )
                    
            except Exception as e:
                self.log_result(
                    "Environment Loading",
                    test["name"],
                    "Environment Test",
                    0,
                    error=str(e)
                )
            finally:
                # Restore original environment
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
    
    async def test_jwt_analysis(self):
        """Analyze JWT tokens if present"""
        print("🔐 Testing JWT Analysis")
        
        # Check if we have JWT tokens in environment
        jwt_vars = [k for k in os.environ.keys() if 'JWT' in k.upper() or 'TOKEN' in k.upper()]
        
        if jwt_vars:
            print(f"   Found JWT-related environment variables: {jwt_vars}")
            
            for var in jwt_vars:
                token = os.environ[var]
                if token and len(token) > 50:  # Likely a JWT
                    header_info = self._decode_jwt_header(token)
                    print(f"   {var}: {header_info}")
                    
                    # Test with JWT token
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "apikey": self.service_role_key
                    }
                    
                    endpoint = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
                    
                    try:
                        async with httpx.AsyncClient(timeout=30) as client:
                            response = await client.head(endpoint, headers=headers)
                            self.log_result(
                                "JWT Analysis",
                                f"JWT from {var}",
                                endpoint,
                                response.status_code,
                                response.text,
                                headers=dict(response.headers)
                            )
                    except Exception as e:
                        self.log_result(
                            "JWT Analysis",
                            f"JWT from {var}",
                            endpoint,
                            0,
                            error=str(e)
                        )
        else:
            print("   No JWT-related environment variables found")
    
    async def test_storage_policies(self):
        """Test different storage policy scenarios"""
        print("📋 Testing Storage Policies")
        
        # Test with different bucket names to isolate policy issues
        test_buckets = ["files", "test-bucket", "public"]
        
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            for bucket in test_buckets:
                endpoint = f"{self.base_url}/storage/v1/object/{bucket}/{self.test_file_path}"
                
                try:
                    response = await client.head(endpoint, headers=headers)
                    self.log_result(
                        "Storage Policies",
                        f"Bucket: {bucket}",
                        endpoint,
                        response.status_code,
                        response.text,
                        headers=dict(response.headers)
                    )
                except Exception as e:
                    self.log_result(
                        "Storage Policies",
                        f"Bucket: {bucket}",
                        endpoint,
                        0,
                        error=str(e)
                    )
    
    async def test_time_based_issues(self):
        """Test for time-based authentication issues"""
        print("⏰ Testing Time-based Issues")
        
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        endpoint = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
        
        # Test multiple times to check for consistency
        for i in range(3):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.head(endpoint, headers=headers)
                    self.log_result(
                        "Time-based Test",
                        f"Attempt {i+1}",
                        endpoint,
                        response.status_code,
                        response.text,
                        headers=dict(response.headers)
                    )
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
                    
            except Exception as e:
                self.log_result(
                    "Time-based Test",
                    f"Attempt {i+1}",
                    endpoint,
                    0,
                    error=str(e)
                )
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 AUTH MATRIX TEST REPORT")
        print("="*80)
        
        # Summary statistics
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["status_code"] == 200])
        failed_tests = len([r for r in self.results if r["status_code"] >= 400])
        error_tests = len([r for r in self.results if r["status_code"] == 0])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful (200): {successful_tests}")
        print(f"Failed (4xx+): {failed_tests}")
        print(f"Errors (0): {error_tests}")
        print()
        
        # Group results by test name
        by_test = {}
        for result in self.results:
            test_name = result["test_name"]
            if test_name not in by_test:
                by_test[test_name] = []
            by_test[test_name].append(result)
        
        # Print results by test
        for test_name, results in by_test.items():
            print(f"🔍 {test_name}")
            print("-" * 40)
            
            for result in results:
                status_emoji = "✅" if result["status_code"] == 200 else "❌" if result["status_code"] >= 400 else "⚠️"
                print(f"{status_emoji} {result['context']} - {result['endpoint']} - {result['status_code']}")
                
                if result["error"]:
                    print(f"   Error: {result['error']}")
                elif result["response_text"] and result["status_code"] != 200:
                    print(f"   Response: {result['response_text'][:100]}...")
            
            print()
        
        # Save detailed results to file
        report_file = f"auth_matrix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📁 Detailed results saved to: {report_file}")
        
        # Analysis and recommendations
        print("\n🔍 ANALYSIS & RECOMMENDATIONS")
        print("-" * 40)
        
        if failed_tests > 0:
            print("❌ Issues Found:")
            
            # Check for common patterns
            status_codes = [r["status_code"] for r in self.results if r["status_code"] > 0]
            if 400 in status_codes:
                print("   - 400 Bad Request errors detected (likely authentication issue)")
            if 401 in status_codes:
                print("   - 401 Unauthorized errors detected (likely invalid credentials)")
            if 403 in status_codes:
                print("   - 403 Forbidden errors detected (likely policy issue)")
            
            # Check for endpoint differences
            old_endpoint_results = [r for r in self.results if "/object/" in r["endpoint"] and "/storage/v1/object/" not in r["endpoint"]]
            new_endpoint_results = [r for r in self.results if "/storage/v1/object/" in r["endpoint"]]
            
            if old_endpoint_results and new_endpoint_results:
                old_success = len([r for r in old_endpoint_results if r["status_code"] == 200])
                new_success = len([r for r in new_endpoint_results if r["status_code"] == 200])
                
                if old_success > new_success:
                    print("   - Old endpoint format works better than new format")
                elif new_success > old_success:
                    print("   - New endpoint format works better than old format")
        
        if successful_tests > 0:
            print("✅ Working Configurations:")
            working_configs = [r for r in self.results if r["status_code"] == 200]
            for config in working_configs[:3]:  # Show first 3 working configs
                print(f"   - {config['context']} with {config['endpoint']}")
        
        print("\n🎯 Next Steps:")
        print("   1. Compare working vs failing configurations")
        print("   2. Check environment variable loading in worker context")
        print("   3. Verify storage policies and authentication method")
        print("   4. Test with actual worker deployment")

async def main():
    """Main test execution"""
    print("🚀 Starting FM-027 Auth Matrix Investigation")
    print("="*80)
    
    tester = AuthMatrixTester()
    
    # Run all tests
    await tester.test_direct_api_calls()
    await tester.test_worker_simulation()
    await tester.test_environment_variable_loading()
    await tester.test_jwt_analysis()
    await tester.test_storage_policies()
    await tester.test_time_based_issues()
    
    # Generate report
    tester.generate_report()
    
    print("\n✅ Auth Matrix Investigation Complete")

if __name__ == "__main__":
    asyncio.run(main())