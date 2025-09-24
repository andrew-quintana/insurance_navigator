#!/usr/bin/env python3
"""
Simple Phase 3 Integration Test - Bypasses complex configuration issues
Tests basic connectivity and functionality without requiring full API startup
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class SimplePhase3Tester:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    async def test_supabase_connectivity(self) -> bool:
        """Test Supabase connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test Supabase API
                async with session.get('http://localhost:54321/rest/v1/', 
                                    headers={'apikey': os.getenv('SUPABASE_ANON_KEY', 'mock-anon-key')}) as response:
                    if response.status == 200:
                        self.results.append({"test": "supabase_connectivity", "status": "PASS", "message": "Supabase API accessible"})
                        return True
                    else:
                        self.results.append({"test": "supabase_connectivity", "status": "FAIL", "message": f"Supabase API returned status {response.status}"})
                        return False
        except Exception as e:
            self.results.append({"test": "supabase_connectivity", "status": "FAIL", "message": f"Supabase connectivity failed: {e}"})
            return False
    
    async def test_docker_containers(self) -> bool:
        """Test Docker container status"""
        try:
            import subprocess
            result = subprocess.run(['docker', 'ps', '--format', 'json'], capture_output=True, text=True)
            containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
            
            supabase_containers = [c for c in containers if 'supabase' in c.get('Names', '')]
            api_containers = [c for c in containers if 'insurance_navigator' in c.get('Names', '')]
            
            if len(supabase_containers) >= 5:  # Expected number of Supabase containers
                self.results.append({"test": "docker_containers", "status": "PASS", "message": f"Found {len(supabase_containers)} Supabase containers"})
                return True
            else:
                self.results.append({"test": "docker_containers", "status": "FAIL", "message": f"Only found {len(supabase_containers)} Supabase containers"})
                return False
        except Exception as e:
            self.results.append({"test": "docker_containers", "status": "FAIL", "message": f"Docker container check failed: {e}"})
            return False
    
    async def test_network_connectivity(self) -> bool:
        """Test network connectivity between containers"""
        try:
            # Test if we can reach Supabase from the host
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:54321/health') as response:
                    if response.status == 200:
                        self.results.append({"test": "network_connectivity", "status": "PASS", "message": "Network connectivity working"})
                        return True
                    else:
                        self.results.append({"test": "network_connectivity", "status": "FAIL", "message": f"Health check returned status {response.status}"})
                        return False
        except Exception as e:
            self.results.append({"test": "network_connectivity", "status": "FAIL", "message": f"Network connectivity failed: {e}"})
            return False
    
    async def test_environment_variables(self) -> bool:
        """Test environment variable configuration"""
        try:
            import os
            required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SERVICE_ROLE_KEY', 'JWT_SECRET']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if not missing_vars:
                self.results.append({"test": "environment_variables", "status": "PASS", "message": "All required environment variables present"})
                return True
            else:
                self.results.append({"test": "environment_variables", "status": "FAIL", "message": f"Missing variables: {missing_vars}"})
                return False
        except Exception as e:
            self.results.append({"test": "environment_variables", "status": "FAIL", "message": f"Environment variable check failed: {e}"})
            return False
    
    async def test_database_connection(self) -> bool:
        """Test direct database connection"""
        try:
            import asyncpg
            # Try to connect to the Supabase database directly
            conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:54322/postgres')
            await conn.close()
            self.results.append({"test": "database_connection", "status": "PASS", "message": "Database connection successful"})
            return True
        except Exception as e:
            self.results.append({"test": "database_connection", "status": "FAIL", "message": f"Database connection failed: {e}"})
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("🚀 Starting Simple Phase 3 Integration Tests")
        print("=" * 50)
        
        tests = [
            self.test_docker_containers,
            self.test_environment_variables,
            self.test_network_connectivity,
            self.test_database_connection,
            self.test_supabase_connectivity,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
            except Exception as e:
                self.results.append({"test": test.__name__, "status": "ERROR", "message": f"Test failed with exception: {e}"})
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        success_rate = (passed / total) * 100
        
        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": success_rate,
            "duration_seconds": duration,
            "timestamp": end_time.isoformat(),
            "results": self.results
        }
        
        print(f"\n📊 Test Results Summary:")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        print(f"\n📋 Detailed Results:")
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']} - {result['message']}")
        
        return summary

async def main():
    """Main test execution"""
    tester = SimplePhase3Tester()
    results = await tester.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"phase3_simple_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    
    # Return exit code based on success rate
    if results["success_rate"] >= 80:
        print("\n🎉 Phase 3 Simple Tests PASSED!")
        return 0
    else:
        print("\n❌ Phase 3 Simple Tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
