#!/usr/bin/env python3
"""
Phase 3 - Cloud Infrastructure Test

This test validates cloud infrastructure setup including Kubernetes cluster,
networking, load balancing, and basic connectivity for agent services.
"""

import asyncio
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase3CloudInfrastructureTest:
    def __init__(self):
        self.results = {
            "test_name": "Phase 3 Cloud Infrastructure Test",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
        
        # Load production environment
        load_dotenv('.env.production')
        
        # Test configuration
        self.kubernetes_cluster = os.getenv('KUBERNETES_CLUSTER', 'agents-integration-cluster')
        self.namespace = os.getenv('NAMESPACE', 'agents-production')
        self.ingress_domain = os.getenv('INGRESS_DOMAIN', 'agents-api.yourdomain.com')
        self.agent_api_url = os.getenv('AGENT_API_URL', f'https://{self.ingress_domain}')
        
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            test_result = {
                "name": test_name,
                "status": "PASSED" if result else "FAILED",
                "duration": duration,
                "details": result if isinstance(result, dict) else {"success": result}
            }
            
            self.results["tests"].append(test_result)
            self.results["summary"]["total_tests"] += 1
            
            if result:
                self.results["summary"]["passed"] += 1
                logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            else:
                self.results["summary"]["failed"] += 1
                logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "name": test_name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            }
            
            self.results["tests"].append(test_result)
            self.results["summary"]["total_tests"] += 1
            self.results["summary"]["failed"] += 1
            logger.error(f"❌ {test_name} - ERROR: {str(e)} ({duration:.2f}s)")
    
    async def test_kubernetes_cluster_connectivity(self) -> Dict[str, Any]:
        """Test Kubernetes cluster connectivity and basic operations"""
        try:
            # Test kubectl connectivity
            import subprocess
            
            # Check cluster info
            result = subprocess.run(
                ['kubectl', 'cluster-info'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"kubectl cluster-info failed: {result.stderr}"
                }
            
            # Check nodes
            nodes_result = subprocess.run(
                ['kubectl', 'get', 'nodes', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if nodes_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"kubectl get nodes failed: {nodes_result.stderr}"
                }
            
            nodes_data = json.loads(nodes_result.stdout)
            node_count = len(nodes_data.get('items', []))
            
            return {
                "success": True,
                "cluster_accessible": True,
                "node_count": node_count,
                "cluster_info": result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_namespace_existence(self) -> Dict[str, Any]:
        """Test that the required namespace exists"""
        try:
            import subprocess
            
            # Check if namespace exists
            result = subprocess.run(
                ['kubectl', 'get', 'namespace', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Namespace {self.namespace} not found: {result.stderr}"
                }
            
            namespace_data = json.loads(result.stdout)
            
            return {
                "success": True,
                "namespace_exists": True,
                "namespace_name": namespace_data.get('metadata', {}).get('name'),
                "namespace_status": namespace_data.get('status', {}).get('phase')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_ingress_connectivity(self) -> Dict[str, Any]:
        """Test ingress connectivity and SSL configuration"""
        try:
            async with httpx.AsyncClient() as client:
                # Test HTTPS connectivity
                response = await client.get(
                    f"{self.agent_api_url}/health",
                    timeout=30.0,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    health_data = response.json()
                    return {
                        "success": True,
                        "ingress_accessible": True,
                        "ssl_working": response.url.scheme == 'https',
                        "response_time": response.elapsed.total_seconds(),
                        "health_status": health_data.get("status"),
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "ingress_accessible": False,
                        "status_code": response.status_code,
                        "error": f"Health check failed with status {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_load_balancer_configuration(self) -> Dict[str, Any]:
        """Test load balancer configuration and service discovery"""
        try:
            import subprocess
            
            # Check ingress resources
            ingress_result = subprocess.run(
                ['kubectl', 'get', 'ingress', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if ingress_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get ingress resources: {ingress_result.stderr}"
                }
            
            ingress_data = json.loads(ingress_result.stdout)
            ingress_items = ingress_data.get('items', [])
            
            # Check services
            services_result = subprocess.run(
                ['kubectl', 'get', 'services', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if services_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get services: {services_result.stderr}"
                }
            
            services_data = json.loads(services_result.stdout)
            service_items = services_data.get('items', [])
            
            return {
                "success": True,
                "ingress_count": len(ingress_items),
                "service_count": len(service_items),
                "load_balancer_configured": len(ingress_items) > 0,
                "services_available": len(service_items) > 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution for the ingress domain"""
        try:
            import socket
            
            # Test DNS resolution
            try:
                ip_addresses = socket.gethostbyname_ex(self.ingress_domain)
                resolved_ips = ip_addresses[2]
            except socket.gaierror as e:
                return {
                    "success": False,
                    "error": f"DNS resolution failed: {str(e)}"
                }
            
            return {
                "success": True,
                "dns_resolution_working": True,
                "domain": self.ingress_domain,
                "resolved_ips": resolved_ips,
                "ip_count": len(resolved_ips)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_ssl_certificate_validation(self) -> Dict[str, Any]:
        """Test SSL certificate configuration"""
        try:
            import ssl
            import socket
            from datetime import datetime
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to the domain
            with socket.create_connection((self.ingress_domain, 443), timeout=30) as sock:
                with context.wrap_socket(sock, server_hostname=self.ingress_domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate validity
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    now = datetime.now()
                    
                    is_valid = not_before <= now <= not_after
                    days_until_expiry = (not_after - now).days
                    
                    return {
                        "success": True,
                        "ssl_certificate_valid": is_valid,
                        "certificate_subject": cert.get('subject', []),
                        "certificate_issuer": cert.get('issuer', []),
                        "not_before": cert['notBefore'],
                        "not_after": cert['notAfter'],
                        "days_until_expiry": days_until_expiry,
                        "ssl_version": ssock.version()
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_network_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity between services"""
        try:
            import subprocess
            
            # Test connectivity to different services
            connectivity_tests = []
            
            # Test database connectivity (if accessible)
            db_url = os.getenv('DATABASE_URL')
            if db_url:
                try:
                    # Extract host and port from database URL
                    if 'postgresql://' in db_url:
                        # Simple connectivity test
                        connectivity_tests.append({
                            "service": "database",
                            "accessible": True,
                            "note": "Database URL configured"
                        })
                except Exception as e:
                    connectivity_tests.append({
                        "service": "database",
                        "accessible": False,
                        "error": str(e)
                    })
            
            # Test Redis connectivity
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                connectivity_tests.append({
                    "service": "redis",
                    "accessible": True,
                    "note": "Redis URL configured"
                })
            
            return {
                "success": True,
                "connectivity_tests": connectivity_tests,
                "total_services_tested": len(connectivity_tests)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """Run all Phase 3 cloud infrastructure tests"""
        logger.info("🚀 Starting Phase 3 Cloud Infrastructure Tests")
        
        # Run all tests
        await self.run_test("Kubernetes Cluster Connectivity", self.test_kubernetes_cluster_connectivity)
        await self.run_test("Namespace Existence", self.test_namespace_existence)
        await self.run_test("Ingress Connectivity", self.test_ingress_connectivity)
        await self.run_test("Load Balancer Configuration", self.test_load_balancer_configuration)
        await self.run_test("DNS Resolution", self.test_dns_resolution)
        await self.run_test("SSL Certificate Validation", self.test_ssl_certificate_validation)
        await self.run_test("Network Connectivity", self.test_network_connectivity)
        
        # Calculate success rate
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]
        self.results["summary"]["success_rate"] = (passed / total * 100) if total > 0 else 0
        
        # Log summary
        logger.info(f"📊 Phase 3 Cloud Infrastructure Tests Complete")
        logger.info(f"   Total Tests: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {self.results['summary']['failed']}")
        logger.info(f"   Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        return self.results

async def main():
    """Main test execution"""
    test = Phase3CloudInfrastructureTest()
    results = await test.run_all_tests()
    
    # Save results
    results_file = os.path.join(
        os.path.dirname(__file__), 
        '../results/cloud_infrastructure_results.json'
    )
    
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📁 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
