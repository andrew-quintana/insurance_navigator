#!/usr/bin/env python3
"""
Environment Configuration Management
003 Worker Refactor - Phase 2

Manages and validates environment variables, configuration consistency,
and secrets management across all services.
"""

import os
import json
import logging
import re
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from cryptography.fernet import Fernet
import hashlib


@dataclass
class EnvironmentVariable:
    """Environment variable definition"""
    name: str
    value: str
    required: bool = True
    sensitive: bool = False
    validation_regex: Optional[str] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.value is None and self.default_value:
            self.value = self.default_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, masking sensitive values"""
        data = asdict(self)
        if self.sensitive and self.value:
            data['value'] = '***MASKED***'
        return data


@dataclass
class ConfigurationValidationResult:
    """Result of configuration validation"""
    service: str
    config_type: str
    valid: bool
    errors: List[str]
    warnings: List[str]
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SecretsConfig:
    """Secrets configuration"""
    encryption_key: Optional[str] = None
    key_file: Optional[str] = None
    rotation_interval_days: int = 90
    audit_logging: bool = True
    access_control: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.access_control is None:
            self.access_control = {}


class EnvironmentManager:
    """Environment configuration management system"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.encryption_key = None
        self.fernet = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption if configured
        self._initialize_encryption()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def _initialize_encryption(self):
        """Initialize encryption for secrets management"""
        try:
            secrets_config = self.config.get('secrets', {})
            
            if 'encryption_key' in secrets_config:
                self.encryption_key = secrets_config['encryption_key']
            elif 'key_file' in secrets_config:
                key_file = Path(secrets_config['key_file'])
                if key_file.exists():
                    with open(key_file, 'rb') as f:
                        self.encryption_key = f.read()
            
            if self.encryption_key:
                self.fernet = Fernet(self.encryption_key)
                self.logger.info("Encryption initialized successfully")
            else:
                self.logger.warning("No encryption key configured, secrets will not be encrypted")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
    
    def validate_environment_variables(self, service_name: str = None) -> List[ConfigurationValidationResult]:
        """Validate environment variables for all services or a specific service"""
        results = []
        
        if service_name:
            services = {service_name: self.config.get('services', {}).get(service_name, {})}
        else:
            services = self.config.get('services', {})
        
        for svc_name, svc_config in services.items():
            result = self._validate_service_environment(svc_name, svc_config)
            results.append(result)
        
        return results
    
    def _validate_service_environment(self, service_name: str, service_config: Dict[str, Any]) -> ConfigurationValidationResult:
        """Validate environment variables for a specific service"""
        errors = []
        warnings = []
        
        # Get required environment variables for this service
        required_env_vars = service_config.get('required_environment_variables', [])
        optional_env_vars = service_config.get('optional_environment_variables', [])
        
        # Check required environment variables
        for env_var in required_env_vars:
            if isinstance(env_var, str):
                var_name = env_var
                validation_regex = None
                sensitive = False
            else:
                var_name = env_var.get('name')
                validation_regex = env_var.get('validation_regex')
                sensitive = env_var.get('sensitive', False)
            
            # Check if variable exists
            if var_name not in os.environ:
                errors.append(f"Required environment variable '{var_name}' is not set")
                continue
            
            # Check if variable has a value
            value = os.environ[var_name]
            if not value:
                errors.append(f"Required environment variable '{var_name}' is empty")
                continue
            
            # Validate against regex if specified
            if validation_regex:
                if not re.match(validation_regex, value):
                    errors.append(f"Environment variable '{var_name}' does not match validation pattern")
            
            # Check for sensitive variables in logs
            if sensitive and value != '***MASKED***':
                warnings.append(f"Sensitive environment variable '{var_name}' is set (consider masking in logs)")
        
        # Check optional environment variables
        for env_var in optional_env_vars:
            if isinstance(env_var, str):
                var_name = env_var
            else:
                var_name = env_var.get('name')
            
            if var_name in os.environ:
                value = os.environ[var_name]
                if validation_regex := env_var.get('validation_regex'):
                    if not re.match(validation_regex, value):
                        warnings.append(f"Optional environment variable '{var_name}' does not match validation pattern")
        
        # Check for unexpected environment variables
        expected_vars = set()
        for env_var in required_env_vars + optional_env_vars:
            if isinstance(env_var, str):
                expected_vars.add(env_var)
            else:
                expected_vars.add(env_var.get('name'))
        
        unexpected_vars = set(os.environ.keys()) - expected_vars
        if unexpected_vars:
            warnings.append(f"Unexpected environment variables found: {', '.join(unexpected_vars)}")
        
        valid = len(errors) == 0
        
        return ConfigurationValidationResult(
            service=service_name,
            config_type="environment_variables",
            valid=valid,
            errors=errors,
            warnings=warnings,
            metadata={
                'required_vars': len(required_env_vars),
                'optional_vars': len(optional_env_vars),
                'unexpected_vars': len(unexpected_vars)
            }
        )
    
    def validate_configuration_consistency(self) -> List[ConfigurationValidationResult]:
        """Validate configuration consistency across services"""
        results = []
        
        # Check database configuration consistency
        db_result = self._validate_database_consistency()
        results.append(db_result)
        
        # Check service configuration consistency
        service_result = self._validate_service_consistency()
        results.append(service_result)
        
        # Check external service consistency
        external_result = self._validate_external_service_consistency()
        results.append(external_result)
        
        # Check security configuration consistency
        security_result = self._validate_security_consistency()
        results.append(security_result)
        
        return results
    
    def _validate_database_consistency(self) -> ConfigurationValidationResult:
        """Validate database configuration consistency"""
        errors = []
        warnings = []
        
        db_config = self.config.get('database', {})
        
        # Check if all required database fields are present
        required_fields = ['host', 'port', 'database', 'user']
        for field in required_fields:
            if field not in db_config:
                errors.append(f"Database configuration missing required field: {field}")
        
        # Check port number validity
        if 'port' in db_config:
            try:
                port = int(db_config['port'])
                if not (1 <= port <= 65535):
                    errors.append(f"Database port {port} is not valid (must be 1-65535)")
            except ValueError:
                errors.append(f"Database port '{db_config['port']}' is not a valid number")
        
        # Check for password security
        if 'password' in db_config and db_config['password']:
            if len(db_config['password']) < 8:
                warnings.append("Database password is shorter than recommended 8 characters")
        
        valid = len(errors) == 0
        
        return ConfigurationValidationResult(
            service="database",
            config_type="configuration_consistency",
            valid=valid,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_service_consistency(self) -> ConfigurationValidationResult:
        """Validate service configuration consistency"""
        errors = []
        warnings = []
        
        services = self.config.get('services', {})
        
        # Check for port conflicts
        used_ports = set()
        for service_name, service_config in services.items():
            port = service_config.get('port')
            if port:
                if port in used_ports:
                    errors.append(f"Port {port} is used by multiple services")
                else:
                    used_ports.add(port)
        
        # Check for host consistency
        hosts = set()
        for service_name, service_config in services.items():
            host = service_config.get('host', 'localhost')
            hosts.add(host)
        
        if len(hosts) > 1:
            warnings.append(f"Services are distributed across {len(hosts)} different hosts: {', '.join(hosts)}")
        
        # Check for health endpoint consistency
        for service_name, service_config in services.items():
            if 'health_endpoint' not in service_config:
                warnings.append(f"Service '{service_name}' does not have a health endpoint configured")
        
        valid = len(errors) == 0
        
        return ConfigurationValidationResult(
            service="services",
            config_type="configuration_consistency",
            valid=valid,
            errors=errors,
            warnings=warnings,
            metadata={
                'total_services': len(services),
                'unique_hosts': len(hosts),
                'unique_ports': len(used_ports)
            }
        )
    
    def _validate_external_service_consistency(self) -> ConfigurationValidationResult:
        """Validate external service configuration consistency"""
        errors = []
        warnings = []
        
        external_services = self.config.get('external_services', {})
        
        # Check LlamaParse configuration
        if 'llamaparse' in external_services:
            llamaparse_config = external_services['llamaparse']
            if 'api_key' not in llamaparse_config:
                warnings.append("LlamaParse service configured but no API key provided")
        
        # Check OpenAI configuration
        if 'openai' in external_services:
            openai_config = external_services['openai']
            if 'api_key' not in openai_config:
                warnings.append("OpenAI service configured but no API key provided")
            
            # Check rate limiting configuration
            if 'rate_limit' in openai_config:
                rate_limit = openai_config['rate_limit']
                if rate_limit.get('requests_per_minute', 0) > 1000:
                    warnings.append("OpenAI rate limit is set very high, consider reviewing")
        
        valid = len(errors) == 0
        
        return ConfigurationValidationResult(
            service="external_services",
            config_type="configuration_consistency",
            valid=valid,
            errors=errors,
            warnings=warnings,
            metadata={
                'total_external_services': len(external_services),
                'configured_services': list(external_services.keys())
            }
        )
    
    def _validate_security_consistency(self) -> ConfigurationValidationResult:
        """Validate security configuration consistency"""
        errors = []
        warnings = []
        
        security_config = self.config.get('security', {})
        
        # Check CORS configuration
        cors_config = security_config.get('cors', {})
        if cors_config:
            allowed_origins = cors_config.get('allowed_origins', [])
            if '*' in allowed_origins:
                warnings.append("CORS allows all origins (*), consider restricting for production")
            
            if not allowed_origins:
                warnings.append("CORS allowed origins is empty, requests may be blocked")
        
        # Check authentication configuration
        auth_config = security_config.get('authentication', {})
        if auth_config:
            if not auth_config.get('enabled', False):
                warnings.append("Authentication is disabled, consider enabling for production")
            
            if auth_config.get('enabled', False) and not auth_config.get('secret_key'):
                errors.append("Authentication enabled but no secret key configured")
        
        # Check encryption configuration
        if not self.encryption_key:
            warnings.append("No encryption key configured for secrets management")
        
        valid = len(errors) == 0
        
        return ConfigurationValidationResult(
            service="security",
            config_type="configuration_consistency",
            valid=valid,
            errors=errors,
            warnings=warnings
        )
    
    def validate_environment_parity(self, target_environment: str) -> ConfigurationValidationResult:
        """Validate environment parity between local and target environment"""
        errors = []
        warnings = []
        
        # Load target environment configuration
        target_config_path = self.config_path.parent / f"deployment_config_{target_environment}.yaml"
        
        if not target_config_path.exists():
            errors.append(f"Target environment configuration not found: {target_config_path}")
            return ConfigurationValidationResult(
                service="environment_parity",
                config_type="parity_validation",
                valid=False,
                errors=errors,
                warnings=warnings
            )
        
        try:
            with open(target_config_path, 'r') as f:
                target_config = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"Failed to load target environment configuration: {e}")
            return ConfigurationValidationResult(
                service="environment_parity",
                config_type="parity_validation",
                valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Compare database configurations
        local_db = self.config.get('database', {})
        target_db = target_config.get('database', {})
        
        if local_db.get('host') != target_db.get('host'):
            warnings.append(f"Database host differs: local={local_db.get('host')}, target={target_db.get('host')}")
        
        if local_db.get('port') != target_db.get('port'):
            warnings.append(f"Database port differs: local={local_db.get('port')}, target={target_db.get('port')}")
        
        # Compare service configurations
        local_services = self.config.get('services', {})
        target_services = target_config.get('services', {})
        
        # Check for missing services in target
        missing_services = set(local_services.keys()) - set(target_services.keys())
        if missing_services:
            errors.append(f"Services missing in target environment: {', '.join(missing_services)}")
        
        # Check for additional services in target
        additional_services = set(target_services.keys()) - set(local_services.keys())
        if additional_services:
            warnings.append(f"Additional services in target environment: {', '.join(additional_services)}")
        
        # Compare common service configurations
        common_services = set(local_services.keys()) & set(target_services.keys())
        for service_name in common_services:
            local_service = local_services[service_name]
            target_service = target_services[service_name]
            
            if local_service.get('port') != target_service.get('port'):
                warnings.append(f"Service '{service_name}' port differs: local={local_service.get('port')}, target={target_service.get('port')}")
        
        valid = len(errors) == 0
        
        return ConfigurationValidationResult(
            service="environment_parity",
            config_type="parity_validation",
            valid=valid,
            errors=errors,
            warnings=warnings,
            metadata={
                'target_environment': target_environment,
                'common_services': len(common_services),
                'missing_services': len(missing_services),
                'additional_services': len(additional_services)
            }
        )
    
    def manage_secrets(self, action: str, secret_name: str, secret_value: str = None) -> Dict[str, Any]:
        """Manage secrets (encrypt, decrypt, rotate)"""
        try:
            if action == "encrypt":
                if not self.fernet:
                    return {"success": False, "error": "Encryption not initialized"}
                
                encrypted_value = self.fernet.encrypt(secret_value.encode())
                return {
                    "success": True,
                    "encrypted_value": encrypted_value.decode(),
                    "secret_name": secret_name
                }
            
            elif action == "decrypt":
                if not self.fernet:
                    return {"success": False, "error": "Encryption not initialized"}
                
                decrypted_value = self.fernet.decrypt(secret_value.encode())
                return {
                    "success": True,
                    "decrypted_value": decrypted_value.decode(),
                    "secret_name": secret_name
                }
            
            elif action == "rotate":
                # Generate new encryption key
                new_key = Fernet.generate_key()
                new_fernet = Fernet(new_key)
                
                # Re-encrypt existing secrets with new key
                # This is a simplified implementation
                return {
                    "success": True,
                    "new_key": new_key.decode(),
                    "message": "New encryption key generated"
                }
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_environment_report(self) -> Dict[str, Any]:
        """Generate comprehensive environment report"""
        # Validate all configurations
        env_validation = self.validate_environment_variables()
        consistency_validation = self.validate_configuration_consistency()
        
        # Calculate overall status
        all_results = env_validation + consistency_validation
        total_checks = len(all_results)
        passed_checks = sum(1 for result in all_results if result.valid)
        
        overall_valid = passed_checks == total_checks
        
        # Collect all errors and warnings
        all_errors = []
        all_warnings = []
        
        for result in all_results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_valid": overall_valid,
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": total_checks - passed_checks,
                "total_errors": len(all_errors),
                "total_warnings": len(all_warnings)
            },
            "validation_results": [result.to_dict() for result in all_results],
            "errors": all_errors,
            "warnings": all_warnings,
            "environment_info": {
                "python_version": os.sys.version,
                "platform": os.sys.platform,
                "environment_variables_count": len(os.environ),
                "config_file": str(self.config_path)
            }
        }
    
    def save_environment_report(self, filename: str = None) -> str:
        """Save environment report to file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"environment_report_{timestamp}.json"
        
        report = self.generate_environment_report()
        
        # Ensure reports directory exists
        reports_dir = Path("infrastructure/validation/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reports_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(report_path)


async def main():
    """Main function for testing"""
    env_manager = EnvironmentManager("infrastructure/config/deployment_config.yaml")
    
    try:
        print("🔧 Environment Configuration Management")
        print("=" * 50)
        
        # Validate environment variables
        print("\n📋 Validating environment variables...")
        env_validation = env_manager.validate_environment_variables()
        
        for result in env_validation:
            status_icon = "✅" if result.valid else "❌"
            print(f"  {status_icon} {result.service}: {result.valid}")
            if result.errors:
                for error in result.errors:
                    print(f"    ❌ {error}")
            if result.warnings:
                for warning in result.warnings:
                    print(f"    ⚠️  {warning}")
        
        # Validate configuration consistency
        print("\n🔗 Validating configuration consistency...")
        consistency_validation = env_manager.validate_configuration_consistency()
        
        for result in consistency_validation:
            status_icon = "✅" if result.valid else "❌"
            print(f"  {status_icon} {result.service}: {result.valid}")
            if result.errors:
                for error in result.errors:
                    print(f"    ❌ {error}")
            if result.warnings:
                for warning in result.warnings:
                    print(f"    ⚠️  {warning}")
        
        # Generate and save report
        print("\n📊 Generating environment report...")
        report_path = env_manager.save_environment_report()
        print(f"  📄 Report saved to: {report_path}")
        
        # Test secrets management
        print("\n🔐 Testing secrets management...")
        test_secret = "test_secret_value"
        
        if env_manager.fernet:
            # Test encryption
            encrypt_result = env_manager.manage_secrets("encrypt", "test_secret", test_secret)
            if encrypt_result["success"]:
                print("  ✅ Encryption working")
                
                # Test decryption
                decrypt_result = env_manager.manage_secrets("decrypt", "test_secret", encrypt_result["encrypted_value"])
                if decrypt_result["success"] and decrypt_result["decrypted_value"] == test_secret:
                    print("  ✅ Decryption working")
                else:
                    print("  ❌ Decryption failed")
            else:
                print(f"  ❌ Encryption failed: {encrypt_result['error']}")
        else:
            print("  ⚠️  Encryption not available")
        
        print("\n🎯 Environment validation complete!")
        
    except Exception as e:
        print(f"💥 Environment validation failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
