#!/usr/bin/env python3
"""
Automated Rollback System for 003 Worker Refactor - Phase 5

This module provides automated rollback procedures for infrastructure deployment
failures, preventing the configuration issues experienced in 002 by ensuring
rapid recovery to known good states.
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
import shutil
from dataclasses import dataclass, asdict

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RollbackAction:
    """A rollback action to be executed"""
    action_type: str
    description: str
    command: str
    rollback_command: Optional[str] = None
    timeout_seconds: int = 300
    critical: bool = True
    executed: bool = False
    success: Optional[bool] = None
    error_message: Optional[str] = None
    execution_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        if self.execution_time:
            result['execution_time'] = self.execution_time.isoformat()
        return result


@dataclass
class RollbackResult:
    """Result of a rollback operation"""
    rollback_id: str
    timestamp: datetime
    trigger_reason: str
    actions_executed: int
    actions_successful: int
    actions_failed: int
    overall_success: bool
    duration_seconds: float
    details: List[RollbackAction]
    error_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['details'] = [action.to_dict() for action in self.details]
        return result


class AutomatedRollback:
    """
    Automated rollback system for infrastructure deployment failures
    
    Provides rapid recovery to known good states when infrastructure
    validation fails, preventing configuration issues from 002.
    """
    
    def __init__(self, config_path: str, rollback_config_path: str = None):
        """Initialize rollback system with configuration"""
        self.config_path = Path(config_path)
        self.rollback_config_path = Path(rollback_config_path) if rollback_config_path else Path("infrastructure/config/rollback_config.yaml")
        
        self.config = self._load_config()
        self.rollback_config = self._load_rollback_config()
        
        # Rollback history tracking
        self.rollback_history: List[RollbackResult] = []
        
        # Backup and restore paths
        self.backup_dir = Path("infrastructure/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized AutomatedRollback system")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _load_rollback_config(self) -> Dict[str, Any]:
        """Load rollback configuration"""
        if not self.rollback_config_path.exists():
            # Create default rollback configuration
            self._create_default_rollback_config()
        
        with open(self.rollback_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _create_default_rollback_config(self):
        """Create default rollback configuration if none exists"""
        default_config = {
            'rollback_triggers': {
                'health_check_failure_threshold': 3,
                'performance_degradation_threshold': 5.0,
                'security_validation_failure': True,
                'database_connection_failure': True,
                'service_startup_failure': True
            },
            'rollback_actions': {
                'docker_services': {
                    'description': 'Rollback Docker services to last known good state',
                    'type': 'docker_compose',
                    'command': 'docker-compose down && docker-compose up -d',
                    'rollback_command': 'docker-compose down',
                    'timeout_seconds': 300,
                    'critical': True
                },
                'database_restore': {
                    'description': 'Restore database from last backup',
                    'type': 'database_restore',
                    'command': 'pg_restore',
                    'rollback_command': 'pg_restore',
                    'timeout_seconds': 600,
                    'critical': True
                },
                'git_revert': {
                    'description': 'Revert code changes to last known good commit',
                    'type': 'git_revert',
                    'command': 'git reset --hard HEAD~1',
                    'rollback_command': 'git reset --hard HEAD~1',
                    'timeout_seconds': 60,
                    'critical': False
                },
                'configuration_restore': {
                    'description': 'Restore configuration files from backup',
                    'type': 'file_restore',
                    'command': 'cp backup/config.yaml config.yaml',
                    'rollback_command': 'cp backup/config.yaml config.yaml',
                    'timeout_seconds': 30,
                    'critical': False
                }
            },
            'backup_strategy': {
                'database_backup_interval_hours': 1,
                'config_backup_interval_hours': 24,
                'max_backups': 10,
                'backup_retention_days': 7
            }
        }
        
        self.rollback_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rollback_config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created default rollback configuration: {self.rollback_config_path}")
    
    async def check_rollback_triggers(self, current_state: Dict[str, Any]) -> bool:
        """
        Check if rollback triggers are activated
        
        Args:
            current_state: Current system state to evaluate
            
        Returns:
            True if rollback should be triggered, False otherwise
        """
        triggers = self.rollback_config.get('rollback_triggers', {})
        
        try:
            # Health check failure threshold
            health_failures = current_state.get('health_check_failures', 0)
            if health_failures >= triggers.get('health_check_failure_threshold', 3):
                logger.warning(f"Rollback triggered: Health check failures ({health_failures}) exceeded threshold")
                return True
            
            # Performance degradation threshold
            performance_degradation = current_state.get('performance_degradation_multiplier', 1.0)
            if performance_degradation >= triggers.get('performance_degradation_threshold', 5.0):
                logger.warning(f"Rollback triggered: Performance degradation ({performance_degradation}) exceeded threshold")
                return True
            
            # Security validation failure
            if current_state.get('security_validation_failure', False) and triggers.get('security_validation_failure', True):
                logger.warning("Rollback triggered: Security validation failure")
                return True
            
            # Database connection failure
            if current_state.get('database_connection_failure', False) and triggers.get('database_connection_failure', True):
                logger.warning("Rollback triggered: Database connection failure")
                return True
            
            # Service startup failure
            if current_state.get('service_startup_failure', False) and triggers.get('service_startup_failure', True):
                logger.warning("Rollback triggered: Service startup failure")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rollback triggers: {e}")
            # Default to triggering rollback on error
            return True
    
    async def execute_rollback(self, trigger_reason: str, target_state: str = "last_known_good") -> RollbackResult:
        """
        Execute automated rollback to target state
        
        Args:
            trigger_reason: Reason for rollback trigger
            target_state: Target state to rollback to
            
        Returns:
            RollbackResult with execution details
        """
        rollback_start = time.time()
        rollback_id = f"rollback_{int(time.time())}"
        
        logger.warning(f"Executing automated rollback {rollback_id}: {trigger_reason}")
        
        # Create rollback actions
        actions = self._create_rollback_actions(target_state)
        
        # Execute rollback actions
        successful_actions = 0
        failed_actions = 0
        
        for action in actions:
            try:
                logger.info(f"Executing rollback action: {action.description}")
                
                action.execution_time = datetime.utcnow()
                action_start = time.time()
                
                success = await self._execute_rollback_action(action)
                
                action.duration_seconds = time.time() - action_start
                action.executed = True
                action.success = success
                
                if success:
                    successful_actions += 1
                    logger.info(f"Rollback action successful: {action.description}")
                else:
                    failed_actions += 1
                    logger.error(f"Rollback action failed: {action.description}")
                
            except Exception as e:
                action.executed = True
                action.success = False
                action.error_message = str(e)
                action.duration_seconds = time.time() - action_start if 'action_start' in locals() else 0
                
                failed_actions += 1
                logger.error(f"Rollback action error: {action.description} - {e}")
        
        # Determine overall success
        overall_success = failed_actions == 0 or (failed_actions < len(actions) and all(
            not action.critical for action in actions if not action.success
        ))
        
        # Create rollback result
        rollback_result = RollbackResult(
            rollback_id=rollback_id,
            timestamp=datetime.utcnow(),
            trigger_reason=trigger_reason,
            actions_executed=len(actions),
            actions_successful=successful_actions,
            actions_failed=failed_actions,
            overall_success=overall_success,
            duration_seconds=time.time() - rollback_start,
            details=actions,
            error_summary=self._create_error_summary(actions) if failed_actions > 0 else None
        )
        
        # Add to history
        self.rollback_history.append(rollback_result)
        
        # Save rollback report
        await self._save_rollback_report(rollback_result)
        
        if overall_success:
            logger.info(f"Rollback {rollback_id} completed successfully in {rollback_result.duration_seconds:.2f} seconds")
        else:
            logger.error(f"Rollback {rollback_id} failed: {failed_actions} actions failed")
        
        return rollback_result
    
    def _create_rollback_actions(self, target_state: str) -> List[RollbackAction]:
        """Create rollback actions based on target state"""
        actions = []
        rollback_actions = self.rollback_config.get('rollback_actions', {})
        
        if target_state == "last_known_good":
            # Execute all rollback actions in order
            for action_name, action_config in rollback_actions.items():
                action = RollbackAction(
                    action_type=action_config.get('type', 'unknown'),
                    description=action_config.get('description', f'Rollback {action_name}'),
                    command=action_config.get('command', ''),
                    rollback_command=action_config.get('rollback_command'),
                    timeout_seconds=action_config.get('timeout_seconds', 300),
                    critical=action_config.get('critical', True)
                )
                actions.append(action)
        
        elif target_state == "docker_only":
            # Only rollback Docker services
            docker_action = rollback_actions.get('docker_services', {})
            if docker_action:
                action = RollbackAction(
                    action_type=docker_action.get('type', 'docker_compose'),
                    description=docker_action.get('description', 'Rollback Docker services'),
                    command=docker_action.get('command', 'docker-compose down'),
                    timeout_seconds=docker_action.get('timeout_seconds', 300),
                    critical=True
                )
                actions.append(action)
        
        elif target_state == "database_only":
            # Only rollback database
            db_action = rollback_actions.get('database_restore', {})
            if db_action:
                action = RollbackAction(
                    action_type=db_action.get('type', 'database_restore'),
                    description=db_action.get('description', 'Restore database'),
                    command=db_action.get('command', 'pg_restore'),
                    timeout_seconds=db_action.get('timeout_seconds', 600),
                    critical=True
                )
                actions.append(action)
        
        return actions
    
    async def _execute_rollback_action(self, action: RollbackAction) -> bool:
        """Execute a single rollback action"""
        try:
            if action.action_type == 'docker_compose':
                return await self._execute_docker_rollback(action)
            elif action.action_type == 'database_restore':
                return await self._execute_database_rollback(action)
            elif action.action_type == 'git_revert':
                return await self._execute_git_rollback(action)
            elif action.action_type == 'file_restore':
                return await self._execute_file_restore(action)
            else:
                logger.warning(f"Unknown rollback action type: {action.action_type}")
                return False
                
        except Exception as e:
            action.error_message = str(e)
            logger.error(f"Rollback action execution failed: {e}")
            return False
    
    async def _execute_docker_rollback(self, action: RollbackAction) -> bool:
        """Execute Docker service rollback"""
        try:
            # Stop all services
            stop_result = subprocess.run(
                ["docker-compose", "down"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=action.timeout_seconds
            )
            
            if stop_result.returncode != 0:
                logger.error(f"Failed to stop Docker services: {stop_result.stderr}")
                return False
            
            # Wait a moment for cleanup
            await asyncio.sleep(5)
            
            # Start services again
            start_result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=action.timeout_seconds
            )
            
            if start_result.returncode != 0:
                logger.error(f"Failed to restart Docker services: {start_result.stderr}")
                return False
            
            # Wait for services to be healthy
            await asyncio.sleep(30)
            
            # Verify services are running
            ps_result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if "Up" not in ps_result.stdout:
                logger.error("Docker services not running after rollback")
                return False
            
            logger.info("Docker services rollback completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Docker rollback action timed out")
            return False
        except Exception as e:
            logger.error(f"Docker rollback action failed: {e}")
            return False
    
    async def _execute_database_rollback(self, action: RollbackAction) -> bool:
        """Execute database rollback from backup"""
        try:
            # Find latest database backup
            backup_files = list(self.backup_dir.glob("database_backup_*.sql"))
            if not backup_files:
                logger.error("No database backup files found")
                return False
            
            # Sort by modification time and get latest
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            logger.info(f"Restoring database from backup: {latest_backup}")
            
            # Get database configuration
            db_config = self.config.get('database', {})
            if not db_config:
                logger.error("Database configuration not found")
                return False
            
            # Execute database restore
            restore_cmd = [
                "psql",
                "-h", db_config.get('host', 'localhost'),
                "-p", str(db_config.get('port', 5432)),
                "-U", db_config.get('user', 'postgres'),
                "-d", db_config.get('database', 'accessa_dev'),
                "-f", str(latest_backup)
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config.get('password', '')
            
            restore_result = subprocess.run(
                restore_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=action.timeout_seconds
            )
            
            if restore_result.returncode != 0:
                logger.error(f"Database restore failed: {restore_result.stderr}")
                return False
            
            logger.info("Database rollback completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Database rollback action timed out")
            return False
        except Exception as e:
            logger.error(f"Database rollback action failed: {e}")
            return False
    
    async def _execute_git_rollback(self, action: RollbackAction) -> bool:
        """Execute Git code rollback"""
        try:
            # Check if we're in a Git repository
            git_check = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if git_check.returncode != 0:
                logger.warning("Not in a Git repository, skipping Git rollback")
                return True
            
            # Get current commit hash
            current_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if current_commit.returncode != 0:
                logger.error("Failed to get current commit hash")
                return False
            
            current_hash = current_commit.stdout.strip()
            logger.info(f"Current commit: {current_hash}")
            
            # Reset to previous commit
            reset_result = subprocess.run(
                ["git", "reset", "--hard", "HEAD~1"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=action.timeout_seconds
            )
            
            if reset_result.returncode != 0:
                logger.error(f"Git reset failed: {reset_result.stderr}")
                return False
            
            # Get new commit hash
            new_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if new_commit.returncode != 0:
                logger.error("Failed to get new commit hash")
                return False
            
            new_hash = new_commit.stdout.strip()
            logger.info(f"Rolled back to commit: {new_hash}")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Git rollback action timed out")
            return False
        except Exception as e:
            logger.error(f"Git rollback action failed: {e}")
            return False
    
    async def _execute_file_restore(self, action: RollbackAction) -> bool:
        """Execute file restoration from backup"""
        try:
            # Find configuration backup
            config_backup = self.backup_dir / "config_backup.yaml"
            if not config_backup.exists():
                logger.warning("Configuration backup not found, skipping file restore")
                return True
            
            # Restore configuration file
            target_config = Path("infrastructure/config/deployment_config.yaml")
            if target_config.exists():
                # Create backup of current config
                current_backup = self.backup_dir / f"config_current_{int(time.time())}.yaml"
                shutil.copy2(target_config, current_backup)
                logger.info(f"Backed up current config to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(config_backup, target_config)
            logger.info(f"Restored configuration from: {config_backup}")
            
            return True
            
        except Exception as e:
            logger.error(f"File restore action failed: {e}")
            return False
    
    def _create_error_summary(self, actions: List[RollbackAction]) -> str:
        """Create summary of rollback action errors"""
        failed_actions = [action for action in actions if not action.success]
        
        if not failed_actions:
            return "No errors occurred"
        
        error_summary = f"Rollback failed for {len(failed_actions)} actions:\n"
        for action in failed_actions:
            error_summary += f"- {action.description}: {action.error_message or 'Unknown error'}\n"
        
        return error_summary
    
    async def _save_rollback_report(self, rollback_result: RollbackResult):
        """Save rollback report to file"""
        try:
            reports_dir = Path("infrastructure/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"rollback_report_{rollback_result.rollback_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(rollback_result.to_dict(), f, indent=2)
            
            logger.info(f"Rollback report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save rollback report: {e}")
    
    async def create_backup(self, backup_type: str = "full") -> str:
        """
        Create backup before deployment
        
        Args:
            backup_type: Type of backup to create
            
        Returns:
            Path to created backup file
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            if backup_type == "database":
                backup_file = self.backup_dir / f"database_backup_{timestamp}.sql"
                await self._create_database_backup(backup_file)
                
            elif backup_type == "config":
                backup_file = self.backup_dir / f"config_backup_{timestamp}.yaml"
                await self._create_config_backup(backup_file)
                
            elif backup_type == "full":
                backup_file = self.backup_dir / f"full_backup_{timestamp}.tar.gz"
                await self._create_full_backup(backup_file)
                
            else:
                raise ValueError(f"Unknown backup type: {backup_type}")
            
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise
    
    async def _create_database_backup(self, backup_file: Path):
        """Create database backup"""
        db_config = self.config.get('database', {})
        if not db_config:
            raise ValueError("Database configuration not found")
        
        # Create pg_dump command
        dump_cmd = [
            "pg_dump",
            "-h", db_config.get('host', 'localhost'),
            "-p", str(db_config.get('port', 5432)),
            "-U", db_config.get('user', 'postgres'),
            "-d", db_config.get('database', 'accessa_dev'),
            "-f", str(backup_file)
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.get('password', '')
        
        # Execute backup
        result = subprocess.run(
            dump_cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=600  # 10 minutes for database backup
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Database backup failed: {result.stderr}")
    
    async def _create_config_backup(self, backup_file: Path):
        """Create configuration backup"""
        config_file = Path("infrastructure/config/deployment_config.yaml")
        if not config_file.exists():
            raise FileNotFoundError("Deployment configuration file not found")
        
        shutil.copy2(config_file, backup_file)
    
    async def _create_full_backup(self, backup_file: Path):
        """Create full system backup"""
        # Create temporary backup directory
        temp_backup_dir = self.backup_dir / f"temp_backup_{int(time.time())}"
        temp_backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Backup key directories
            key_dirs = ["infrastructure", "backend", "api", "utils"]
            for dir_name in key_dirs:
                dir_path = project_root / dir_name
                if dir_path.exists():
                    shutil.copytree(dir_path, temp_backup_dir / dir_name)
            
            # Backup key files
            key_files = ["docker-compose.yml", "requirements.txt", "pyproject.toml"]
            for file_name in key_files:
                file_path = project_root / file_name
                if file_path.exists():
                    shutil.copy2(file_path, temp_backup_dir / file_name)
            
            # Create tar.gz archive
            shutil.make_archive(
                str(backup_file.with_suffix('')),
                'gztar',
                temp_backup_dir
            )
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_backup_dir)
    
    async def cleanup_old_backups(self):
        """Clean up old backup files based on retention policy"""
        try:
            backup_strategy = self.rollback_config.get('backup_strategy', {})
            max_backups = backup_strategy.get('max_backups', 10)
            retention_days = backup_strategy.get('backup_retention_days', 7)
            
            # Get all backup files
            backup_files = list(self.backup_dir.glob("*"))
            backup_files = [f for f in backup_files if f.is_file()]
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove old backups beyond retention period
            cutoff_time = time.time() - (retention_days * 24 * 3600)
            for backup_file in backup_files:
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file}")
            
            # Keep only the most recent backups within max_backups limit
            if len(backup_files) > max_backups:
                files_to_remove = backup_files[:-max_backups]
                for backup_file in files_to_remove:
                    backup_file.unlink()
                    logger.info(f"Removed excess backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def get_rollback_history(self) -> List[RollbackResult]:
        """Get rollback execution history"""
        return self.rollback_history.copy()
    
    async def generate_rollback_report(self) -> Dict[str, Any]:
        """Generate comprehensive rollback report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_rollbacks': len(self.rollback_history),
            'successful_rollbacks': len([r for r in self.rollback_history if r.overall_success]),
            'failed_rollbacks': len([r for r in self.rollback_history if not r.overall_success]),
            'recent_rollbacks': [r.to_dict() for r in self.rollback_history[-5:]],  # Last 5 rollbacks
            'backup_status': {
                'backup_directory': str(self.backup_dir),
                'backup_files': len(list(self.backup_dir.glob("*"))),
                'last_backup': self._get_last_backup_time()
            }
        }
        
        return report
    
    def _get_last_backup_time(self) -> Optional[str]:
        """Get timestamp of last backup"""
        try:
            backup_files = list(self.backup_dir.glob("*"))
            if not backup_files:
                return None
            
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            return datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat()
            
        except Exception:
            return None


async def main():
    """Main entry point for rollback system testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Rollback System")
    parser.add_argument("--config", default="infrastructure/config/deployment_config.yaml",
                       help="Path to deployment configuration file")
    parser.add_argument("--action", choices=["backup", "rollback", "status", "cleanup"],
                       default="status", help="Action to perform")
    parser.add_argument("--backup-type", choices=["database", "config", "full"],
                       default="full", help="Type of backup to create")
    parser.add_argument("--rollback-target", choices=["last_known_good", "docker_only", "database_only"],
                       default="last_known_good", help="Target state for rollback")
    parser.add_argument("--trigger-reason", default="Manual trigger",
                       help="Reason for rollback trigger")
    
    args = parser.parse_args()
    
    try:
        # Initialize rollback system
        rollback_system = AutomatedRollback(args.config)
        
        if args.action == "backup":
            # Create backup
            backup_file = await rollback_system.create_backup(args.backup_type)
            print(f"✅ Backup created: {backup_file}")
            
        elif args.action == "rollback":
            # Execute rollback
            rollback_result = await rollback_system.execute_rollback(
                args.trigger_reason, args.rollback_target
            )
            
            print(f"\n🔄 Rollback Execution Summary")
            print(f"=============================")
            print(f"Rollback ID: {rollback_result.rollback_id}")
            print(f"Trigger: {rollback_result.trigger_reason}")
            print(f"Success: {'✅' if rollback_result.overall_success else '❌'}")
            print(f"Actions: {rollback_result.actions_successful}/{rollback_result.actions_executed} successful")
            print(f"Duration: {rollback_result.duration_seconds:.2f} seconds")
            
        elif args.action == "status":
            # Show status
            report = await rollback_system.generate_rollback_report()
            
            print(f"\n📊 Rollback System Status")
            print(f"=========================")
            print(f"Total Rollbacks: {report['total_rollbacks']}")
            print(f"Successful: {report['successful_rollbacks']}")
            print(f"Failed: {report['failed_rollbacks']}")
            print(f"Backup Files: {report['backup_status']['backup_files']}")
            print(f"Last Backup: {report['backup_status']['last_backup'] or 'Never'}")
            
        elif args.action == "cleanup":
            # Clean up old backups
            await rollback_system.cleanup_old_backups()
            print("✅ Backup cleanup completed")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Rollback system operation failed: {e}")
        print(f"\n❌ Rollback system operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
