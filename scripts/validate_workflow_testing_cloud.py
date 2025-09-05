#!/usr/bin/env python3
"""
Workflow Testing Cloud Validation Script
Phase 2: Cloud Deployment Testing
Validates cloud deployment on Render.com and Vercel with production Supabase integration
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class ServiceConfig:
    """Configuration for a cloud service"""
    name: str
    url: str
    health_endpoint: str
    expected_status: int = 200
    timeout: int = 30

@dataclass
class ValidationResult:
    """Result of a validation check"""
    service: str
    check: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    response_time: Optional[float] = None
    details: Optional[Dict] = None

class CloudDeploymentValidator:
    """Validates cloud deployment for workflow testing"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "env.workflow-testing-cloud"
        self.results: List[ValidationResult] = []
        self.services = self._load_service_configs()
        
    def _load_service_configs(self) -> Dict[str, ServiceConfig]:
        """Load service configurations from environment file"""
        services = {}
        
        # Default service URLs (will be updated from environment)
        api_url = os.getenv('RENDER_API_URL', 'https://insurance-navigator-api-workflow-testing.onrender.com')
        frontend_url = os.getenv('VERCEL_URL', 'https://insurance-navigator-frontend-workflow-testing.vercel.app')
        
        # Try to load from environment file
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'RENDER_API_URL':
                            api_url = value
                        elif key == 'VERCEL_URL':
                            frontend_url = value
        
        services = {
            'api': ServiceConfig(
                name='API Service',
                url=api_url,
                health_endpoint=f'{api_url}/health'
            ),
            'frontend': ServiceConfig(
                name='Frontend Service',
                url=frontend_url,
                health_endpoint=f'{frontend_url}/health'
            )
        }
        
        return services
    
    def _make_request(self, url: str, timeout: int = 30) -> Tuple[bool, Optional[Dict], float, Optional[str]]:
        """Make HTTP request and return success, response, response_time, error"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return True, data, response_time, None
                except json.JSONDecodeError:
                    return True, {'text': response.text}, response_time, None
            else:
                return False, None, response_time, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, None, timeout, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, None, 0, "Connection error"
        except Exception as e:
            return False, None, 0, str(e)
    
    def validate_service_health(self, service_name: str) -> ValidationResult:
        """Validate individual service health"""
        service = self.services.get(service_name)
        if not service:
            return ValidationResult(
                service=service_name,
                check='health',
                status='fail',
                message=f'Service {service_name} not configured'
            )
        
        success, response, response_time, error = self._make_request(service.health_endpoint)
        
        if success and response:
            # Check if response indicates healthy status
            if isinstance(response, dict) and response.get('status') == 'healthy':
                return ValidationResult(
                    service=service_name,
                    check='health',
                    status='pass',
                    message=f'{service.name} is healthy',
                    response_time=response_time,
                    details=response
                )
            else:
                return ValidationResult(
                    service=service_name,
                    check='health',
                    status='warning',
                    message=f'{service.name} responded but status unclear',
                    response_time=response_time,
                    details=response
                )
        else:
            return ValidationResult(
                service=service_name,
                check='health',
                status='fail',
                message=f'{service.name} health check failed: {error}',
                response_time=response_time
            )
    
    def validate_cross_platform_communication(self) -> ValidationResult:
        """Validate communication between frontend and API"""
        frontend = self.services.get('frontend')
        api = self.services.get('api')
        
        if not frontend or not api:
            return ValidationResult(
                service='cross-platform',
                check='communication',
                status='fail',
                message='Frontend or API service not configured'
            )
        
        # Test if frontend can reach API
        try:
            # This would typically be tested through the frontend's health check
            # which should include API connectivity
            success, response, response_time, error = self._make_request(frontend.health_endpoint)
            
            if success and response:
                # Check if frontend health includes API status
                checks = response.get('checks', {})
                api_check = checks.get('api', {})
                
                if api_check.get('status') == 'healthy':
                    return ValidationResult(
                        service='cross-platform',
                        check='communication',
                        status='pass',
                        message='Frontend can communicate with API',
                        response_time=response_time,
                        details=api_check
                    )
                else:
                    return ValidationResult(
                        service='cross-platform',
                        check='communication',
                        status='fail',
                        message='Frontend cannot communicate with API',
                        response_time=response_time,
                        details=api_check
                    )
            else:
                return ValidationResult(
                    service='cross-platform',
                    check='communication',
                    status='fail',
                    message=f'Frontend health check failed: {error}',
                    response_time=response_time
                )
                
        except Exception as e:
            return ValidationResult(
                service='cross-platform',
                check='communication',
                status='fail',
                message=f'Cross-platform communication test failed: {str(e)}'
            )
    
    def validate_supabase_integration(self) -> ValidationResult:
        """Validate Supabase integration"""
        try:
            # Test Supabase connectivity through API service
            api = self.services.get('api')
            if not api:
                return ValidationResult(
                    service='supabase',
                    check='integration',
                    status='fail',
                    message='API service not configured'
                )
            
            success, response, response_time, error = self._make_request(api.health_endpoint)
            
            if success and response:
                # Check if API health includes database status
                database_status = response.get('database', 'unknown')
                
                if database_status == 'connected':
                    return ValidationResult(
                        service='supabase',
                        check='integration',
                        status='pass',
                        message='Supabase integration is healthy',
                        response_time=response_time,
                        details={'database': database_status}
                    )
                else:
                    return ValidationResult(
                        service='supabase',
                        check='integration',
                        status='fail',
                        message=f'Supabase integration issue: {database_status}',
                        response_time=response_time,
                        details={'database': database_status}
                    )
            else:
                return ValidationResult(
                    service='supabase',
                    check='integration',
                    status='fail',
                    message=f'Cannot validate Supabase integration: {error}',
                    response_time=response_time
                )
                
        except Exception as e:
            return ValidationResult(
                service='supabase',
                check='integration',
                status='fail',
                message=f'Supabase integration validation failed: {str(e)}'
            )
    
    def validate_external_apis(self) -> ValidationResult:
        """Validate external API integrations"""
        try:
            # Test external API connectivity through API service
            api = self.services.get('api')
            if not api:
                return ValidationResult(
                    service='external-apis',
                    check='integration',
                    status='fail',
                    message='API service not configured'
                )
            
            success, response, response_time, error = self._make_request(api.health_endpoint)
            
            if success and response:
                # Check if API health includes external services status
                external_services = response.get('external_services', {})
                
                if external_services:
                    all_configured = all(
                        status in ['configured', 'healthy'] 
                        for status in external_services.values()
                    )
                    
                    if all_configured:
                        return ValidationResult(
                            service='external-apis',
                            check='integration',
                            status='pass',
                            message='External API integrations are configured',
                            response_time=response_time,
                            details=external_services
                        )
                    else:
                        return ValidationResult(
                            service='external-apis',
                            check='integration',
                            status='warning',
                            message='Some external API integrations may have issues',
                            response_time=response_time,
                            details=external_services
                        )
                else:
                    return ValidationResult(
                        service='external-apis',
                        check='integration',
                        status='warning',
                        message='External API status not available in health check',
                        response_time=response_time
                    )
            else:
                return ValidationResult(
                    service='external-apis',
                    check='integration',
                    status='fail',
                    message=f'Cannot validate external APIs: {error}',
                    response_time=response_time
                )
                
        except Exception as e:
            return ValidationResult(
                service='external-apis',
                check='integration',
                status='fail',
                message=f'External API validation failed: {str(e)}'
            )
    
    def validate_performance_baselines(self) -> ValidationResult:
        """Validate performance against baselines"""
        try:
            # Collect response times from all services
            response_times = []
            
            for service_name, service in self.services.items():
                success, response, response_time, error = self._make_request(service.health_endpoint)
                if success and response_time:
                    response_times.append(response_time)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                # Performance thresholds (adjust based on requirements)
                avg_threshold = 2.0  # 2 seconds average
                max_threshold = 5.0  # 5 seconds maximum
                
                if avg_response_time <= avg_threshold and max_response_time <= max_threshold:
                    return ValidationResult(
                        service='performance',
                        check='baselines',
                        status='pass',
                        message=f'Performance within acceptable limits (avg: {avg_response_time:.2f}s, max: {max_response_time:.2f}s)',
                        details={
                            'average_response_time': avg_response_time,
                            'max_response_time': max_response_time,
                            'thresholds': {
                                'average': avg_threshold,
                                'max': max_threshold
                            }
                        }
                    )
                else:
                    return ValidationResult(
                        service='performance',
                        check='baselines',
                        status='warning',
                        message=f'Performance may be degraded (avg: {avg_response_time:.2f}s, max: {max_response_time:.2f}s)',
                        details={
                            'average_response_time': avg_response_time,
                            'max_response_time': max_response_time,
                            'thresholds': {
                                'average': avg_threshold,
                                'max': max_threshold
                            }
                        }
                    )
            else:
                return ValidationResult(
                    service='performance',
                    check='baselines',
                    status='fail',
                    message='No response time data available'
                )
                
        except Exception as e:
            return ValidationResult(
                service='performance',
                check='baselines',
                status='fail',
                message=f'Performance validation failed: {str(e)}'
            )
    
    def run_validation(self, service: str = None) -> List[ValidationResult]:
        """Run comprehensive validation"""
        self.results = []
        
        print(f"Starting cloud deployment validation at {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Service health checks
        if not service or service == 'api':
            print("Validating API service health...")
            self.results.append(self.validate_service_health('api'))
        
        if not service or service == 'frontend':
            print("Validating Frontend service health...")
            self.results.append(self.validate_service_health('frontend'))
        
        # Cross-platform communication
        if not service:
            print("Validating cross-platform communication...")
            self.results.append(self.validate_cross_platform_communication())
        
        # Supabase integration
        if not service:
            print("Validating Supabase integration...")
            self.results.append(self.validate_supabase_integration())
        
        # External API integrations
        if not service:
            print("Validating external API integrations...")
            self.results.append(self.validate_external_apis())
        
        # Performance baselines
        if not service:
            print("Validating performance baselines...")
            self.results.append(self.validate_performance_baselines())
        
        return self.results
    
    def print_results(self, json_output: bool = False):
        """Print validation results"""
        if json_output:
            # JSON output for programmatic use
            output = {
                'timestamp': datetime.now().isoformat(),
                'total_checks': len(self.results),
                'passed': len([r for r in self.results if r.status == 'pass']),
                'warnings': len([r for r in self.results if r.status == 'warning']),
                'failed': len([r for r in self.results if r.status == 'fail']),
                'results': [
                    {
                        'service': r.service,
                        'check': r.check,
                        'status': r.status,
                        'message': r.message,
                        'response_time': r.response_time,
                        'details': r.details
                    }
                    for r in self.results
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print("\n" + "=" * 60)
            print("VALIDATION RESULTS")
            print("=" * 60)
            
            for result in self.results:
                status_symbol = {
                    'pass': '✅',
                    'warning': '⚠️',
                    'fail': '❌'
                }.get(result.status, '❓')
                
                print(f"{status_symbol} {result.service.upper()} - {result.check.upper()}")
                print(f"   {result.message}")
                if result.response_time:
                    print(f"   Response time: {result.response_time:.2f}s")
                if result.details:
                    print(f"   Details: {json.dumps(result.details, indent=2)}")
                print()
            
            # Summary
            total = len(self.results)
            passed = len([r for r in self.results if r.status == 'pass'])
            warnings = len([r for r in self.results if r.status == 'warning'])
            failed = len([r for r in self.results if r.status == 'fail'])
            
            print("=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Total checks: {total}")
            print(f"Passed: {passed}")
            print(f"Warnings: {warnings}")
            print(f"Failed: {failed}")
            
            if failed == 0:
                print("\n🎉 All validations passed! Cloud deployment is healthy.")
            elif failed <= 2:
                print("\n⚠️  Some validations failed, but deployment may still be functional.")
            else:
                print("\n❌ Multiple validations failed. Please check the deployment.")

def main():
    parser = argparse.ArgumentParser(description='Validate cloud deployment for workflow testing')
    parser.add_argument('--service', choices=['api', 'frontend'], help='Validate specific service only')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--config', help='Path to environment configuration file')
    parser.add_argument('--quiet', action='store_true', help='Only show errors and warnings')
    
    args = parser.parse_args()
    
    # Load environment variables
    config_file = args.config or 'env.workflow-testing-cloud'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Run validation
    validator = CloudDeploymentValidator(config_file)
    results = validator.run_validation(args.service)
    
    # Print results
    if not args.quiet or any(r.status == 'fail' for r in results):
        validator.print_results(args.json)
    
    # Exit with appropriate code
    failed_count = len([r for r in results if r.status == 'fail'])
    sys.exit(failed_count)

if __name__ == '__main__':
    main()
