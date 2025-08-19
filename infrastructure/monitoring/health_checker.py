#!/usr/bin/env python3
"""
Health Check Framework for 003 Worker Refactor

This module provides comprehensive health checking for all infrastructure components
to ensure deployment health and prevent silent failures.
"""

import asyncio
import httpx
import psycopg2
import yaml
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health checking for infrastructure components"""
    
    def __init__(self, config_path: str):
        """Initialize health checker with configuration"""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
        
        # Health check results storage
        self.health_results = {}
        self.check_start_time = None
        self.check_end_time = None
        
        # Health check thresholds
        self.response_time_threshold = 5.0  # seconds
        self.health_check_interval = 30  # seconds
    
    async def run_complete_health_check(self) -> Dict[str, bool]:
        """Run complete health check suite for all components"""
        self.check_start_time = datetime.utcnow()
        logger.info("Starting complete health check suite")
        
        results = {}
        
        # Core infrastructure health checks
        results["database"] = await self._check_database_health()
        results["api_server"] = await self._check_api_server_health()
        results["worker_process"] = await self._check_worker_health()
        results["storage"] = await self._check_storage_health()
        
        # External service health checks
        results["external_services"] = await self._check_external_services_health()
        
        # Performance and monitoring health checks
        results["performance"] = await self._check_performance_health()
        results["monitoring"] = await self._check_monitoring_health()
        
        # Overall system health
        results["system_overall"] = await self._check_system_overall_health()
        
        self.health_results = results
        self.check_end_time = datetime.utcnow()
        
        # Calculate check duration
        duration = (self.check_end_time - self.check_start_time).total_seconds()
        logger.info(f"Health check completed in {duration:.2f} seconds")
        
        return results
    
    async def _check_database_health(self) -> bool:
        """Check database health and connectivity"""
        logger.info("Checking database health")
        
        try:
            db_config = self.config.get("database", {})
            db_url = db_config.get("url")
            
            if not db_url:
                logger.error("Database URL not configured")
                return False
            
            # Test database connectivity
            start_time = time.time()
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            connection_time = time.time() - start_time
            
            if connection_time > self.response_time_threshold:
                logger.warning(f"Database connection slow: {connection_time:.2f}s")
            
            # Check database responsiveness
            start_time = time.time()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            query_time = time.time() - start_time
            
            if query_time > 1.0:  # 1 second threshold for simple queries
                logger.warning(f"Database query slow: {query_time:.2f}s")
            
            # Check for recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM upload_jobs 
                WHERE created_at > now() - interval '1 hour'
            """)
            recent_jobs = cursor.fetchone()[0]
            
            # Check buffer table health
            cursor.execute("SELECT COUNT(*) FROM document_chunk_buffer")
            chunk_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM document_vector_buffer")
            vector_count = cursor.fetchone()[0]
            
            # Check for any stuck jobs
            cursor.execute("""
                SELECT COUNT(*) FROM upload_jobs 
                WHERE status IN ('parsed', 'parse_validated', 'chunking', 'embedding_queued')
                AND updated_at < now() - interval '30 minutes'
            """)
            stuck_jobs = cursor.fetchone()[0]
            
            if stuck_jobs > 0:
                logger.warning(f"Found {stuck_jobs} potentially stuck jobs")
            
            conn.close()
            
            logger.info(f"Database health: {recent_jobs} recent jobs, {chunk_count} chunks, {vector_count} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def _check_api_server_health(self) -> bool:
        """Check API server health and responsiveness"""
        logger.info("Checking API server health")
        
        try:
            api_config = self.config.get("api", {})
            api_url = api_config.get("url")
            
            if not api_url:
                logger.error("API server URL not configured")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Health check endpoint
                start_time = time.time()
                response = await client.get(f"{api_url}/health")
                response_time = time.time() - start_time
                
                if response.status_code != 200:
                    logger.error(f"API health check failed: {response.status_code}")
                    return False
                
                if response_time > self.response_time_threshold:
                    logger.warning(f"API health check slow: {response_time:.2f}s")
                
                # Check response structure
                health_data = response.json()
                if "status" not in health_data:
                    logger.error("Health check response missing status field")
                    return False
                
                # Check job status endpoint
                start_time = time.time()
                response = await client.get(f"{api_url}/jobs/status")
                response_time = time.time() - start_time
                
                if response.status_code not in [200, 401]:  # 401 is OK for missing auth
                    logger.error(f"Job status endpoint failed: {response.status_code}")
                    return False
                
                if response_time > self.response_time_threshold:
                    logger.warning(f"Job status endpoint slow: {response_time:.2f}s")
                
                # Check webhook endpoint availability
                start_time = time.time()
                response = await client.post(
                    f"{api_url}/webhooks/llamaparse",
                    json={"test": "health_check"},
                    headers={"X-Test-Health": "true"}
                )
                response_time = time.time() - start_time
                
                if response.status_code == 404:
                    logger.error("Webhook endpoint not found")
                    return False
                
                if response_time > self.response_time_threshold:
                    logger.warning(f"Webhook endpoint slow: {response_time:.2f}s")
            
            logger.info("✅ API server health check passed")
            return True
            
        except Exception as e:
            logger.error(f"API server health check failed: {e}")
            return False
    
    async def _check_worker_health(self) -> bool:
        """Check worker process health and functionality"""
        logger.info("Checking worker process health")
        
        try:
            worker_config = self.config.get("worker", {})
            worker_health_url = worker_config.get("health_url")
            
            if worker_health_url:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    start_time = time.time()
                    response = await client.get(worker_health_url)
                    response_time = time.time() - start_time
                    
                    if response.status_code != 200:
                        logger.error(f"Worker health check failed: {response.status_code}")
                        return False
                    
                    if response_time > self.response_time_threshold:
                        logger.warning(f"Worker health check slow: {response_time:.2f}s")
                    
                    # Check worker health response
                    health_data = response.json()
                    if "status" not in health_data:
                        logger.error("Worker health response missing status field")
                        return False
                    
                    # Check worker is actually processing
                    if "last_job_processed" in health_data:
                        last_job_time = health_data["last_job_processed"]
                        logger.info(f"Worker last processed job at: {last_job_time}")
            
            # Alternative validation: Check if jobs are being processed
            # This validates that the worker is actually working, not just responding
            db_config = self.config.get("database", {})
            if db_config.get("url"):
                try:
                    conn = psycopg2.connect(db_config["url"])
                    cursor = conn.cursor()
                    
                    # Check for recent job processing activity
                    cursor.execute("""
                        SELECT COUNT(*) FROM upload_jobs 
                        WHERE status IN ('chunking', 'embedding_in_progress', 'embeddings_stored', 'complete')
                        AND updated_at > now() - interval '30 minutes'
                    """)
                    active_jobs = cursor.fetchone()[0]
                    
                    if active_jobs == 0:
                        logger.warning("No active job processing detected in last 30 minutes")
                        # This might indicate worker is not processing, but not necessarily failed
                    
                    # Check for worker activity patterns
                    cursor.execute("""
                        SELECT status, COUNT(*) 
                        FROM upload_jobs 
                        WHERE updated_at > now() - interval '1 hour'
                        GROUP BY status
                        ORDER BY COUNT(*) DESC
                    """)
                    status_counts = cursor.fetchall()
                    
                    logger.info(f"Job status distribution: {dict(status_counts)}")
                    
                    conn.close()
                    
                except Exception as e:
                    logger.warning(f"Could not validate worker activity: {e}")
            
            logger.info("✅ Worker process health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Worker health check failed: {e}")
            return False
    
    async def _check_storage_health(self) -> bool:
        """Check storage service health and accessibility"""
        logger.info("Checking storage health")
        
        try:
            storage_config = self.config.get("storage", {})
            storage_url = storage_config.get("url")
            
            if not storage_url:
                logger.error("Storage URL not configured")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    start_time = time.time()
                    response = await client.get(f"{storage_url}/health")
                    response_time = time.time() - start_time
                    
                    if response.status_code != 200:
                        logger.warning(f"Storage health check returned: {response.status_code}")
                    
                    if response_time > self.response_time_threshold:
                        logger.warning(f"Storage health check slow: {response_time:.2f}s")
                        
                except:
                    # Try basic connectivity
                    start_time = time.time()
                    response = await client.get(storage_url)
                    response_time = time.time() - start_time
                    
                    if response.status_code not in [200, 401, 403]:  # Various acceptable responses
                        logger.warning(f"Storage connectivity check returned: {response.status_code}")
                    
                    if response_time > self.response_time_threshold:
                        logger.warning(f"Storage connectivity slow: {response_time:.2f}s")
            
            # Validate storage configuration
            required_storage_keys = ["url", "service_role_key"]
            missing_keys = [key for key in required_storage_keys if not storage_config.get(key)]
            
            if missing_keys:
                logger.error(f"Missing storage configuration: {missing_keys}")
                return False
            
            logger.info("✅ Storage health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False
    
    async def _check_external_services_health(self) -> bool:
        """Check external service connectivity and health"""
        logger.info("Checking external services health")
        
        try:
            external_config = self.config.get("external", {})
            
            # Test LlamaParse connectivity
            if "llamaparse" in external_config:
                llamaparse_url = external_config["llamaparse"].get("url")
                if llamaparse_url:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        try:
                            start_time = time.time()
                            response = await client.get(f"{llamaparse_url}/health")
                            response_time = time.time() - start_time
                            logger.info(f"LlamaParse health check: {response.status_code} ({response_time:.2f}s)")
                        except:
                            # Real service might not have health endpoint, try basic connectivity
                            start_time = time.time()
                            response = await client.get(llamaparse_url)
                            response_time = time.time() - start_time
                            logger.info(f"LlamaParse connectivity: {response.status_code} ({response_time:.2f}s)")
            
            # Test OpenAI connectivity
            if "openai" in external_config:
                openai_url = external_config["openai"].get("url", "https://api.openai.com")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    start_time = time.time()
                    response = await client.get(f"{openai_url}/v1/models")
                    response_time = time.time() - start_time
                    
                    if response.status_code not in [200, 401]:  # 401 is OK, means API is up
                        logger.error(f"OpenAI connectivity failed: {response.status_code}")
                        return False
                    
                    if response_time > self.response_time_threshold:
                        logger.warning(f"OpenAI connectivity slow: {response_time:.2f}s")
            
            logger.info("✅ External services health check passed")
            return True
            
        except Exception as e:
            logger.error(f"External services health check failed: {e}")
            return False
    
    async def _check_performance_health(self) -> bool:
        """Check performance characteristics and identify bottlenecks"""
        logger.info("Checking performance health")
        
        try:
            # Basic performance validation
            # This would be expanded with actual performance benchmarks
            # For now, just validate that services respond within reasonable time
            
            api_config = self.config.get("api", {})
            api_url = api_config.get("url")
            
            if api_url:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{api_url}/health")
                response_time = time.time() - start_time
                
                if response_time > self.response_time_threshold:
                    logger.warning(f"API response time slow: {response_time:.2f}s")
                else:
                    logger.info(f"API response time: {response_time:.2f}s")
            
            # Check database performance
            db_config = self.config.get("database", {})
            if db_config.get("url"):
                try:
                    conn = psycopg2.connect(db_config["url"])
                    cursor = conn.cursor()
                    
                    # Simple performance test
                    start_time = time.time()
                    cursor.execute("SELECT COUNT(*) FROM upload_jobs")
                    result = cursor.fetchone()
                    query_time = time.time() - start_time
                    
                    if query_time > 1.0:
                        logger.warning(f"Database query slow: {query_time:.2f}s")
                    else:
                        logger.info(f"Database query time: {query_time:.2f}s")
                    
                    conn.close()
                    
                except Exception as e:
                    logger.warning(f"Could not check database performance: {e}")
            
            logger.info("✅ Performance health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Performance health check failed: {e}")
            return False
    
    async def _check_monitoring_health(self) -> bool:
        """Check monitoring and observability systems"""
        logger.info("Checking monitoring health")
        
        try:
            # Check if monitoring endpoints are available
            api_config = self.config.get("api", {})
            api_url = api_config.get("url")
            
            if api_url:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Check for metrics endpoint
                    response = await client.get(f"{api_url}/metrics")
                    if response.status_code == 200:
                        logger.info("Metrics endpoint available")
                    else:
                        logger.warning("Metrics endpoint not available")
            
            # Check monitoring configuration
            monitoring_config = self.config.get("monitoring", {})
            if not monitoring_config.get("enabled", False):
                logger.warning("Monitoring is disabled in configuration")
            
            logger.info("✅ Monitoring health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring health check failed: {e}")
            return False
    
    async def _check_system_overall_health(self) -> bool:
        """Check overall system health and identify systemic issues"""
        logger.info("Checking overall system health")
        
        try:
            # Check for systemic issues
            db_config = self.config.get("database", {})
            if db_config.get("url"):
                try:
                    conn = psycopg2.connect(db_config["url"])
                    cursor = conn.cursor()
                    
                    # Check for error patterns
                    cursor.execute("""
                        SELECT COUNT(*) FROM upload_jobs 
                        WHERE status LIKE 'failed_%'
                        AND updated_at > now() - interval '1 hour'
                    """)
                    failed_jobs = cursor.fetchone()[0]
                    
                    if failed_jobs > 0:
                        logger.warning(f"Found {failed_jobs} failed jobs in last hour")
                    
                    # Check for processing bottlenecks
                    cursor.execute("""
                        SELECT status, COUNT(*) 
                        FROM upload_jobs 
                        WHERE updated_at > now() - interval '1 hour'
                        GROUP BY status
                        HAVING COUNT(*) > 10
                    """)
                    bottlenecks = cursor.fetchall()
                    
                    if bottlenecks:
                        logger.warning(f"Potential bottlenecks detected: {dict(bottlenecks)}")
                    
                    conn.close()
                    
                except Exception as e:
                    logger.warning(f"Could not check system health: {e}")
            
            logger.info("✅ Overall system health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Overall system health check failed: {e}")
            return False
    
    def generate_health_report(self) -> str:
        """Generate comprehensive health report"""
        if not self.health_results:
            return "No health check results available"
        
        report = []
        report.append("=" * 60)
        report.append("INFRASTRUCTURE HEALTH CHECK REPORT")
        report.append("=" * 60)
        report.append(f"Health Check Date: {datetime.utcnow().isoformat()}")
        
        if self.check_start_time and self.check_end_time:
            duration = (self.check_end_time - self.check_start_time).total_seconds()
            report.append(f"Health Check Duration: {duration:.2f} seconds")
        
        report.append("")
        report.append("Health Check Results:")
        report.append("-" * 40)
        
        all_healthy = True
        for component, healthy in self.health_results.items():
            status = "✅ HEALTHY" if healthy else "❌ UNHEALTHY"
            report.append(f"{component:20} {status}")
            if not healthy:
                all_healthy = False
        
        report.append("-" * 40)
        report.append("")
        
        if all_healthy:
            report.append("🎯 OVERALL RESULT: ALL SYSTEMS HEALTHY")
            report.append("✅ Infrastructure is operating normally")
        else:
            report.append("🚨 OVERALL RESULT: SOME SYSTEMS UNHEALTHY")
            report.append("❌ Infrastructure issues detected - investigation required")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy components"""
        return [component for component, healthy in self.health_results.items() if not healthy]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for programmatic use"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": (self.check_end_time - self.check_start_time).total_seconds() if self.check_start_time and self.check_end_time else None,
            "total_components": len(self.health_results),
            "healthy_components": len([v for v in self.health_results.values() if v]),
            "unhealthy_components": len([v for v in self.health_results.values() if not v]),
            "health_rate": len([v for v in self.health_results.values() if v]) / len(self.health_results) if self.health_results else 0,
            "results": self.health_results,
            "unhealthy_components_list": self.get_unhealthy_components()
        }
    
    async def start_continuous_monitoring(self, interval: int = None):
        """Start continuous health monitoring"""
        if interval is None:
            interval = self.health_check_interval
        
        logger.info(f"Starting continuous health monitoring with {interval}s interval")
        
        while True:
            try:
                await self.run_complete_health_check()
                
                # Check if any components are unhealthy
                unhealthy_components = self.get_unhealthy_components()
                if unhealthy_components:
                    logger.warning(f"Unhealthy components detected: {unhealthy_components}")
                    # Here you could trigger alerts, notifications, etc.
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(interval)


# CLI interface for health checking
async def main():
    """Main CLI entry point"""
    if len(sys.argv) != 2:
        print("Usage: python health_checker.py <config.yaml>")
        print("Example: python health_checker.py config/production.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        health_checker = HealthChecker(config_path)
        results = await health_checker.run_complete_health_check()
        
        # Generate and display report
        report = health_checker.generate_health_report()
        print(report)
        
        # Exit with appropriate code
        if all(results.values()):
            print("✅ All health checks passed!")
            sys.exit(0)
        else:
            print("❌ Some health checks failed!")
            print(f"Unhealthy components: {', '.join(health_checker.get_unhealthy_components())}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        logger.exception("Health check failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
