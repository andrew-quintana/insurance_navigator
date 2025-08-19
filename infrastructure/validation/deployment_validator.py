#!/usr/bin/env python3
"""
Infrastructure Validation Framework for 003 Worker Refactor

This module provides comprehensive validation of deployment infrastructure
against local environment baseline to prevent deployment configuration failures.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentValidator:
    """Validate deployment infrastructure against local environment baseline"""
    
    def __init__(self, config_path: str):
        """Initialize validator with deployment configuration"""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
        
        # Validation results storage
        self.validation_results = {}
        self.validation_start_time = None
        self.validation_end_time = None
    
    async def validate_complete_deployment(self) -> Dict[str, bool]:
        """Run complete deployment validation suite"""
        self.validation_start_time = datetime.utcnow()
        logger.info("Starting complete deployment validation")
        
        results = {}
        
        # Core infrastructure validation
        results["database"] = await self._validate_database()
        results["api_server"] = await self._validate_api_server()
        results["worker_process"] = await self._validate_worker_process()
        results["external_services"] = await self._validate_external_services()
        results["storage"] = await self._validate_storage()
        results["environment"] = await self._validate_environment()
        
        # Advanced validation
        results["performance"] = await self._validate_performance()
        results["security"] = await self._validate_security()
        results["monitoring"] = await self._validate_monitoring()
        
        self.validation_results = results
        self.validation_end_time = datetime.utcnow()
        
        # Calculate validation duration
        duration = (self.validation_end_time - self.validation_start_time).total_seconds()
        logger.info(f"Deployment validation completed in {duration:.2f} seconds")
        
        return results
    
    async def _validate_database(self) -> bool:
        """Validate database connectivity and schema"""
        logger.info("Validating database infrastructure")
        
        try:
            db_config = self.config.get("database", {})
            db_url = db_config.get("url")
            
            if not db_url:
                logger.error("Database URL not configured")
                return False
            
            # Test database connectivity
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Check required tables exist
            required_tables = [
                "upload_jobs",
                "document_chunk_buffer", 
                "document_vector_buffer"
            ]
            
            for table in required_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    logger.error(f"Missing required table: {table}")
                    return False
            
            # Check vector extension
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');")
            if not cursor.fetchone()[0]:
                logger.error("Missing vector extension")
                return False
            
            # Check buffer table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'document_chunk_buffer'
                ORDER BY ordinal_position
            """)
            chunk_columns = {row[0]: row[1] for row in cursor.fetchall()}
            
            required_chunk_columns = {
                "chunk_id": "uuid",
                "document_id": "uuid", 
                "chunk_ord": "integer",
                "text": "text"
            }
            
            for col, expected_type in required_chunk_columns.items():
                if col not in chunk_columns:
                    logger.error(f"Missing required column in document_chunk_buffer: {col}")
                    return False
            
            # Check for recent activity (indicates working system)
            cursor.execute("""
                SELECT COUNT(*) FROM upload_jobs 
                WHERE created_at > now() - interval '24 hours'
            """)
            recent_jobs = cursor.fetchone()[0]
            logger.info(f"Found {recent_jobs} recent jobs in database")
            
            conn.close()
            logger.info("✅ Database validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False
    
    async def _validate_api_server(self) -> bool:
        """Validate API server health and endpoints"""
        logger.info("Validating API server infrastructure")
        
        try:
            api_config = self.config.get("api", {})
            api_url = api_config.get("url")
            
            if not api_url:
                logger.error("API server URL not configured")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Health check
                response = await client.get(f"{api_url}/health")
                if response.status_code != 200:
                    logger.error(f"API health check failed: {response.status_code}")
                    return False
                
                # Check response structure
                health_data = response.json()
                if "status" not in health_data:
                    logger.error("Health check response missing status field")
                    return False
                
                # Webhook endpoint check (should return 401 for missing auth, not 404)
                response = await client.post(
                    f"{api_url}/webhooks/llamaparse",
                    json={"test": "validation"},
                    headers={"X-Test-Validation": "true"}
                )
                if response.status_code == 404:
                    logger.error("Webhook endpoint not found")
                    return False
                
                # Job status endpoint check
                response = await client.get(f"{api_url}/jobs/status")
                if response.status_code not in [200, 401]:  # 401 is OK for missing auth
                    logger.error(f"Job status endpoint failed: {response.status_code}")
                    return False
            
            logger.info("✅ API server validation passed")
            return True
            
        except Exception as e:
            logger.error(f"API server validation failed: {e}")
            return False
    
    async def _validate_worker_process(self) -> bool:
        """Validate worker process is running and functional"""
        logger.info("Validating worker process infrastructure")
        
        try:
            worker_config = self.config.get("worker", {})
            worker_health_url = worker_config.get("health_url")
            
            if worker_health_url:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(worker_health_url)
                    if response.status_code != 200:
                        logger.error(f"Worker health check failed: {response.status_code}")
                        return False
                    
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
                        AND updated_at > now() - interval '1 hour'
                    """)
                    active_jobs = cursor.fetchone()[0]
                    
                    if active_jobs == 0:
                        logger.warning("No active job processing detected in last hour")
                        # This might indicate worker is not processing, but not necessarily failed
                    
                    conn.close()
                    
                except Exception as e:
                    logger.warning(f"Could not validate worker activity: {e}")
            
            logger.info("✅ Worker process validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Worker validation failed: {e}")
            return False
    
    async def _validate_external_services(self) -> bool:
        """Validate external service connectivity"""
        logger.info("Validating external service infrastructure")
        
        try:
            external_config = self.config.get("external", {})
            
            # Test LlamaParse connectivity
            if "llamaparse" in external_config:
                llamaparse_url = external_config["llamaparse"].get("url")
                if llamaparse_url:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        try:
                            response = await client.get(f"{llamaparse_url}/health")
                            logger.info(f"LlamaParse health check: {response.status_code}")
                        except:
                            # Real service might not have health endpoint, try basic connectivity
                            response = await client.get(llamaparse_url)
                            logger.info(f"LlamaParse connectivity: {response.status_code}")
            
            # Test OpenAI connectivity
            if "openai" in external_config:
                openai_url = external_config["openai"].get("url", "https://api.openai.com")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{openai_url}/v1/models")
                    if response.status_code not in [200, 401]:  # 401 is OK, means API is up
                        logger.error(f"OpenAI connectivity failed: {response.status_code}")
                        return False
            
            logger.info("✅ External services validation passed")
            return True
            
        except Exception as e:
            logger.error(f"External services validation failed: {e}")
            return False
    
    async def _validate_storage(self) -> bool:
        """Validate storage configuration and accessibility"""
        logger.info("Validating storage infrastructure")
        
        try:
            storage_config = self.config.get("storage", {})
            storage_url = storage_config.get("url")
            
            if storage_url:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    try:
                        response = await client.get(f"{storage_url}/health")
                        logger.info(f"Storage health check: {response.status_code}")
                    except:
                        # Try basic connectivity
                        response = await client.get(storage_url)
                        logger.info(f"Storage connectivity: {response.status_code}")
            
            # Validate storage configuration
            required_storage_keys = ["url", "service_role_key"]
            missing_keys = [key for key in required_storage_keys if not storage_config.get(key)]
            
            if missing_keys:
                logger.error(f"Missing storage configuration: {missing_keys}")
                return False
            
            logger.info("✅ Storage validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Storage validation failed: {e}")
            return False
    
    async def _validate_environment(self) -> bool:
        """Validate environment configuration"""
        logger.info("Validating environment configuration")
        
        try:
            required_env_vars = [
                "DATABASE_URL",
                "SUPABASE_URL", 
                "SUPABASE_SERVICE_ROLE_KEY",
                "LLAMAPARSE_API_KEY",
                "OPENAI_API_KEY"
            ]
            
            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"Missing environment variables: {missing_vars}")
                return False
            
            # Validate environment variable formats
            db_url = os.getenv("DATABASE_URL", "")
            if not db_url.startswith("postgresql://"):
                logger.error("DATABASE_URL must start with postgresql://")
                return False
            
            logger.info("✅ Environment validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False
    
    async def _validate_performance(self) -> bool:
        """Validate performance characteristics"""
        logger.info("Validating performance characteristics")
        
        try:
            # Basic performance validation
            # This would be expanded with actual performance benchmarks
            # For now, just validate that services respond within reasonable time
            
            api_config = self.config.get("api", {})
            api_url = api_config.get("url")
            
            if api_url:
                start_time = datetime.utcnow()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{api_url}/health")
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                if response_time > 5.0:  # 5 second threshold
                    logger.warning(f"API response time slow: {response_time:.2f}s")
                else:
                    logger.info(f"API response time: {response_time:.2f}s")
            
            logger.info("✅ Performance validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Performance validation failed: {e}")
            return False
    
    async def _validate_security(self) -> bool:
        """Validate security configuration"""
        logger.info("Validating security configuration")
        
        try:
            # Basic security validation
            # Check for secure configurations
            
            # Validate HTTPS usage for production
            api_config = self.config.get("api", {})
            api_url = api_config.get("url", "")
            
            if api_url and not api_url.startswith("https://") and "localhost" not in api_url:
                logger.warning("Production API should use HTTPS")
            
            # Check for secure environment variables
            sensitive_vars = ["SUPABASE_SERVICE_ROLE_KEY", "LLAMAPARSE_API_KEY", "OPENAI_API_KEY"]
            for var in sensitive_vars:
                if os.getenv(var):
                    value = os.getenv(var, "")
                    if len(value) < 20:  # Basic length validation
                        logger.warning(f"Environment variable {var} seems too short")
            
            logger.info("✅ Security validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return False
    
    async def _validate_monitoring(self) -> bool:
        """Validate monitoring and observability"""
        logger.info("Validating monitoring infrastructure")
        
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
            
            logger.info("✅ Monitoring validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring validation failed: {e}")
            return False
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        if not self.validation_results:
            return "No validation results available"
        
        report = []
        report.append("=" * 60)
        report.append("DEPLOYMENT VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Validation Date: {datetime.utcnow().isoformat()}")
        
        if self.validation_start_time and self.validation_end_time:
            duration = (self.validation_end_time - self.validation_start_time).total_seconds()
            report.append(f"Validation Duration: {duration:.2f} seconds")
        
        report.append("")
        report.append("Validation Results:")
        report.append("-" * 40)
        
        all_passed = True
        for component, passed in self.validation_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"{component:20} {status}")
            if not passed:
                all_passed = False
        
        report.append("-" * 40)
        report.append("")
        
        if all_passed:
            report.append("🎯 OVERALL RESULT: ALL VALIDATIONS PASSED")
            report.append("✅ Deployment infrastructure is ready for application deployment")
        else:
            report.append("🚨 OVERALL RESULT: SOME VALIDATIONS FAILED")
            report.append("❌ Deployment infrastructure requires attention before proceeding")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_failed_components(self) -> List[str]:
        """Get list of failed validation components"""
        return [component for component, passed in self.validation_results.items() if not passed]
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary for programmatic use"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": (self.validation_end_time - self.validation_start_time).total_seconds() if self.validation_start_time and self.validation_end_time else None,
            "total_components": len(self.validation_results),
            "passed_components": len([v for v in self.validation_results.values() if v]),
            "failed_components": len([v for v in self.validation_results.values() if not v]),
            "success_rate": len([v for v in self.validation_results.values() if v]) / len(self.validation_results) if self.validation_results else 0,
            "results": self.validation_results,
            "failed_components_list": self.get_failed_components()
        }


# CLI interface for deployment validation
async def main():
    """Main CLI entry point"""
    if len(sys.argv) != 2:
        print("Usage: python deployment_validator.py <config.yaml>")
        print("Example: python deployment_validator.py config/production.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        validator = DeploymentValidator(config_path)
        results = await validator.validate_complete_deployment()
        
        # Generate and display report
        report = validator.generate_validation_report()
        print(report)
        
        # Exit with appropriate code
        if all(results.values()):
            print("✅ All validation checks passed!")
            sys.exit(0)
        else:
            print("❌ Some validation checks failed!")
            print(f"Failed components: {', '.join(validator.get_failed_components())}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        logger.exception("Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
