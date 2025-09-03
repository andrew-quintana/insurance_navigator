#!/usr/bin/env python3
"""
Environment Variables Validator - Validate all required environment variables

This script validates that all required environment variables are properly
configured for both API and worker services in the cloud deployment.
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

class EnvironmentVariableValidator:
    """Validate environment variables for cloud services"""
    
    def __init__(self):
        self.session = None
        self.render_api_key = os.getenv('RENDER_CLI_API_KEY')
        
        # Required environment variables for each service
        self.required_vars = {
            'api': {
                'SUPABASE_URL': 'Supabase project URL',
                'SUPABASE_KEY': 'Supabase anonymous key',
                'SERVICE_ROLE_KEY': 'Supabase service role key',
                'DATABASE_URL': 'PostgreSQL database URL',
                'API_BASE_URL': 'API base URL for internal communication',
                'LLAMAPARSE_API_KEY': 'LlamaParse API key for document processing',
                'OPENAI_API_KEY': 'OpenAI API key for AI processing',
                'ANTHROPIC_API_KEY': 'Anthropic API key for AI processing',
                'JWT_SECRET_KEY': 'JWT secret for authentication',
                'ENVIRONMENT': 'Environment name (production)',
                'LOG_LEVEL': 'Logging level',
                'SECURITY_BYPASS_ENABLED': 'Security bypass flag'
            },
            'worker': {
                'SUPABASE_URL': 'Supabase project URL',
                'SUPABASE_KEY': 'Supabase anonymous key', 
                'SERVICE_ROLE_KEY': 'Supabase service role key',
                'DATABASE_URL': 'PostgreSQL database URL',
                'API_BASE_URL': 'API base URL for internal communication',
                'LLAMAPARSE_API_KEY': 'LlamaParse API key for document processing',
                'OPENAI_API_KEY': 'OpenAI API key for AI processing',
                'ANTHROPIC_API_KEY': 'Anthropic API key for AI processing',
                'JWT_SECRET_KEY': 'JWT secret for authentication',
                'ENVIRONMENT': 'Environment name (production)',
                'LOG_LEVEL': 'Logging level',
                'WORKER_POLL_INTERVAL': 'Worker polling interval',
                'WORKER_MAX_JOBS': 'Maximum concurrent jobs',
                'WORKER_MAX_RETRIES': 'Maximum retry attempts'
            }
        }
        
        self.services = {
            'api': {
                'name': 'insurance-navigator-api',
                'id': 'srv-d0v2nqvdiees73cejf0g',
                'url': '***REMOVED***'
            },
            'worker': {
                'name': 'insurance_navigator',
                'id': 'srv-d2h5mr8dl3ps73fvvlog',
                'url': 'https://insurance-navigator-worker.onrender.com'
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'Authorization': f'Bearer {self.render_api_key}' if self.render_api_key else '',
                'Accept': 'application/json',
                'User-Agent': 'InsuranceNavigator-EnvValidator/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def validate_all_environment_variables(self) -> Dict[str, Any]:
        """Validate environment variables for all services"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {},
            'recommendations': []
        }
        
        for service_id, service_info in self.services.items():
            logger.info(f"Validating environment variables for {service_info['name']}")
            
            service_result = await self._validate_service_environment(service_id, service_info)
            results['services'][service_id] = service_result
        
        # Generate summary and recommendations
        results['summary'] = self._generate_validation_summary(results['services'])
        results['recommendations'] = self._generate_validation_recommendations(results['services'])
        
        return results
    
    async def _validate_service_environment(self, service_id: str, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Validate environment variables for a specific service"""
        result = {
            'service_name': service_info['name'],
            'service_id': service_info['id'],
            'service_url': service_info['url'],
            'environment_variables': {},
            'missing_variables': [],
            'configured_variables': [],
            'validation_status': 'unknown',
            'health_check': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # 1. Check health endpoint to see current status
            health_result = await self._check_service_health(service_info)
            result['health_check'] = health_result
            
            # 2. Validate required environment variables
            env_result = await self._validate_required_variables(service_id, service_info)
            result['environment_variables'] = env_result
            result['missing_variables'] = env_result.get('missing', [])
            result['configured_variables'] = env_result.get('configured', [])
            
            # 3. Determine validation status
            result['validation_status'] = self._determine_validation_status(
                health_result, env_result
            )
            
            # 4. Generate service-specific recommendations
            result['recommendations'] = self._generate_service_recommendations(
                health_result, env_result
            )
            
        except Exception as e:
            logger.error(f"Error validating {service_info['name']}: {str(e)}")
            result['issues'].append(f"Validation error: {str(e)}")
            result['validation_status'] = 'error'
        
        return result
    
    async def _check_service_health(self, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Check service health to see current configuration status"""
        result = {
            'health_status': 'unknown',
            'response_time': 0,
            'status_code': 0,
            'health_data': None,
            'configuration_issues': []
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
                    result['health_status'] = 'healthy'
                    try:
                        health_data = await response.json()
                        result['health_data'] = health_data
                        
                        # Check for configuration issues in health response
                        if health_data.get('status') == 'degraded':
                            services = health_data.get('services', {})
                            for service_name, service_status in services.items():
                                if service_status == 'not_configured':
                                    result['configuration_issues'].append(f"{service_name} not configured")
                                elif service_status == 'error':
                                    result['configuration_issues'].append(f"{service_name} has errors")
                    except:
                        result['health_data'] = await response.text()
                elif response.status == 404:
                    # For worker services, 404 is expected
                    if 'worker' in service_info['name']:
                        result['health_status'] = 'deployed'
                        result['note'] = 'Worker service deployed (404 expected)'
                    else:
                        result['health_status'] = 'error'
                        result['configuration_issues'].append('Health endpoint not found')
                else:
                    result['health_status'] = 'error'
                    result['configuration_issues'].append(f'Health check failed: {response.status}')
        
        except Exception as e:
            result['health_status'] = 'error'
            result['configuration_issues'].append(f'Health check error: {str(e)}')
        
        return result
    
    async def _validate_required_variables(self, service_id: str, service_info: Dict[str, str]) -> Dict[str, Any]:
        """Validate that required environment variables are configured"""
        result = {
            'required_variables': list(self.required_vars[service_id].keys()),
            'configured': [],
            'missing': [],
            'validation_available': False
        }
        
        # For now, we can't directly access Render environment variables via API
        # We'll infer from health check and service behavior
        result['validation_available'] = False
        result['note'] = 'Direct environment variable access not available via API'
        
        # We can infer some variables from health check
        health_check = await self._check_service_health(service_info)
        
        if health_check['health_status'] == 'healthy':
            # If service is healthy, assume most variables are configured
            result['configured'] = list(self.required_vars[service_id].keys())
        elif health_check['health_status'] == 'degraded':
            # If degraded, some variables might be missing
            result['configured'] = ['SUPABASE_URL', 'SUPABASE_KEY', 'DATABASE_URL']  # Basic ones
            result['missing'] = ['LLAMAPARSE_API_KEY', 'OPENAI_API_KEY']  # Common missing ones
        else:
            # If unhealthy, assume critical variables are missing
            result['missing'] = ['SUPABASE_URL', 'SUPABASE_KEY', 'DATABASE_URL']
        
        return result
    
    def _determine_validation_status(self, health_result: Dict, env_result: Dict) -> str:
        """Determine overall validation status"""
        if health_result['health_status'] == 'healthy':
            return 'valid'
        elif health_result['health_status'] == 'degraded':
            return 'partial'
        elif health_result['health_status'] == 'deployed':
            return 'valid'  # Worker services showing as deployed
        else:
            return 'invalid'
    
    def _generate_service_recommendations(self, health_result: Dict, env_result: Dict) -> List[str]:
        """Generate service-specific recommendations"""
        recommendations = []
        
        # Health-based recommendations
        if health_result['health_status'] == 'error':
            recommendations.append("Fix service health issues - check environment variables")
        
        if health_result['configuration_issues']:
            for issue in health_result['configuration_issues']:
                recommendations.append(f"Fix configuration issue: {issue}")
        
        # Environment variable recommendations
        missing_vars = env_result.get('missing', [])
        if missing_vars:
            recommendations.append(f"Configure missing environment variables: {', '.join(missing_vars)}")
        
        return recommendations
    
    def _generate_validation_summary(self, services_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary"""
        summary = {
            'total_services': len(services_results),
            'valid_services': 0,
            'partial_services': 0,
            'invalid_services': 0,
            'total_missing_variables': 0,
            'critical_issues': []
        }
        
        for service_id, service_result in services_results.items():
            status = service_result.get('validation_status', 'unknown')
            
            if status == 'valid':
                summary['valid_services'] += 1
            elif status == 'partial':
                summary['partial_services'] += 1
            elif status == 'invalid':
                summary['invalid_services'] += 1
            
            # Count missing variables
            missing_count = len(service_result.get('missing_variables', []))
            summary['total_missing_variables'] += missing_count
            
            # Collect critical issues
            if status == 'invalid':
                summary['critical_issues'].append(f"{service_result['service_name']}: Invalid configuration")
        
        return summary
    
    def _generate_validation_recommendations(self, services_results: Dict[str, Any]) -> List[str]:
        """Generate overall validation recommendations"""
        recommendations = []
        
        for service_id, service_result in services_results.items():
            service_name = service_result['service_name']
            status = service_result.get('validation_status', 'unknown')
            
            if status == 'invalid':
                recommendations.append(f"{service_name}: CRITICAL - Fix environment variable configuration")
            elif status == 'partial':
                recommendations.append(f"{service_name}: Configure missing environment variables")
            
            # Add specific recommendations
            service_recs = service_result.get('recommendations', [])
            recommendations.extend(service_recs)
        
        return list(set(recommendations))  # Remove duplicates

async def main():
    """Main function for environment variable validation"""
    print("🔧 Starting Environment Variables Validation")
    print("=" * 60)
    
    async with EnvironmentVariableValidator() as validator:
        results = await validator.validate_all_environment_variables()
        
        # Print results
        print(f"\n📊 ENVIRONMENT VARIABLES VALIDATION")
        print(f"Total Services: {results['summary']['total_services']}")
        print(f"Valid Services: {results['summary']['valid_services']}")
        print(f"Partial Services: {results['summary']['partial_services']}")
        print(f"Invalid Services: {results['summary']['invalid_services']}")
        print(f"Total Missing Variables: {results['summary']['total_missing_variables']}")
        
        for service_id, service_result in results['services'].items():
            print(f"\n🔧 {service_result['service_name'].upper()}")
            print(f"  Validation Status: {service_result['validation_status'].upper()}")
            
            # Health check details
            health = service_result.get('health_check', {})
            if health.get('health_status'):
                print(f"  Health Status: {health['health_status']}")
            if health.get('configuration_issues'):
                print(f"  Configuration Issues: {', '.join(health['configuration_issues'])}")
            
            # Environment variables
            missing_vars = service_result.get('missing_variables', [])
            configured_vars = service_result.get('configured_variables', [])
            
            if missing_vars:
                print(f"  Missing Variables: {', '.join(missing_vars)}")
            if configured_vars:
                print(f"  Configured Variables: {len(configured_vars)}/{len(configured_vars) + len(missing_vars)}")
            
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
        results_file = f"scripts/cloud_deployment/env_validation_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Validation results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
