#!/usr/bin/env python3
"""
Configuration Validation Script for 003 Worker Refactor

This script validates deployment configuration against local environment baseline
to ensure configuration consistency and prevent deployment failures.
"""

import yaml
import os
import sys
from typing import Dict, List, Any, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Validate deployment configuration against local baseline"""
    
    def __init__(self, local_config_path: str, deployment_config_path: str):
        """Initialize validator with local and deployment config paths"""
        self.local_config_path = local_config_path
        self.deployment_config_path = deployment_config_path
        self.local_config = None
        self.deployment_config = None
        self.validation_results = {}
        
    def load_configurations(self) -> bool:
        """Load both configuration files"""
        try:
            # Load local configuration
            with open(self.local_config_path, 'r') as f:
                self.local_config = yaml.safe_load(f)
            logger.info(f"Loaded local configuration from {self.local_config_path}")
            
            # Load deployment configuration
            with open(self.deployment_config_path, 'r') as f:
                self.deployment_config = yaml.safe_load(f)
            logger.info(f"Loaded deployment configuration from {self.deployment_config_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            return False
    
    def validate_configuration_structure(self) -> Dict[str, bool]:
        """Validate that both configurations have the same structure"""
        logger.info("Validating configuration structure")
        
        results = {}
        
        # Check top-level sections
        local_sections = set(self.local_config.keys())
        deployment_sections = set(self.deployment_config.keys())
        
        missing_in_deployment = local_sections - deployment_sections
        extra_in_deployment = deployment_sections - local_sections
        
        if missing_in_deployment:
            logger.error(f"Missing sections in deployment config: {missing_in_deployment}")
            results["structure"] = False
        elif extra_in_deployment:
            logger.warning(f"Extra sections in deployment config: {extra_in_deployment}")
            results["structure"] = True  # Warning but not failure
        else:
            results["structure"] = True
        
        # Validate each section structure
        for section in local_sections:
            if section in self.deployment_config:
                section_valid = self._validate_section_structure(
                    section, 
                    self.local_config[section], 
                    self.deployment_config[section]
                )
                results[f"section_{section}"] = section_valid
        
        return results
    
    def _validate_section_structure(self, section_name: str, local_section: Dict, 
                                  deployment_section: Dict) -> bool:
        """Validate structure of a specific configuration section"""
        try:
            # Recursively check nested structure
            return self._compare_config_structure(local_section, deployment_section)
        except Exception as e:
            logger.error(f"Error validating section {section_name}: {e}")
            return False
    
    def _compare_config_structure(self, local_config: Any, deployment_config: Any) -> bool:
        """Recursively compare configuration structure"""
        if type(local_config) != type(deployment_config):
            return False
        
        if isinstance(local_config, dict):
            local_keys = set(local_config.keys())
            deployment_keys = set(deployment_config.keys())
            
            # Check if deployment has all required keys
            missing_keys = local_keys - deployment_keys
            if missing_keys:
                logger.error(f"Missing keys in deployment config: {missing_keys}")
                return False
            
            # Recursively validate nested structures
            for key in local_keys:
                if not self._compare_config_structure(local_config[key], deployment_config[key]):
                    return False
            
            return True
        
        elif isinstance(local_config, list):
            if len(local_config) != len(deployment_config):
                return False
            
            # For lists, check if all elements have the same structure
            for local_item, deployment_item in zip(local_config, deployment_config):
                if not self._compare_config_structure(local_item, deployment_item):
                    return False
            
            return True
        
        else:
            # For primitive types, just check if they exist
            return True
    
    def validate_environment_variables(self) -> Dict[str, bool]:
        """Validate that required environment variables are configured"""
        logger.info("Validating environment variable configuration")
        
        results = {}
        
        # Extract environment variables from deployment config
        deployment_env_vars = self._extract_environment_variables(self.deployment_config)
        local_env_vars = self._extract_environment_variables(self.local_config)
        
        # Check for missing environment variables
        missing_vars = local_env_vars - deployment_env_vars
        if missing_vars:
            logger.error(f"Missing environment variables in deployment: {missing_vars}")
            results["env_vars_complete"] = False
        else:
            results["env_vars_complete"] = True
        
        # Check for extra environment variables (warnings)
        extra_vars = deployment_env_vars - local_env_vars
        if extra_vars:
            logger.warning(f"Extra environment variables in deployment: {extra_vars}")
        
        # Validate environment variable formats
        results["env_var_formats"] = self._validate_env_var_formats(deployment_env_vars)
        
        return results
    
    def _extract_environment_variables(self, config: Any) -> set:
        """Recursively extract environment variable references from config"""
        env_vars = set()
        
        if isinstance(config, dict):
            for value in config.values():
                env_vars.update(self._extract_environment_variables(value))
        elif isinstance(config, list):
            for item in config:
                env_vars.update(self._extract_environment_variables(item))
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]  # Remove ${ and }
            env_vars.add(env_var)
        
        return env_vars
    
    def _validate_env_var_formats(self, env_vars: set) -> bool:
        """Validate environment variable format consistency"""
        for env_var in env_vars:
            if not env_var.isupper() and not env_var.startswith("STAGING_"):
                logger.warning(f"Environment variable {env_var} should be uppercase")
                # Not a failure, just a warning
        
        return True
    
    def validate_deployment_specific_settings(self) -> Dict[str, bool]:
        """Validate deployment-specific configuration settings"""
        logger.info("Validating deployment-specific settings")
        
        results = {}
        
        # Check deployment platform configuration
        local_platform = self.local_config.get("deployment", {}).get("platform")
        deployment_platform = self.deployment_config.get("deployment", {}).get("platform")
        
        if local_platform == deployment_platform:
            logger.warning("Deployment platform should be different from local")
            results["platform_differentiation"] = False
        else:
            results["platform_differentiation"] = True
        
        # Check resource allocation differences
        local_workers = self.local_config.get("api", {}).get("workers", 1)
        deployment_workers = self.deployment_config.get("api", {}).get("workers", 1)
        
        if deployment_workers <= local_workers:
            logger.warning("Deployment should have more workers than local environment")
            results["resource_scaling"] = False
        else:
            results["resource_scaling"] = True
        
        # Check security settings
        local_security = self.local_config.get("security", {})
        deployment_security = self.deployment_config.get("security", {})
        
        # Security should be more restrictive in deployment
        local_rate_limiting = local_security.get("rate_limiting", {}).get("enabled", False)
        deployment_rate_limiting = deployment_security.get("rate_limiting", {}).get("enabled", False)
        
        if not deployment_rate_limiting and local_rate_limiting:
            logger.warning("Deployment should have rate limiting enabled")
            results["security_enhancement"] = False
        else:
            results["security_enhancement"] = True
        
        return results
    
    def validate_configuration_consistency(self) -> Dict[str, bool]:
        """Validate overall configuration consistency"""
        logger.info("Validating configuration consistency")
        
        results = {}
        
        # Check for configuration drift
        drift_detected = self._detect_configuration_drift()
        results["no_drift"] = not drift_detected
        
        # Check for configuration completeness
        completeness = self._check_configuration_completeness()
        results["complete"] = completeness
        
        return results
    
    def _detect_configuration_drift(self) -> bool:
        """Detect configuration drift between local and deployment"""
        drift_detected = False
        
        # Check for significant differences in critical settings
        critical_sections = ["database", "api", "worker", "storage"]
        
        for section in critical_sections:
            if section in self.local_config and section in self.deployment_config:
                local_section = self.local_config[section]
                deployment_section = self.deployment_config[section]
                
                # Check for missing critical keys
                critical_keys = list(local_section.keys())
                for key in critical_keys:
                    if key not in deployment_section:
                        logger.error(f"Critical configuration missing in deployment: {section}.{key}")
                        drift_detected = True
        
        return drift_detected
    
    def _check_configuration_completeness(self) -> bool:
        """Check if deployment configuration is complete"""
        required_sections = ["database", "api", "worker", "storage", "external"]
        
        for section in required_sections:
            if section not in self.deployment_config:
                logger.error(f"Required section missing: {section}")
                return False
            
            section_config = self.deployment_config[section]
            if not section_config:
                logger.error(f"Section {section} is empty")
                return False
        
        return True
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete configuration validation"""
        logger.info("Starting complete configuration validation")
        
        # Load configurations
        if not self.load_configurations():
            return {"success": False, "error": "Failed to load configurations"}
        
        # Run all validation checks
        self.validation_results = {}
        
        self.validation_results["structure"] = self.validate_configuration_structure()
        self.validation_results["environment"] = self.validate_environment_variables()
        self.validation_results["deployment"] = self.validate_deployment_specific_settings()
        self.validation_results["consistency"] = self.validate_configuration_consistency()
        
        # Calculate overall success
        all_passed = True
        for category, results in self.validation_results.items():
            if isinstance(results, dict):
                for check, passed in results.items():
                    if not passed:
                        all_passed = False
            else:
                if not results:
                    all_passed = False
        
        self.validation_results["overall_success"] = all_passed
        
        return self.validation_results
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        if not self.validation_results:
            return "No validation results available"
        
        report = []
        report.append("=" * 60)
        report.append("CONFIGURATION VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Local Config: {self.local_config_path}")
        report.append(f"Deployment Config: {self.deployment_config_path}")
        report.append("")
        
        # Structure validation
        report.append("Configuration Structure:")
        report.append("-" * 30)
        structure_results = self.validation_results.get("structure", {})
        for check, passed in structure_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"{check:25} {status}")
        
        report.append("")
        
        # Environment variables
        report.append("Environment Variables:")
        report.append("-" * 30)
        env_results = self.validation_results.get("environment", {})
        for check, passed in env_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"{check:25} {status}")
        
        report.append("")
        
        # Deployment settings
        report.append("Deployment Settings:")
        report.append("-" * 30)
        deployment_results = self.validation_results.get("deployment", {})
        for check, passed in deployment_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"{check:25} {status}")
        
        report.append("")
        
        # Consistency
        report.append("Configuration Consistency:")
        report.append("-" * 30)
        consistency_results = self.validation_results.get("consistency", {})
        for check, passed in consistency_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"{check:25} {status}")
        
        report.append("")
        report.append("-" * 60)
        
        # Overall result
        overall_success = self.validation_results.get("overall_success", False)
        if overall_success:
            report.append("🎯 OVERALL RESULT: CONFIGURATION VALIDATION PASSED")
            report.append("✅ Deployment configuration is consistent with local baseline")
        else:
            report.append("🚨 OVERALL RESULT: CONFIGURATION VALIDATION FAILED")
            report.append("❌ Configuration issues need to be resolved before deployment")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main CLI entry point"""
    if len(sys.argv) != 3:
        print("Usage: python config_validator.py <local_config.yaml> <deployment_config.yaml>")
        print("Example: python config_validator.py config/local.yaml config/production.yaml")
        sys.exit(1)
    
    local_config_path = sys.argv[1]
    deployment_config_path = sys.argv[2]
    
    # Check if files exist
    if not os.path.exists(local_config_path):
        print(f"❌ Local configuration file not found: {local_config_path}")
        sys.exit(1)
    
    if not os.path.exists(deployment_config_path):
        print(f"❌ Deployment configuration file not found: {deployment_config_path}")
        sys.exit(1)
    
    try:
        validator = ConfigurationValidator(local_config_path, deployment_config_path)
        results = validator.run_complete_validation()
        
        if results.get("success") is False:
            print(f"❌ Validation failed: {results.get('error')}")
            sys.exit(1)
        
        # Generate and display report
        report = validator.generate_validation_report()
        print(report)
        
        # Exit with appropriate code
        if results.get("overall_success"):
            print("✅ Configuration validation passed!")
            sys.exit(0)
        else:
            print("❌ Configuration validation failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        logger.exception("Configuration validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
