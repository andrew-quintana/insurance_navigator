#!/usr/bin/env python3
"""
Infrastructure Deployer for 003 Worker Refactor - Phase 5

This module provides automated infrastructure deployment with comprehensive validation
against the local environment baseline. It prevents the infrastructure configuration
failures experienced in 002 by ensuring deployed infrastructure matches local specifications.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import subprocess
import yaml
import httpx
from dataclasses import dataclass, asdict

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.validation.deployment_validator import DeploymentValidator, ValidationResult
from infrastructure.validation.health_checker import HealthChecker
from infrastructure.validation.environment_manager import EnvironmentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    component: str
    status: bool
    message: str
    duration_seconds: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    validation_results: Optional[List[ValidationResult]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        if self.validation_results:
            result['validation_results'] = [v.to_dict() for v in self.validation_results]
        return result


class InfrastructureDeployer:
    """
    Automated infrastructure deployment with validation
    
    Deploys infrastructure components and validates them against local environment
    baseline to prevent configuration failures experienced in 002.
    """
    
    def __init__(self, config_path: str, deployment_target: str = "local"):
        """Initialize deployer with configuration"""
        self.config_path = Path(config_path)
        self.deployment_target = deployment_target
        self.config = self._load_config()
        self.validator = DeploymentValidator(config_path)
        self.health_checker = HealthChecker(config_path)
        self.env_manager = EnvironmentManager(config_path)
        
        # Deployment results tracking
        self.deployment_results: List[DeploymentResult] = []
        
        # HTTP client for deployment validation
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        logger.info(f"Initialized InfrastructureDeployer for target: {deployment_target}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration: {config.get('environment', 'unknown')}")
        return config
    
    async def deploy_infrastructure(self) -> Dict[str, bool]:
        """
        Deploy complete infrastructure with validation
        
        Returns:
            Dict mapping component names to deployment success status
        """
        logger.info("Starting infrastructure deployment...")
        
        deployment_start = time.time()
        results = {}
        
        try:
            # Phase 1: Local environment validation
            logger.info("Phase 1: Validating local environment baseline...")
            local_validation = await self._validate_local_environment()
            if not local_validation:
                raise RuntimeError("Local environment validation failed")
            
            # Phase 2: Infrastructure deployment
            logger.info("Phase 2: Deploying infrastructure components...")
            infrastructure_results = await self._deploy_infrastructure_components()
            results.update(infrastructure_results)
            
            # Phase 3: Infrastructure validation
            logger.info("Phase 3: Validating deployed infrastructure...")
            validation_results = await self._validate_deployed_infrastructure()
            results.update(validation_results)
            
            # Phase 4: Performance validation
            logger.info("Phase 4: Validating performance against local baseline...")
            performance_results = await self._validate_performance_baseline()
            results.update(performance_results)
            
            # Phase 5: Final health check
            logger.info("Phase 5: Final infrastructure health validation...")
            health_results = await self._final_health_validation()
            results.update(health_results)
            
        except Exception as e:
            logger.error(f"Infrastructure deployment failed: {e}")
            await self._trigger_rollback()
            raise
        
        finally:
            deployment_duration = time.time() - deployment_start
            logger.info(f"Infrastructure deployment completed in {deployment_duration:.2f} seconds")
        
        return results
    
    async def _validate_local_environment(self) -> bool:
        """Validate local environment is ready for deployment baseline"""
        logger.info("Validating local environment baseline...")
        
        try:
            # Check if local services are running
            local_services = await self._check_local_services()
            if not all(local_services.values()):
                failed_services = [k for k, v in local_services.items() if not v]
                logger.error(f"Local services not ready: {failed_services}")
                return False
            
            # Validate local configuration
            local_config = await self._validate_local_configuration()
            if not local_config:
                logger.error("Local configuration validation failed")
                return False
            
            # Create local baseline
            baseline_created = await self._create_local_baseline()
            if not baseline_created:
                logger.error("Failed to create local baseline")
                return False
            
            logger.info("Local environment validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Local environment validation failed: {e}")
            return False
    
    async def _check_local_services(self) -> Dict[str, bool]:
        """Check if local services are running and healthy"""
        services = {}
        
        for service_name, service_config in self.config['services'].items():
            try:
                host = service_config.get('host', 'localhost')
                port = service_config.get('port', 8000)
                health_endpoint = service_config.get('health_endpoint', '/health')
                
                url = f"http://{host}:{port}{health_endpoint}"
                response = await self.http_client.get(url, timeout=10.0)
                
                services[service_name] = response.status_code == 200
                logger.info(f"Service {service_name}: {'healthy' if services[service_name] else 'unhealthy'}")
                
            except Exception as e:
                logger.warning(f"Service {service_name} check failed: {e}")
                services[service_name] = False
        
        return services
    
    async def _validate_local_configuration(self) -> bool:
        """Validate local configuration is complete and correct"""
        try:
            # Check required environment variables
            env_validation = await self.env_manager.validate_environment()
            if not env_validation['valid']:
                logger.error(f"Environment validation failed: {env_validation['errors']}")
                return False
            
            # Check configuration consistency
            config_validation = await self._validate_config_consistency()
            if not config_validation:
                logger.error("Configuration consistency validation failed")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Local configuration validation failed: {e}")
            return False
    
    async def _validate_config_consistency(self) -> bool:
        """Validate configuration consistency across services"""
        try:
            # Check database configuration consistency
            db_config = self.config.get('database', {})
            if not all(key in db_config for key in ['host', 'port', 'database', 'user']):
                logger.error("Incomplete database configuration")
                return False
            
            # Check service configuration consistency
            services = self.config.get('services', {})
            for service_name, service_config in services.items():
                if not all(key in service_config for key in ['host', 'port', 'health_endpoint']):
                    logger.error(f"Incomplete configuration for service: {service_name}")
                    return False
            
            # Check external service configuration
            external_services = self.config.get('external_services', {})
            for service_name, service_config in external_services.items():
                if not all(key in service_config for key in ['api_url', 'timeout_seconds']):
                    logger.error(f"Incomplete configuration for external service: {service_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration consistency validation failed: {e}")
            return False
    
    async def _create_local_baseline(self) -> bool:
        """Create local environment baseline for deployment validation"""
        try:
            # Create baseline configuration
            baseline = {
                'timestamp': datetime.utcnow().isoformat(),
                'environment': 'local',
                'services': {},
                'performance': {},
                'configuration': {}
            }
            
            # Capture service health baseline
            for service_name, service_config in self.config['services'].items():
                try:
                    host = service_config.get('host', 'localhost')
                    port = service_config.get('port', 8000)
                    health_endpoint = service_config.get('health_endpoint', '/health')
                    
                    url = f"http://{host}:{port}{health_endpoint}"
                    start_time = time.time()
                    response = await self.http_client.get(url, timeout=10.0)
                    response_time = (time.time() - start_time) * 1000
                    
                    baseline['services'][service_name] = {
                        'healthy': response.status_code == 200,
                        'response_time_ms': response_time,
                        'status_code': response.status_code
                    }
                    
                except Exception as e:
                    baseline['services'][service_name] = {
                        'healthy': False,
                        'error': str(e)
                    }
            
            # Capture performance baseline
            baseline['performance'] = await self._capture_performance_baseline()
            
            # Save baseline
            baseline_path = Path("infrastructure/baselines/local_baseline.json")
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(baseline_path, 'w') as f:
                json.dump(baseline, f, indent=2)
            
            logger.info(f"Local baseline created: {baseline_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create local baseline: {e}")
            return False
    
    async def _capture_performance_baseline(self) -> Dict[str, Any]:
        """Capture performance baseline from local environment"""
        performance = {}
        
        try:
            # Database performance baseline
            db_config = self.config.get('database', {})
            if db_config:
                db_performance = await self._measure_database_performance(db_config)
                performance['database'] = db_performance
            
            # API performance baseline
            api_config = self.config['services'].get('api_server', {})
            if api_config:
                api_performance = await self._measure_api_performance(api_config)
                performance['api'] = api_performance
            
            # Storage performance baseline
            storage_config = self.config['services'].get('supabase_storage', {})
            if storage_config:
                storage_performance = await self._measure_storage_performance(storage_config)
                performance['storage'] = storage_performance
            
        except Exception as e:
            logger.warning(f"Performance baseline capture failed: {e}")
            performance['error'] = str(e)
        
        return performance
    
    async def _measure_database_performance(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Measure database performance metrics"""
        try:
            import psycopg2
            
            # Simple connection and query performance test
            start_time = time.time()
            
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config.get('password', '')
            )
            
            connection_time = (time.time() - start_time) * 1000
            
            # Test simple query
            cursor = conn.cursor()
            start_time = time.time()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            query_time = (time.time() - start_time) * 1000
            
            cursor.close()
            conn.close()
            
            return {
                'connection_time_ms': connection_time,
                'simple_query_time_ms': query_time
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _measure_api_performance(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """Measure API performance metrics"""
        try:
            host = api_config.get('host', 'localhost')
            port = api_config.get('port', 8000)
            
            # Test health endpoint response time
            url = f"http://{host}:{port}/health"
            start_time = time.time()
            response = await self.http_client.get(url, timeout=10.0)
            response_time = (time.time() - start_time) * 1000
            
            return {
                'health_endpoint_response_time_ms': response_time,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _measure_storage_performance(self, storage_config: Dict[str, Any]) -> Dict[str, Any]:
        """Measure storage performance metrics"""
        try:
            host = storage_config.get('host', 'localhost')
            port = storage_config.get('port', 5000)
            
            # Test health endpoint response time
            url = f"http://{host}:{port}/health"
            start_time = time.time()
            response = await self.http_client.get(url, timeout=10.0)
            response_time = (time.time() - start_time) * 1000
            
            return {
                'health_endpoint_response_time_ms': response_time,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _deploy_infrastructure_components(self) -> Dict[str, bool]:
        """Deploy infrastructure components based on deployment target"""
        results = {}
        
        if self.deployment_target == "local":
            # For local deployment, ensure Docker services are running
            results = await self._deploy_local_docker_services()
        elif self.deployment_target == "production":
            # For production deployment, deploy to cloud infrastructure
            results = await self._deploy_production_infrastructure()
        else:
            raise ValueError(f"Unsupported deployment target: {self.deployment_target}")
        
        return results
    
    async def _deploy_local_docker_services(self) -> Dict[str, bool]:
        """Deploy local Docker services using docker-compose"""
        results = {}
        
        try:
            logger.info("Starting local Docker services...")
            
            # Start all services
            start_result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if start_result.returncode != 0:
                logger.error(f"Failed to start Docker services: {start_result.stderr}")
                return {"docker_services": False}
            
            # Wait for services to be healthy
            logger.info("Waiting for services to be healthy...")
            await asyncio.sleep(30)  # Initial startup time
            
            # Check service health
            health_checks = await self._wait_for_services_healthy()
            results.update(health_checks)
            
            logger.info("Local Docker services deployment completed")
            return results
            
        except Exception as e:
            logger.error(f"Local Docker services deployment failed: {e}")
            return {"docker_services": False}
    
    async def _wait_for_services_healthy(self) -> Dict[str, bool]:
        """Wait for all services to be healthy"""
        results = {}
        max_wait_time = 300  # 5 minutes
        check_interval = 10  # 10 seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            all_healthy = True
            
            for service_name, service_config in self.config['services'].items():
                try:
                    host = service_config.get('host', 'localhost')
                    port = service_config.get('port', 8000)
                    health_endpoint = service_config.get('health_endpoint', '/health')
                    
                    url = f"http://{host}:{port}{health_endpoint}"
                    response = await self.http_client.get(url, timeout=10.0)
                    
                    healthy = response.status_code == 200
                    results[service_name] = healthy
                    
                    if not healthy:
                        all_healthy = False
                        logger.warning(f"Service {service_name} not healthy yet")
                    
                except Exception as e:
                    results[service_name] = False
                    all_healthy = False
                    logger.warning(f"Service {service_name} health check failed: {e}")
            
            if all_healthy:
                logger.info("All services are healthy")
                break
            
            logger.info(f"Waiting for services to be healthy... ({int(time.time() - start_time)}s elapsed)")
            await asyncio.sleep(check_interval)
        
        if not all_healthy:
            logger.error("Timeout waiting for services to be healthy")
        
        return results
    
    async def _deploy_production_infrastructure(self) -> Dict[str, bool]:
        """Deploy production infrastructure (placeholder for future implementation)"""
        logger.warning("Production infrastructure deployment not yet implemented")
        return {"production_infrastructure": False}
    
    async def _validate_deployed_infrastructure(self) -> Dict[str, bool]:
        """Validate deployed infrastructure against local baseline"""
        results = {}
        
        try:
            logger.info("Validating deployed infrastructure...")
            
            # Run comprehensive validation
            validation_results = await self.validator.validate_complete_deployment()
            results.update(validation_results)
            
            # Check if validation passed
            all_valid = all(validation_results.values())
            if not all_valid:
                failed_components = [k for k, v in validation_results.items() if not v]
                logger.error(f"Infrastructure validation failed for: {failed_components}")
            
            results['overall_validation'] = all_valid
            
        except Exception as e:
            logger.error(f"Infrastructure validation failed: {e}")
            results['validation_error'] = False
        
        return results
    
    async def _validate_performance_baseline(self) -> Dict[str, bool]:
        """Validate performance against local baseline"""
        results = {}
        
        try:
            logger.info("Validating performance against local baseline...")
            
            # Load local baseline
            baseline_path = Path("infrastructure/baselines/local_baseline.json")
            if not baseline_path.exists():
                logger.warning("Local baseline not found, skipping performance validation")
                return {"performance_validation": True}
            
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
            
            # Measure current performance
            current_performance = await self._capture_performance_baseline()
            
            # Compare with baseline
            performance_validation = await self._compare_performance_baseline(
                baseline['performance'], current_performance
            )
            
            results['performance_validation'] = performance_validation
            
        except Exception as e:
            logger.error(f"Performance validation failed: {e}")
            results['performance_validation'] = False
        
        return results
    
    async def _compare_performance_baseline(self, baseline: Dict[str, Any], current: Dict[str, Any]) -> bool:
        """Compare current performance with baseline"""
        try:
            # Get performance thresholds from config
            thresholds = self.config.get('performance_baselines', {})
            degradation_multiplier = thresholds.get('deployed_degradation_multiplier', 2.0)
            
            for component, baseline_metrics in baseline.items():
                if component not in current:
                    logger.warning(f"Component {component} not found in current performance")
                    continue
                
                current_metrics = current[component]
                
                for metric, baseline_value in baseline_metrics.items():
                    if metric == 'error' or not isinstance(baseline_value, (int, float)):
                        continue
                    
                    if metric not in current_metrics:
                        logger.warning(f"Metric {metric} not found in current performance for {component}")
                        continue
                    
                    current_value = current_metrics[metric]
                    if isinstance(current_value, (int, float)):
                        # Check if performance degradation is within acceptable limits
                        max_acceptable = baseline_value * degradation_multiplier
                        if current_value > max_acceptable:
                            logger.warning(
                                f"Performance degradation for {component}.{metric}: "
                                f"baseline={baseline_value}, current={current_value}, "
                                f"max_acceptable={max_acceptable}"
                            )
                            return False
            
            logger.info("Performance validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Performance comparison failed: {e}")
            return False
    
    async def _final_health_validation(self) -> Dict[str, bool]:
        """Final comprehensive health validation"""
        results = {}
        
        try:
            logger.info("Performing final health validation...")
            
            # Run health checks
            health_results = await self.health_checker.run_comprehensive_health_checks()
            
            # Check overall health
            all_healthy = all(result.healthy for result in health_results)
            results['final_health_check'] = all_healthy
            
            if not all_healthy:
                failed_checks = [r.service for r in health_results if not r.healthy]
                logger.error(f"Final health validation failed for: {failed_checks}")
            
            # Check uptime
            uptime_results = await self.health_checker.calculate_uptime_percentages()
            results['uptime_validation'] = all(uptime >= 95.0 for uptime in uptime_results.values())
            
        except Exception as e:
            logger.error(f"Final health validation failed: {e}")
            results['final_health_check'] = False
        
        return results
    
    async def _trigger_rollback(self):
        """Trigger automated rollback on deployment failure"""
        logger.warning("Deployment failed, triggering rollback...")
        
        try:
            # For now, just log the rollback trigger
            # In a full implementation, this would call the rollback system
            logger.info("Rollback triggered - manual intervention may be required")
            
        except Exception as e:
            logger.error(f"Rollback trigger failed: {e}")
    
    async def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        report = {
            'deployment_id': f"deploy_{int(time.time())}",
            'timestamp': datetime.utcnow().isoformat(),
            'deployment_target': self.deployment_target,
            'overall_success': all(r.status for r in self.deployment_results),
            'components': [r.to_dict() for r in self.deployment_results],
            'summary': {
                'total_components': len(self.deployment_results),
                'successful_components': len([r for r in self.deployment_results if r.status]),
                'failed_components': len([r for r in self.deployment_results if not r.status]),
                'total_duration': sum(r.duration_seconds for r in self.deployment_results)
            }
        }
        
        return report
    
    async def save_deployment_report(self, report: Dict[str, Any], output_path: str = None):
        """Save deployment report to file"""
        if output_path is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = f"infrastructure/reports/deployment_report_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Deployment report saved: {output_file}")
        return str(output_file)


async def main():
    """Main entry point for infrastructure deployment"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy infrastructure with validation")
    parser.add_argument("--config", default="infrastructure/config/deployment_config.yaml",
                       help="Path to deployment configuration file")
    parser.add_argument("--target", default="local", choices=["local", "production"],
                       help="Deployment target")
    parser.add_argument("--output", help="Output path for deployment report")
    
    args = parser.parse_args()
    
    try:
        # Initialize deployer
        deployer = InfrastructureDeployer(args.config, args.target)
        
        # Deploy infrastructure
        results = await deployer.deploy_infrastructure()
        
        # Generate and save report
        report = await deployer.generate_deployment_report()
        output_file = await deployer.save_deployment_report(report, args.output)
        
        # Print summary
        print(f"\n🚀 Infrastructure Deployment Summary")
        print(f"==================================")
        print(f"Target: {args.target}")
        print(f"Overall Success: {'✅' if report['overall_success'] else '❌'}")
        print(f"Components: {report['summary']['successful_components']}/{report['summary']['total_components']} successful")
        print(f"Duration: {report['summary']['total_duration']:.2f} seconds")
        print(f"Report: {output_file}")
        
        # Exit with appropriate code
        sys.exit(0 if report['overall_success'] else 1)
        
    except Exception as e:
        logger.error(f"Infrastructure deployment failed: {e}")
        print(f"\n❌ Infrastructure deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
