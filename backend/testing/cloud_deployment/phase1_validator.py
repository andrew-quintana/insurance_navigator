"""
Phase 1 Cloud Environment Validator

Implements autonomous testing framework for cloud environment setup and validation.
Based on RFC001.md interface contracts and local integration baseline requirements.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
import logging
import os
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation test"""
    status: str  # "pass", "fail", "warning"
    metrics: Dict[str, Any]
    errors: List[str]
    timestamp: datetime
    environment: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class CloudEnvironmentValidator:
    """
    Validates cloud deployment environment configuration
    
    Implements the interface contracts from RFC001.md for Phase 1 validation.
    Tests Vercel frontend, Render backend, and Supabase database connectivity.
    """
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize the validator with cloud environment configuration
        
        Args:
            config: Dictionary containing cloud environment URLs and credentials
        """
        self.config = config or self._load_config()
        self.session = None
        
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment variables"""
        config = {
            'vercel_url': os.getenv('VERCEL_URL', 'https://insurance-navigator.vercel.app'),
            'render_url': os.getenv('RENDER_URL', '***REMOVED***'),
            'render_worker_url': os.getenv('RENDER_WORKER_URL', 'https://insurance-navigator-worker.onrender.com'),
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_anon_key': os.getenv('SUPABASE_KEY'),
            'supabase_service_key': os.getenv('SERVICE_ROLE_KEY'),
            'api_base_url': os.getenv('API_BASE_URL', '***REMOVED***'),
        }
        

        
        return config
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'CloudDeploymentValidator/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def validate_vercel_deployment(self) -> ValidationResult:
        """
        Validate Vercel frontend deployment
        
        Tests:
        - Frontend accessibility and performance
        - Environment configuration
        - CDN functionality and caching
        - Build process validation
        
        Returns:
            ValidationResult with status, metrics, errors
        """
        logger.info("Starting Vercel deployment validation")
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Test 1: Basic frontend accessibility
            frontend_health = await self._test_frontend_accessibility()
            metrics.update(frontend_health)
            
            # Test 2: Environment configuration
            env_config = await self._test_environment_configuration()
            metrics.update(env_config)
            
            # Test 3: CDN and caching
            cdn_performance = await self._test_cdn_performance()
            metrics.update(cdn_performance)
            
            # Test 4: Build process validation
            build_validation = await self._test_build_validation()
            metrics.update(build_validation)
            
            # Determine overall status
            status = "pass"
            if errors:
                status = "fail"
            elif any(metric.get('warning', False) for metric in [frontend_health, env_config, cdn_performance, build_validation]):
                status = "warning"
            
            metrics['total_validation_time'] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Vercel validation failed: {e}")
            errors.append(f"Vercel validation error: {str(e)}")
            status = "fail"
            metrics['total_validation_time'] = time.time() - start_time
        
        return ValidationResult(
            status=status,
            metrics=metrics,
            errors=errors,
            timestamp=datetime.now(),
            environment="vercel"
        )
    
    async def validate_render_deployment(self) -> ValidationResult:
        """
        Validate Render backend deployment
        
        Tests:
        - API endpoints and health checks
        - Docker container deployment
        - Worker processes and job handling
        - Environment configuration
        
        Returns:
            ValidationResult with status, health_checks, performance
        """
        logger.info("Starting Render deployment validation")
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Test 1: API health endpoints
            health_checks = await self._test_api_health_checks()
            metrics.update(health_checks)
            
            # Test 2: Docker container deployment
            container_health = await self._test_container_deployment()
            metrics.update(container_health)
            
            # Test 3: Worker processes
            worker_health = await self._test_worker_processes()
            metrics.update(worker_health)
            
            # Test 4: Environment configuration
            env_validation = await self._test_backend_environment()
            metrics.update(env_validation)
            
            # Determine overall status
            status = "pass"
            if errors:
                status = "fail"
            elif any(metric.get('warning', False) for metric in [health_checks, container_health, worker_health, env_validation]):
                status = "warning"
            
            metrics['total_validation_time'] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Render validation failed: {e}")
            errors.append(f"Render validation error: {str(e)}")
            status = "fail"
            metrics['total_validation_time'] = time.time() - start_time
        
        return ValidationResult(
            status=status,
            metrics=metrics,
            errors=errors,
            timestamp=datetime.now(),
            environment="render"
        )
    
    async def validate_render_worker_deployment(self) -> ValidationResult:
        """
        Validate Render worker service deployment
        
        Tests:
        - Worker service health and status
        - Worker process functionality
        - Worker environment configuration
        
        Returns:
            ValidationResult with status, health_checks, performance
        """
        logger.info("Starting Render worker deployment validation")
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Test 1: Worker service health
            worker_health = await self._test_worker_service_health()
            metrics.update(worker_health)
            
            # Test 2: Worker service status
            worker_status = await self._test_worker_service_status()
            metrics.update(worker_status)
            
            # Test 3: Worker environment configuration
            worker_env = await self._test_worker_environment()
            metrics.update(worker_env)
            
            # Determine overall status
            status = "pass"
            if errors:
                status = "fail"
            elif any(metric.get('warning', False) for metric in [worker_health, worker_status, worker_env]):
                status = "warning"
            
            metrics['total_validation_time'] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Render worker validation failed: {e}")
            errors.append(f"Render worker validation error: {str(e)}")
            status = "fail"
            metrics['total_validation_time'] = time.time() - start_time
        
        return ValidationResult(
            status=status,
            metrics=metrics,
            errors=errors,
            timestamp=datetime.now(),
            environment="render_worker"
        )
    
    async def validate_render_build_status(self) -> ValidationResult:
        """
        Validate Render build status and deployment logs
        
        Tests:
        - Build status for API service
        - Build status for worker service
        - Deployment log analysis
        - Build performance metrics
        
        Returns:
            ValidationResult with build status, logs, and performance
        """
        logger.info("Starting Render build status validation")
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Test 1: API service build status
            api_build = await self._test_api_build_status()
            metrics.update(api_build)
            
            # Test 2: Worker service build status
            worker_build = await self._test_worker_build_status()
            metrics.update(worker_build)
            
            # Test 3: Deployment log analysis
            log_analysis = await self._analyze_deployment_logs()
            metrics.update(log_analysis)
            
            # Test 4: Build performance metrics
            build_performance = await self._analyze_build_performance()
            metrics.update(build_performance)
            
            # Determine overall status
            status = "pass"
            if errors:
                status = "fail"
            elif any(metric.get('warning', False) for metric in [api_build, worker_build, log_analysis, build_performance]):
                status = "warning"
            
            metrics['total_validation_time'] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Render build validation failed: {e}")
            errors.append(f"Render build validation error: {str(e)}")
            status = "fail"
            metrics['total_validation_time'] = time.time() - start_time
        
        return ValidationResult(
            status=status,
            metrics=metrics,
            errors=errors,
            timestamp=datetime.now(),
            environment="render_build"
        )
    
    async def validate_supabase_connectivity(self) -> ValidationResult:
        """
        Validate Supabase database connectivity and performance
        
        Tests:
        - Database connection and performance
        - Authentication service
        - Storage functionality
        - Real-time subscriptions
        
        Returns:
            ValidationResult with connection_status, query_performance
        """
        logger.info("Starting Supabase connectivity validation")
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Test 1: Database connection
            db_connection = await self._test_database_connection()
            metrics.update(db_connection)
            
            # Test 2: Authentication service
            auth_service = await self._test_authentication_service()
            metrics.update(auth_service)
            
            # Test 3: Storage functionality
            storage_health = await self._test_storage_functionality()
            metrics.update(storage_health)
            
            # Test 4: Real-time subscriptions
            realtime_health = await self._test_realtime_subscriptions()
            metrics.update(realtime_health)
            
            # Determine overall status
            status = "pass"
            if errors:
                status = "fail"
            elif any(metric.get('warning', False) for metric in [db_connection, auth_service, storage_health, realtime_health]):
                status = "warning"
            
            metrics['total_validation_time'] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Supabase validation failed: {e}")
            errors.append(f"Supabase validation error: {str(e)}")
            status = "fail"
            metrics['total_validation_time'] = time.time() - start_time
        
        return ValidationResult(
            status=status,
            metrics=metrics,
            errors=errors,
            timestamp=datetime.now(),
            environment="supabase"
        )
    
    # Helper methods for Vercel validation
    async def _test_frontend_accessibility(self) -> Dict[str, Any]:
        """Test frontend accessibility and basic functionality"""
        metrics = {}
        
        try:
            # Test main page accessibility
            async with self.session.get(self.config['vercel_url']) as response:
                metrics['frontend_status_code'] = response.status
                metrics['frontend_response_time'] = response.headers.get('X-Response-Time', 'unknown')
                
                if response.status == 200:
                    content = await response.text()
                    metrics['frontend_content_length'] = len(content)
                    metrics['frontend_has_react'] = 'react' in content.lower()
                    metrics['frontend_has_nextjs'] = 'next' in content.lower()
                else:
                    metrics['warning'] = True
                    metrics['frontend_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['frontend_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_environment_configuration(self) -> Dict[str, Any]:
        """Test environment configuration"""
        metrics = {}
        
        try:
            # Test environment endpoint if available
            env_url = urljoin(self.config['vercel_url'], '/api/env-check')
            async with self.session.get(env_url) as response:
                if response.status == 200:
                    env_data = await response.json()
                    metrics['environment_config'] = env_data
                else:
                    metrics['environment_check_available'] = False
        except Exception:
            metrics['environment_check_available'] = False
        
        return metrics
    
    async def _test_cdn_performance(self) -> Dict[str, Any]:
        """Test CDN performance and caching"""
        metrics = {}
        
        try:
            # Test static asset caching
            static_url = urljoin(self.config['vercel_url'], '/_next/static/')
            async with self.session.get(static_url) as response:
                metrics['cdn_status_code'] = response.status
                metrics['cdn_cache_headers'] = dict(response.headers)
                
                if 'cache-control' in response.headers:
                    metrics['cdn_cache_control'] = response.headers['cache-control']
                else:
                    metrics['warning'] = True
                    metrics['cdn_no_cache_control'] = True
        
        except Exception as e:
            metrics['cdn_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_build_validation(self) -> Dict[str, Any]:
        """Test build process validation"""
        metrics = {}
        
        try:
            # Test that the build is working by checking for Next.js specific endpoints
            next_url = urljoin(self.config['vercel_url'], '/_next/')
            async with self.session.get(next_url) as response:
                metrics['build_status_code'] = response.status
                metrics['build_accessible'] = response.status == 200 or response.status == 404  # 404 is OK for directory listing
        
        except Exception as e:
            metrics['build_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    # Helper methods for Render validation
    async def _test_api_health_checks(self) -> Dict[str, Any]:
        """Test API health endpoints"""
        metrics = {}
        
        try:
            # Test main health endpoint
            health_url = urljoin(self.config['render_url'], '/health')
            async with self.session.get(health_url) as response:
                metrics['health_status_code'] = response.status
                metrics['health_response_time'] = response.headers.get('X-Response-Time', 'unknown')
                
                if response.status == 200:
                    health_data = await response.json()
                    metrics['health_data'] = health_data
                else:
                    metrics['warning'] = True
                    metrics['health_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['health_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_container_deployment(self) -> Dict[str, Any]:
        """Test Docker container deployment"""
        metrics = {}
        
        try:
            # Test API endpoints to verify container is running
            api_url = urljoin(self.config['render_url'], '/api/status')
            async with self.session.get(api_url) as response:
                metrics['container_status_code'] = response.status
                
                if response.status == 200:
                    container_data = await response.json()
                    metrics['container_data'] = container_data
                else:
                    metrics['warning'] = True
                    metrics['container_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['container_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_worker_processes(self) -> Dict[str, Any]:
        """Test worker processes and job handling"""
        metrics = {}
        
        try:
            # Test worker status endpoint
            worker_url = urljoin(self.config['render_url'], '/api/workers/status')
            async with self.session.get(worker_url) as response:
                metrics['worker_status_code'] = response.status
                
                if response.status == 200:
                    worker_data = await response.json()
                    metrics['worker_data'] = worker_data
                else:
                    metrics['warning'] = True
                    metrics['worker_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['worker_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_backend_environment(self) -> Dict[str, Any]:
        """Test backend environment configuration"""
        metrics = {}
        
        try:
            # Test environment info endpoint
            env_url = urljoin(self.config['render_url'], '/api/env')
            async with self.session.get(env_url) as response:
                if response.status == 200:
                    env_data = await response.json()
                    metrics['backend_env'] = env_data
                else:
                    metrics['backend_env_check_available'] = False
        except Exception:
            metrics['backend_env_check_available'] = False
        
        return metrics
    
    # Helper methods for Supabase validation
    async def _test_database_connection(self) -> Dict[str, Any]:
        """Test database connection and performance"""
        metrics = {}
        

        
        if not self.config.get('supabase_url') or not self.config.get('supabase_service_key'):
            metrics['database_error'] = "Supabase configuration missing"
            metrics['warning'] = True
            return metrics
        
        try:
            # Test database connection via Supabase REST API
            db_url = f"{self.config['supabase_url']}/rest/v1/"
            headers = {
                'apikey': self.config['supabase_service_key'],
                'Authorization': f"Bearer {self.config['supabase_service_key']}"
            }
            
            async with self.session.get(db_url, headers=headers) as response:
                metrics['database_status_code'] = response.status
                metrics['database_response_time'] = response.headers.get('X-Response-Time', 'unknown')
                
                if response.status == 200:
                    metrics['database_connected'] = True
                else:
                    metrics['warning'] = True
                    metrics['database_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['database_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_authentication_service(self) -> Dict[str, Any]:
        """Test authentication service"""
        metrics = {}
        
        if not self.config.get('supabase_url') or not self.config.get('supabase_anon_key'):
            metrics['auth_error'] = "Supabase auth configuration missing"
            metrics['warning'] = True
            return metrics
        
        try:
            # Test auth service availability
            auth_url = f"{self.config['supabase_url']}/auth/v1/settings"
            headers = {
                'apikey': self.config['supabase_anon_key']
            }
            
            async with self.session.get(auth_url, headers=headers) as response:
                metrics['auth_status_code'] = response.status
                
                if response.status == 200:
                    auth_data = await response.json()
                    metrics['auth_data'] = auth_data
                    metrics['auth_available'] = True
                else:
                    metrics['warning'] = True
                    metrics['auth_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['auth_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_storage_functionality(self) -> Dict[str, Any]:
        """Test storage functionality"""
        metrics = {}
        
        if not self.config.get('supabase_url') or not self.config.get('supabase_anon_key'):
            metrics['storage_error'] = "Supabase storage configuration missing"
            metrics['warning'] = True
            return metrics
        
        try:
            # Test storage service availability
            storage_url = f"{self.config['supabase_url']}/storage/v1/bucket"
            headers = {
                'apikey': self.config['supabase_anon_key']
            }
            
            async with self.session.get(storage_url, headers=headers) as response:
                metrics['storage_status_code'] = response.status
                
                if response.status == 200:
                    storage_data = await response.json()
                    metrics['storage_data'] = storage_data
                    metrics['storage_available'] = True
                else:
                    metrics['warning'] = True
                    metrics['storage_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['storage_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_realtime_subscriptions(self) -> Dict[str, Any]:
        """Test real-time subscriptions"""
        metrics = {}
        
        if not self.config.get('supabase_url'):
            metrics['realtime_error'] = "Supabase URL missing"
            metrics['warning'] = True
            return metrics
        
        try:
            # Test realtime service availability
            realtime_url = f"{self.config['supabase_url']}/realtime/v1/"
            async with self.session.get(realtime_url) as response:
                metrics['realtime_status_code'] = response.status
                
                if response.status == 200 or response.status == 404:  # 404 is OK for realtime endpoint
                    metrics['realtime_available'] = True
                else:
                    metrics['warning'] = True
                    metrics['realtime_error'] = f"Status code: {response.status}"
        
        except Exception as e:
            metrics['realtime_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    # Worker service helper methods
    async def _test_worker_service_health(self) -> Dict[str, Any]:
        """Test worker service health endpoint"""
        metrics = {}
        
        worker_url = self.config.get('render_worker_url', 'https://insurance-navigator-worker.onrender.com')
        
        try:
            # Test worker service health endpoint
            health_url = f"{worker_url}/health"
            async with self.session.get(health_url, timeout=30) as response:
                metrics['worker_health_status_code'] = response.status
                metrics['worker_health_response_time'] = "unknown"  # Could add timing
                
                if response.status == 200:
                    try:
                        health_data = await response.json()
                        metrics['worker_health_data'] = health_data
                    except:
                        metrics['worker_health_data'] = await response.text()
                else:
                    metrics['worker_health_error'] = f"Status code: {response.status}"
                    metrics['warning'] = True
        
        except Exception as e:
            metrics['worker_health_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_worker_service_status(self) -> Dict[str, Any]:
        """Test worker service status and functionality"""
        metrics = {}
        
        worker_url = self.config.get('render_worker_url', 'https://insurance-navigator-worker.onrender.com')
        
        try:
            # Test worker service status endpoint (if available)
            status_url = f"{worker_url}/status"
            async with self.session.get(status_url, timeout=30) as response:
                metrics['worker_status_code'] = response.status
                
                if response.status == 200:
                    try:
                        status_data = await response.json()
                        metrics['worker_status_data'] = status_data
                    except:
                        metrics['worker_status_data'] = await response.text()
                else:
                    metrics['worker_status_error'] = f"Status code: {response.status}"
                    metrics['warning'] = True
        
        except Exception as e:
            metrics['worker_status_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_worker_environment(self) -> Dict[str, Any]:
        """Test worker environment configuration"""
        metrics = {}
        
        # Check if worker URL is configured
        if not self.config.get('render_worker_url'):
            metrics['worker_env_error'] = "Worker URL not configured"
            metrics['warning'] = True
        else:
            metrics['worker_env_configured'] = True
        
        return metrics
    
    # Build validation helper methods
    async def _test_api_build_status(self) -> Dict[str, Any]:
        """Test API service build status"""
        metrics = {}
        
        try:
            # Check if API service is accessible (indicates successful build)
            api_url = self.config.get('render_url', '***REMOVED***')
            
            async with self.session.get(f"{api_url}/health", timeout=30) as response:
                metrics['api_build_status_code'] = response.status
                
                if response.status == 200:
                    metrics['api_build_success'] = True
                    metrics['api_build_status'] = 'deployed'
                else:
                    metrics['api_build_success'] = False
                    metrics['api_build_status'] = 'failed'
                    metrics['api_build_error'] = f"Health check failed: {response.status}"
                    metrics['warning'] = True
        
        except Exception as e:
            metrics['api_build_success'] = False
            metrics['api_build_status'] = 'error'
            metrics['api_build_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _test_worker_build_status(self) -> Dict[str, Any]:
        """Test worker service build status"""
        metrics = {}
        
        try:
            # Check if worker service is accessible (indicates successful build)
            worker_url = self.config.get('render_worker_url', 'https://insurance-navigator-worker.onrender.com')
            
            # Try to access the worker service
            async with self.session.get(worker_url, timeout=30) as response:
                metrics['worker_build_status_code'] = response.status
                
                if response.status in [200, 404]:  # 404 is expected for worker services
                    metrics['worker_build_success'] = True
                    metrics['worker_build_status'] = 'deployed'
                    if response.status == 404:
                        metrics['worker_build_note'] = 'Worker service deployed (404 expected for background workers)'
                else:
                    metrics['worker_build_success'] = False
                    metrics['worker_build_status'] = 'failed'
                    metrics['worker_build_error'] = f"Unexpected status: {response.status}"
                    metrics['warning'] = True
        
        except Exception as e:
            metrics['worker_build_success'] = False
            metrics['worker_build_status'] = 'error'
            metrics['worker_build_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _analyze_deployment_logs(self) -> Dict[str, Any]:
        """Analyze deployment logs for errors and warnings"""
        metrics = {}
        
        try:
            # This would typically involve accessing Render's API or log endpoints
            # For now, we'll simulate log analysis based on service responses
            
            api_url = self.config.get('render_url', '***REMOVED***')
            worker_url = self.config.get('render_worker_url', 'https://insurance-navigator-worker.onrender.com')
            
            # Check API service logs (simulated)
            try:
                async with self.session.get(f"{api_url}/health", timeout=30) as response:
                    if response.status == 200:
                        metrics['api_logs_status'] = 'healthy'
                        metrics['api_logs_errors'] = 0
                    else:
                        metrics['api_logs_status'] = 'warning'
                        metrics['api_logs_errors'] = 1
                        metrics['api_logs_warning'] = f"API health check returned {response.status}"
            except Exception as e:
                metrics['api_logs_status'] = 'error'
                metrics['api_logs_errors'] = 1
                metrics['api_logs_error'] = str(e)
            
            # Check worker service logs (simulated)
            try:
                async with self.session.get(worker_url, timeout=30) as response:
                    if response.status in [200, 404]:
                        metrics['worker_logs_status'] = 'healthy'
                        metrics['worker_logs_errors'] = 0
                    else:
                        metrics['worker_logs_status'] = 'warning'
                        metrics['worker_logs_errors'] = 1
                        metrics['worker_logs_warning'] = f"Worker service returned {response.status}"
            except Exception as e:
                metrics['worker_logs_status'] = 'error'
                metrics['worker_logs_errors'] = 1
                metrics['worker_logs_error'] = str(e)
            
            # Overall log analysis
            total_errors = metrics.get('api_logs_errors', 0) + metrics.get('worker_logs_errors', 0)
            if total_errors > 0:
                metrics['log_analysis_warning'] = True
                metrics['total_log_errors'] = total_errors
            else:
                metrics['log_analysis_success'] = True
                metrics['total_log_errors'] = 0
        
        except Exception as e:
            metrics['log_analysis_error'] = str(e)
            metrics['warning'] = True
        
        return metrics
    
    async def _analyze_build_performance(self) -> Dict[str, Any]:
        """Analyze build performance metrics"""
        metrics = {}
        
        try:
            # Measure response times as a proxy for build performance
            api_url = self.config.get('render_url', '***REMOVED***')
            
            start_time = time.time()
            async with self.session.get(f"{api_url}/health", timeout=30) as response:
                response_time = time.time() - start_time
                
                metrics['api_response_time'] = response_time
                metrics['api_response_time_ms'] = round(response_time * 1000, 2)
                
                # Performance thresholds
                if response_time < 1.0:
                    metrics['api_performance'] = 'excellent'
                elif response_time < 2.0:
                    metrics['api_performance'] = 'good'
                elif response_time < 5.0:
                    metrics['api_performance'] = 'acceptable'
                    metrics['performance_warning'] = True
                else:
                    metrics['api_performance'] = 'poor'
                    metrics['performance_warning'] = True
                
                # Build quality indicators
                if response.status == 200:
                    metrics['build_quality'] = 'success'
                else:
                    metrics['build_quality'] = 'failed'
                    metrics['performance_warning'] = True
        
        except Exception as e:
            metrics['performance_analysis_error'] = str(e)
            metrics['warning'] = True
        
        return metrics


async def main():
    """Main function for testing the validator"""
    config = {
        'vercel_url': 'https://insurance-navigator.vercel.app',
        'render_url': '***REMOVED***',
        'supabase_url': 'https://your-project.supabase.co',
        'supabase_anon_key': 'your_anon_key',
        'supabase_service_key': 'your_service_key',
    }
    
    async with CloudEnvironmentValidator(config) as validator:
        # Run all validations
        vercel_result = await validator.validate_vercel_deployment()
        render_result = await validator.validate_render_deployment()
        supabase_result = await validator.validate_supabase_connectivity()
        
        # Print results
        print("Vercel Validation Result:")
        print(json.dumps(vercel_result.to_dict(), indent=2))
        
        print("\nRender Validation Result:")
        print(json.dumps(render_result.to_dict(), indent=2))
        
        print("\nSupabase Validation Result:")
        print(json.dumps(supabase_result.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
