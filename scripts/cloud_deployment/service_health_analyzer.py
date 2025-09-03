#!/usr/bin/env python3
"""
Service Health Analyzer - Focus on actual service health and logs

This script analyzes the actual health of services by examining:
- Service logs for errors and patterns
- Instance failures and recovery patterns
- Runtime stability issues
- Configuration problems
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

class ServiceHealthAnalyzer:
    """Analyze actual service health and stability"""
    
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
                'User-Agent': 'InsuranceNavigator-HealthAnalyzer/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_service_health(self) -> Dict[str, Any]:
        """Analyze actual service health and stability"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {},
            'recommendations': []
        }
        
        for service_id, service_info in self.services.items():
            logger.info(f"Analyzing health of {service_info['name']}")
            
            service_result = await self._analyze_service_health(service_id, service_info)
            results['services'][service_id] = service_result
        
        # Generate summary and recommendations
        results['summary'] = self._generate_health_summary(results['services'])
        results['recommendations'] = self._generate_health_recommendations(results['services'])
        
        return results
    
    async def _analyze_service_health(self, service_id: str, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze health of a specific service"""
        result = {
            'service_name': service_info['name'],
            'service_id': service_info['id'],
            'service_type': service_info['type'],
            'service_url': service_info['url'],
            'health_status': 'unknown',
            'stability_analysis': {},
            'log_analysis': {},
            'error_patterns': [],
            'configuration_issues': [],
            'stability_score': 0,
            'recommendations': []
        }
        
        try:
            # 1. Analyze service stability and error patterns
            stability_result = await self._analyze_service_stability(service_info)
            result['stability_analysis'] = stability_result
            
            # 2. Analyze service logs for errors
            log_result = await self._analyze_service_logs(service_info)
            result['log_analysis'] = log_result
            
            # 3. Check configuration and health endpoints
            config_result = await self._check_service_configuration(service_info)
            result['configuration_issues'] = config_result
            
            # 4. Calculate stability score
            result['stability_score'] = self._calculate_stability_score(stability_result, log_result, config_result)
            
            # 5. Determine overall health status
            result['health_status'] = self._determine_health_status(result['stability_score'], stability_result, log_result)
            
            # 6. Generate service-specific recommendations
            result['recommendations'] = self._generate_service_recommendations(result)
            
        except Exception as e:
            logger.error(f"Error analyzing {service_info['name']}: {str(e)}")
            result['error'] = f"Analysis error: {str(e)}"
            result['health_status'] = 'error'
        
        return result
    
    async def _analyze_service_stability(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze service stability and error patterns"""
        result = {
            'stability_analysis_available': False,
            'recent_events': [],
            'failure_patterns': [],
            'recovery_patterns': [],
            'stability_issues': []
        }
        
        if not self.render_api_key:
            result['error'] = 'Render API key not available'
            return result
        
        try:
            # Get service events (failures, recoveries, etc.)
            events_url = f"https://api.render.com/v1/services/{service_info['id']}/events"
            async with self.session.get(events_url) as response:
                if response.status == 200:
                    result['stability_analysis_available'] = True
                    events_data = await response.json()
                    
                    # Analyze recent events
                    for event in events_data[:20]:  # Last 20 events
                        event_info = {
                            'type': event.get('type'),
                            'title': event.get('title'),
                            'description': event.get('description'),
                            'created_at': event.get('createdAt'),
                            'severity': event.get('severity', 'info')
                        }
                        result['recent_events'].append(event_info)
                        
                        # Analyze failure patterns
                        if 'failed' in event_info['type'].lower() or 'error' in event_info['type'].lower():
                            result['failure_patterns'].append(event_info)
                            result['stability_issues'].append(f"Failure: {event_info['title']} - {event_info['description']}")
                        
                        # Analyze recovery patterns
                        if 'recovered' in event_info['type'].lower() or 'healthy' in event_info['type'].lower():
                            result['recovery_patterns'].append(event_info)
                
                else:
                    result['error'] = f"Failed to get service events: {response.status}"
        
        except Exception as e:
            result['error'] = f"Stability analysis error: {str(e)}"
        
        return result
    
    async def _analyze_service_logs(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze service logs for errors and patterns"""
        result = {
            'log_analysis_available': False,
            'recent_logs': [],
            'error_logs': [],
            'warning_logs': [],
            'log_patterns': [],
            'common_errors': []
        }
        
        try:
            # Try to get logs using Render CLI if available
            log_result = await self._get_service_logs_cli(service_info)
            if log_result:
                result.update(log_result)
                result['log_analysis_available'] = True
            else:
                # Fallback to API-based log analysis
                result['log_analysis_available'] = False
                result['note'] = 'CLI-based log analysis not available, using API fallback'
        
        except Exception as e:
            result['error'] = f"Log analysis error: {str(e)}"
        
        return result
    
    async def _get_service_logs_cli(self, service_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get service logs using Render CLI"""
        try:
            # Try to get logs using render CLI
            cmd = ['render', 'logs', '--resources', service_info['id'], '--limit', '50', '--output', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logs_data = json.loads(result.stdout)
                return self._analyze_log_data(logs_data)
            else:
                logger.warning(f"CLI log command failed: {result.stderr}")
                return None
        
        except Exception as e:
            logger.warning(f"CLI log analysis failed: {str(e)}")
            return None
    
    def _analyze_log_data(self, logs_data: List[Dict]) -> Dict[str, Any]:
        """Analyze log data for patterns"""
        result = {
            'recent_logs': [],
            'error_logs': [],
            'warning_logs': [],
            'log_patterns': [],
            'common_errors': []
        }
        
        error_counts = {}
        
        for log_entry in logs_data:
            log_info = {
                'timestamp': log_entry.get('timestamp'),
                'level': log_entry.get('level', 'info'),
                'message': log_entry.get('message', ''),
                'service': log_entry.get('service', ''),
                'instance': log_entry.get('instance', '')
            }
            result['recent_logs'].append(log_info)
            
            # Categorize logs
            if log_info['level'].lower() in ['error', 'fatal', 'critical']:
                result['error_logs'].append(log_info)
                # Count common errors
                error_key = log_info['message'][:100]  # First 100 chars
                error_counts[error_key] = error_counts.get(error_key, 0) + 1
            elif log_info['level'].lower() == 'warning':
                result['warning_logs'].append(log_info)
        
        # Identify common errors
        for error_msg, count in error_counts.items():
            if count > 1:
                result['common_errors'].append(f"{error_msg} (occurred {count} times)")
        
        return result
    
    async def _check_service_configuration(self, service_info: Dict[str, str]) -> List[str]:
        """Check service configuration and health"""
        issues = []
        
        try:
            # Check health endpoint
            health_url = f"{service_info['url']}/health"
            async with self.session.get(health_url, timeout=30) as response:
                if response.status == 200:
                    health_data = await response.json()
                    
                    # Check for configuration issues
                    if health_data.get('status') == 'degraded':
                        services = health_data.get('services', {})
                        for service_name, service_status in services.items():
                            if service_status == 'not_configured':
                                issues.append(f"{service_name} service not configured")
                            elif service_status == 'error':
                                issues.append(f"{service_name} service has errors")
                else:
                    issues.append(f"Health endpoint returned {response.status}")
        
        except Exception as e:
            issues.append(f"Configuration check error: {str(e)}")
        
        return issues
    
    def _calculate_stability_score(self, stability_result: Dict, log_result: Dict, config_issues: List[str]) -> int:
        """Calculate stability score (0-100)"""
        score = 100
        
        # Deduct for failure patterns
        failure_count = len(stability_result.get('failure_patterns', []))
        score -= min(failure_count * 10, 50)  # Max 50 points for failures
        
        # Deduct for error logs
        error_count = len(log_result.get('error_logs', []))
        score -= min(error_count * 5, 30)  # Max 30 points for errors
        
        # Deduct for configuration issues
        config_count = len(config_issues)
        score -= min(config_count * 15, 20)  # Max 20 points for config issues
        
        return max(score, 0)
    
    def _determine_health_status(self, stability_score: int, stability_result: Dict, log_result: Dict) -> str:
        """Determine overall health status"""
        if stability_score >= 80:
            return 'healthy'
        elif stability_score >= 60:
            return 'degraded'
        elif stability_score >= 40:
            return 'unstable'
        else:
            return 'critical'
    
    def _generate_service_recommendations(self, service_result: Dict[str, Any]) -> List[str]:
        """Generate service-specific recommendations"""
        recommendations = []
        
        # Stability recommendations
        failure_patterns = service_result.get('stability_analysis', {}).get('failure_patterns', [])
        if failure_patterns:
            recommendations.append("Address recurring instance failures - check logs for root cause")
        
        # Log recommendations
        error_logs = service_result.get('log_analysis', {}).get('error_logs', [])
        if error_logs:
            recommendations.append("Fix errors in service logs - review error patterns")
        
        # Configuration recommendations
        config_issues = service_result.get('configuration_issues', [])
        if config_issues:
            recommendations.append(f"Fix configuration issues: {', '.join(config_issues)}")
        
        # Stability score recommendations
        stability_score = service_result.get('stability_score', 0)
        if stability_score < 60:
            recommendations.append("Service stability is poor - investigate and fix underlying issues")
        
        return recommendations
    
    def _generate_health_summary(self, services_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health summary"""
        summary = {
            'total_services': len(services_results),
            'healthy_services': 0,
            'degraded_services': 0,
            'unstable_services': 0,
            'critical_services': 0,
            'average_stability_score': 0,
            'total_failures': 0,
            'total_errors': 0,
            'critical_issues': []
        }
        
        total_score = 0
        service_count = 0
        
        for service_id, service_result in services_results.items():
            health_status = service_result.get('health_status', 'unknown')
            stability_score = service_result.get('stability_score', 0)
            
            if health_status == 'healthy':
                summary['healthy_services'] += 1
            elif health_status == 'degraded':
                summary['degraded_services'] += 1
            elif health_status == 'unstable':
                summary['unstable_services'] += 1
            elif health_status == 'critical':
                summary['critical_services'] += 1
            
            total_score += stability_score
            service_count += 1
            
            # Count failures and errors
            failure_count = len(service_result.get('stability_analysis', {}).get('failure_patterns', []))
            error_count = len(service_result.get('log_analysis', {}).get('error_logs', []))
            
            summary['total_failures'] += failure_count
            summary['total_errors'] += error_count
            
            # Collect critical issues
            if stability_score < 40:
                summary['critical_issues'].append(f"{service_result['service_name']}: Critical stability issues")
        
        if service_count > 0:
            summary['average_stability_score'] = total_score / service_count
        
        return summary
    
    def _generate_health_recommendations(self, services_results: Dict[str, Any]) -> List[str]:
        """Generate overall health recommendations"""
        recommendations = []
        
        for service_id, service_result in services_results.items():
            service_name = service_result['service_name']
            health_status = service_result.get('health_status', 'unknown')
            
            if health_status == 'critical':
                recommendations.append(f"{service_name}: CRITICAL - Immediate attention required")
            elif health_status == 'unstable':
                recommendations.append(f"{service_name}: UNSTABLE - Address stability issues")
            elif health_status == 'degraded':
                recommendations.append(f"{service_name}: DEGRADED - Fix configuration and errors")
        
        return list(set(recommendations))

async def main():
    """Main function for service health analysis"""
    print("🏥 Starting Service Health Analysis")
    print("=" * 60)
    
    async with ServiceHealthAnalyzer() as analyzer:
        results = await analyzer.analyze_service_health()
        
        # Print results
        print(f"\n📊 SERVICE HEALTH ANALYSIS")
        print(f"Total Services: {results['summary']['total_services']}")
        print(f"Healthy Services: {results['summary']['healthy_services']}")
        print(f"Degraded Services: {results['summary']['degraded_services']}")
        print(f"Unstable Services: {results['summary']['unstable_services']}")
        print(f"Critical Services: {results['summary']['critical_services']}")
        print(f"Average Stability Score: {results['summary']['average_stability_score']:.1f}/100")
        print(f"Total Failures: {results['summary']['total_failures']}")
        print(f"Total Errors: {results['summary']['total_errors']}")
        
        for service_id, service_result in results['services'].items():
            print(f"\n🔧 {service_result['service_name'].upper()}")
            print(f"  Health Status: {service_result['health_status'].upper()}")
            print(f"  Stability Score: {service_result['stability_score']}/100")
            
            # Stability analysis
            stability = service_result.get('stability_analysis', {})
            if stability.get('failure_patterns'):
                print(f"  Recent Failures: {len(stability['failure_patterns'])}")
                for failure in stability['failure_patterns'][:3]:  # Show first 3
                    print(f"    - {failure['title']}: {failure['description']}")
            
            # Log analysis
            logs = service_result.get('log_analysis', {})
            if logs.get('error_logs'):
                print(f"  Error Logs: {len(logs['error_logs'])}")
            if logs.get('common_errors'):
                print(f"  Common Errors: {len(logs['common_errors'])}")
                for error in logs['common_errors'][:2]:  # Show first 2
                    print(f"    - {error}")
            
            # Configuration issues
            config_issues = service_result.get('configuration_issues', [])
            if config_issues:
                print(f"  Configuration Issues: {', '.join(config_issues)}")
            
            # Recommendations
            recommendations = service_result.get('recommendations', [])
            if recommendations:
                print(f"  Recommendations:")
                for rec in recommendations:
                    print(f"    - {rec}")
        
        # Print critical issues
        if results['summary']['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(results['summary']['critical_issues'], 1):
                print(f"  {i}. {issue}")
        
        # Print overall recommendations
        if results['recommendations']:
            print(f"\n💡 OVERALL RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scripts/cloud_deployment/service_health_analysis_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Health analysis saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
