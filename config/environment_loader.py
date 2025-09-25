#!/usr/bin/env python3
"""
Environment Configuration Loader
Handles environment variable loading for different deployment environments:
- Local development: Loads from .env files
- Cloud deployment (staging/production): Uses environment variables directly from platform
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvironmentLoader:
    """Handles environment variable loading for different deployment contexts"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.is_cloud_deployment = self._detect_cloud_deployment()
        
    def _detect_cloud_deployment(self) -> bool:
        """Detect if we're running in a cloud deployment environment"""
        # Check for common cloud deployment indicators
        cloud_indicators = [
            'RENDER',  # Render platform
            'VERCEL',  # Vercel platform
            'HEROKU',  # Heroku platform
            'AWS_LAMBDA_FUNCTION_NAME',  # AWS Lambda
            'K_SERVICE',  # Google Cloud Run
            'DYNO',  # Heroku dyno
        ]
        
        return any(os.getenv(indicator) for indicator in cloud_indicators)
    
    def load_environment_variables(self) -> Dict[str, Any]:
        """
        Load environment variables based on deployment context
        
        Returns:
            Dict containing loaded environment variables
        """
        if self.is_cloud_deployment:
            return self._load_cloud_environment()
        else:
            return self._load_local_environment()
    
    def _load_cloud_environment(self) -> Dict[str, Any]:
        """Load environment variables from cloud platform (Render, Vercel, etc.)"""
        logger.info(f"Loading environment variables from cloud platform (environment: {self.environment})")
        
        # In cloud deployment, environment variables are already available
        # We just need to validate they exist
        required_vars = self._get_required_environment_variables()
        missing_vars = []
        
        for var_name in required_vars:
            if not os.getenv(var_name):
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables in cloud deployment: {', '.join(missing_vars)}")
        
        logger.info("Cloud environment variables validated successfully")
        return {var: os.getenv(var) for var in required_vars if os.getenv(var)}
    
    def _load_local_environment(self) -> Dict[str, Any]:
        """Load environment variables from .env files for local development"""
        logger.info(f"Loading environment variables from .env files (environment: {self.environment})")
        
        # Determine which .env file to load
        env_file = f".env.{self.environment}"
        
        if not os.path.exists(env_file):
            # Fallback to default .env file
            env_file = ".env"
            if not os.path.exists(env_file):
                raise FileNotFoundError(f"Environment file not found: {env_file} or .env.{self.environment}")
        
        # Load the environment file
        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from {env_file}")
        
        # Validate required variables
        required_vars = self._get_required_environment_variables()
        missing_vars = []
        
        for var_name in required_vars:
            if not os.getenv(var_name):
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables in local development: {', '.join(missing_vars)}")
        
        logger.info("Local environment variables validated successfully")
        return {var: os.getenv(var) for var in required_vars if os.getenv(var)}
    
    def _get_required_environment_variables(self) -> list:
        """Get list of required environment variables based on environment"""
        base_vars = [
            'ENVIRONMENT',
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY',
            'DATABASE_URL',
            'OPENAI_API_KEY',
            'LLAMAPARSE_API_KEY'
        ]
        
        if self.environment in ['staging', 'production']:
            # Additional variables for staging/production
            base_vars.extend([
                'SUPABASE_ANON_KEY',
                'ANTHROPIC_API_KEY',
                'LOG_LEVEL'
            ])
        
        return base_vars
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about the current environment configuration"""
        return {
            'environment': self.environment,
            'is_cloud_deployment': self.is_cloud_deployment,
            'platform': self._detect_platform(),
            'required_vars': self._get_required_environment_variables(),
            'loaded_vars': list(self.load_environment_variables().keys())
        }
    
    def _detect_platform(self) -> str:
        """Detect the cloud platform being used"""
        if os.getenv('RENDER'):
            return 'render'
        elif os.getenv('VERCEL'):
            return 'vercel'
        elif os.getenv('HEROKU'):
            return 'heroku'
        elif os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            return 'aws_lambda'
        elif os.getenv('K_SERVICE'):
            return 'google_cloud_run'
        else:
            return 'local'

# Global instance
environment_loader = EnvironmentLoader()

def load_environment() -> Dict[str, Any]:
    """Convenience function to load environment variables"""
    return environment_loader.load_environment_variables()

def get_environment_info() -> Dict[str, Any]:
    """Convenience function to get environment information"""
    return environment_loader.get_environment_info()
