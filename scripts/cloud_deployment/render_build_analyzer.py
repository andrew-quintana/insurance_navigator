#!/usr/bin/env python3
"""
Render Build Analyzer - Advanced build validation and deployment log analysis

This script provides comprehensive build validation for Render services including:
- Build status monitoring
- Deployment log analysis
- Build performance metrics
- Error detection and debugging
"""

import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime
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

class RenderBuildAnalyzer:
    """Advanced build analyzer for Render services"""
    
    def __init__(self):
        self.session = None
        self.render_api_key = os.getenv('RENDER_CLI_API_KEY')
        self.services = {
            'api': {
                'name': 'insurance-navigator-api',
                'url': '***REMOVED***',
                'type': 'web'
            },
            'worker': {
                'name': 'insurance-navigator-worker', 
                'url': 'https://insurance-navigator-worker.onrender.com',
                'type': 'worker'
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'Authorization': f'Bearer {self.render_api_key}' if self.render_api_key else '',
                'Accept': 'application/json',
                'User-Agent': 'InsuranceNavigator-BuildAnalyzer/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_all_builds(self) -> Dict[str, Any]:
        """Analyze build status for all services"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {}
        }
        
        for service_id, service_info in self.services.items():
            logger.info(f"Analyzing build for {service_info['name']}")
            
            service_result = await self._analyze_service_build(service_id, service_info)
            results['services'][service_id] = service_result
        
        # Generate summary
        results['summary'] = self._generate_build_summary(results['services'])
        
        return results
    
    async def _analyze_service_build(self, service_id: str, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze build for a specific service"""
        result = {
            'service_name': service_info['name'],
            'service_type': service_info['type'],
            'service_url': service_info['url'],
            'build_status': 'unknown',
            'deployment_status': 'unknown',
            'health_status': 'unknown',
            'performance_metrics': {},
            'logs_analysis': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # 1. Check service health
            health_result = await self._check_service_health(service_info['url'])
            result.update(health_result)
            
            # 2. Analyze deployment logs (if API key available)
            if self.render_api_key:
                logs_result = await self._analyze_deployment_logs(service_info['name'])
                result['logs_analysis'] = logs_result
            else:
                result['warnings'].append("Render API key not available - cannot access deployment logs")
            
            # 3. Performance analysis
            perf_result = await self._analyze_performance(service_info['url'])
            result['performance_metrics'] = perf_result
            
            # 4. Build quality assessment
            build_quality = self._assess_build_quality(result)
            result['build_quality'] = build_quality
            
        except Exception as e:
            logger.error(f"Error analyzing {service_info['name']}: {str(e)}")
            result['errors'].append(f"Analysis error: {str(e)}")
            result['build_status'] = 'error'
        
        return result
    
    async def _check_service_health(self, service_url: str) -> Dict[str, Any]:
        """Check service health and deployment status"""
        result = {
            'health_status': 'unknown',
            'deployment_status': 'unknown',
            'response_time': 0,
            'status_code': 0
        }
        
        try:
            start_time = time.time()
            
            # Try health endpoint first
            health_url = f"{service_url}/health"
            async with self.session.get(health_url, timeout=30) as response:
                response_time = time.time() - start_time
                
                result['response_time'] = response_time
                result['status_code'] = response.status
                
                if response.status == 200:
                    result['health_status'] = 'healthy'
                    result['deployment_status'] = 'deployed'
                    
                    try:
                        health_data = await response.json()
                        result['health_data'] = health_data
                    except:
                        result['health_data'] = await response.text()
                        
                elif response.status == 404:
                    # Try root endpoint for worker services
                    async with self.session.get(service_url, timeout=30) as root_response:
                        if root_response.status in [200, 404]:
                            result['health_status'] = 'deployed'
                            result['deployment_status'] = 'deployed'
                            result['note'] = 'Service deployed (404 expected for background workers)'
                        else:
                            result['health_status'] = 'error'
                            result['deployment_status'] = 'failed'
                            result['error'] = f"Unexpected status: {root_response.status}"
                else:
                    result['health_status'] = 'error'
                    result['deployment_status'] = 'failed'
                    result['error'] = f"Health check failed: {response.status}"
        
        except Exception as e:
            result['health_status'] = 'error'
            result['deployment_status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    async def _analyze_deployment_logs(self, service_name: str) -> Dict[str, Any]:
        """Analyze deployment logs from Render API"""
        result = {
            'log_analysis_available': False,
            'build_logs': {},
            'deployment_logs': {},
            'errors_found': [],
            'warnings_found': []
        }
        
        if not self.render_api_key:
            result['error'] = 'Render API key not available'
            return result
        
        try:
            # Get service information
            service_url = f"https://api.render.com/v1/services"
            async with self.session.get(service_url) as response:
                if response.status == 200:
                    services_data = await response.json()
                    
                    # Find our service
                    target_service = None
                    for service in services_data:
                        if service.get('name') == service_name:
                            target_service = service
                            break
                    
                    if target_service:
                        result['log_analysis_available'] = True
                        result['service_id'] = target_service.get('id')
                        result['service_status'] = target_service.get('serviceDetails', {}).get('buildStatus')
                        
                        # Get deployment logs
                        logs_url = f"https://api.render.com/v1/services/{target_service['id']}/deploys"
                        async with self.session.get(logs_url) as logs_response:
                            if logs_response.status == 200:
                                deploys_data = await logs_response.json()
                                result['deployment_logs'] = self._analyze_deploy_logs(deploys_data)
                            else:
                                result['error'] = f"Failed to get deployment logs: {logs_response.status}"
                    else:
                        result['error'] = f"Service {service_name} not found in Render"
                else:
                    result['error'] = f"Failed to get services: {response.status}"
        
        except Exception as e:
            result['error'] = f"Log analysis error: {str(e)}"
        
        return result
    
    def _analyze_deploy_logs(self, deploys_data: List[Dict]) -> Dict[str, Any]:
        """Analyze deployment logs for errors and warnings"""
        analysis = {
            'total_deployments': len(deploys_data),
            'successful_deployments': 0,
            'failed_deployments': 0,
            'recent_deployment': None,
            'common_errors': [],
            'build_times': []
        }
        
        if not deploys_data:
            return analysis
        
        # Analyze recent deployments
        for deploy in deploys_data[:5]:  # Last 5 deployments
            status = deploy.get('deploy', {}).get('status')
            
            if status == 'live':
                analysis['successful_deployments'] += 1
            elif status in ['build_failed', 'update_failed']:
                analysis['failed_deployments'] += 1
                analysis['common_errors'].append(f"Deployment failed: {deploy.get('deploy', {}).get('commit', {}).get('message', 'Unknown error')}")
            
            # Track build times
            if 'finishedAt' in deploy.get('deploy', {}) and 'createdAt' in deploy.get('deploy', {}):
                start = datetime.fromisoformat(deploy['deploy']['createdAt'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(deploy['deploy']['finishedAt'].replace('Z', '+00:00'))
                build_time = (end - start).total_seconds()
                analysis['build_times'].append(build_time)
        
        # Set recent deployment
        if deploys_data:
            recent = deploys_data[0]
            analysis['recent_deployment'] = {
                'status': recent.get('deploy', {}).get('status'),
                'commit': recent.get('deploy', {}).get('commit', {}).get('message', 'No commit message'),
                'created_at': recent.get('deploy', {}).get('createdAt')
            }
        
        return analysis
    
    async def _analyze_performance(self, service_url: str) -> Dict[str, Any]:
        """Analyze service performance metrics"""
        result = {
            'response_times': [],
            'average_response_time': 0,
            'performance_grade': 'unknown',
            'reliability_score': 0
        }
        
        try:
            # Perform multiple requests to get average response time
            response_times = []
            successful_requests = 0
            
            for i in range(5):  # 5 test requests
                try:
                    start_time = time.time()
                    async with self.session.get(f"{service_url}/health", timeout=30) as response:
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        
                        if response.status == 200:
                            successful_requests += 1
                        
                        # Small delay between requests
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"Request {i+1} failed: {str(e)}")
            
            if response_times:
                result['response_times'] = response_times
                result['average_response_time'] = sum(response_times) / len(response_times)
                result['reliability_score'] = (successful_requests / 5) * 100
                
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
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _assess_build_quality(self, service_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall build quality"""
        quality = {
            'overall_score': 0,
            'grade': 'F',
            'issues': [],
            'recommendations': []
        }
        
        score = 0
        max_score = 100
        
        # Health status (40 points)
        if service_result.get('health_status') == 'healthy':
            score += 40
        elif service_result.get('health_status') == 'deployed':
            score += 30
        else:
            quality['issues'].append("Service health check failed")
            quality['recommendations'].append("Check service configuration and dependencies")
        
        # Performance (30 points)
        perf_grade = service_result.get('performance_metrics', {}).get('performance_grade', 'unknown')
        if perf_grade == 'excellent':
            score += 30
        elif perf_grade == 'good':
            score += 25
        elif perf_grade == 'acceptable':
            score += 15
        else:
            quality['issues'].append("Poor performance detected")
            quality['recommendations'].append("Optimize service performance and response times")
        
        # Reliability (20 points)
        reliability = service_result.get('performance_metrics', {}).get('reliability_score', 0)
        score += (reliability / 100) * 20
        
        if reliability < 80:
            quality['issues'].append("Low reliability score")
            quality['recommendations'].append("Investigate intermittent failures")
        
        # Log analysis (10 points)
        if service_result.get('logs_analysis', {}).get('log_analysis_available'):
            score += 10
        else:
            quality['issues'].append("Deployment logs not accessible")
            quality['recommendations'].append("Configure Render API key for log access")
        
        quality['overall_score'] = score
        
        # Grade assignment
        if score >= 90:
            quality['grade'] = 'A'
        elif score >= 80:
            quality['grade'] = 'B'
        elif score >= 70:
            quality['grade'] = 'C'
        elif score >= 60:
            quality['grade'] = 'D'
        else:
            quality['grade'] = 'F'
        
        return quality
    
    def _generate_build_summary(self, services_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall build summary"""
        summary = {
            'total_services': len(services_results),
            'healthy_services': 0,
            'failed_services': 0,
            'overall_grade': 'F',
            'critical_issues': [],
            'recommendations': []
        }
        
        total_score = 0
        service_count = 0
        
        for service_id, service_result in services_results.items():
            if service_result.get('health_status') == 'healthy':
                summary['healthy_services'] += 1
            elif service_result.get('health_status') == 'error':
                summary['failed_services'] += 1
                summary['critical_issues'].append(f"{service_result['service_name']}: {service_result.get('error', 'Unknown error')}")
            
            # Add to overall score
            build_quality = service_result.get('build_quality', {})
            if build_quality:
                total_score += build_quality.get('overall_score', 0)
                service_count += 1
                
                # Collect recommendations
                recommendations = build_quality.get('recommendations', [])
                summary['recommendations'].extend(recommendations)
        
        # Calculate overall grade
        if service_count > 0:
            avg_score = total_score / service_count
            if avg_score >= 90:
                summary['overall_grade'] = 'A'
            elif avg_score >= 80:
                summary['overall_grade'] = 'B'
            elif avg_score >= 70:
                summary['overall_grade'] = 'C'
            elif avg_score >= 60:
                summary['overall_grade'] = 'D'
            else:
                summary['overall_grade'] = 'F'
        
        return summary

async def main():
    """Main function for build analysis"""
    print("🔨 Starting Render Build Analysis")
    print("=" * 50)
    
    async with RenderBuildAnalyzer() as analyzer:
        results = await analyzer.analyze_all_builds()
        
        # Print results
        print(f"\n📊 BUILD ANALYSIS RESULTS")
        print(f"Overall Grade: {results['summary']['overall_grade']}")
        print(f"Healthy Services: {results['summary']['healthy_services']}/{results['summary']['total_services']}")
        
        for service_id, service_result in results['services'].items():
            print(f"\n🔧 {service_result['service_name'].upper()}")
            print(f"  Health Status: {service_result['health_status']}")
            print(f"  Deployment Status: {service_result['deployment_status']}")
            
            if service_result.get('performance_metrics'):
                perf = service_result['performance_metrics']
                print(f"  Performance: {perf.get('performance_grade', 'unknown')}")
                print(f"  Avg Response Time: {perf.get('average_response_time', 0):.2f}s")
                print(f"  Reliability: {perf.get('reliability_score', 0):.1f}%")
            
            if service_result.get('build_quality'):
                quality = service_result['build_quality']
                print(f"  Build Quality: {quality['grade']} ({quality['overall_score']:.1f}/100)")
                
                if quality.get('issues'):
                    print(f"  Issues: {', '.join(quality['issues'])}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scripts/cloud_deployment/render_build_analysis_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Print recommendations
        if results['summary']['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(set(results['summary']['recommendations']), 1):
                print(f"  {i}. {rec}")
        
        if results['summary']['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(results['summary']['critical_issues'], 1):
                print(f"  {i}. {issue}")

if __name__ == "__main__":
    asyncio.run(main())
