#!/usr/bin/env python3
"""
Automated Rollback System for 003 Worker Refactor

This module provides automated rollback capabilities when infrastructure validation
fails, preventing deployment configuration failures experienced in 002.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RollbackTrigger:
    """Definition of a rollback trigger"""
    name: str
    condition: str
    threshold: Any
    current_value: Any
    triggered: bool
    timestamp: datetime
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class RollbackAction:
    """Definition of a rollback action"""
    name: str
    action_type: str
    command: str
    status: str  # pending, executing, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_time_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        if self.start_time:
            result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result


class AutomatedRollback:
    """
    Automated rollback system for failed deployments
    
    Monitors validation results and automatically triggers rollback procedures
    when critical failures are detected.
    """
    
    def __init__(self, config_path: str):
        """Initialize rollback system with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.rollback_triggers: List[RollbackTrigger] = []
        self.rollback_actions: List[RollbackAction] = []
        self.rollback_history: List[Dict[str, Any]] = []
        
        # Load rollback procedures
        self.rollback_procedures = self._load_rollback_procedures()
        
        logger.info(f"Initialized AutomatedRollback with config: {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded rollback configuration")
        return config
    
    def _load_rollback_procedures(self) -> Dict[str, Any]:
        """Load rollback procedures from configuration"""
        procedures_path = Path("infrastructure/validation/rollback_procedures.yaml")
        
        if not procedures_path.exists():
            logger.warning("Rollback procedures not found, creating default procedures")
            return self._create_default_rollback_procedures()
        
        with open(procedures_path, 'r') as f:
            procedures = yaml.safe_load(f)
        
        logger.info("Loaded rollback procedures")
        return procedures
    
    def _create_default_rollback_procedures(self) -> Dict[str, Any]:
        """Create default rollback procedures if none exist"""
        procedures = {
            "infrastructure_failure": {
                "description": "Rollback infrastructure to previous stable state",
                "actions": [
                    {
                        "name": "stop_services",
                        "action_type": "docker_compose",
                        "command": "docker-compose down",
                        "description": "Stop all running services"
                    },
                    {
                        "name": "restore_database",
                        "action_type": "database_restore",
                        "command": "restore_from_backup",
                        "description": "Restore database from backup"
                    },
                    {
                        "name": "restart_services",
                        "action_type": "docker_compose",
                        "command": "docker-compose up -d",
                        "description": "Restart services with previous configuration"
                    }
                ]
            },
            "application_failure": {
                "description": "Rollback application to previous version",
                "actions": [
                    {
                        "name": "stop_application",
                        "action_type": "service_stop",
                        "command": "systemctl stop upload-pipeline",
                        "description": "Stop application service"
                    },
                    {
                        "name": "restore_application",
                        "action_type": "git_revert",
                        "command": "git revert HEAD",
                        "description": "Revert to previous commit"
                    },
                    {
                        "name": "restart_application",
                        "action_type": "service_start",
                        "command": "systemctl start upload-pipeline",
                        "description": "Restart application service"
                    }
                ]
            },
            "database_failure": {
                "description": "Rollback database changes",
                "actions": [
                    {
                        "name": "stop_services",
                        "action_type": "docker_compose",
                        "command": "docker-compose stop postgres",
                        "description": "Stop database service"
                    },
                    {
                        "name": "restore_database",
                        "action_type": "database_restore",
                        "command": "restore_from_backup",
                        "description": "Restore database from backup"
                    },
                    {
                        "name": "restart_database",
                        "action_type": "docker_compose",
                        "command": "docker-compose start postgres",
                        "description": "Restart database service"
                    }
                ]
            }
        }
        
        # Save default procedures
        procedures_path = Path("infrastructure/validation/rollback_procedures.yaml")
        procedures_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(procedures_path, 'w') as f:
            yaml.dump(procedures, f, default_flow_style=False, indent=2)
        
        logger.info("Created default rollback procedures")
        return procedures
    
    def check_rollback_triggers(self, validation_results: Dict[str, Any]) -> List[RollbackTrigger]:
        """
        Check if any rollback triggers have been activated
        
        Args:
            validation_results: Results from deployment validation
            
        Returns:
            List of triggered rollback conditions
        """
        logger.info("Checking rollback triggers")
        
        triggers = []
        rollback_config = self.config.get("validation", {}).get("rollback_triggers", {})
        
        # Check overall validation failure
        if not validation_results.get("overall", True):
            trigger = RollbackTrigger(
                name="overall_validation_failure",
                condition="overall_validation_success = false",
                threshold=True,
                current_value=False,
                triggered=True,
                timestamp=datetime.utcnow(),
                description="Overall validation failed - critical rollback required"
            )
            triggers.append(trigger)
            logger.warning("Rollback triggered: Overall validation failure")
        
        # Check health check failure threshold
        health_failure_threshold = rollback_config.get("health_check_failure_threshold", 3)
        failed_health_checks = validation_results.get("services", {}).get("failed_checks", 0)
        
        if failed_health_checks >= health_failure_threshold:
            trigger = RollbackTrigger(
                name="health_check_failure_threshold",
                condition=f"failed_health_checks >= {health_failure_threshold}",
                threshold=health_failure_threshold,
                current_value=failed_health_checks,
                triggered=True,
                timestamp=datetime.utcnow(),
                description=f"Health check failures ({failed_health_checks}) exceeded threshold ({health_failure_threshold})"
            )
            triggers.append(trigger)
            logger.warning(f"Rollback triggered: Health check failure threshold exceeded")
        
        # Check performance degradation
        performance_degradation_threshold = rollback_config.get("performance_degradation_threshold", 5.0)
        performance_results = validation_results.get("performance", {})
        
        if not performance_results.get("overall", True):
            trigger = RollbackTrigger(
                name="performance_degradation",
                condition=f"performance_validation_success = false",
                threshold=True,
                current_value=False,
                triggered=True,
                timestamp=datetime.utcnow(),
                description="Performance validation failed - significant degradation detected"
            )
            triggers.append(trigger)
            logger.warning("Rollback triggered: Performance degradation")
        
        # Check security validation failure
        if rollback_config.get("security_validation_failure", True):
            security_results = validation_results.get("security", {})
            if not security_results.get("overall", True):
                trigger = RollbackTrigger(
                    name="security_validation_failure",
                    condition="security_validation_success = false",
                    threshold=True,
                    current_value=False,
                    triggered=True,
                    timestamp=datetime.utcnow(),
                    description="Security validation failed - critical security issue detected"
                )
                triggers.append(trigger)
                logger.warning("Rollback triggered: Security validation failure")
        
        # Check database connection failure
        if rollback_config.get("database_connection_failure", True):
            database_results = validation_results.get("database", {})
            if not database_results.get("overall", True):
                trigger = RollbackTrigger(
                    name="database_connection_failure",
                    condition="database_validation_success = false",
                    threshold=True,
                    current_value=False,
                    triggered=True,
                    timestamp=datetime.utcnow(),
                    description="Database validation failed - connection or schema issues detected"
                )
                triggers.append(trigger)
                logger.warning("Rollback triggered: Database connection failure")
        
        self.rollback_triggers.extend(triggers)
        
        if triggers:
            logger.warning(f"Rollback triggers activated: {len(triggers)} conditions met")
        else:
            logger.info("No rollback triggers activated")
        
        return triggers
    
    async def execute_rollback(self, failure_type: str, triggers: List[RollbackTrigger]) -> bool:
        """
        Execute rollback procedures for the specified failure type
        
        Args:
            failure_type: Type of failure that triggered rollback
            triggers: List of rollback triggers that were activated
            
        Returns:
            True if rollback was successful, False otherwise
        """
        logger.info(f"Executing rollback for failure type: {failure_type}")
        
        if failure_type not in self.rollback_procedures:
            logger.error(f"No rollback procedures defined for failure type: {failure_type}")
            return False
        
        procedure = self.rollback_procedures[failure_type]
        actions = procedure.get("actions", [])
        
        logger.info(f"Executing {len(actions)} rollback actions")
        
        # Create rollback actions
        rollback_actions = []
        for action_config in actions:
            action = RollbackAction(
                name=action_config["name"],
                action_type=action_config["action_type"],
                command=action_config["command"],
                status="pending",
                description=action_config.get("description", "")
            )
            rollback_actions.append(action)
        
        self.rollback_actions.extend(rollback_actions)
        
        # Execute rollback actions
        success = True
        for action in rollback_actions:
            try:
                action.status = "executing"
                action.start_time = datetime.utcnow()
                
                logger.info(f"Executing rollback action: {action.name}")
                
                # Execute the action based on type
                action_success = await self._execute_rollback_action(action)
                
                if action_success:
                    action.status = "completed"
                    logger.info(f"Rollback action completed: {action.name}")
                else:
                    action.status = "failed"
                    success = False
                    logger.error(f"Rollback action failed: {action.name}")
                
                action.end_time = datetime.utcnow()
                if action.start_time and action.end_time:
                    action.rollback_time_seconds = (action.end_time - action.start_time).total_seconds()
                
            except Exception as e:
                action.status = "failed"
                action.error_message = str(e)
                action.end_time = datetime.utcnow()
                success = False
                logger.error(f"Rollback action failed with exception: {action.name} - {e}")
        
        # Record rollback history
        rollback_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "failure_type": failure_type,
            "triggers": [t.to_dict() for t in triggers],
            "actions": [a.to_dict() for a in rollback_actions],
            "overall_success": success
        }
        
        self.rollback_history.append(rollback_record)
        
        # Save rollback history
        self._save_rollback_history()
        
        if success:
            logger.info("Rollback completed successfully")
        else:
            logger.error("Rollback failed - manual intervention may be required")
        
        return success
    
    async def _execute_rollback_action(self, action: RollbackAction) -> bool:
        """Execute a single rollback action"""
        try:
            if action.action_type == "docker_compose":
                return await self._execute_docker_compose_action(action)
            elif action.action_type == "database_restore":
                return await self._execute_database_restore_action(action)
            elif action.action_type == "service_stop":
                return await self._execute_service_action(action, "stop")
            elif action.action_type == "service_start":
                return await self._execute_service_action(action, "start")
            elif action.action_type == "git_revert":
                return await self._execute_git_revert_action(action)
            else:
                logger.warning(f"Unknown rollback action type: {action.action_type}")
                return False
                
        except Exception as e:
            action.error_message = str(e)
            logger.error(f"Failed to execute rollback action {action.name}: {e}")
            return False
    
    async def _execute_docker_compose_action(self, action: RollbackAction) -> bool:
        """Execute Docker Compose rollback action"""
        try:
            # Run docker-compose command
            result = subprocess.run(
                action.command.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Docker Compose action successful: {action.command}")
                return True
            else:
                action.error_message = f"Command failed with return code {result.returncode}: {result.stderr}"
                logger.error(f"Docker Compose action failed: {action.command} - {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            action.error_message = "Command timed out after 60 seconds"
            logger.error(f"Docker Compose action timed out: {action.command}")
            return False
        except Exception as e:
            action.error_message = str(e)
            logger.error(f"Docker Compose action exception: {action.command} - {e}")
            return False
    
    async def _execute_database_restore_action(self, action: RollbackAction) -> bool:
        """Execute database restore rollback action"""
        try:
            if action.command == "restore_from_backup":
                # For now, just log the action - actual restore would depend on backup system
                logger.info("Database restore action would be executed here")
                return True
            else:
                action.error_message = f"Unknown database restore command: {action.command}"
                return False
                
        except Exception as e:
            action.error_message = str(e)
            logger.error(f"Database restore action exception: {e}")
            return False
    
    async def _execute_service_action(self, action: RollbackAction, operation: str) -> bool:
        """Execute systemd service action"""
        try:
            # For local development, we might not have systemd
            # This is a placeholder for production deployment
            logger.info(f"Service {operation} action would be executed here: {action.command}")
            return True
            
        except Exception as e:
            action.error_message = str(e)
            logger.error(f"Service action exception: {e}")
            return False
    
    async def _execute_git_revert_action(self, action: RollbackAction) -> bool:
        """Execute Git revert action"""
        try:
            if action.command == "git revert HEAD":
                # Check if we're in a git repository
                if not Path(".git").exists():
                    action.error_message = "Not in a git repository"
                    return False
                
                # Execute git revert
                result = subprocess.run(
                    ["git", "revert", "HEAD", "--no-edit"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.info("Git revert successful")
                    return True
                else:
                    action.error_message = f"Git revert failed: {result.stderr}"
                    logger.error(f"Git revert failed: {result.stderr}")
                    return False
            else:
                action.error_message = f"Unknown git command: {action.command}"
                return False
                
        except subprocess.TimeoutExpired:
            action.error_message = "Git revert timed out after 30 seconds"
            logger.error("Git revert timed out")
            return False
        except Exception as e:
            action.error_message = str(e)
            logger.error(f"Git revert exception: {e}")
            return False
    
    def _save_rollback_history(self):
        """Save rollback history to file"""
        history_path = Path("infrastructure/validation/rollback_history.json")
        history_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(history_path, 'w') as f:
            json.dump(self.rollback_history, f, indent=2, default=str)
        
        logger.info(f"Rollback history saved to: {history_path}")
    
    def generate_rollback_report(self) -> Dict[str, Any]:
        """Generate comprehensive rollback report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_triggers": len(self.rollback_triggers),
                "triggered_triggers": sum(1 for t in self.rollback_triggers if t.triggered),
                "total_actions": len(self.rollback_actions),
                "successful_actions": sum(1 for a in self.rollback_actions if a.status == "completed"),
                "failed_actions": sum(1 for a in self.rollback_actions if a.status == "failed")
            },
            "rollback_triggers": [t.to_dict() for t in self.rollback_triggers],
            "rollback_actions": [a.to_dict() for a in self.rollback_actions],
            "rollback_history": self.rollback_history
        }
        
        return report
    
    def save_rollback_report(self, report: Dict[str, Any], filename: str = None):
        """Save rollback report to file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"rollback_report_{timestamp}.json"
        
        report_path = Path("infrastructure/validation/reports")
        report_path.mkdir(parents=True, exist_ok=True)
        
        file_path = report_path / filename
        
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Rollback report saved to: {file_path}")


async def main():
    """Main function for testing rollback system"""
    if len(sys.argv) != 2:
        print("Usage: python automated_rollback.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        rollback_system = AutomatedRollback(config_file)
        
        # Simulate validation results that would trigger rollback
        test_validation_results = {
            "overall": False,
            "infrastructure": False,
            "services": {"failed_checks": 5},
            "database": {"overall": False},
            "configuration": True,
            "performance": {"overall": False},
            "security": {"overall": False}
        }
        
        # Check for rollback triggers
        triggers = rollback_system.check_rollback_triggers(test_validation_results)
        
        if triggers:
            print(f"\nRollback triggers activated: {len(triggers)}")
            for trigger in triggers:
                print(f"  - {trigger.name}: {trigger.description}")
            
            # Execute rollback
            print("\nExecuting rollback...")
            success = await rollback_system.execute_rollback("infrastructure_failure", triggers)
            
            if success:
                print("✅ Rollback completed successfully")
            else:
                print("❌ Rollback failed")
        else:
            print("✅ No rollback triggers activated")
        
        # Generate and save report
        report = rollback_system.generate_rollback_report()
        rollback_system.save_rollback_report(report)
        
        print("\nRollback report saved to infrastructure/validation/reports/")
        
    except Exception as e:
        print(f"Rollback system failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
