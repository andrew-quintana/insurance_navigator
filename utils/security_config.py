"""
Security configuration module for Insurance Navigator
Centralizes all security-related settings and provides secure access to credentials.

Configuration Priority (highest to lowest):
1. Environment variables (.env file)
2. Configuration file (config/config.yaml) 
3. Default values

Security Settings via Environment Variables:
- JWT_SECRET_KEY: Secret key for JWT token signing (REQUIRED for production)
- JWT_ALGORITHM: Algorithm for JWT tokens (default: HS256)
- JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time (default: 30)
- SECURITY_VALIDATE_INPUTS: Enable input validation (default: true)
- SECURITY_SANITIZE_OUTPUTS: Enable output sanitization (default: true) 
- SECURITY_MAX_TOKEN_LIMIT: Maximum token limit (default: 4096)

This approach follows security best practices by:
- Keeping secrets in environment variables (not version control)
- Allowing environment-specific configuration
- Providing safe fallbacks for development
"""

import os
import yaml
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Centralized security configuration management"""
    
    def __init__(self):
        self._jwt_secret_key: Optional[str] = None
        self._config_data: Optional[Dict[str, Any]] = None
        self._load_config()
        
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            # Look for config.yaml in the config directory
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 
                'config.yaml'
            )
            with open(config_path, 'r') as file:
                self._config_data = yaml.safe_load(file)
        except Exception as e:
            logger.warning(f"Could not load config.yaml: {e}. Using defaults.")
            self._config_data = {}
        
    @property
    def jwt_secret_key(self) -> str:
        """
        Get JWT secret key from environment variable
        Falls back to development key if not set (not recommended for production)
        """
        if self._jwt_secret_key is None:
            # Try to get from environment first (production approach)
            self._jwt_secret_key = os.getenv("JWT_SECRET_KEY")
            
            if self._jwt_secret_key is None:
                # Development fallback - warn about security risk
                self._jwt_secret_key = "your-secret-key-change-in-production"
                logger.warning(
                    "🚨 SECURITY WARNING: Using default JWT secret key. "
                    "Set JWT_SECRET_KEY environment variable for production!"
                )
                
        return self._jwt_secret_key
    
    @property 
    def jwt_algorithm(self) -> str:
        """Get JWT algorithm from environment variable or configuration"""
        # Prioritize environment variable over config file
        env_algorithm = os.getenv("JWT_ALGORITHM")
        if env_algorithm:
            return env_algorithm
            
        try:
            return self._config_data.get("authentication", {}).get("jwt", {}).get("algorithm", "HS256")
        except Exception:
            logger.warning("Could not load JWT algorithm from config, using default HS256")
            return "HS256"
    
    @property
    def access_token_expire_minutes(self) -> int:
        """Get access token expiration time from environment variable or configuration"""
        # Prioritize environment variable over config file
        env_expire = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
        if env_expire:
            try:
                return int(env_expire)
            except ValueError:
                logger.warning(f"Invalid JWT_ACCESS_TOKEN_EXPIRE_MINUTES value: {env_expire}")
                
        try:
            return self._config_data.get("authentication", {}).get("jwt", {}).get("access_token_expire_minutes", 30)
        except Exception:
            logger.warning("Could not load token expiration from config, using default 30 minutes")
            return 30
    
    @property
    def validate_inputs(self) -> bool:
        """Get input validation setting from environment variable or configuration"""
        # Prioritize environment variable over config file
        env_validate = os.getenv("SECURITY_VALIDATE_INPUTS")
        if env_validate:
            return env_validate.lower() in ('true', '1', 'yes', 'on')
            
        try:
            return self._config_data.get("security", {}).get("validate_inputs", True)
        except Exception:
            return True
    
    @property
    def sanitize_outputs(self) -> bool:
        """Get output sanitization setting from environment variable or configuration"""
        # Prioritize environment variable over config file
        env_sanitize = os.getenv("SECURITY_SANITIZE_OUTPUTS")
        if env_sanitize:
            return env_sanitize.lower() in ('true', '1', 'yes', 'on')
            
        try:
            return self._config_data.get("security", {}).get("sanitize_outputs", True)
        except Exception:
            return True
    
    @property
    def max_token_limit(self) -> int:
        """Get maximum token limit from environment variable or configuration"""
        # Prioritize environment variable over config file
        env_limit = os.getenv("SECURITY_MAX_TOKEN_LIMIT")
        if env_limit:
            try:
                return int(env_limit)
            except ValueError:
                logger.warning(f"Invalid SECURITY_MAX_TOKEN_LIMIT value: {env_limit}")
                
        try:
            return self._config_data.get("security", {}).get("max_token_limit", 4096)
        except Exception:
            return 4096
    
    @property
    def blocked_patterns(self) -> list:
        """Get list of blocked patterns for prompt injection detection"""
        try:
            return self._config_data.get("security", {}).get("blocked_patterns", [])
        except Exception:
            return [
                'ignore previous instructions',
                'disregard all instructions', 
                'system prompt'
            ]

# Global security config instance
_security_config = None

def get_security_config() -> SecurityConfig:
    """Get the global security configuration instance"""
    global _security_config
    if _security_config is None:
        _security_config = SecurityConfig()
    return _security_config 