#!/usr/bin/env python3
"""
Deployment Issues Debugger - Comprehensive analysis of Render deployment problems

This script provides detailed debugging for deployment issues including:
- Service status analysis
- Build log analysis
- Performance monitoring
- Configuration validation
"""

import asyncio
import aiohttp
import json
import os
import time
import subprocess
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

class DeploymentDebugger:
    """Comprehensive deployment debugger for Render services"""
    
    def __init__(self):
        self.session = None
        self.render_api_key = os.getenv('RENDER_CLI_API_KEY')
        self.services = {
            'api': {
                'name': 'insurance-navigator-api',
                'id': 'srv-d0v2nqvdiees73cejf0g',
                'url': '***REMOVED***',
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
                'User-Agent': 'InsuranceNavigator-DeploymentDebugger/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def debug_all_issues(self) -> Dict[str, Any]:
        """Debug all deployment issues"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {},
            'recommendations': []
        }
        
        for service_id, service_info in self.services.items():
            logger.info(f"Debugging {service_info['name']}")
            
            service_result = await self._debug_service(service_id, service_info)
            results['services'][service_id] = service_result
        
        # Generate summary and recommendations
        results['summary'] = self._generate_debug_summary(results['services'])
        results['recommendations'] = self._generate_recommendations(results['services'])
        
        return results
    
    async def _debug_service(self, service_id: str, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Debug a specific service"""
        result = {
            'service_name': service_info['name'],
            'service_id': service_info['id'],
            'service_type': service_info['type'],
            'service_url': service_info['url'],
            'current_status': 'unknown',
            'health_check': {},
            'deployment_status': {},
            'build_analysis': {},
            'performance_metrics': {},
            'configuration_issues': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            # 1. Check current service status
            status_result = await self._check_service_status(service_info)
            result['current_status'] = status_result.get('status', 'unknown')
            result['health_check'] = status_result
            
            # 2. Analyze deployment status
            deploy_result = await self._analyze_deployment_status(service_info)
            result['deployment_status'] = deploy_result
            
            # 3. Build analysis
            build_result = await self._analyze_build_issues(service_info)
            result['build_analysis'] = build_result
            
            # 4. Performance analysis
            perf_result = await self._analyze_performance(service_info)
            result['performance_metrics'] = perf_result
            
            # 5. Configuration validation
            config_result = await self._validate_configuration(service_info)
            result['configuration_issues'] = config_result
            
        except Exception as e:
            logger.error(f"Error debugging {service_info['name']}: {str(e)}")
            result['errors'].append(f"Debug error: {str(e)}")
        
        return result
    
    async def _check_service_status(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Check current service status and health"""
        result = {
            'status': 'unknown',
            'health_response': None,
            'response_time': 0,
            'status_code': 0,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Try health endpoint
            health_url = f"{service_info['url']}/health"
            async with self.session.get(health_url, timeout=30) as response:
                response_time = time.time() - start_time
                
                result['response_time'] = response_time
                result['status_code'] = response.status
                
                if response.status == 200:
                    result['status'] = 'healthy'
                    try:
                        result['health_response'] = await response.json()
                    except:
                        result['health_response'] = await response.text()
                elif response.status == 404:
                    # Try root endpoint for worker services
                    async with self.session.get(service_info['url'], timeout=30) as root_response:
                        if root_response.status in [200, 404]:
                            result['status'] = 'deployed'
                            result['note'] = 'Service deployed (404 expected for background workers)'
                        else:
                            result['status'] = 'error'
                            result['error'] = f"Unexpected status: {root_response.status}"
                else:
                    result['status'] = 'error'
                    result['error'] = f"Health check failed: {response.status}"
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    async def _analyze_deployment_status(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze deployment status and recent deployments"""
        result = {
            'deployment_analysis_available': False,
            'recent_deployments': [],
            'current_deployment': None,
            'deployment_issues': []
        }
        
        if not self.render_api_key:
            result['error'] = 'Render API key not available'
            return result
        
        try:
            # Get recent deployments
            deploys_url = f"https://api.render.com/v1/services/{service_info['id']}/deploys"
            async with self.session.get(deploys_url) as response:
                if response.status == 200:
                    deploys_data = await response.json()
                    result['deployment_analysis_available'] = True
                    
                    # Analyze recent deployments
                    for deploy in deploys_data[:5]:  # Last 5 deployments
                        deploy_info = {
                            'id': deploy.get('deploy', {}).get('id'),
                            'status': deploy.get('deploy', {}).get('status'),
                            'created_at': deploy.get('deploy', {}).get('createdAt'),
                            'finished_at': deploy.get('deploy', {}).get('finishedAt'),
                            'commit_message': deploy.get('deploy', {}).get('commit', {}).get('message', 'No commit message')
                        }
                        result['recent_deployments'].append(deploy_info)
                        
                        # Check for issues
                        if deploy_info['status'] in ['build_failed', 'update_failed']:
                            result['deployment_issues'].append(f"Deployment {deploy_info['id']} failed: {deploy_info['commit_message']}")
                        elif deploy_info['status'] == 'build_in_progress':
                            # Check if it's been running too long
                            if deploy_info['created_at']:
                                created_time = datetime.fromisoformat(deploy_info['created_at'].replace('Z', '+00:00'))
                                if datetime.now(created_time.tzinfo) - created_time > timedelta(hours=1):
                                    result['deployment_issues'].append(f"Deployment {deploy_info['id']} has been running for over 1 hour")
                    
                    # Set current deployment
                    if deploys_data:
                        current = deploys_data[0]
                        result['current_deployment'] = {
                            'id': current.get('deploy', {}).get('id'),
                            'status': current.get('deploy', {}).get('status'),
                            'created_at': current.get('deploy', {}).get('createdAt'),
                            'commit_message': current.get('deploy', {}).get('commit', {}).get('message', 'No commit message')
                        }
                else:
                    result['error'] = f"Failed to get deployments: {response.status}"
        
        except Exception as e:
            result['error'] = f"Deployment analysis error: {str(e)}"
        
        return result
    
    async def _analyze_build_issues(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze build issues and potential causes"""
        result = {
            'build_analysis_available': False,
            'build_issues': [],
            'potential_causes': [],
            'suggested_fixes': []
        }
        
        # Get deployment status
        deploy_result = await self._analyze_deployment_status(service_info)
        
        if deploy_result.get('current_deployment'):
            current = deploy_result['current_deployment']
            result['build_analysis_available'] = True
            
            if current['status'] == 'build_failed':
                result['build_issues'].append("Build process failed")
                result['potential_causes'].extend([
                    "Docker build errors",
                    "Missing dependencies",
                    "Environment variable issues",
                    "Dockerfile syntax errors",
                    "Resource constraints"
                ])
                result['suggested_fixes'].extend([
                    "Check Dockerfile syntax",
                    "Verify all dependencies are available",
                    "Check environment variable configuration",
                    "Review build logs for specific errors",
                    "Consider increasing build resources"
                ])
            
            elif current['status'] == 'build_in_progress':
                # Check if it's been running too long
                if current['created_at']:
                    created_time = datetime.fromisoformat(current['created_at'].replace('Z', '+00:00'))
                    duration = datetime.now(created_time.tzinfo) - created_time
                    
                    if duration > timedelta(hours=1):
                        result['build_issues'].append(f"Build running for {duration}")
                        result['potential_causes'].extend([
                            "Large dependency installation",
                            "Docker layer caching issues",
                            "Resource constraints",
                            "Network connectivity issues",
                            "Infinite build loop"
                        ])
                        result['suggested_fixes'].extend([
                            "Check build logs for progress",
                            "Consider optimizing Dockerfile",
                            "Check for infinite loops in build process",
                            "Verify network connectivity",
                            "Consider canceling and retrying"
                        ])
        
        return result
    
    async def _analyze_performance(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze service performance"""
        result = {
            'performance_analysis_available': False,
            'response_times': [],
            'average_response_time': 0,
            'performance_grade': 'unknown',
            'performance_issues': []
        }
        
        try:
            # Perform multiple requests to get average response time
            response_times = []
            successful_requests = 0
            
            for i in range(3):  # 3 test requests
                try:
                    start_time = time.time()
                    async with self.session.get(f"{service_info['url']}/health", timeout=30) as response:
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        
                        if response.status == 200:
                            successful_requests += 1
                        
                        # Small delay between requests
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"Request {i+1} failed: {str(e)}")
            
            if response_times:
                result['performance_analysis_available'] = True
                result['response_times'] = response_times
                result['average_response_time'] = sum(response_times) / len(response_times)
                
                # Performance grading
                avg_time = result['average_response_time']
                if avg_time < 1.0:
                    result['performance_grade'] = 'excellent'
                elif avg_time < 2.0:
                    result['performance_grade'] = 'good'
                elif avg_time < 5.0:
                    result['performance_grade'] = 'acceptable'
                else:
                    result['performance_grade'] = 'poor'
                    result['performance_issues'].append(f"Slow response time: {avg_time:.2f}s")
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    async def _validate_configuration(self, service_info: Dict[str, str]) -> List[str]:
        """Validate service configuration"""
        issues = []
        
        # Check health response for configuration issues
        try:
            async with self.session.get(f"{service_info['url']}/health", timeout=30) as response:
                if response.status == 200:
                    health_data = await response.json()
                    
                    # Check for degraded services
                    if health_data.get('status') == 'degraded':
                        services = health_data.get('services', {})
                        for service_name, service_status in services.items():
                            if service_status == 'not_configured':
                                issues.append(f"{service_name} service not configured")
                            elif service_status == 'error':
                                issues.append(f"{service_name} service has errors")
        
        except Exception as e:
            issues.append(f"Configuration validation error: {str(e)}")
        
        return issues
    
    def _generate_debug_summary(self, services_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall debug summary"""
        summary = {
            'total_services': len(services_results),
            'healthy_services': 0,
            'degraded_services': 0,
            'failed_services': 0,
            'services_with_issues': 0,
            'critical_issues': [],
            'build_issues': [],
            'performance_issues': []
        }
        
        for service_id, service_result in services_results.items():
            status = service_result.get('current_status', 'unknown')
            
            if status == 'healthy':
                summary['healthy_services'] += 1
            elif status == 'deployed':
                summary['degraded_services'] += 1
            elif status == 'error':
                summary['failed_services'] += 1
            
            # Check for issues
            if service_result.get('configuration_issues'):
                summary['services_with_issues'] += 1
                summary['critical_issues'].extend(service_result['configuration_issues'])
            
            if service_result.get('build_analysis', {}).get('build_issues'):
                summary['build_issues'].extend(service_result['build_analysis']['build_issues'])
            
            if service_result.get('performance_metrics', {}).get('performance_issues'):
                summary['performance_issues'].extend(service_result['performance_metrics']['performance_issues'])
        
        return summary
    
    def _generate_recommendations(self, services_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        for service_id, service_result in services_results.items():
            service_name = service_result['service_name']
            
            # Build issues
            build_issues = service_result.get('build_analysis', {}).get('build_issues', [])
            if build_issues:
                recommendations.append(f"{service_name}: Address build issues - {', '.join(build_issues)}")
            
            # Configuration issues
            config_issues = service_result.get('configuration_issues', [])
            if config_issues:
                recommendations.append(f"{service_name}: Fix configuration issues - {', '.join(config_issues)}")
            
            # Performance issues
            perf_issues = service_result.get('performance_metrics', {}).get('performance_issues', [])
            if perf_issues:
                recommendations.append(f"{service_name}: Optimize performance - {', '.join(perf_issues)}")
        
        return list(set(recommendations))  # Remove duplicates

async def main():
    """Main function for deployment debugging"""
    print("🔍 Starting Deployment Issues Debugging")
    print("=" * 60)
    
    async with DeploymentDebugger() as debugger:
        results = await debugger.debug_all_issues()
        
        # Print results
        print(f"\n📊 DEPLOYMENT DEBUG RESULTS")
        print(f"Total Services: {results['summary']['total_services']}")
        print(f"Healthy Services: {results['summary']['healthy_services']}")
        print(f"Degraded Services: {results['summary']['degraded_services']}")
        print(f"Failed Services: {results['summary']['failed_services']}")
        
        for service_id, service_result in results['services'].items():
            print(f"\n🔧 {service_result['service_name'].upper()}")
            print(f"  Current Status: {service_result['current_status']}")
            
            # Health check details
            health = service_result.get('health_check', {})
            if health.get('status_code'):
                print(f"  Health Status Code: {health['status_code']}")
            if health.get('response_time'):
                print(f"  Response Time: {health['response_time']:.2f}s")
            if health.get('error'):
                print(f"  Health Error: {health['error']}")
            
            # Deployment status
            deploy = service_result.get('deployment_status', {})
            if deploy.get('current_deployment'):
                current = deploy['current_deployment']
                print(f"  Current Deployment: {current['status']}")
                print(f"  Deployment ID: {current['id']}")
                if current['created_at']:
                    created_time = datetime.fromisoformat(current['created_at'].replace('Z', '+00:00'))
                    duration = datetime.now(created_time.tzinfo) - created_time
                    print(f"  Deployment Duration: {duration}")
            
            # Build issues
            build = service_result.get('build_analysis', {})
            if build.get('build_issues'):
                print(f"  Build Issues: {', '.join(build['build_issues'])}")
            
            # Configuration issues
            config_issues = service_result.get('configuration_issues', [])
            if config_issues:
                print(f"  Configuration Issues: {', '.join(config_issues)}")
            
            # Performance
            perf = service_result.get('performance_metrics', {})
            if perf.get('performance_grade'):
                print(f"  Performance: {perf['performance_grade']}")
        
        # Print critical issues
        if results['summary']['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(results['summary']['critical_issues'], 1):
                print(f"  {i}. {issue}")
        
        # Print build issues
        if results['summary']['build_issues']:
            print(f"\n🔨 BUILD ISSUES:")
            for i, issue in enumerate(results['summary']['build_issues'], 1):
                print(f"  {i}. {issue}")
        
        # Print recommendations
        if results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scripts/cloud_deployment/deployment_debug_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Debug results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
