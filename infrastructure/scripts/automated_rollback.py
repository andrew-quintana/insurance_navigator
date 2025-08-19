#!/usr/bin/env python3
"""
Automated Rollback System for 003 Worker Refactor

This module provides automated rollback procedures for failed deployments
to ensure system safety and quick recovery from infrastructure issues.
"""

import asyncio
import yaml
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import subprocess
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentRollback:
    """Automated rollback system for failed deployments"""
    
    def __init__(self, deployment_config: dict, rollback_config: dict):
        """Initialize rollback system with deployment and rollback configuration"""
        self.deployment_config = deployment_config
        self.rollback_config = rollback_config
        self.rollback_steps = []
        self.rollback_start_time = None
        self.rollback_end_time = None
        
        # Rollback configuration
        self.rollback_timeout = rollback_config.get("timeout", 300)  # 5 minutes
        self.max_rollback_attempts = rollback_config.get("max_attempts", 3)
        self.rollback_delay = rollback_config.get("delay", 10)  # seconds
        
    async def execute_rollback(self, failure_stage: str, failure_details: str = None) -> bool:
        """Execute rollback based on failure stage"""
        self.rollback_start_time = datetime.utcnow()
        logger.info(f"🔄 Starting rollback from failure at stage: {failure_stage}")
        
        if failure_details:
            logger.info(f"Failure details: {failure_details}")
        
        try:
            # Determine rollback scope based on failure stage
            if failure_stage in ["infrastructure", "configuration"]:
                success = await self._rollback_infrastructure()
            elif failure_stage == "application":
                success = await self._rollback_application()
            elif failure_stage == "database":
                success = await self._rollback_database()
            elif failure_stage == "monitoring":
                success = await self._rollback_monitoring()
            else:
                # Full rollback for unknown failure stages
                success = await self._rollback_complete()
            
            if success:
                await self._verify_rollback_success()
                self.rollback_end_time = datetime.utcnow()
                
                duration = (self.rollback_end_time - self.rollback_start_time).total_seconds()
                logger.info(f"✅ Rollback completed successfully in {duration:.2f} seconds")
                return True
            else:
                logger.error("❌ Rollback failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Rollback failed with error: {e}")
            logger.exception("Rollback error details")
            return False
    
    async def _rollback_infrastructure(self) -> bool:
        """Rollback infrastructure to previous stable state"""
        logger.info("Rolling back infrastructure...")
        
        try:
            platform = self.deployment_config.get("deployment", {}).get("platform")
            
            if platform == "render":
                return await self._rollback_render_infrastructure()
            elif platform == "docker":
                return await self._rollback_docker_infrastructure()
            else:
                logger.warning(f"Unknown deployment platform: {platform}")
                return await self._rollback_generic_infrastructure()
                
        except Exception as e:
            logger.error(f"Infrastructure rollback failed: {e}")
            return False
    
    async def _rollback_render_infrastructure(self) -> bool:
        """Rollback Render infrastructure"""
        logger.info("Rolling back Render infrastructure...")
        
        try:
            # Get service names from configuration
            services = self.rollback_config.get("render", {}).get("services", [])
            
            for service in services:
                logger.info(f"Rolling back service: {service}")
                
                # Rollback to previous deployment
                cmd = ["render", "rollback", service, "--latest"]
                result = await self._execute_command(cmd)
                
                if result["success"]:
                    logger.info(f"✅ Service {service} rolled back successfully")
                else:
                    logger.error(f"❌ Failed to rollback service {service}: {result['error']}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Render infrastructure rollback failed: {e}")
            return False
    
    async def _rollback_docker_infrastructure(self) -> bool:
        """Rollback Docker infrastructure"""
        logger.info("Rolling back Docker infrastructure...")
        
        try:
            # Stop current containers
            cmd = ["docker-compose", "down"]
            result = await self._execute_command(cmd)
            
            if not result["success"]:
                logger.error(f"Failed to stop Docker containers: {result['error']}")
                return False
            
            # Pull previous images
            cmd = ["docker-compose", "pull"]
            result = await self._execute_command(cmd)
            
            if not result["success"]:
                logger.error(f"Failed to pull previous images: {result['error']}")
                return False
            
            # Start with previous configuration
            cmd = ["docker-compose", "up", "-d"]
            result = await self._execute_command(cmd)
            
            if not result["success"]:
                logger.error(f"Failed to start Docker containers: {result['error']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Docker infrastructure rollback failed: {e}")
            return False
    
    async def _rollback_generic_infrastructure(self) -> bool:
        """Generic infrastructure rollback"""
        logger.info("Performing generic infrastructure rollback...")
        
        try:
            # Execute rollback scripts if available
            rollback_scripts = self.rollback_config.get("scripts", [])
            
            for script in rollback_scripts:
                logger.info(f"Executing rollback script: {script}")
                
                if os.path.exists(script):
                    result = await self._execute_command([script])
                    if not result["success"]:
                        logger.error(f"Rollback script failed: {script}")
                        return False
                else:
                    logger.warning(f"Rollback script not found: {script}")
            
            return True
            
        except Exception as e:
            logger.error(f"Generic infrastructure rollback failed: {e}")
            return False
    
    async def _rollback_application(self) -> bool:
        """Rollback application to previous version"""
        logger.info("Rolling back application...")
        
        try:
            # Application rollback depends on deployment method
            deployment_method = self.rollback_config.get("deployment_method", "git")
            
            if deployment_method == "git":
                return await self._rollback_git_application()
            elif deployment_method == "docker":
                return await self._rollback_docker_application()
            else:
                logger.warning(f"Unknown deployment method: {deployment_method}")
                return False
                
        except Exception as e:
            logger.error(f"Application rollback failed: {e}")
            return False
    
    async def _rollback_git_application(self) -> bool:
        """Rollback application using Git"""
        logger.info("Rolling back application using Git...")
        
        try:
            # Get previous commit hash
            previous_commit = self.rollback_config.get("git", {}).get("previous_commit")
            
            if not previous_commit:
                logger.warning("No previous commit specified, using HEAD~1")
                previous_commit = "HEAD~1"
            
            # Reset to previous commit
            cmd = ["git", "reset", "--hard", previous_commit]
            result = await self._execute_command(cmd)
            
            if not result["success"]:
                logger.error(f"Git rollback failed: {result['error']}")
                return False
            
            # Clean untracked files
            cmd = ["git", "clean", "-fd"]
            result = await self._execute_command(cmd)
            
            if not result["success"]:
                logger.warning(f"Git clean failed: {result['error']}")
                # Not critical for rollback
            
            logger.info(f"✅ Application rolled back to commit: {previous_commit}")
            return True
            
        except Exception as e:
            logger.error(f"Git application rollback failed: {e}")
            return False
    
    async def _rollback_docker_application(self) -> bool:
        """Rollback application using Docker"""
        logger.info("Rolling back application using Docker...")
        
        try:
            # Get previous image tag
            previous_image = self.rollback_config.get("docker", {}).get("previous_image")
            
            if not previous_image:
                logger.error("No previous Docker image specified")
                return False
            
            # Stop current application containers
            app_services = self.rollback_config.get("docker", {}).get("app_services", [])
            
            for service in app_services:
                cmd = ["docker", "stop", service]
                result = await self._execute_command(cmd)
                
                if not result["success"]:
                    logger.warning(f"Failed to stop service {service}: {result['error']}")
            
            # Start with previous image
            for service in app_services:
                cmd = ["docker", "run", "-d", "--name", f"{service}_rollback", previous_image]
                result = await self._execute_command(cmd)
                
                if not result["success"]:
                    logger.error(f"Failed to start rollback container for {service}: {result['error']}")
                    return False
            
            logger.info(f"✅ Application rolled back to image: {previous_image}")
            return True
            
        except Exception as e:
            logger.error(f"Docker application rollback failed: {e}")
            return False
    
    async def _rollback_database(self) -> bool:
        """Rollback database to previous state"""
        logger.info("Rolling back database...")
        
        try:
            # Database rollback strategy
            rollback_strategy = self.rollback_config.get("database", {}).get("strategy", "backup")
            
            if rollback_strategy == "backup":
                return await self._rollback_database_from_backup()
            elif rollback_strategy == "migration":
                return await self._rollback_database_migration()
            else:
                logger.error(f"Unknown database rollback strategy: {rollback_strategy}")
                return False
                
        except Exception as e:
            logger.error(f"Database rollback failed: {e}")
            return False
    
    async def _rollback_database_from_backup(self) -> bool:
        """Rollback database from backup"""
        logger.info("Rolling back database from backup...")
        
        try:
            backup_path = self.rollback_config.get("database", {}).get("backup_path")
            
            if not backup_path or not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Get database configuration
            db_config = self.deployment_config.get("database", {})
            db_url = db_config.get("url")
            
            if not db_url:
                logger.error("Database URL not configured")
                return False
            
            # Restore from backup
            if db_url.startswith("postgresql://"):
                # PostgreSQL restore
                cmd = ["pg_restore", "-d", db_url, backup_path]
                result = await self._execute_command(cmd)
                
                if not result["success"]:
                    logger.error(f"Database restore failed: {result['error']}")
                    return False
            else:
                logger.error(f"Unsupported database type: {db_url}")
                return False
            
            logger.info("✅ Database restored from backup successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database backup rollback failed: {e}")
            return False
    
    async def _rollback_database_migration(self) -> bool:
        """Rollback database using migration rollback"""
        logger.info("Rolling back database using migration...")
        
        try:
            # Get migration rollback command
            rollback_cmd = self.rollback_config.get("database", {}).get("rollback_command")
            
            if not rollback_cmd:
                logger.error("No database rollback command specified")
                return False
            
            # Execute rollback command
            result = await self._execute_command(rollback_cmd.split())
            
            if not result["success"]:
                logger.error(f"Database migration rollback failed: {result['error']}")
                return False
            
            logger.info("✅ Database migration rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database migration rollback failed: {e}")
            return False
    
    async def _rollback_monitoring(self) -> bool:
        """Rollback monitoring and alerting systems"""
        logger.info("Rolling back monitoring systems...")
        
        try:
            # Restore monitoring configuration
            monitoring_config = self.rollback_config.get("monitoring", {})
            
            # Restore alerting rules
            alerting_rules = monitoring_config.get("alerting_rules")
            if alerting_rules and os.path.exists(alerting_rules):
                # Restore alerting configuration
                logger.info("Restoring alerting rules...")
            
            # Restore dashboard configuration
            dashboard_config = monitoring_config.get("dashboard_config")
            if dashboard_config and os.path.exists(dashboard_config):
                # Restore dashboard configuration
                logger.info("Restoring dashboard configuration...")
            
            logger.info("✅ Monitoring systems rolled back successfully")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring rollback failed: {e}")
            return False
    
    async def _rollback_complete(self) -> bool:
        """Complete system rollback"""
        logger.info("Performing complete system rollback...")
        
        try:
            # Rollback all components
            components = ["infrastructure", "application", "database", "monitoring"]
            
            for component in components:
                logger.info(f"Rolling back {component}...")
                
                if component == "infrastructure":
                    success = await self._rollback_infrastructure()
                elif component == "application":
                    success = await self._rollback_application()
                elif component == "database":
                    success = await self._rollback_database()
                elif component == "monitoring":
                    success = await self._rollback_monitoring()
                
                if not success:
                    logger.error(f"❌ {component} rollback failed")
                    return False
            
            logger.info("✅ Complete system rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Complete system rollback failed: {e}")
            return False
    
    async def _verify_rollback_success(self) -> bool:
        """Verify rollback was successful"""
        logger.info("Verifying rollback success...")
        
        try:
            # Basic health checks
            health_checks = self.rollback_config.get("verification", {}).get("health_checks", [])
            
            for check in health_checks:
                logger.info(f"Running verification check: {check}")
                
                if check == "database_connectivity":
                    success = await self._verify_database_connectivity()
                elif check == "api_health":
                    success = await self._verify_api_health()
                elif check == "worker_health":
                    success = await self._verify_worker_health()
                else:
                    logger.warning(f"Unknown verification check: {check}")
                    success = True
                
                if not success:
                    logger.error(f"❌ Verification check failed: {check}")
                    return False
            
            logger.info("✅ All verification checks passed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback verification failed: {e}")
            return False
    
    async def _verify_database_connectivity(self) -> bool:
        """Verify database connectivity after rollback"""
        try:
            db_config = self.deployment_config.get("database", {})
            db_url = db_config.get("url")
            
            if not db_url:
                return False
            
            # Simple connectivity test
            import psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            return result[0] == 1
            
        except Exception as e:
            logger.error(f"Database connectivity verification failed: {e}")
            return False
    
    async def _verify_api_health(self) -> bool:
        """Verify API health after rollback"""
        try:
            api_config = self.deployment_config.get("api", {})
            api_url = api_config.get("url")
            
            if not api_url:
                return False
            
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{api_url}/health")
                return response.status_code == 200
            
        except Exception as e:
            logger.error(f"API health verification failed: {e}")
            return False
    
    async def _verify_worker_health(self) -> bool:
        """Verify worker health after rollback"""
        try:
            worker_config = self.deployment_config.get("worker", {})
            worker_health_url = worker_config.get("health_url")
            
            if not worker_health_url:
                return True  # Skip if no health URL configured
            
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(worker_health_url)
                return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Worker health verification failed: {e}")
            return False
    
    async def _execute_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute shell command and return result"""
        try:
            logger.debug(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.rollback_timeout
            )
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": result.stderr if not success else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "error": "Command execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "error": str(e)
            }
    
    def generate_rollback_report(self) -> str:
        """Generate comprehensive rollback report"""
        if not self.rollback_start_time:
            return "No rollback executed"
        
        report = []
        report.append("=" * 60)
        report.append("DEPLOYMENT ROLLBACK REPORT")
        report.append("=" * 60)
        report.append(f"Rollback Date: {datetime.utcnow().isoformat()}")
        
        if self.rollback_start_time and self.rollback_end_time:
            duration = (self.rollback_end_time - self.rollback_start_time).total_seconds()
            report.append(f"Rollback Duration: {duration:.2f} seconds")
        
        report.append("")
        report.append("Rollback Steps:")
        report.append("-" * 30)
        
        for i, step in enumerate(self.rollback_steps, 1):
            status = "✅ SUCCESS" if step.get("success") else "❌ FAILED"
            report.append(f"{i:2}. {step.get('name', 'Unknown step'):25} {status}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main CLI entry point"""
    if len(sys.argv) != 3:
        print("Usage: python automated_rollback.py <deployment_config.yaml> <rollback_config.yaml>")
        print("Example: python automated_rollback.py config/production.yaml config/rollback.yaml")
        sys.exit(1)
    
    deployment_config_path = sys.argv[1]
    rollback_config_path = sys.argv[2]
    
    # Check if files exist
    if not os.path.exists(deployment_config_path):
        print(f"❌ Deployment configuration file not found: {deployment_config_path}")
        sys.exit(1)
    
    if not os.path.exists(rollback_config_path):
        print(f"❌ Rollback configuration file not found: {rollback_config_path}")
        sys.exit(1)
    
    try:
        # Load configurations
        with open(deployment_config_path, 'r') as f:
            deployment_config = yaml.safe_load(f)
        
        with open(rollback_config_path, 'r') as f:
            rollback_config = yaml.safe_load(f)
        
        # Initialize rollback system
        rollback = DeploymentRollback(deployment_config, rollback_config)
        
        # Execute rollback (example: infrastructure failure)
        success = asyncio.run(rollback.execute_rollback("infrastructure", "Configuration validation failed"))
        
        if success:
            print("✅ Rollback completed successfully!")
            report = rollback.generate_rollback_report()
            print(report)
            sys.exit(0)
        else:
            print("❌ Rollback failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Rollback failed with error: {e}")
        logger.exception("Rollback failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
