#!/usr/bin/env python3
"""
FM-027 Experiments E1-E6
Comprehensive testing to identify the root cause of 400 Bad Request errors
"""

import asyncio
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv

class FM027Experiments:
    def __init__(self):
        load_dotenv('.env.staging')
        self.base_url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        # Test file path
        self.test_file_path = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
        
        # Results storage
        self.results = []
        
        print(f"🔬 FM-027 Experiments E1-E6 Initialized")
        print(f"   Base URL: {self.base_url}")
        print(f"   Service Role Key: {'✅ Present' if self.service_role_key else '❌ Missing'}")
        print(f"   Anon Key: {'✅ Present' if self.anon_key else '❌ Missing'}")
        print(f"   Test File: {self.test_file_path}")
        print("=" * 80)

    async def run_experiment(self, name, description, test_func):
        """Run a single experiment and record results"""
        print(f"\n🧪 {name}")
        print(f"   {description}")
        print("-" * 60)
        
        try:
            result = await test_func()
            self.results.append({
                "experiment": name,
                "description": description,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            if result.get("success", False):
                print(f"✅ {name} - SUCCESS")
                if "details" in result:
                    print(f"   {result['details']}")
            else:
                print(f"❌ {name} - FAILED")
                if "error" in result:
                    print(f"   Error: {result['error']}")
                if "details" in result:
                    print(f"   {result['details']}")
                    
        except Exception as e:
            error_result = {
                "experiment": name,
                "description": description,
                "result": {"success": False, "error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(error_result)
            print(f"💥 {name} - EXCEPTION: {e}")

    async def test_request(self, url, headers, method="HEAD"):
        """Make a test request and return detailed results"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "HEAD":
                    response = await client.head(url, headers=headers)
                else:
                    response = await client.get(url, headers=headers)
                
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": url,
                    "method": method,
                    "response_text": response.text[:200] if response.text else ""
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "url": url,
                    "method": method
                }

    async def experiment_e1_headers_comparison(self):
        """E1: Compare request headers between worker and local"""
        print("Testing different header combinations...")
        
        # Test 1: Worker simulation headers
        worker_headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        # Test 2: Supabase client headers
        supabase_headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json"
        }
        
        # Test 3: Minimal headers
        minimal_headers = {
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        # Test 4: API key only
        apikey_only_headers = {
            "apikey": self.service_role_key
        }
        
        url = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
        
        tests = [
            ("Worker Headers", worker_headers),
            ("Supabase Client Headers", supabase_headers),
            ("Minimal Headers", minimal_headers),
            ("API Key Only", apikey_only_headers)
        ]
        
        results = {}
        for test_name, headers in tests:
            result = await self.test_request(url, headers)
            results[test_name] = result
            print(f"   {test_name}: {result['status_code']} {'✅' if result['success'] else '❌'}")
        
        # Check if all successful
        all_success = all(r['success'] for r in results.values())
        
        return {
            "success": all_success,
            "details": f"Header comparison complete - {sum(1 for r in results.values() if r['success'])}/{len(results)} successful",
            "results": results
        }

    async def experiment_e2_user_agent_testing(self):
        """E2: Test different User-Agent headers"""
        print("Testing different User-Agent strings...")
        
        user_agents = [
            "httpx/0.24.1",
            "Python/3.11 httpx/0.24.1",
            "Mozilla/5.0 (compatible; SupabaseClient/1.0)",
            "Python-urllib/3.11",
            "curl/7.68.0",
            ""  # No User-Agent
        ]
        
        url = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        results = {}
        for ua in user_agents:
            test_headers = headers.copy()
            if ua:
                test_headers["User-Agent"] = ua
            
            result = await self.test_request(url, test_headers)
            results[ua or "No User-Agent"] = result
            print(f"   {ua or 'No User-Agent'}: {result['status_code']} {'✅' if result['success'] else '❌'}")
        
        all_success = all(r['success'] for r in results.values())
        
        return {
            "success": all_success,
            "details": f"User-Agent testing complete - {sum(1 for r in results.values() if r['success'])}/{len(results)} successful",
            "results": results
        }

    async def experiment_e3_network_configuration(self):
        """E3: Test network configuration differences"""
        print("Testing network configuration...")
        
        url = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        # Test different timeout values
        timeouts = [5, 10, 30, 60]
        results = {}
        
        for timeout in timeouts:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.head(url, headers=headers)
                    results[f"timeout_{timeout}s"] = {
                        "success": response.status_code == 200,
                        "status_code": response.status_code
                    }
                    print(f"   Timeout {timeout}s: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            except Exception as e:
                results[f"timeout_{timeout}s"] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"   Timeout {timeout}s: ERROR - {e}")
        
        all_success = all(r['success'] for r in results.values())
        
        return {
            "success": all_success,
            "details": f"Network configuration testing complete - {sum(1 for r in results.values() if r['success'])}/{len(results)} successful",
            "results": results
        }

    async def experiment_e4_ssl_tls_testing(self):
        """E4: Test SSL/TLS configuration"""
        print("Testing SSL/TLS configuration...")
        
        url = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        # Test different SSL configurations
        ssl_configs = [
            {"verify": True, "name": "SSL Verify True"},
            {"verify": False, "name": "SSL Verify False"},
        ]
        
        results = {}
        for config in ssl_configs:
            try:
                async with httpx.AsyncClient(verify=config["verify"], timeout=30.0) as client:
                    response = await client.head(url, headers=headers)
                    results[config["name"]] = {
                        "success": response.status_code == 200,
                        "status_code": response.status_code
                    }
                    print(f"   {config['name']}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            except Exception as e:
                results[config["name"]] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"   {config['name']}: ERROR - {e}")
        
        all_success = all(r['success'] for r in results.values())
        
        return {
            "success": all_success,
            "details": f"SSL/TLS testing complete - {sum(1 for r in results.values() if r['success'])}/{len(results)} successful",
            "results": results
        }

    async def experiment_e5_rate_limiting(self):
        """E5: Test rate limiting and concurrent requests"""
        print("Testing rate limiting and concurrent requests...")
        
        url = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        # Test concurrent requests
        async def make_request():
            return await self.test_request(url, headers)
        
        # Test 1: Single request
        single_result = await make_request()
        print(f"   Single request: {single_result['status_code']} {'✅' if single_result['success'] else '❌'}")
        
        # Test 2: 5 concurrent requests
        concurrent_results = await asyncio.gather(*[make_request() for _ in range(5)], return_exceptions=True)
        concurrent_success = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get('success', False))
        print(f"   5 concurrent requests: {concurrent_success}/5 successful")
        
        # Test 3: Rapid sequential requests
        rapid_results = []
        for i in range(5):
            result = await make_request()
            rapid_results.append(result)
            print(f"   Rapid request {i+1}: {result['status_code']} {'✅' if result['success'] else '❌'}")
            await asyncio.sleep(0.1)  # Small delay between requests
        
        rapid_success = sum(1 for r in rapid_results if r.get('success', False))
        
        return {
            "success": single_result['success'] and concurrent_success >= 4 and rapid_success >= 4,
            "details": f"Rate limiting test - Single: {single_result['success']}, Concurrent: {concurrent_success}/5, Rapid: {rapid_success}/5",
            "results": {
                "single": single_result,
                "concurrent": concurrent_results,
                "rapid": rapid_results
            }
        }

    async def experiment_e6_environment_isolation(self):
        """E6: Test environment isolation and context differences"""
        print("Testing environment isolation...")
        
        # Test 1: Check environment variables
        env_vars = {
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT"),
            "NODE_ENV": os.getenv("NODE_ENV"),
            "PYTHONPATH": os.getenv("PYTHONPATH")
        }
        
        print("   Environment variables:")
        for key, value in env_vars.items():
            if value:
                print(f"     {key}: {'✅ Present' if value else '❌ Empty'}")
            else:
                print(f"     {key}: ❌ Missing")
        
        # Test 2: Check Python environment
        import sys
        python_info = {
            "version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable
        }
        
        print("   Python environment:")
        for key, value in python_info.items():
            print(f"     {key}: {value}")
        
        # Test 3: Check network connectivity
        test_url = f"{self.base_url}/storage/v1/object/files/{self.test_file_path}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}"
        }
        
        connectivity_result = await self.test_request(test_url, headers)
        print(f"   Network connectivity: {connectivity_result['status_code']} {'✅' if connectivity_result['success'] else '❌'}")
        
        return {
            "success": connectivity_result['success'],
            "details": f"Environment isolation test - Connectivity: {connectivity_result['success']}",
            "results": {
                "env_vars": env_vars,
                "python_info": python_info,
                "connectivity": connectivity_result
            }
        }

    async def run_all_experiments(self):
        """Run all experiments E1-E6"""
        print("🚀 Starting FM-027 Experiments E1-E6")
        print("=" * 80)
        
        # Run all experiments
        await self.run_experiment(
            "E1: Headers Comparison",
            "Compare different header combinations to identify optimal configuration",
            self.experiment_e1_headers_comparison
        )
        
        await self.run_experiment(
            "E2: User-Agent Testing",
            "Test different User-Agent strings to identify potential blocking",
            self.experiment_e2_user_agent_testing
        )
        
        await self.run_experiment(
            "E3: Network Configuration",
            "Test different timeout and network configurations",
            self.experiment_e3_network_configuration
        )
        
        await self.run_experiment(
            "E4: SSL/TLS Testing",
            "Test SSL/TLS configuration differences",
            self.experiment_e4_ssl_tls_testing
        )
        
        await self.run_experiment(
            "E5: Rate Limiting",
            "Test rate limiting and concurrent request handling",
            self.experiment_e5_rate_limiting
        )
        
        await self.run_experiment(
            "E6: Environment Isolation",
            "Test environment isolation and context differences",
            self.experiment_e6_environment_isolation
        )
        
        # Generate final report
        self.generate_report()

    def generate_report(self):
        """Generate final experiment report"""
        print("\n" + "=" * 80)
        print("📊 FM-027 EXPERIMENTS E1-E6 REPORT")
        print("=" * 80)
        
        successful_experiments = sum(1 for r in self.results if r["result"].get("success", False))
        total_experiments = len(self.results)
        
        print(f"Total Experiments: {total_experiments}")
        print(f"Successful: {successful_experiments}")
        print(f"Failed: {total_experiments - successful_experiments}")
        print(f"Success Rate: {(successful_experiments/total_experiments)*100:.1f}%")
        
        print("\n🔍 DETAILED RESULTS:")
        print("-" * 60)
        
        for result in self.results:
            status = "✅ SUCCESS" if result["result"].get("success", False) else "❌ FAILED"
            print(f"{status} - {result['experiment']}")
            print(f"   {result['description']}")
            if "details" in result["result"]:
                print(f"   Details: {result['result']['details']}")
            if "error" in result["result"]:
                print(f"   Error: {result['result']['error']}")
            print()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fm027_experiments_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📁 Detailed results saved to: {filename}")
        
        # Generate recommendations
        self.generate_recommendations()

    def generate_recommendations(self):
        """Generate recommendations based on experiment results"""
        print("\n🎯 RECOMMENDATIONS:")
        print("-" * 60)
        
        # Analyze results
        failed_experiments = [r for r in self.results if not r["result"].get("success", False)]
        
        if not failed_experiments:
            print("✅ All experiments passed! The issue is likely not in the tested areas.")
            print("   Consider investigating:")
            print("   - Render-specific environment variables")
            print("   - Network routing differences")
            print("   - Supabase service configuration")
        else:
            print("❌ Some experiments failed. Focus on:")
            for exp in failed_experiments:
                print(f"   - {exp['experiment']}: {exp['result'].get('error', 'Unknown error')}")
        
        print("\n🔧 NEXT STEPS:")
        print("   1. Compare worker logs with experiment results")
        print("   2. Test with actual worker deployment")
        print("   3. Check Render-specific environment differences")
        print("   4. Verify Supabase service configuration")

async def main():
    experiments = FM027Experiments()
    await experiments.run_all_experiments()

if __name__ == "__main__":
    asyncio.run(main())
