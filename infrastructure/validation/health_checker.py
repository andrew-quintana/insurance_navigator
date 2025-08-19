#!/usr/bin/env python3
"""
Health Check Framework
003 Worker Refactor - Phase 2

Comprehensive health checking for all services in the infrastructure.
"""

import asyncio
import httpx
import json
import logging
import psycopg2
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service: str
    endpoint: str
    status_code: int
    response_time_ms: float
    healthy: bool
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ServiceHealth:
    """Overall health status of a service"""
    service: str
    overall_healthy: bool
    last_check: str
    consecutive_failures: int
    uptime_percentage: float
    average_response_time_ms: float
    health_checks: List[HealthCheckResult]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.service_health: Dict[str, ServiceHealth] = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all configured services"""
        services = self.config.get('services', {})
        results = {}
        
        for service_name, service_config in services.items():
            try:
                service_health = await self._check_service_health(service_name, service_config)
                results[service_name] = service_health
                self.service_health[service_name] = service_health
            except Exception as e:
                self.logger.error(f"Failed to check service {service_name}: {e}")
                # Create failed health result
                failed_health = ServiceHealth(
                    service=service_name,
                    overall_healthy=False,
                    last_check=datetime.utcnow().isoformat(),
                    consecutive_failures=1,
                    uptime_percentage=0.0,
                    average_response_time_ms=0.0,
                    health_checks=[]
                )
                results[service_name] = failed_health
        
        return results
    
    async def _check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> ServiceHealth:
        """Check health of a specific service"""
        health_checks = []
        overall_healthy = True
        total_response_time = 0.0
        successful_checks = 0
        
        # Check main health endpoint
        if 'health_endpoint' in service_config:
            health_result = await self._check_health_endpoint(service_name, service_config)
            health_checks.append(health_result)
            
            if not health_result.healthy:
                overall_healthy = False
            
            if health_result.healthy:
                total_response_time += health_result.response_time_ms
                successful_checks += 1
        
        # Check additional endpoints
        for endpoint in service_config.get('endpoints', []):
            endpoint_result = await self._check_endpoint(service_name, service_config, endpoint)
            health_checks.append(endpoint_result)
            
            if not endpoint_result.healthy:
                overall_healthy = False
            
            if endpoint_result.healthy:
                total_response_time += endpoint_result.response_time_ms
                successful_checks += 1
        
        # Calculate metrics
        average_response_time = total_response_time / max(successful_checks, 1)
        
        # Update health history
        if service_name not in self.health_history:
            self.health_history[service_name] = []
        
        self.health_history[service_name].extend(health_checks)
        
        # Keep only last 100 checks for history
        if len(self.health_history[service_name]) > 100:
            self.health_history[service_name] = self.health_history[service_name][-100:]
        
        # Calculate uptime percentage
        uptime_percentage = self._calculate_uptime_percentage(service_name)
        
        # Count consecutive failures
        consecutive_failures = self._count_consecutive_failures(service_name)
        
        return ServiceHealth(
            service=service_name,
            overall_healthy=overall_healthy,
            last_check=datetime.utcnow().isoformat(),
            consecutive_failures=consecutive_failures,
            uptime_percentage=uptime_percentage,
            average_response_time_ms=average_response_time,
            health_checks=health_checks
        )
    
    async def _check_health_endpoint(self, service_name: str, service_config: Dict[str, Any]) -> HealthCheckResult:
        """Check the main health endpoint of a service"""
        try:
            host = service_config.get('host', 'localhost')
            port = service_config.get('port', 80)
            health_endpoint = service_config.get('health_endpoint', '/health')
            
            url = f"http://{host}:{port}{health_endpoint}"
            
            start_time = time.time()
            response = await self.http_client.get(url)
            response_time = (time.time() - start_time) * 1000
            
            healthy = response.status_code == 200
            
            return HealthCheckResult(
                service=service_name,
                endpoint=health_endpoint,
                status_code=response.status_code,
                response_time_ms=response_time,
                healthy=healthy,
                metadata={
                    'url': url,
                    'response_headers': dict(response.headers),
                    'response_body': response.text[:500] if response.text else None
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service=service_name,
                endpoint=service_config.get('health_endpoint', '/health'),
                status_code=0,
                response_time_ms=0.0,
                healthy=False,
                error_message=str(e)
            )
    
    async def _check_endpoint(self, service_name: str, service_config: Dict[str, Any], endpoint: str) -> HealthCheckResult:
        """Check a specific endpoint of a service"""
        try:
            host = service_config.get('host', 'localhost')
            port = service_config.get('port', 80)
            
            url = f"http://{host}:{port}{endpoint}"
            
            start_time = time.time()
            response = await self.http_client.get(url)
            response_time = (time.time() - start_time) * 1000
            
            # Consider endpoint healthy if it responds (even with non-200 status)
            healthy = response.status_code < 500
            
            return HealthCheckResult(
                service=service_name,
                endpoint=endpoint,
                status_code=response.status_code,
                response_time_ms=response_time,
                healthy=healthy,
                metadata={
                    'url': url,
                    'response_headers': dict(response.headers),
                    'response_body': response.text[:500] if response.text else None
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service=service_name,
                endpoint=endpoint,
                status_code=0,
                response_time_ms=0.0,
                healthy=False,
                error_message=str(e)
            )
    
    async def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and health"""
        try:
            db_config = self.config.get('database', {})
            
            start_time = time.time()
            
            # Test connection
            conn = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                database=db_config.get('database', 'postgres'),
                user=db_config.get('user', 'postgres'),
                password=db_config.get('password', 'postgres')
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            # Test pgvector extension if available
            try:
                cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                pgvector_available = cursor.fetchone() is not None
            except:
                pgvector_available = False
            
            cursor.close()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service="database",
                endpoint="connection",
                status_code=200,
                response_time_ms=response_time,
                healthy=True,
                metadata={
                    'version': version[0] if version else 'unknown',
                    'pgvector_available': pgvector_available,
                    'host': db_config.get('host'),
                    'port': db_config.get('port'),
                    'database': db_config.get('database')
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="database",
                endpoint="connection",
                status_code=0,
                response_time_ms=0.0,
                healthy=False,
                error_message=str(e)
            )
    
    async def check_storage_health(self) -> HealthCheckResult:
        """Check storage service health"""
        try:
            storage_config = self.config.get('storage', {})
            
            if not storage_config:
                return HealthCheckResult(
                    service="storage",
                    endpoint="status",
                    status_code=200,
                    response_time_ms=0.0,
                    healthy=True,
                    metadata={'message': 'No storage configuration'}
                )
            
            # For local Supabase storage simulation, check if directory exists
            storage_path = storage_config.get('local_path')
            if storage_path:
                path = Path(storage_path)
                if path.exists() and path.is_dir():
                    return HealthCheckResult(
                        service="storage",
                        endpoint="status",
                        status_code=200,
                        response_time_ms=0.0,
                        healthy=True,
                        metadata={
                            'type': 'local',
                            'path': str(path),
                            'exists': True,
                            'is_directory': True
                        }
                    )
                else:
                    return HealthCheckResult(
                        service="storage",
                        endpoint="status",
                        status_code=404,
                        response_time_ms=0.0,
                        healthy=False,
                        error_message=f"Storage path {storage_path} does not exist or is not a directory"
                    )
            
            # For remote storage, check connectivity
            if 'host' in storage_config:
                host = storage_config['host']
                port = storage_config.get('port', 80)
                
                url = f"http://{host}:{port}/health"
                
                start_time = time.time()
                response = await self.http_client.get(url)
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    service="storage",
                    endpoint="health",
                    status_code=response.status_code,
                    response_time_ms=response_time,
                    healthy=response.status_code == 200,
                    metadata={
                        'url': url,
                        'type': 'remote'
                    }
                )
            
            return HealthCheckResult(
                service="storage",
                endpoint="status",
                status_code=200,
                response_time_ms=0.0,
                healthy=True,
                metadata={'message': 'Storage service available'}
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="storage",
                endpoint="status",
                status_code=0,
                response_time_ms=0.0,
                healthy=False,
                error_message=str(e)
            )
    
    async def check_external_services(self) -> List[HealthCheckResult]:
        """Check external service dependencies"""
        external_services = self.config.get('external_services', {})
        results = []
        
        for service_name, service_config in external_services.items():
            try:
                if service_name == 'llamaparse':
                    result = await self._check_llamaparse_service(service_config)
                elif service_name == 'openai':
                    result = await self._check_openai_service(service_config)
                else:
                    result = await self._check_generic_external_service(service_name, service_config)
                
                results.append(result)
                
            except Exception as e:
                results.append(HealthCheckResult(
                    service=service_name,
                    endpoint="health",
                    status_code=0,
                    response_time_ms=0.0,
                    healthy=False,
                    error_message=str(e)
                ))
        
        return results
    
    async def _check_llamaparse_service(self, service_config: Dict[str, Any]) -> HealthCheckResult:
        """Check LlamaParse service health"""
        try:
            host = service_config.get('host', 'localhost')
            port = service_config.get('port', 8001)
            
            url = f"http://{host}:{port}/health"
            
            start_time = time.time()
            response = await self.http_client.get(url)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service="llamaparse",
                endpoint="health",
                status_code=response.status_code,
                response_time_ms=response_time,
                healthy=response.status_code == 200,
                metadata={
                    'url': url,
                    'type': 'document_parsing'
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="llamaparse",
                endpoint="health",
                status_code=0,
                response_time_ms=0.0,
                healthy=False,
                error_message=str(e)
            )
    
    async def _check_openai_service(self, service_config: Dict[str, Any]) -> HealthCheckResult:
        """Check OpenAI service health"""
        try:
            host = service_config.get('host', 'localhost')
            port = service_config.get('port', 8002)
            
            url = f"http://{host}:{port}/health"
            
            start_time = time.time()
            response = await self.http_client.get(url)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service="openai",
                endpoint="health",
                status_code=response.status_code,
                response_time_ms=response_time,
                healthy=response.status_code == 200,
                metadata={
                    'url': url,
                    'type': 'ai_processing'
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="openai",
                endpoint="health",
                status_code=0,
                response_time_ms=0.0,
                healthy=False,
                error_message=str(e)
            )
    
    async def _check_generic_external_service(self, service_name: str, service_config: Dict[str, Any]) -> HealthCheckResult:
        """Check generic external service health"""
        try:
            host = service_config.get('host', 'localhost')
            port = service_config.get('port', 80)
            endpoint = service_config.get('health_endpoint', '/health')
            
            url = f"http://{host}:{port}{endpoint}"
            
            start_time = time.time()
            response = await self.http_client.get(url)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=service_name,
                endpoint=endpoint,
                status_code=response.status_code,
                response_time_ms=response_time,
                healthy=response.status_code == 200,
                metadata={
                    'url': url,
                    'type': 'external'
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service=service_name,
                endpoint="health",
                status_code=0,
                response_time_ms=0.0,
                healthy=False,
                error_message=str(e)
            )
    
    def _calculate_uptime_percentage(self, service_name: str) -> float:
        """Calculate uptime percentage for a service"""
        if service_name not in self.health_history:
            return 100.0
        
        checks = self.health_history[service_name]
        if not checks:
            return 100.0
        
        healthy_checks = sum(1 for check in checks if check.healthy)
        return (healthy_checks / len(checks)) * 100.0
    
    def _count_consecutive_failures(self, service_name: str) -> int:
        """Count consecutive failures for a service"""
        if service_name not in self.health_history:
            return 0
        
        checks = self.health_history[service_name]
        if not checks:
            return 0
        
        consecutive_failures = 0
        for check in reversed(checks):
            if not check.healthy:
                consecutive_failures += 1
            else:
                break
        
        return consecutive_failures
    
    def get_overall_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        if not self.service_health:
            return {
                'overall_healthy': False,
                'message': 'No health checks performed yet',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        total_services = len(self.service_health)
        healthy_services = sum(1 for health in self.service_health.values() if health.overall_healthy)
        
        overall_healthy = healthy_services == total_services
        
        # Calculate average metrics
        total_uptime = sum(health.uptime_percentage for health in self.service_health.values())
        average_uptime = total_uptime / total_services if total_services > 0 else 0
        
        total_response_time = sum(health.average_response_time_ms for health in self.service_health.values())
        average_response_time = total_response_time / total_services if total_services > 0 else 0
        
        return {
            'overall_healthy': overall_healthy,
            'total_services': total_services,
            'healthy_services': healthy_services,
            'unhealthy_services': total_services - healthy_services,
            'average_uptime_percentage': average_uptime,
            'average_response_time_ms': average_response_time,
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                name: health.to_dict() for name, health in self.service_health.items()
            }
        }
    
    def save_health_report(self, filename: str = None) -> str:
        """Save health report to file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"
        
        report = self.get_overall_health_summary()
        
        # Ensure reports directory exists
        reports_dir = Path("infrastructure/validation/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reports_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(report_path)
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


async def main():
    """Main function for testing"""
    health_checker = HealthChecker("infrastructure/config/deployment_config.yaml")
    
    try:
        print("🏥 Starting comprehensive health check...")
        
        # Check all services
        service_health = await health_checker.check_all_services()
        
        # Check database
        db_health = await health_checker.check_database_health()
        
        # Check storage
        storage_health = await health_checker.check_storage_health()
        
        # Check external services
        external_health = await health_checker.check_external_services()
        
        # Get overall summary
        summary = health_checker.get_overall_health_summary()
        
        print(f"\n📊 Health Check Summary:")
        print(f"Overall Healthy: {summary['overall_healthy']}")
        print(f"Total Services: {summary['total_services']}")
        print(f"Healthy Services: {summary['healthy_services']}")
        print(f"Unhealthy Services: {summary['unhealthy_services']}")
        print(f"Average Uptime: {summary['average_uptime_percentage']:.1f}%")
        print(f"Average Response Time: {summary['average_response_time_ms']:.1f}ms")
        
        # Save report
        report_path = health_checker.save_health_report()
        print(f"\n📄 Health report saved to: {report_path}")
        
        # Print service details
        print(f"\n🔍 Service Details:")
        for service_name, health in service_health.items():
            status_icon = "✅" if health.overall_healthy else "❌"
            print(f"  {status_icon} {service_name}: {health.overall_healthy}")
            print(f"    Uptime: {health.uptime_percentage:.1f}%")
            print(f"    Avg Response: {health.average_response_time_ms:.1f}ms")
            print(f"    Consecutive Failures: {health.consecutive_failures}")
        
        # Print database health
        db_status_icon = "✅" if db_health.healthy else "❌"
        print(f"\n🗄️  Database: {db_status_icon} {db_health.healthy}")
        if db_health.metadata:
            print(f"  Version: {db_health.metadata.get('version', 'unknown')}")
            print(f"  pgvector: {db_health.metadata.get('pgvector_available', False)}")
        
        # Print storage health
        storage_status_icon = "✅" if storage_health.healthy else "❌"
        print(f"\n💾 Storage: {storage_status_icon} {storage_health.healthy}")
        
        # Print external services
        print(f"\n🌐 External Services:")
        for ext_health in external_health:
            ext_status_icon = "✅" if ext_health.healthy else "❌"
            print(f"  {ext_status_icon} {ext_health.service}: {ext_health.healthy}")
        
    finally:
        await health_checker.close()


if __name__ == "__main__":
    asyncio.run(main())
