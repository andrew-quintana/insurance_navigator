#!/usr/bin/env python3
"""
Improved Deployment Status Checker - Accurate deployment status detection

This script provides accurate deployment status checking with improved querying
to properly detect failed deployments and current service states.
"""

import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging

# Load production environment variables
load_dotenv('.env.production')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedDeploymentChecker:
    """Improved deployment status checker with accurate detection"""
    
    def __init__(self):
        self.session = None
        self.render_api_key = os.getenv('RENDER_CLI_API_KEY')
        self.services = {
            'api': {
                'name': 'insurance-navigator-api',
                'id': 'srv-d0v2nqvdiees73cejf0g',
                'url': 'https://insurance-navigator-api.onrender.com',
                'type': 'web_service'
            },
            'worker': {
                'name': 'insurance_navigator',
                'id': 'srv-d2h5mr8dl3ps73fvvlog', 
                'url': 'https://insurance-navigator-worker.onrender.com',
                'type': 'background_worker'
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'Authorization': f'Bearer {self.render_api_key}' if self.render_api_key else '',
                'Accept': 'application/json',
                'User-Agent': 'InsuranceNavigator-ImprovedChecker/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_all_deployments(self) -> Dict[str, Any]:
        """Check deployment status for all services with improved accuracy"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {},
            'recommendations': []
        }
        
        for service_id, service_info in self.services.items():
            logger.info(f"Checking {service_info['name']}")
            
            service_result = await self._check_service_deployment(service_id, service_info)
            results['services'][service_id] = service_result
        
        # Generate summary and recommendations
        results['summary'] = self._generate_deployment_summary(results['services'])
        results['recommendations'] = self._generate_deployment_recommendations(results['services'])
        
        return results
    
    async def _check_service_deployment(self, service_id: str, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Check deployment status for a specific service with improved accuracy"""
        result = {
            'service_name': service_info['name'],
            'service_id': service_info['id'],
            'service_type': service_info['type'],
            'service_url': service_info['url'],
            'deployment_status': 'unknown',
            'current_deployment': None,
            'recent_deployments': [],
            'service_health': {},
            'configuration_status': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            # 1. Get accurate deployment status from Render API
            deploy_result = await self._get_accurate_deployment_status(service_info)
            result['deployment_status'] = deploy_result.get('status', 'unknown')
            result['current_deployment'] = deploy_result.get('current_deployment')
            result['recent_deployments'] = deploy_result.get('recent_deployments', [])
            
            # 2. Check service health and responsiveness
            health_result = await self._check_service_health(service_info)
            result['service_health'] = health_result
            
            # 3. Check configuration status
            config_result = await self._check_configuration_status(service_info)
            result['configuration_status'] = config_result
            
            # 4. Identify issues and warnings
            issues = self._identify_deployment_issues(deploy_result, health_result, config_result)
            result['issues'] = issues['issues']
            result['warnings'] = issues['warnings']
            
        except Exception as e:
            logger.error(f"Error checking {service_info['name']}: {str(e)}")
            result['issues'].append(f"Check error: {str(e)}")
        
        return result
    
    async def _get_accurate_deployment_status(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Get accurate deployment status from Render API"""
        result = {
            'status': 'unknown',
            'current_deployment': None,
            'recent_deployments': [],
            'api_available': False
        }
        
        if not self.render_api_key:
            result['error'] = 'Render API key not available'
            return result
        
        try:
            # Get recent deployments
            deploys_url = f"https://api.render.com/v1/services/{service_info['id']}/deploys"
            async with self.session.get(deploys_url) as response:
                if response.status == 200:
                    result['api_available'] = True
                    deploys_data = await response.json()
                    
                    # Process recent deployments
                    for deploy in deploys_data[:5]:  # Last 5 deployments
                        deploy_info = {
                            'id': deploy.get('deploy', {}).get('id'),
                            'status': deploy.get('deploy', {}).get('status'),
                            'created_at': deploy.get('deploy', {}).get('createdAt'),
                            'finished_at': deploy.get('deploy', {}).get('finishedAt'),
                            'commit_message': deploy.get('deploy', {}).get('commit', {}).get('message', 'No commit message')
                        }
                        result['recent_deployments'].append(deploy_info)
                    
                    # Determine current deployment status
                    if deploys_data:
                        current = deploys_data[0]
                        current_deploy = {
                            'id': current.get('deploy', {}).get('id'),
                            'status': current.get('deploy', {}).get('status'),
                            'created_at': current.get('deploy', {}).get('createdAt'),
                            'finished_at': current.get('deploy', {}).get('finishedAt'),
                            'commit_message': current.get('deploy', {}).get('commit', {}).get('message', 'No commit message')
                        }
                        result['current_deployment'] = current_deploy
                        result['status'] = current_deploy['status']
                        
                        # Check for long-running deployments
                        if current_deploy['status'] == 'build_in_progress' and current_deploy['created_at']:
                            created_time = datetime.fromisoformat(current_deploy['created_at'].replace('Z', '+00:00'))
                            duration = datetime.now(created_time.tzinfo) - created_time
                            if duration > timedelta(hours=2):
                                result['status'] = 'build_timeout'
                else:
                    result['error'] = f"Failed to get deployments: {response.status}"
        
        except Exception as e:
            result['error'] = f"Deployment status error: {str(e)}"
        
        return result
    
    async def _check_service_health(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Check service health and responsiveness"""
        result = {
            'health_status': 'unknown',
            'response_time': 0,
            'status_code': 0,
            'health_data': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Try health endpoint first
            health_url = f"{service_info['url']}/health"
            async with self.session.get(health_url, timeout=30) as response:
                response_time = time.time() - start_time
                
                result['response_time'] = response_time
                result['status_code'] = response.status
                
                if response.status == 200:
                    result['health_status'] = 'healthy'
                    try:
                        result['health_data'] = await response.json()
                    except:
                        result['health_data'] = await response.text()
                elif response.status == 404:
                    # For worker services, try root endpoint
                    if service_info['type'] == 'background_worker':
                        async with self.session.get(service_info['url'], timeout=30) as root_response:
                            if root_response.status in [200, 404]:
                                result['health_status'] = 'deployed'
                                result['note'] = 'Worker service deployed (404 expected)'
                            else:
                                result['health_status'] = 'error'
                                result['error'] = f"Unexpected status: {root_response.status}"
                    else:
                        result['health_status'] = 'error'
                        result['error'] = f"Health endpoint not found: {response.status}"
                else:
                    result['health_status'] = 'error'
                    result['error'] = f"Health check failed: {response.status}"
        
        except Exception as e:
            result['health_status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    async def _check_configuration_status(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Check configuration status for the service"""
        result = {
            'configuration_available': False,
            'configured_services': {},
            'missing_services': [],
            'degraded_services': []
        }
        
        try:
            # Check health endpoint for configuration details
            health_url = f"{service_info['url']}/health"
            async with self.session.get(health_url, timeout=30) as response:
                if response.status == 200:
                    result['configuration_available'] = True
                    health_data = await response.json()
                    
                    if 'services' in health_data:
                        services = health_data['services']
                        for service_name, service_status in services.items():
                            result['configured_services'][service_name] = service_status
                            
                            if service_status == 'not_configured':
                                result['missing_services'].append(service_name)
                            elif service_status == 'error':
                                result['degraded_services'].append(service_name)
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _identify_deployment_issues(self, deploy_result: Dict, health_result: Dict, config_result: Dict) -> Dict[str, List[str]]:
        """Identify deployment issues and warnings"""
        issues = []
        warnings = []
        
        # Deployment issues
        if deploy_result.get('status') == 'build_failed':
            issues.append("Build process failed")
        elif deploy_result.get('status') == 'build_timeout':
            issues.append("Build process timed out (running too long)")
        elif deploy_result.get('status') == 'build_in_progress':
            # Check if it's been running too long
            current_deploy = deploy_result.get('current_deployment')
            if current_deploy and current_deploy.get('created_at'):
                created_time = datetime.fromisoformat(current_deploy['created_at'].replace('Z', '+00:00'))
                duration = datetime.now(created_time.tzinfo) - created_time
                if duration > timedelta(hours=1):
                    warnings.append(f"Build running for {duration} (may be stuck)")
        
        # Health issues
        if health_result.get('health_status') == 'error':
            issues.append(f"Service health check failed: {health_result.get('error', 'Unknown error')}")
        elif health_result.get('health_status') == 'degraded':
            warnings.append("Service is degraded but functional")
        
        # Configuration issues
        if config_result.get('missing_services'):
            issues.append(f"Missing service configurations: {', '.join(config_result['missing_services'])}")
        if config_result.get('degraded_services'):
            warnings.append(f"Degraded services: {', '.join(config_result['degraded_services'])}")
        
        return {'issues': issues, 'warnings': warnings}
    
    def _generate_deployment_summary(self, services_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deployment summary"""
        summary = {
            'total_services': len(services_results),
            'successful_deployments': 0,
            'failed_deployments': 0,
            'degraded_services': 0,
            'services_with_issues': 0,
            'critical_issues': [],
            'warnings': []
        }
        
        for service_id, service_result in services_results.items():
            status = service_result.get('deployment_status', 'unknown')
            
            if status == 'live':
                summary['successful_deployments'] += 1
            elif status in ['build_failed', 'build_timeout']:
                summary['failed_deployments'] += 1
            elif status == 'degraded':
                summary['degraded_services'] += 1
            
            # Collect issues and warnings
            issues = service_result.get('issues', [])
            warnings = service_result.get('warnings', [])
            
            if issues:
                summary['services_with_issues'] += 1
                summary['critical_issues'].extend(issues)
            
            summary['warnings'].extend(warnings)
        
        return summary
    
    def _generate_deployment_recommendations(self, services_results: Dict[str, Any]) -> List[str]:
        """Generate deployment recommendations"""
        recommendations = []
        
        for service_id, service_result in services_results.items():
            service_name = service_result['service_name']
            
            # Build issues
            if service_result.get('deployment_status') == 'build_failed':
                recommendations.append(f"{service_name}: Fix build failure - check logs and configuration")
            elif service_result.get('deployment_status') == 'build_timeout':
                recommendations.append(f"{service_name}: Build timeout - consider canceling and retrying")
            
            # Configuration issues
            config_issues = service_result.get('configuration_status', {}).get('missing_services', [])
            if config_issues:
                recommendations.append(f"{service_name}: Configure missing services - {', '.join(config_issues)}")
            
            # Health issues
            if service_result.get('service_health', {}).get('health_status') == 'error':
                recommendations.append(f"{service_name}: Fix service health issues")
        
        return list(set(recommendations))  # Remove duplicates

async def main():
    """Main function for improved deployment checking"""
    print("🔍 Starting Improved Deployment Status Check")
    print("=" * 60)
    
    async with ImprovedDeploymentChecker() as checker:
        results = await checker.check_all_deployments()
        
        # Print results
        print(f"\n📊 IMPROVED DEPLOYMENT STATUS")
        print(f"Total Services: {results['summary']['total_services']}")
        print(f"Successful Deployments: {results['summary']['successful_deployments']}")
        print(f"Failed Deployments: {results['summary']['failed_deployments']}")
        print(f"Degraded Services: {results['summary']['degraded_services']}")
        print(f"Services with Issues: {results['summary']['services_with_issues']}")
        
        for service_id, service_result in results['services'].items():
            print(f"\n🔧 {service_result['service_name'].upper()}")
            print(f"  Deployment Status: {service_result['deployment_status']}")
            
            # Current deployment details
            current_deploy = service_result.get('current_deployment')
            if current_deploy:
                print(f"  Current Deployment ID: {current_deploy['id']}")
                print(f"  Deployment Status: {current_deploy['status']}")
                if current_deploy['created_at']:
                    created_time = datetime.fromisoformat(current_deploy['created_at'].replace('Z', '+00:00'))
                    duration = datetime.now(created_time.tzinfo) - created_time
                    print(f"  Deployment Duration: {duration}")
            
            # Health status
            health = service_result.get('service_health', {})
            if health.get('health_status'):
                print(f"  Health Status: {health['health_status']}")
            if health.get('response_time'):
                print(f"  Response Time: {health['response_time']:.2f}s")
            
            # Configuration status
            config = service_result.get('configuration_status', {})
            if config.get('missing_services'):
                print(f"  Missing Services: {', '.join(config['missing_services'])}")
            if config.get('degraded_services'):
                print(f"  Degraded Services: {', '.join(config['degraded_services'])}")
            
            # Issues and warnings
            issues = service_result.get('issues', [])
            warnings = service_result.get('warnings', [])
            
            if issues:
                print(f"  🚨 Issues: {', '.join(issues)}")
            if warnings:
                print(f"  ⚠️  Warnings: {', '.join(warnings)}")
        
        # Print critical issues
        if results['summary']['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(results['summary']['critical_issues'], 1):
                print(f"  {i}. {issue}")
        
        # Print warnings
        if results['summary']['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for i, warning in enumerate(results['summary']['warnings'], 1):
                print(f"  {i}. {warning}")
        
        # Print recommendations
        if results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scripts/cloud_deployment/improved_deployment_check_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
