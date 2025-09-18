#!/usr/bin/env python3
"""
Phase 3 - Service Deployment Test

This test validates that all agent services are properly deployed in the cloud
environment including pods, services, ingress, and configuration.
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

class Phase3ServiceDeploymentTest:
    def __init__(self):
        self.results = {
            "test_name": "Phase 3 Service Deployment Test",
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
        self.namespace = os.getenv('NAMESPACE', 'agents-production')
        self.agent_api_url = os.getenv('AGENT_API_URL', 'https://agents-api.yourdomain.com')
        self.rag_service_url = os.getenv('RAG_SERVICE_URL', 'https://rag-service.yourdomain.com')
        self.chat_service_url = os.getenv('CHAT_SERVICE_URL', 'https://chat-service.yourdomain.com')
        
        # Expected services
        self.expected_services = [
            'agent-api-service',
            'rag-service',
            'chat-service'
        ]
        
        # Expected deployments
        self.expected_deployments = [
            'agent-api-deployment',
            'rag-service-deployment',
            'chat-service-deployment'
        ]
    
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
    
    async def test_deployments_exist(self) -> Dict[str, Any]:
        """Test that all expected deployments exist and are running"""
        try:
            import subprocess
            
            # Get all deployments in the namespace
            result = subprocess.run(
                ['kubectl', 'get', 'deployments', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get deployments: {result.stderr}"
                }
            
            deployments_data = json.loads(result.stdout)
            deployments = deployments_data.get('items', [])
            
            # Check each expected deployment
            deployment_status = {}
            for expected_deployment in self.expected_deployments:
                found = False
                for deployment in deployments:
                    if deployment['metadata']['name'] == expected_deployment:
                        found = True
                        status = deployment['status']
                        ready_replicas = status.get('readyReplicas', 0)
                        desired_replicas = status.get('replicas', 0)
                        
                        deployment_status[expected_deployment] = {
                            "exists": True,
                            "ready_replicas": ready_replicas,
                            "desired_replicas": desired_replicas,
                            "is_ready": ready_replicas == desired_replicas and desired_replicas > 0
                        }
                        break
                
                if not found:
                    deployment_status[expected_deployment] = {
                        "exists": False,
                        "ready_replicas": 0,
                        "desired_replicas": 0,
                        "is_ready": False
                    }
            
            # Calculate overall status
            total_deployments = len(self.expected_deployments)
            ready_deployments = sum(1 for status in deployment_status.values() if status.get('is_ready', False))
            
            return {
                "success": ready_deployments == total_deployments,
                "total_deployments": total_deployments,
                "ready_deployments": ready_deployments,
                "deployment_status": deployment_status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_services_exist(self) -> Dict[str, Any]:
        """Test that all expected services exist and are accessible"""
        try:
            import subprocess
            
            # Get all services in the namespace
            result = subprocess.run(
                ['kubectl', 'get', 'services', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get services: {result.stderr}"
                }
            
            services_data = json.loads(result.stdout)
            services = services_data.get('items', [])
            
            # Check each expected service
            service_status = {}
            for expected_service in self.expected_services:
                found = False
                for service in services:
                    if expected_service in service['metadata']['name']:
                        found = True
                        spec = service['spec']
                        status = service['status']
                        
                        service_status[expected_service] = {
                            "exists": True,
                            "type": spec.get('type', 'Unknown'),
                            "cluster_ip": spec.get('clusterIP', 'None'),
                            "ports": spec.get('ports', []),
                            "selector": spec.get('selector', {})
                        }
                        break
                
                if not found:
                    service_status[expected_service] = {
                        "exists": False,
                        "type": "Unknown",
                        "cluster_ip": "None",
                        "ports": [],
                        "selector": {}
                    }
            
            # Calculate overall status
            total_services = len(self.expected_services)
            existing_services = sum(1 for status in service_status.values() if status.get('exists', False))
            
            return {
                "success": existing_services == total_services,
                "total_services": total_services,
                "existing_services": existing_services,
                "service_status": service_status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_pods_health(self) -> Dict[str, Any]:
        """Test that all pods are healthy and running"""
        try:
            import subprocess
            
            # Get all pods in the namespace
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get pods: {result.stderr}"
                }
            
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            
            # Analyze pod health
            pod_status = {}
            healthy_pods = 0
            total_pods = len(pods)
            
            for pod in pods:
                pod_name = pod['metadata']['name']
                status = pod['status']
                phase = status.get('phase', 'Unknown')
                conditions = status.get('conditions', [])
                
                # Check if pod is ready
                is_ready = False
                for condition in conditions:
                    if condition['type'] == 'Ready' and condition['status'] == 'True':
                        is_ready = True
                        break
                
                pod_status[pod_name] = {
                    "phase": phase,
                    "is_ready": is_ready,
                    "restart_count": sum(container.get('restartCount', 0) for container in status.get('containerStatuses', [])),
                    "conditions": conditions
                }
                
                if phase == 'Running' and is_ready:
                    healthy_pods += 1
            
            return {
                "success": healthy_pods == total_pods and total_pods > 0,
                "total_pods": total_pods,
                "healthy_pods": healthy_pods,
                "pod_status": pod_status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_ingress_configuration(self) -> Dict[str, Any]:
        """Test ingress configuration and routing"""
        try:
            import subprocess
            
            # Get ingress resources
            result = subprocess.run(
                ['kubectl', 'get', 'ingress', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get ingress: {result.stderr}"
                }
            
            ingress_data = json.loads(result.stdout)
            ingress_items = ingress_data.get('items', [])
            
            if not ingress_items:
                return {
                    "success": False,
                    "error": "No ingress resources found"
                }
            
            # Analyze ingress configuration
            ingress_status = []
            for ingress in ingress_items:
                metadata = ingress['metadata']
                spec = ingress['spec']
                status = ingress.get('status', {})
                
                ingress_info = {
                    "name": metadata['name'],
                    "hosts": [rule['host'] for rule in spec.get('rules', [])],
                    "tls": spec.get('tls', []),
                    "load_balancer_ips": [lb.get('ip', '') for lb in status.get('loadBalancer', {}).get('ingress', [])],
                    "rules_count": len(spec.get('rules', []))
                }
                ingress_status.append(ingress_info)
            
            return {
                "success": len(ingress_status) > 0,
                "ingress_count": len(ingress_status),
                "ingress_status": ingress_status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_configmaps_and_secrets(self) -> Dict[str, Any]:
        """Test that required configmaps and secrets exist"""
        try:
            import subprocess
            
            # Get configmaps
            configmaps_result = subprocess.run(
                ['kubectl', 'get', 'configmaps', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Get secrets
            secrets_result = subprocess.run(
                ['kubectl', 'get', 'secrets', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            configmaps_data = json.loads(configmaps_result.stdout) if configmaps_result.returncode == 0 else {"items": []}
            secrets_data = json.loads(secrets_result.stdout) if secrets_result.returncode == 0 else {"items": []}
            
            configmaps = configmaps_data.get('items', [])
            secrets = secrets_data.get('items', [])
            
            return {
                "success": True,
                "configmaps_count": len(configmaps),
                "secrets_count": len(secrets),
                "configmaps": [cm['metadata']['name'] for cm in configmaps],
                "secrets": [secret['metadata']['name'] for secret in secrets]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_service_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to deployed services"""
        try:
            connectivity_results = []
            
            # Test agent API service
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.agent_api_url}/health", timeout=10.0)
                    connectivity_results.append({
                        "service": "agent-api",
                        "url": self.agent_api_url,
                        "accessible": response.status_code == 200,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    })
            except Exception as e:
                connectivity_results.append({
                    "service": "agent-api",
                    "url": self.agent_api_url,
                    "accessible": False,
                    "error": str(e)
                })
            
            # Test RAG service (if accessible)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.rag_service_url}/health", timeout=10.0)
                    connectivity_results.append({
                        "service": "rag-service",
                        "url": self.rag_service_url,
                        "accessible": response.status_code == 200,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    })
            except Exception as e:
                connectivity_results.append({
                    "service": "rag-service",
                    "url": self.rag_service_url,
                    "accessible": False,
                    "error": str(e)
                })
            
            # Test chat service (if accessible)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.chat_service_url}/health", timeout=10.0)
                    connectivity_results.append({
                        "service": "chat-service",
                        "url": self.chat_service_url,
                        "accessible": response.status_code == 200,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    })
            except Exception as e:
                connectivity_results.append({
                    "service": "chat-service",
                    "url": self.chat_service_url,
                    "accessible": False,
                    "error": str(e)
                })
            
            accessible_services = sum(1 for result in connectivity_results if result.get('accessible', False))
            
            return {
                "success": accessible_services > 0,
                "accessible_services": accessible_services,
                "total_services_tested": len(connectivity_results),
                "connectivity_results": connectivity_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_auto_scaling_configuration(self) -> Dict[str, Any]:
        """Test horizontal pod autoscaler configuration"""
        try:
            import subprocess
            
            # Get HPA resources
            result = subprocess.run(
                ['kubectl', 'get', 'hpa', '-n', self.namespace, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get HPA resources: {result.stderr}"
                }
            
            hpa_data = json.loads(result.stdout)
            hpa_items = hpa_data.get('items', [])
            
            # Analyze HPA configuration
            hpa_status = []
            for hpa in hpa_items:
                metadata = hpa['metadata']
                spec = hpa['spec']
                status = hpa.get('status', {})
                
                hpa_info = {
                    "name": metadata['name'],
                    "target_deployment": spec.get('scaleTargetRef', {}).get('name', 'Unknown'),
                    "min_replicas": spec.get('minReplicas', 1),
                    "max_replicas": spec.get('maxReplicas', 1),
                    "current_replicas": status.get('currentReplicas', 0),
                    "desired_replicas": status.get('desiredReplicas', 0),
                    "metrics": spec.get('metrics', [])
                }
                hpa_status.append(hpa_info)
            
            return {
                "success": len(hpa_status) > 0,
                "hpa_count": len(hpa_status),
                "hpa_status": hpa_status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """Run all Phase 3 service deployment tests"""
        logger.info("🚀 Starting Phase 3 Service Deployment Tests")
        
        # Run all tests
        await self.run_test("Deployments Exist", self.test_deployments_exist)
        await self.run_test("Services Exist", self.test_services_exist)
        await self.run_test("Pods Health", self.test_pods_health)
        await self.run_test("Ingress Configuration", self.test_ingress_configuration)
        await self.run_test("ConfigMaps and Secrets", self.test_configmaps_and_secrets)
        await self.run_test("Service Connectivity", self.test_service_connectivity)
        await self.run_test("Auto Scaling Configuration", self.test_auto_scaling_configuration)
        
        # Calculate success rate
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]
        self.results["summary"]["success_rate"] = (passed / total * 100) if total > 0 else 0
        
        # Log summary
        logger.info(f"📊 Phase 3 Service Deployment Tests Complete")
        logger.info(f"   Total Tests: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {self.results['summary']['failed']}")
        logger.info(f"   Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        return self.results

async def main():
    """Main test execution"""
    test = Phase3ServiceDeploymentTest()
    results = await test.run_all_tests()
    
    # Save results
    results_file = os.path.join(
        os.path.dirname(__file__), 
        '../results/service_deployment_results.json'
    )
    
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📁 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
